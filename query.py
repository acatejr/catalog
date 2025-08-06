import os
import sys
import click
import psycopg2
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import requests
from dotenv import load_dotenv

load_dotenv()

# Database connection setup
dbname = os.environ.get("PG_DBNAME") or "postgres"
dbuser = os.environ.get("POSTGRES_USER")
dbpass = os.environ.get("POSTGRES_PASSWORD")
pg_connection_string = f"dbname={dbname} user={dbuser} password={dbpass} host='0.0.0.0'"

# Initialize console for rich output
console = Console()


def get_query_embedding(
    query: str, model_name: str = "all-MiniLM-L6-v2"
) -> List[float]:
    """Generate embedding for the query text."""
    model = SentenceTransformer(model_name)
    embedding = model.encode(query)
    return embedding.tolist()


def get_keyword_frequencies(
    top_k: int = 20, data_source: Optional[str] = None
) -> List[Dict]:
    """
    Get the most frequent keywords from all documents.
    """
    with psycopg2.connect(pg_connection_string) as conn:
        cur = conn.cursor()

        # Build query to unnest keywords array and count frequencies
        query = """
        SELECT
            keyword,
            COUNT(*) as frequency
        FROM (
            SELECT unnest(keywords) as keyword
            FROM documents
            WHERE keywords IS NOT NULL
            AND array_length(keywords, 1) > 0
        """

        params = []
        if data_source:
            query += " AND data_source = %s"
            params.append(data_source)

        query += """
        ) as keywords_unnested
        GROUP BY keyword
        ORDER BY frequency DESC
        LIMIT %s
        """
        params.append(top_k)

        cur.execute(query, params)

        results = []
        for row in cur.fetchall():
            results.append({"keyword": row[0], "frequency": row[1]})

        cur.close()
        return results


def get_duplicate_titles(
    data_source: Optional[str] = None, min_occurrences: int = 2
) -> List[Dict]:
    """
    Get documents with duplicate titles.
    """
    with psycopg2.connect(pg_connection_string) as conn:
        cur = conn.cursor()

        # Build query to find duplicate titles
        query = """
        SELECT
            title,
            COUNT(*) as count,
            array_agg(DISTINCT doc_id) as doc_ids,
            array_agg(DISTINCT data_source) as sources
        FROM documents
        WHERE title IS NOT NULL AND title != ''
        """

        params = []
        if data_source:
            query += " AND data_source = %s"
            params.append(data_source)

        query += """
        GROUP BY title
        HAVING COUNT(*) >= %s
        ORDER BY COUNT(*) DESC, title
        """
        params.append(min_occurrences)

        cur.execute(query, params)

        results = []
        for row in cur.fetchall():
            results.append(
                {"title": row[0], "count": row[1], "doc_ids": row[2], "sources": row[3]}
            )

        cur.close()
        return results


def search_similar_documents(
    query_embedding: List[float],
    top_k: int = 5,
    data_source: Optional[str] = None,
    threshold: float = 0.5,
) -> List[Dict]:
    """
    Search for similar documents using vector similarity.
    Uses cosine similarity (1 - cosine distance).
    """
    with psycopg2.connect(pg_connection_string) as conn:
        cur = conn.cursor()

        # Build the query with optional filters
        base_query = """
        SELECT
            id,
            doc_id,
            title,
            description,
            chunk_text,
            chunk_index,
            data_source,
            keywords,
            1 - (embedding <=> %s::vector) as similarity
        FROM documents
        WHERE 1=1
        """

        params = [query_embedding]

        if data_source:
            base_query += " AND data_source = %s"
            params.append(data_source)

        base_query += """
        AND 1 - (embedding <=> %s::vector) > %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
        params.extend([query_embedding, threshold, query_embedding, top_k])

        cur.execute(base_query, params)

        results = []
        for row in cur.fetchall():
            results.append(
                {
                    "id": row[0],
                    "doc_id": row[1],
                    "title": row[2],
                    "description": row[3],
                    "chunk_text": row[4],
                    "chunk_index": row[5],
                    "data_source": row[6],
                    "keywords": row[7],
                    "similarity": row[8],
                }
            )

        cur.close()
        return results


def query_llm(query: str, context: List[Dict], model: str = "ollama/llama3.1") -> str:
    """
    Query the LLM with the user's question and retrieved context.
    Uses LiteLLM proxy for Ollama.
    """
    # Prepare context from retrieved documents
    context_text = "\n\n".join(
        [
            f"Document {i + 1} (Similarity: {doc['similarity']:.3f}):\n"
            f"Title: {doc['title']}\n"
            f"Description: {doc['description']}\n"
            f"Content: {doc['chunk_text']}\n"
            f"Keywords: {', '.join(doc['keywords']) if doc['keywords'] else 'None'}"
            for i, doc in enumerate(context)
        ]
    )

    # Construct the prompt
    prompt = f"""You are a helpful assistant that answers questions based on the provided context.
