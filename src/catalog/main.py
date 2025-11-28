import click
from catalog.fsgeodata import FSGeodataDownloader


@click.group()
def cli():
    """Catalog CLI group."""
    pass


@cli.command()
@click.option("--name", "-n", default="catalog", help="Name to greet.")
def hello(name: str) -> None:
    """Print a hello message."""

    click.echo(f"Hello, {name}!")


@cli.command()
def health() -> None:
    """Print a simple health status."""

    click.echo("status: ok")


@cli.command()
def download_fsgeodata() -> None:
    """Download FSGEO data files."""

    click.echo("Downloading FSGEO data files...")

    downloader = FSGeodataDownloader(data_dir="data/fsgeodata")
    downloader.download_all()


def main() -> None:
    """Entry point that runs the CLI group."""
    cli()


if __name__ == "__main__":
    main()
