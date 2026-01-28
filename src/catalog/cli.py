from dotenv import load_dotenv
import click
from catalog.usfs import USFS
from catalog.core import ChromaVectorDB
from catalog.bots import OllamaBot

load_dotenv()


@click.group()
def cli():
    """Catalog CLI group."""
    pass


@cli.command()
def health() -> None:
    """The applications health status."""
    click.echo("status: ok")


@cli.command()
def download_fs_metadata() -> None:
    """Download USFS metadata"""

    click.echo("Downloading USFS metadata files...")
    usfs = USFS()
    usfs.download_metadata()


@cli.command()
def build_fs_catalog() -> None:
    """
    Generate the USFS metadata catalog
    """

    usfs = USFS()
    usfs.build_catalog()


@cli.command()
def build_fs_chromadb() -> None:
    """
    Generate the USFS ChromaDB vector store
    """

    usfs = USFS()
    usfs.build_chromadb()


@cli.command()
@click.option("--qstn", "-q", required=True)
@click.option("--nresults", "-n", default=5, help="Number of results to return.")
def query_fs_chromadb(qstn: str, nresults: int = 5) -> None:
    """
    Query the USFS ChromaDB vector store
    """

    db = ChromaVectorDB()
    resp = db.query(qstn=qstn, nresults=nresults)
    for doc, distance in resp:
        click.echo(doc.to_markdown(distance=distance))
        click.echo("---")


@cli.command()
@click.option("--qstn", "-q", required=True)
@click.option("--nresults", "-n", default=5, help="Number of results to return.")
def ollama_chat(qstn: str, nresults: int = 5) -> None:
    """
    Runs a chromadb query and uses Ollama to answer the question.

    :param qstn: Description
    :type qstn: str
    :param nresults: Description
    :type nresults: int
    """

    cvdb = ChromaVectorDB()
    resp = cvdb.query(qstn=qstn, nresults=nresults)
    if resp:
        context = "\n\n---\n\n".join(
            doc.to_markdown(distance=distance) for doc, distance in resp
        )
        client = OllamaBot()
        bot_response = client.chat(question=qstn, context=context)
        click.echo(bot_response)


def main() -> None:
    """Entry point that runs the CLI group."""
    cli()


if __name__ == "__main__":
    main()
