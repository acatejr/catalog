import typer
import os
# from catalog.core.config import settings
# typer.echo(f"Current settings: {settings.json()}")
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

cli = typer.Typer()


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
    from catalog.core.crawlers import FSGeodataHarvester

    fsgeodata = FSGeodataHarvester()
    fsgeodata.download_metadata_files()
    fsgeodata_documents = fsgeodata.parse_metadata()
    typer.echo(f"Extracted {len(fsgeodata_documents)} items from FS Geodata.")


@cli.command()
def harvest_datahub() -> None:
    """
    Harvest data from DataHub.
    """
    from catalog.core.crawlers import DataHubHarvester

    datahub = DataHubHarvester()
    datahub.download_metadata_files()
    datahub_documents = datahub.parse_metadata()
    typer.echo(f"Extracted {len(datahub_documents)} items from DataHub.")

@cli.command()
def harvest_rda() -> None:
    """
    Harvest data from RDA.
    """
    from catalog.core.crawlers import RDAHarvester

    rda = RDAHarvester()
    rda.download_metadata_files()
    rda_documents = rda.parse_metadata()
    typer.echo(f"Extracted {len(rda_documents)} items from RDA.")

@cli.command()
def harvest_all() -> None:
    """
    Harvest data from all sources: FS Geodata, DataHub, and RDA.
    """
    from catalog.core.crawlers import FSGeodataHarvester, DataHubHarvester, RDAHarvester

    fsgeodata = FSGeodataHarvester()
    fsgeodata.download_metadata_files()
    fsgeodata_documents = fsgeodata.parse_metadata()
    typer.echo(f"Extracted {len(fsgeodata_documents)} items from FS Geodata.")

    datahub = DataHubHarvester()
    datahub.download_metadata_files()
    datahub_documents = datahub.parse_metadata()
    typer.echo(f"Extracted {len(datahub_documents)} items from DataHub.")

    rda = RDAHarvester()
    rda.download_metadata_files()
    rda_documents = rda.parse_metadata()
    typer.echo(f"Extracted {len(rda_documents)} items from RDA.")

    documents = fsgeodata_documents + datahub_documents + rda_documents
    typer.echo(f"Total documents extracted: {len(documents)}")

if __name__ == "__main__":
    cli()