Use the following documents to answer the user's question. If the answer cannot be found in the context, say so.

Context:
{context_text}

User Question: {query}

Please provide a comprehensive answer based on the above context. Include relevant details and cite which documents you're drawing information from."""

    # Call LiteLLM proxy
    litellm_url = os.environ.get("LITELLM_URL", "http://localhost:4000")

    try:
        response = requests.post(
            f"{litellm_url}/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('LITELLM_MASTER_KEY', '')}",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based on provided context.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 1000,
            },
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"Error querying LLM: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Error connecting to LLM: {str(e)}"


def display_keyword_frequencies(
    keywords: List[Dict], data_source: Optional[str] = None
):
    """Display keyword frequencies in a formatted table."""
    title = "Most Frequent Keywords"
    if data_source:
        title += f" (Source: {data_source})"

    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="cyan", width=6)
    table.add_column("Keyword", style="green", width=40)
    table.add_column("Frequency", style="yellow", width=10)

    for i, item in enumerate(keywords):
        table.add_row(str(i + 1), item["keyword"], str(item["frequency"]))

    console.print(table)


def display_duplicate_titles(duplicates: List[Dict], data_source: Optional[str] = None):
    """Display duplicate titles in a formatted table."""
    title = "Documents with Duplicate Titles"
    if data_source:
        title += f" (Source: {data_source})"

    if not duplicates:
        console.print("[yellow]No duplicate titles found.[/yellow]")
        return

    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Title", style="green", width=50)
    table.add_column("Count", style="yellow", width=8)
    table.add_column("Document IDs", style="cyan", width=40)
    table.add_column("Sources", style="blue", width=20)

    for item in duplicates:
        # Format document IDs and sources for display
        doc_ids_str = ", ".join(item["doc_ids"][:3])
        if len(item["doc_ids"]) > 3:
            doc_ids_str += f" ... (+{len(item['doc_ids']) - 3} more)"

        sources_str = ", ".join(set(item["sources"]))

        table.add_row(
            item["title"][:50] + "..." if len(item["title"]) > 50 else item["title"],
            str(item["count"]),
            doc_ids_str,
            sources_str,
        )

    console.print(table)
    console.print(f"\n[bold]Total duplicate titles found: {len(duplicates)}[/bold]")


def display_results(query: str, results: List[Dict], llm_response: str):
    """Display search results and LLM response in a formatted way."""
    console.print(f"\n[bold blue]Query:[/bold blue] {query}\n")

    # Display retrieved documents
    if results:
        table = Table(
            title="Retrieved Documents", show_header=True, header_style="bold magenta"
        )
        table.add_column("Rank", style="cyan", width=6)
        table.add_column("Title", style="green", width=40)
        table.add_column("Similarity", style="yellow", width=10)
        table.add_column("Source", style="blue", width=15)

        for i, doc in enumerate(results):
            table.add_row(
                str(i + 1),
                doc["title"][:40] + "..." if len(doc["title"]) > 40 else doc["title"],
                f"{doc['similarity']:.3f}",
                doc["data_source"] or "Unknown",
            )

        console.print(table)
        console.print()

        # Display LLM response
        console.print(
            Panel(
                llm_response,
                title="[bold green]AI Response[/bold green]",
                border_style="green",
            )
        )

        # Display detailed results if requested
        console.print("\n[bold]Detailed Results:[/bold]")
        for i, doc in enumerate(results):
            console.print(f"\n[bold cyan]Document {i + 1}:[/bold cyan]")
            console.print(f"[yellow]Title:[/yellow] {doc['title']}")
            console.print(f"[yellow]Description:[/yellow] {doc['description']}")
            console.print(f"[yellow]Chunk:[/yellow] {doc['chunk_text']}")
            console.print(
                f"[yellow]Keywords:[/yellow] {', '.join(doc['keywords']) if doc['keywords'] else 'None'}"
            )
            console.print(f"[yellow]Similarity Score:[/yellow] {doc['similarity']:.3f}")
            console.print("-" * 80)
    else:
        console.print("[red]No similar documents found.[/red]")


