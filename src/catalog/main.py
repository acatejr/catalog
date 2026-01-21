import click
from catalog.fsgeodata import FSGeodataLoader
from catalog.rda import RDALoader
from catalog.gdd import GeospatialDataDiscovery
from catalog.lib import save_json
from catalog.core import SqliteVectorDB, ChromaVectorDB, HybridSearch
from catalog.bots import OpenAIBot, OllamaBot
from dotenv import load_dotenv
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel


load_dotenv()


@click.group()
def cli():
    """Catalog CLI group."""
    pass


@cli.command()
def health() -> None:
    """Print a simple health status."""

    click.echo("status: ok")


@cli.command()
def download_fsgeodata() -> None:
    """Download FSGEO data files."""

    click.echo("Downloading FSGEO data files...")

    downloader = FSGeodataLoader(data_dir="data/fsgeodata")
    downloader.download_all()


@cli.command()
def download_rda() -> None:
    """Download RDA metadata files."""

    click.echo("Downloading RDA metadata files...")

    # download_rda_metadata()
    rda = RDALoader()
    rda.download()
    click.echo("Download completed successfully.")


@cli.command()
def download_gdd() -> None:
    """Download GDD metadata files."""

    gdd = GeospatialDataDiscovery()
    click.echo("Downloading GDD metadata files...")
    gdd.download_gdd_metadata()
    click.echo("Download completed successfully.")


@cli.command()
def download_all() -> None:
    gdd = GeospatialDataDiscovery()
    gdd.download_gdd_metadata()

    rda = RDALoader()
    rda.download()

    fsgeod = FSGeodataLoader(data_dir="data/fsgeodata")
    fsgeod.download_all()


@cli.command()
def build_docs_catalog() -> None:
    """Read all of the metadata source files and build a dict that contains all document objects.  Save the dict to a JSON file."""
    fsgeod = FSGeodataLoader()
    rda = RDALoader()
    gdd = GeospatialDataDiscovery()

    fsgeo_docs = fsgeod.parse_metadata()
    click.secho(f"{len(fsgeo_docs)} FSGeodata documents parsed.", fg="green")

    rda_docs = rda.parse_metadata()
    click.secho(f"{len(rda_docs)} RDA documents parsed.", fg="green")

    gdd_docs = gdd.parse_metadata()
    click.secho(f"{len(gdd_docs)} GDD documents parsed.", fg="green")

    documents = fsgeo_docs + rda_docs + gdd_docs
    click.secho(f"{len(documents)} Total documents parsed.", fg="green")

    save_json(documents, "data/catalog.json")


@cli.command("bsvdb")
def build_sqlite_vectordb() -> None:
    """Builds a SQLite3 based vector database of the catalog metadata."""
    slvdb = SqliteVectorDB()
    slvdb.bulk_insert_documents()


@cli.command()
@click.option("--qstn", "-q", required=True)
def sqlvdb_disc_chat(qstn):
    """Used to run data discovery questions against the catalog."""

    click.secho(f"Asked: {qstn}", fg="green")

    slvdb = SqliteVectorDB()
    documents = slvdb.query_vector_table(query=qstn, limit=5)

    if len(documents) > 0:
        context = "\n\n".join(
            [
                f"Title: {doc['title']}\nDescription: {doc['abstract']}\nKeywords: {doc['keywords']}\nSource: {doc['source']}"
                for doc in documents
            ]
        )

        bot = OllamaBot() # OpenAIBot()
        resp = bot.chat(qstn, context)

        console = Console()
        # Create a syntax-highlighted panel
        panel = Panel(
            Syntax(
                resp,
                "markdown",
                theme="monokai",
                line_numbers=True,
                word_wrap=True,
            ),
            title="OpenAI Response",
            border_style="bold green",
        )
        console.print(panel)


@cli.command()
def load_chromadb():
    chroma = ChromaVectorDB()
    chroma.load_documents()


