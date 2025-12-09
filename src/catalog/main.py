import click
from catalog.fsgeodata import FSGeodataLoader
from catalog.rda import RDALoader
from catalog.gdd import GeospatialDataDiscovery
from catalog.lib import save_json


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


def main() -> None:
    """Entry point that runs the CLI group."""
    cli()


if __name__ == "__main__":
    main()
