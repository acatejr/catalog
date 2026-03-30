import click
import datetime
from rich.console import Console
from .usfs import USFS

console = Console()


@click.group()
def cli():
    """Catalog CLI group."""
    pass


@cli.command()
def health() -> None:
    """Helper command to check the application's status."""
    console.print(f"[bold green]status:[/bold green] ok - {datetime.datetime.now()}")


@cli.command(name="dl-fs-md")
@click.option(
    "--source",
    type=click.Choice(["fsgeodata", "gdd", "rda", "all"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Which metadata source to download.",
)
def download_fs_metadata(source: str) -> None:
    """Download USFS metadata."""

    console.rule("[bold blue]USFS Metadata Download")

    usfs = USFS()

    if source in ("fsgeodata", "all"):
        console.print("[cyan]Downloading fsgeodata metadata...[/cyan]")
        usfs.download_fsgeodata_metadata()
        console.print("[green]✓ fsgeodata metadata complete[/green]")

    if source in ("gdd", "all"):
        console.print("[cyan]Downloading GDD metadata...[/cyan]")
        usfs.download_gdd_metadata()
        console.print("[green]✓ GDD metadata complete[/green]")

    if source in ("rda", "all"):
        console.print("[cyan]Downloading RDA metadata...[/cyan]")
        usfs.download_rda_metadata()
        console.print("[green]✓ RDA metadata complete[/green]")

    console.rule("[bold blue]Done")


@cli.command(name="build-fs-catalog")
def build_fs_catalog() -> None:
    """Builds the USFS metadata catalog from all sources."""
    console.rule("[bold blue]Building USFS Catalog")
    console.print("[cyan]Building USFS catalog from all metadata sources...[/cyan]")
    usfs = USFS()
    usfs.build_catalog()

def _download_all_fs_metadata():
    pass


if __name__ == "__main__":
    cli()
