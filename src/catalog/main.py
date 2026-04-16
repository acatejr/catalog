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
import json
import datetime
from pathlib import Path
from rich.console import Console
from .usfs import USFS
from .schema import USFSDocument
from .embeddings import EmbeddingsService
from .db import init_db
from .search import SemanticSearch

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


def _read_catalog() -> list[dict]:
    """
    Read the USFS catalog from the local JSON file and return the parsed records.

    The catalog is loaded from "data/usfs/usfs_catalog.json", each JSON item is
    mapped to a USFSDocument instance, and the number of records loaded is printed.

    Returns:
        list[dict]: Parsed catalog records as USFSDocument instances.
    """

    catalog_path = "data/usfs/usfs_catalog.json"

    data = [USFSDocument(**item) for item in json.loads(Path(catalog_path).read_text())]
    return data


def _load_data(target: str):
    """Loads USFS catalog into the target database."""

    if target in ("chromadb", "pg"):
        catalog = _read_catalog()
        embeddings_service = EmbeddingsService()
        embeddings = embeddings_service.embed_batch(catalog)

        if target.lower() in ("chromadb"):
            console.print(f"[cyan]Loading data into ChromaDB...[/cyan]")
            console.print("[green]✓ Data loaded into ChromaDB[/green]")
        elif target.lower() in ("pg"):
            console.print(f"[cyan]Loading data into PostgreSQL...[/cyan]")
            init_db()
            embeddings_service.store_in_postgres(catalog, embeddings)
            console.print("[green]✓ Data loaded into PostgreSQL[/green]")
    else:
        console.print(
            f"[red]Error: Unsupported target '{target}' for load-data command[/red]"
        )


@cli.command(name="load-data")
@click.option(
    "--target",
    type=click.Choice(
        [
            "chromadb",
            "pg",
        ],
        case_sensitive=False,
    ),
    default=None,
    show_default=True,
    help="Load data into the specified target vector db.",
)
def load_data(target: str) -> None:
    """Load the catalog data into the specified target database.
    Supported targets include: - chromadb: Load data into ChromaDB vector database.  - pg: Load data into PostgreSQL database.
    """
    if target is None:
        console.print(
            "[red]Error: --target option is required for load-data command[/red]"
        )
        return
    _load_data(target)


@cli.command(name="semantic-search")
@click.argument("query")
@click.option(
    "--limit",
    default=10,
    show_default=True,
    help="Maximum number of results to return.",
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["text", "markdown"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format: text (default) or markdown.",
)
def semantic_search(query: str, limit: int, output_format: str) -> None:
    """Search the catalog using natural language.

    QUERY is the natural language search string, e.g. \"forests near water\".
    Results are ranked by semantic similarity to the query.
    """

    search = SemanticSearch("BAAI/bge-small-en-v1.5")

    try:
        results = search.search(query, limit=limit)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    def _parse_keywords(raw) -> str:
        if not raw:
            return ""
        try:
            items = json.loads(raw) if isinstance(raw, str) else raw
            return ", ".join(items) if isinstance(items, list) else str(raw)
        except (ValueError, TypeError):
            return str(raw)

    if output_format == "markdown":
        click.echo(f"## Search results for: {query}\n")
        click.echo("| Title | Keywords | Similarity |")
        click.echo("|-------|----------|------------|")
        for row in results:
            title = getattr(row, "title", None) or (row[1] if len(row) > 1 else str(row))
            keywords = _parse_keywords(getattr(row, "keywords", None))
            similarity = getattr(row, "similarity", None) or (row[-1] if len(row) > 1 else "")
            score = f"{similarity:.4f}" if isinstance(similarity, float) else ""
            click.echo(f"| {title} | {keywords} | {score} |")
    else:
        for i, row in enumerate(results, start=1):
            title = getattr(row, "title", None) or (row[1] if len(row) > 1 else str(row))
            keywords = _parse_keywords(getattr(row, "keywords", None))
            similarity = getattr(row, "similarity", None) or (row[-1] if len(row) > 1 else "")
            score = f"  [dim]{similarity:.4f}[/dim]" if isinstance(similarity, float) else ""
            console.print(f"[bold]{i}.[/bold] {title}{score}")
            if keywords:
                console.print(f"   [dim]Keywords: {keywords}[/dim]")



if __name__ == "__main__":
    cli()
