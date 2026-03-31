"""
Entry point for the Catalog CLI.

This module defines all Click commands exposed to end users.  Each command
delegates to the USFS service class in ``usfs.py``, keeping CLI concerns
(argument parsing, console output) separate from business logic.

Commands
--------
health
    Quick sanity-check that the tool is installed and responding.
dl-fs-md
    Download raw metadata from one or all USFS sources (FSGeodata, GDD, RDA)
    and persist the files under ``data/usfs/``.
build-fs-catalog
    Read every downloaded metadata file, normalise the records, and write the
    combined catalog to ``data/usfs/usfs_catalog.json``.

Usage
-----
Run ``catalog --help`` from the project root to see all available commands.
"""

import click
import datetime
from rich.console import Console
from .usfs import USFS

console = Console()


@click.group()
def cli():
    """Top-level command group for the Catalog CLI.

    All sub-commands are registered under this group and can be discovered
    by running ``catalog --help``.
    """
    pass


@cli.command()
def health() -> None:
    """Print a status message confirming the tool is running correctly.

    Outputs a green "status: ok" line together with the current timestamp.
    Useful as a quick smoke-test after installation or deployment.
    """
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
    """Download raw metadata files from one or more USFS data sources.

    Fetches metadata from the selected source(s) and writes the results to the
    local ``data/usfs/`` directory tree.  Already-downloaded files are skipped
    so the command is safe to re-run incrementally.

    Sources
    -------
    fsgeodata
        Individual XML metadata files from the USFS Geodata Clearinghouse
        (``data.fs.usda.gov``).  One ``.xml`` file is written per dataset.
    gdd
        A single JSON feed from the USFS ArcGIS Hub (DCAT-US 1.1 format),
        saved to ``data/usfs/gdd/gdd_metadata.json``.
    rda
        A single JSON feed from the USFS Research Data Archive web service,
        saved to ``data/usfs/rda/rda_metadata.json``.
    all
        Downloads all three sources sequentially (default).

    Args:
        source: One of ``fsgeodata``, ``gdd``, ``rda``, or ``all``.
    """

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
    """Build the unified USFS metadata catalog from all downloaded sources.

    Reads every metadata file previously fetched by ``dl-fs-md`` (FSGeodata
    XML files, the GDD JSON feed, and the RDA JSON feed), normalises each
    record into a common document structure, and writes the combined result to
    ``data/usfs/usfs_catalog.json``.

    This command must be run *after* ``dl-fs-md`` has successfully downloaded
    the relevant source files.  Missing source files are skipped with a
    warning rather than causing the command to fail.
    """
    console.rule("[bold blue]Building USFS Catalog")
    console.print("[cyan]Building USFS catalog from all metadata sources...[/cyan]")
    usfs = USFS()
    usfs.build_catalog()


def _download_all_fs_metadata():
    """Reserved for programmatic (non-CLI) bulk download of all USFS metadata.

    Not yet implemented.  Intended for use when the download step needs to be
    invoked from Python code rather than the command line.
    """
    pass


if __name__ == "__main__":
    cli()
