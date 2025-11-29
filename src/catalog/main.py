import click
from catalog.fsgeodata import FSGeodataDownloader
from catalog.rda import download_rda_metadata
from catalog.gdd import download_gdd_metadata

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


@cli.command()
def download_rda() -> None:
    """Download RDA metadata files."""

    click.echo("Downloading RDA metadata files...")

    download_rda_metadata()
    click.echo("Download completed successfully.")


@cli.command()
def download_gdd() -> None:
    """Download GDD metadata files."""

    click.echo("Downloading GDD metadata files...")
    download_gdd_metadata()
    click.echo("Download completed successfully.")

def main() -> None:
    """Entry point that runs the CLI group."""
    cli()


if __name__ == "__main__":
    main()
