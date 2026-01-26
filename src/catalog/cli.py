from dotenv import load_dotenv
import click
from catalog.usfs import USFS
import json
from catalog.schema import USFSDocument
from pathlib import Path
from catalog.core import ChromaVectorDB

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
def download_fs_metadata() -> None:
    """Download USFS metadata"""

    click.echo("Downloading USFS metadata files...")
    usfs = USFS()
    usfs.download_metadata()


@cli.command()
def build_fs_catalog() -> None:
    """
    Generate the USFS metadata catlog
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


def main() -> None:
    """Entry point that runs the CLI group."""
    cli()


if __name__ == "__main__":
    main()
