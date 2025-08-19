"""
Command-line interface for RAG natural language queries.
"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from catalog.lib.rag import run_natural_language_query, RAGSystem

app = typer.Typer(help="Natural Language Query Interface for Catalog Data")
console = Console()


@app.command()
def query(
    query_text: Optional[str] = typer.Argument(None, help="Natural language query"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results to return"),
    data_source: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by data source"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Disable LLM response generation"),
    threshold: float = typer.Option(0.5, "--threshold", "-t", help="Similarity threshold (0-1)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
):
    """
    Run natural language queries against the catalog database.

    Examples:
        catalog rag-query "Show me all forest fire related datasets"
        catalog rag-query "Find records about erosion" --top-k 10
        catalog rag-query "What datasets are from USGS?" --source usgs
    """

    if interactive:
        run_interactive_mode(top_k, data_source, not no_llm, threshold, json_output)
        return

    if not query_text:
        console.print("[red]Error: Query text is required when not in interactive mode.[/red]")
        console.print("Use --help for usage information or --interactive for interactive mode.")
        raise typer.Exit(1)

    # Run the query
    result = run_natural_language_query(
        query=query_text,
        top_k=top_k,
        data_source=data_source,
        use_llm=not no_llm,
        similarity_threshold=threshold
    )

    # Display results
    if json_output:
        console.print(json.dumps(result, indent=2))
    else:
        display_results(result)


@app.command()
def info():
    """Display information about the catalog database."""
    try:
        rag_system = RAGSystem()

        # Get basic stats
        doc_count = rag_system.get_document_count()
        data_sources = rag_system.get_available_data_sources()

        console.print(Panel.fit(
            f"[bold green]Catalog Database Information[/bold green]\n\n"
            f"[yellow]Total Documents:[/yellow] {doc_count:,}\n"
            f"[yellow]Available Data Sources:[/yellow] {len(data_sources)}\n\n"
            f"[cyan]Data Sources:[/cyan]\n" +
            "\n".join([f"  • {source}" for source in sorted(data_sources)]),
            title="Database Stats"
        ))

    except Exception as e:
        console.print(f"[red]Error getting database info: {e}[/red]")
        raise typer.Exit(1)


def run_interactive_mode(
    top_k: int,
    data_source: Optional[str],
    use_llm: bool,
    threshold: float,
    json_output: bool
):
    """Run in interactive query mode."""
    console.print("[bold green]Interactive RAG Query Mode[/bold green]")
    console.print("Type 'exit', 'quit', or press Ctrl+C to stop.")
    console.print("Type 'help' for available commands.\n")

    # Show current settings
    console.print(f"[dim]Settings: top_k={top_k}, threshold={threshold}, "
                 f"llm={'enabled' if use_llm else 'disabled'}, "
                 f"source={data_source or 'all'}[/dim]\n")

    while True:
        try:
            query_text = Prompt.ask("[bold blue]Enter your query")

            if query_text.lower() in ["exit", "quit"]:
                break
            elif query_text.lower() == "help":
                show_help()
                continue
            elif query_text.lower() == "info":
                info()
                continue
            elif query_text.lower().startswith("set "):
                handle_set_command(query_text)
                continue

            # Run the query
            result = run_natural_language_query(
                query=query_text,
                top_k=top_k,
                data_source=data_source,
                use_llm=use_llm,
                similarity_threshold=threshold
            )

            # Display results
            if json_output:
                console.print(json.dumps(result, indent=2))
            else:
                display_results(result)

            console.print("\n" + "=" * 80 + "\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting interactive mode.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def show_help():
    """Show help information in interactive mode."""
    help_text = """
[bold cyan]Available Commands:[/bold cyan]

[yellow]Query Commands:[/yellow]
  • Just type your natural language query
  • Examples:
    - "Show me forest fire datasets"
    - "Find erosion related data"
    - "What datasets are from USGS?"
    - "Most frequent keywords"

