import click
from catalog.fsgeodata import FSGeodataLoader
from catalog.rda import RDALoader
from catalog.gdd import GeospatialDataDiscovery
from catalog.lib import save_json
from catalog.core import SqliteVectorDB, ChromaVectorDB
from catalog.bots import OpenAIBot
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

        bot = OpenAIBot()
        resp = bot.discovery_chat(qstn, context)

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

        bot = OpenAIBot()
        resp = bot.discovery_chat(qstn, context)

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


def main() -> None:
    """Entry point that runs the CLI group."""
    cli()


if __name__ == "__main__":
    main()