def is_keyword_frequency_query(query: str) -> bool:
    """Check if the query is asking about keyword frequencies."""
    frequency_indicators = [
        "most frequent keyword",
        "most common keyword",
        "top keyword",
        "keyword frequency",
        "keyword frequencies",
        "popular keyword",
        "common keyword",
        "frequent keyword",
    ]
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in frequency_indicators)


def is_duplicate_titles_query(query: str) -> bool:
    """Check if the query is asking about duplicate titles."""
    duplicate_indicators = [
        "duplicate title",
        "duplicate titles",
        "same title",
        "repeated title",
        "identical title",
        "title duplicate",
        "titles that appear multiple",
        "titles that repeat",
    ]
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in duplicate_indicators)


def run_query(
    query: str,
    top_k: int = 5,
    data_source: Optional[str] = None,
    use_llm: bool = True,
    similarity_threshold: float = 0.5,
):
    """Main function to run the query pipeline."""
    try:
        # Check if this is a duplicate titles query
        if is_duplicate_titles_query(query):
            console.print("[yellow]Searching for duplicate titles...[/yellow]")
            duplicates = get_duplicate_titles(data_source=data_source)

            display_duplicate_titles(duplicates, data_source)

            # If LLM is enabled, also provide a natural language response
            if use_llm and duplicates:
                duplicate_context = "\n".join(
                    [
                        f"- '{dup['title']}' appears {dup['count']} times in documents: {', '.join(dup['doc_ids'][:5])}"
                        for dup in duplicates[:10]
                    ]
                )

                llm_prompt = f"""Based on the duplicate title data, answer the user's question.

Duplicate Titles Found (top 10):
{duplicate_context}

Total duplicate titles: {len(duplicates)}

User Question: {query}

Provide a natural language response about the duplicate titles."""

                try:
                    response = requests.post(
                        f"{os.environ.get('LITELLM_URL', 'http://localhost:4000')}/v1/chat/completions",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {os.environ.get('LITELLM_MASTER_KEY', '')}",
                        },
                        json={
                            "model": "ollama/llama3.1",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are a helpful assistant that analyzes document duplicate data.",
                                },
                                {"role": "user", "content": llm_prompt},
                            ],
                            "temperature": 0.7,
                            "max_tokens": 500,
                        },
                    )

                    if response.status_code == 200:
                        result = response.json()
                        llm_response = result["choices"][0]["message"]["content"]
                        console.print(
                            Panel(
                                llm_response,
                                title="[bold green]AI Analysis[/bold green]",
                                border_style="green",
                            )
                        )
                except Exception as e:
                    console.print(
                        f"[yellow]Could not get LLM analysis: {str(e)}[/yellow]"
                    )
            return

        # Check if this is a keyword frequency query
        if is_keyword_frequency_query(query):
            console.print("[yellow]Fetching keyword frequencies...[/yellow]")
            keywords = get_keyword_frequencies(top_k=20, data_source=data_source)

            if keywords:
                display_keyword_frequencies(keywords, data_source)

                # If LLM is enabled, also provide a natural language response
                if use_llm:
                    keyword_context = "\n".join(
                        [
                            f"{i + 1}. '{kw['keyword']}' - appears {kw['frequency']} times"
                            for i, kw in enumerate(keywords[:10])
                        ]
                    )

                    llm_prompt = f"""Based on the keyword frequency data, answer the user's question.

Keyword Frequency Data (top 10):
{keyword_context}

User Question: {query}

Provide a natural language response about the keyword frequencies."""

                    try:
                        response = requests.post(
                            f"{os.environ.get('LITELLM_URL', 'http://localhost:4000')}/v1/chat/completions",
                            headers={
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {os.environ.get('LITELLM_MASTER_KEY', '')}",
                            },
                            json={
                                "model": "ollama/llama3.1",
                                "messages": [
                                    {
                                        "role": "system",
                                        "content": "You are a helpful assistant that analyzes keyword frequency data.",
                                    },
                                    {"role": "user", "content": llm_prompt},
                                ],
                                "temperature": 0.7,
                                "max_tokens": 500,
                            },
                        )

                        if response.status_code == 200:
                            result = response.json()
                            llm_response = result["choices"][0]["message"]["content"]
                            console.print(
                                Panel(
                                    llm_response,
                                    title="[bold green]AI Analysis[/bold green]",
                                    border_style="green",
                                )
                            )
                    except Exception as e:
                        console.print(
                            f"[yellow]Could not get LLM analysis: {str(e)}[/yellow]"
                        )
            else:
                console.print("[red]No keywords found in the database.[/red]")
            return

        # Regular vector search flow
        # Generate embedding for the query
        console.print("[yellow]Generating query embedding...[/yellow]")
        query_embedding = get_query_embedding(query)

        # Search for similar documents
        console.print("[yellow]Searching for similar documents...[/yellow]")
        results = search_similar_documents(
            query_embedding,
            top_k=top_k,
            data_source=data_source,
            threshold=similarity_threshold,
        )

        # Query LLM if enabled and results found
        llm_response = ""
        if use_llm and results:
            console.print("[yellow]Querying LLM for comprehensive answer...[/yellow]")
            llm_response = query_llm(query, results)
        elif not use_llm:
            llm_response = "LLM querying disabled. Showing only vector search results."
        else:
            llm_response = "No similar documents found to provide context for LLM."

        # Display results
        display_results(query, results, llm_response)

    except Exception as e:
        console.print(f"[red]Error during query execution: {str(e)}[/red]")
        sys.exit(1)