@cli.command()
@click.option("--qstn", "-q", required=True)
def chroma_chat(qstn):
    """Used to run data discovery questions against the catalog using chromadb."""

    cvdb = ChromaVectorDB()
    resp = cvdb.query(qstn=qstn, nresults=5)

    if resp and len(resp) > 0:
        documents = resp["documents"]
        if len(documents) > 0:
            context = "\n\n".join(
                [
                    f"{doc}"
                    for doc in documents
                ]
            )

        # bot = OpenAIBot()
        # resp = bot.discovery_chat(qstn, context)

        bot = OllamaBot() # OpenAIBot()
        resp = bot.chat(qstn, context)

        console = Console()
        # Create a syntax-highlighted panel
        panel = Panel(
            Syntax(
                resp,
                "markdown",
                theme="monokai",
                line_numbers=True,
                word_wrap=True,
            ),
            title="OpenAI Response",
            border_style="bold green",
        )
        console.print(panel)


@cli.command()
@click.option("--query", "-q", required=True, help="Search query")
@click.option(
    "--db",
    "-d",
    type=click.Choice(["sqlite", "chroma"], case_sensitive=False),
    default="sqlite",
    help="Vector database to use (default: sqlite)",
)
@click.option("--limit", "-k", default=5, help="Number of results to return")
@click.option("--alpha", "-a", default=0.5, help="Weight for vector results (0-1)")
def hybrid_search(query, db, limit, alpha):
    """Run a hybrid search combining BM25 and vector search."""
    console = Console()

    # Load documents for BM25
    if db == "sqlite":
        vector_db = SqliteVectorDB()
    else:
        vector_db = ChromaVectorDB()

    # Load document texts for BM25 tokenization
    documents = vector_db.load_documents()
    if not documents:
        click.secho("No documents found. Run build-docs-catalog first.", fg="red")
        return

    # Create text representations for BM25
    doc_texts = [
        f"{doc.title or ''} {doc.abstract or ''} {doc.purpose or ''}"
        for doc in documents
    ]

    click.secho(f"Searching {len(documents)} documents...", fg="cyan")
    click.secho(f"Query: {query}", fg="green")
    click.secho(f"Database: {db}, Alpha: {alpha}, Limit: {limit}", fg="cyan")

    # Run hybrid search
    hs = HybridSearch(vector_db, doc_texts)
    results = hs.search(query, k=limit, alpha=alpha)

    if not results:
        click.secho("No results found.", fg="yellow")
        return
    
    # Create lookup by ID and index
    doc_by_id = {doc.id: doc for doc in documents}
    doc_list = []
    for i, doc_ref in enumerate(results, 1):
        doc = None
        # Handle both integer indices (from BM25) and string IDs (from vector DB)
        if isinstance(doc_ref, int) and doc_ref < len(documents):
            doc = documents[doc_ref]
        elif isinstance(doc_ref, str) and doc_ref in doc_by_id:
            doc = doc_by_id[doc_ref]

        if doc:
            doc_list.append(doc)

    context = "\n\n".join(
        [
            f"{doc}"
            for doc in doc_list
        ]
    )
    
    bot = OllamaBot() # OpenAIBot()
    resp = bot.chat(query, context)

    console = Console()
    # Create a syntax-highlighted panel
    panel = Panel(
        Syntax(
            resp,
            "markdown",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        ),
        title="OpenAI Response",
        border_style="bold green",
    )
    console.print(panel)

    # Create lookup by ID and index
    # doc_by_id = {doc.id: doc for doc in documents}

    # # Display results
    # click.secho(f"\nFound {len(results)} results:\n", fg="green")
    # for i, doc_ref in enumerate(results, 1):
    #     doc = None
    #     # Handle both integer indices (from BM25) and string IDs (from vector DB)
    #     if isinstance(doc_ref, int) and doc_ref < len(documents):
    #         doc = documents[doc_ref]
    #     elif isinstance(doc_ref, str) and doc_ref in doc_by_id:
    #         doc = doc_by_id[doc_ref]

    #     if doc:
    #         panel = Panel(
    #             f"[bold]Title:[/bold] {doc.title or 'N/A'}\n"
    #             f"[bold]Source:[/bold] {doc.src or 'N/A'}\n"
    #             f"[bold]Abstract:[/bold] {(doc.abstract or 'N/A')[:300]}...",
    #             title=f"Result {i}",
    #             border_style="blue",
    #         )
    #         console.print(panel)


def main() -> None:
    """Entry point that runs the CLI group."""
    cli()


if __name__ == "__main__":
    main()
