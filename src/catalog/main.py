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
def download_fs_metadata() -> None:
    """Download all USFS metadata"""

    console.rule("[bold blue]USFS Metadata Download")

    usfs = USFS()

    console.print("[cyan]Downloading fsgeodata metadata...[/cyan]")
    usfs.download_fsgeodata_metadata()
    console.print("[green]✓ fsgeodata metadata complete[/green]")

    console.print("[cyan]Downloading GDD metadata...[/cyan]")
    usfs.download_gdd_metadata()
    console.print("[green]✓ GDD metadata complete[/green]")

    console.print("[cyan]Downloading RDA metadata...[/cyan]")
    usfs.download_rda_metadata()
    console.print("[green]✓ RDA metadata complete[/green]")

    console.rule("[bold blue]Done")


def _download_all_fs_metadata():
    pass


if __name__ == "__main__":
    cli()