@click.command()
@click.argument("query", required=False)
@click.option(
    "-k", "--top-k", default=5, help="Number of documents to retrieve (default: 5)"
)
@click.option("-s", "--source", help="Filter by data source")
@click.option(
    "--no-llm",
    is_flag=True,
    help="Disable LLM querying, only show vector search results",
)
@click.option(
    "-t", "--threshold", default=0.5, help="Similarity threshold (0-1, default: 0.5)"
)
@click.option("-i", "--interactive", is_flag=True, help="Interactive mode")
def main(query, top_k, source, no_llm, threshold, interactive):
    """Query documents using vector embeddings and LLM"""

    # Ensure the script is run from the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Check if the required environment variable is set
    if "CATALOG_ENV" not in os.environ:
        console.print("[red]Error: CATALOG_ENV environment variable is not set.[/red]")
        sys.exit(1)

    # Interactive mode
    if interactive:
        console.print("[bold green]Interactive Query Mode[/bold green]")
        console.print("Type 'exit' or 'quit' to stop.\n")

        while True:
            try:
                user_query = console.input("[bold blue]Enter your query:[/bold blue] ")
                if user_query.lower() in ["exit", "quit"]:
                    break

                run_query(
                    query=user_query,
                    top_k=top_k,
                    data_source=source,
                    use_llm=not no_llm,
                    similarity_threshold=threshold,
                )
                console.print("\n" + "=" * 80 + "\n")

            except KeyboardInterrupt:
                console.print("\n[yellow]Exiting interactive mode.[/yellow]")
                break
    else:
        # Single query mode
        if not query:
            console.print(
                "[red]Error: Query is required when not in interactive mode.[/red]"
            )
            console.print(
                "Use --help for usage information or -i for interactive mode."
            )
            sys.exit(1)

        run_query(
            query=query,
            top_k=top_k,
            data_source=source,
            use_llm=not no_llm,
            similarity_threshold=threshold,
        )


if __name__ == "__main__":
    main()