[yellow]System Commands:[/yellow]
  • help     - Show this help message
  • info     - Show database information
  • exit/quit - Exit interactive mode

[yellow]Settings Commands:[/yellow]
  • set top_k <number>     - Set number of results
  • set threshold <float>  - Set similarity threshold
  • set source <name>      - Set data source filter
  • set llm on/off        - Enable/disable LLM responses

[yellow]Example Queries:[/yellow]
  • "Show me all the forest fire related data sets"
  • "Find all records related to erosion"
  • "What datasets are available from USGS?"
  • "Most frequent keywords in the database"
"""
    console.print(Panel(help_text, title="Help"))


def handle_set_command(command: str):
    """Handle set commands in interactive mode."""
    parts = command.split()
    if len(parts) < 3:
        console.print("[red]Invalid set command. Use: set <setting> <value>[/red]")
        return

    setting = parts[1].lower()
    value = " ".join(parts[2:])

    # This is a simplified implementation
    # In a real application, you'd want to update the actual variables
    console.print(f"[yellow]Setting {setting} to {value} (note: settings changes not implemented in this demo)[/yellow]")


def display_results(result: dict):
    """Display query results in a formatted way."""
    query = result.get("query", "")
    query_type = result.get("query_type", "")
    documents = result.get("documents", [])
    response = result.get("response", "")
    metadata = result.get("metadata", {})

    console.print(f"\n[bold blue]Query:[/bold blue] {query}")
    console.print(f"[dim]Type: {query_type}[/dim]\n")

    # Display retrieved documents if any
    if documents:
        table = Table(
            title="Retrieved Documents",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Rank", style="cyan", width=6)
        table.add_column("Title", style="green", width=40)
        table.add_column("Similarity", style="yellow", width=10)
        table.add_column("Source", style="blue", width=15)

        for i, doc in enumerate(documents):
            title = doc.get("title", "")
            similarity = doc.get("similarity", 0)
            source = doc.get("data_source", "Unknown")

            table.add_row(
                str(i + 1),
                title[:40] + "..." if len(title) > 40 else title,
                f"{similarity:.3f}",
                source
            )

        console.print(table)
        console.print()

    # Display LLM response
    if response:
        console.print(
            Panel(
                response,
                title="[bold green]AI Response[/bold green]",
                border_style="green",
            )
        )

    # Display metadata
    if metadata and any(k != "error" for k in metadata.keys()):
        metadata_text = []
        for key, value in metadata.items():
            if key == "error":
                continue
            elif key == "keyword_frequencies" and isinstance(value, list):
                # Show top keywords
                top_keywords = value[:5]
                kw_text = ", ".join([f"{kw['keyword']} ({kw['frequency']})" for kw in top_keywords])
                metadata_text.append(f"[yellow]Top Keywords:[/yellow] {kw_text}")
            else:
                metadata_text.append(f"[yellow]{key.replace('_', ' ').title()}:[/yellow] {value}")

        if metadata_text:
            console.print(f"\n[dim]{' | '.join(metadata_text)}[/dim]")

    # Show detailed results if there are documents
    if documents:
        show_details = Prompt.ask(
            "\nShow detailed document content?",
            choices=["y", "n"],
            default="n"
        )

        if show_details.lower() == "y":
            console.print("\n[bold]Detailed Results:[/bold]")
            for i, doc in enumerate(documents):
                console.print(f"\n[bold cyan]Document {i + 1}:[/bold cyan]")
                console.print(f"[yellow]Title:[/yellow] {doc.get('title', 'N/A')}")
                console.print(f"[yellow]Description:[/yellow] {doc.get('description', 'N/A')}")
                console.print(f"[yellow]Content:[/yellow] {doc.get('chunk_text', 'N/A')}")
                console.print(f"[yellow]Keywords:[/yellow] {', '.join(doc.get('keywords', [])) or 'None'}")
                console.print(f"[yellow]Similarity Score:[/yellow] {doc.get('similarity', 0):.3f}")
                console.print("-" * 80)


if __name__ == "__main__":
    app()
