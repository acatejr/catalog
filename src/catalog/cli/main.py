import typer
import json
from catalog.lib.db import save_to_vector_db, count_documents
from catalog.lib.docs import load_docs_from_json
from sentence_transformers import SentenceTransformer
import uvicorn
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

# from catalog.core.config import settings
# typer.echo(f"Current settings: {settings.json()}")
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

cli = typer.Typer()

@cli.command()
def count_docs() -> None:
    count = count_documents()
    typer.echo(f"There are {count} documents in the documents table.")

@cli.command()
def hello() -> None:
    """
    Main entry point for the catalog CLI.
    """
    typer.echo("Hello from catalog!")


@cli.command()
def version() -> None:
    """
    Display the version of the catalog CLI.
    """
    typer.echo("Catalog CLI version 0.1.0")


@cli.command()
def harvest_fsgeodata() -> None:
    """
    Harvest data from FS Geodata.
    """

    from catalog.core.harvester import harvest_fsgeodata
    fsgeodata_documents = harvest_fsgeodata()
    typer.echo(f"Extracted {len(fsgeodata_documents)} items from FS Geodata.")

@cli.command()
def harvest_datahub() -> None:
    """
    Harvest data from DataHub.
    """

    from catalog.core.harvester import _harvest_datahub
    datahub_documents = _harvest_datahub()
    typer.echo(f"Extracted {len(datahub_documents)} items from DataHub.")

@cli.command()
def harvest_rda() -> None:
    """
    Harvest data from RDA.
    """

    from catalog.core.harvester import harvest_rda
    rda_documents = harvest_rda()
    typer.echo(f"Extracted {len(rda_documents)} items from RDA.")

@cli.command()
def harvest_all() -> None:
    """
    Harvest data from all sources: FS Geodata, DataHub, and RDA.
    """

    from catalog.core.harvester import harvest_all
    docs = harvest_all()
    output_path = "./tmp/usfs_docs.json"
    with open(output_path, "w") as f:
        json.dump(docs, f, indent=3)

    typer.echo(f"Extracted {len(docs)} items from all sources.")


@cli.command()
def load_usfs_docs_into_pgdb():
    """Load USFS documents into the PostgreSQL database."""

    model = SentenceTransformer("all-MiniLM-L6-v2")

    fsdocs = load_docs_from_json("./tmp/usfs_docs.json")
    print(f"Loading USFS {len(fsdocs)} documents into PostgreSQL database...")

    recursive_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=65, chunk_overlap=0
    )  # ["\n\n", "\n", " ", ""] 65,450

    for fsdoc in fsdocs:
        title = fsdoc.title
        description = fsdoc.description
        keywords = ",".join(kw for kw in fsdoc.keywords) or []
        combined_text = (
            f"Title: {title}\nDescription: {description}\nKeywords: {keywords}"
        )

        chunks = recursive_text_splitter.create_documents([combined_text])
        for idx, chunk in enumerate(chunks):
            metadata = {
                "doc_id": fsdoc.id,  # or fsdoc.doc_id if that's the field name
                "chunk_type": "title+description+keywords",
                "chunk_index": idx,
                "chunk_text": chunk.page_content,
                "title": fsdoc.title,
                "description": fsdoc.description,
                "keywords": fsdoc.keywords,
                "src": fsdoc.src,  # or another source identifier
            }

            embedding = model.encode(chunk.page_content)
            save_to_vector_db(
                embedding=embedding,
                metadata=metadata,
                title=fsdoc.title,
                desc=fsdoc.description,
            )

    print("USFS documents loaded into PostgreSQL database.")


@cli.command()
def rag_query(
    query_text: str = typer.Argument(..., help="Natural language query"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results to return"),
    data_source: str = typer.Option(None, "--source", "-s", help="Filter by data source"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Disable LLM response generation"),
    threshold: float = typer.Option(0.5, "--threshold", "-t", help="Similarity threshold (0-1)"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
) -> None:
    """
    Run natural language queries against the catalog database using RAG.

    Examples:
        catalog rag-query "Show me all forest fire related datasets"
        catalog rag-query "Find records about erosion" --top-k 10
        catalog rag-query "What datasets are from USGS?" --source usgs
    """
    from catalog.lib.rag import run_natural_language_query

    result = run_natural_language_query(
        query=query_text,
        top_k=top_k,
        data_source=data_source,
        use_llm=not no_llm,
        similarity_threshold=threshold
    )

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        # Simple text output for CLI
        typer.echo(f"\nQuery: {result['query']}")
        typer.echo(f"Type: {result['query_type']}")
        typer.echo(f"Found {len(result['documents'])} documents")

        if result['documents']:
            typer.echo("\nTop Results:")
            for i, doc in enumerate(result['documents'][:3]):
                typer.echo(f"{i+1}. {doc['title']} (similarity: {doc['similarity']:.3f})")

        if result['response']:
            typer.echo(f"\nAI Response:\n{result['response']}")


@cli.command()
def rag_interactive() -> None:
    """
    Start interactive RAG query mode.
    """
    from catalog.cli.rag_query import run_interactive_mode
    run_interactive_mode(5, None, True, 0.5, False)


@cli.command()
def run_adhoc() -> None:
    """
    Run the adhoc catalog web application.
    """
    typer.echo("Starting adhoc catalog web application...")
    uvicorn.run(
        "catalog.adhoc.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    cli()
