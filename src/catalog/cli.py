from dotenv import load_dotenv
import click
from catalog.usfs import USFS

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


def main() -> None:
    """Entry point that runs the CLI group."""
    cli()


if __name__ == "__main__":
    main()
