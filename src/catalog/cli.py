from dotenv import load_dotenv
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from catalog.usfs import USFS
from catalog.core import ChromaVectorDB
from catalog.bots import OllamaBot, VerdeBot
from catalog.search import HybridSearch

load_dotenv()


@click.group()
def cli():
    """Catalog CLI group."""
    pass


@cli.command()
def health() -> None:
    """The applications health status."""
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
    Generate the USFS metadata catalog
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
@click.option(
    "--nresults",
    "-n",
    default=5,
    type=click.IntRange(min=1),
    help="Number of results to return.",
)
def query_fs_chromadb(qstn: str, nresults: int = 5) -> None:
    """
    Query the USFS ChromaDB vector store
    """

    db = ChromaVectorDB()
    resp = db.query(qstn=qstn, nresults=nresults)
    for doc, distance in resp:
        click.echo(doc.to_markdown(distance=distance))
        click.echo("---")


@cli.command()
@click.option("--qstn", "-q", required=True)
@click.option(
    "--nresults",
    "-n",
    default=5,
    type=click.IntRange(min=1),
    help="Number of results to return.",
)
def ollama_chat(qstn: str, nresults: int = 5) -> None:
    """
    Runs a chromadb query and uses Ollama to answer the question.

    :param qstn: Description
    :type qstn: str
    :param nresults: Description
    :type nresults: int
    """
    console = Console()

    cvdb = ChromaVectorDB()
    resp = cvdb.query(qstn=qstn, nresults=nresults)
    if resp:
        context = "\n\n---\n\n".join(
            doc.to_markdown(distance=distance) for doc, distance in resp
        )
        client = OllamaBot()
        bot_response = client.chat(question=qstn, context=context)

        # Render the response as formatted markdown in a styled panel
        console.print(
            Panel(
                Markdown(bot_response),
                title="[bold green]Response[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        console.print("[yellow]No results found for your query.[/yellow]")


@cli.command()
@click.option("--qstn", "-q", required=True)
@click.option(
    "--nresults",
    "-n",
    default=5,
    type=click.IntRange(min=1),
    help="Number of results to return.",
)
def ask_verde(qstn: str, nresults: int = 5) -> None:
    """
    Docstring for ask_verde

    :param qstn: Description
    :type qstn: str
    :param nresults: Description
    :type nresults: int
    """
    console = Console()

    cvdb = ChromaVectorDB()
    resp = cvdb.query(qstn=qstn, nresults=nresults)
    if resp:
        context = "\n\n---\n\n".join(
            doc.to_markdown(distance=distance) for doc, distance in resp
        )

        bot = VerdeBot()
        bot_response = bot.chat(question=qstn, context=context)
        # Render the response as formatted markdown in a styled panel
        console.print(
            Panel(
                Markdown(bot_response),
                title="[bold green]Response[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        console.print("[yellow]No results found for your query.[/yellow]")


@cli.command()
@click.option("--qstn", "-q", required=True)
@click.option(
    "--nresults",
    "-n",
    default=5,
    type=click.IntRange(min=1),
    help="Number of results to return.",
)
@click.option(
    "--bot",
    "-b",
    type=click.Choice(["ollama", "verde"], case_sensitive=False),
    default=None,
    help="Send results to an LLM bot for a synthesized answer.",
)
def hybrid_search(qstn: str, nresults: int = 5, bot: str | None = None) -> None:
    """
    Query using hybrid search (BM25 keyword + vector semantic).
    Optionally pass results to an LLM with --bot ollama or --bot verde.
    """

    console = Console()
    db = ChromaVectorDB()
    hs = HybridSearch(vector_db=db)
    resp = hs.query(qstn=qstn, nresults=nresults)

    if not resp:
        console.print("[yellow]No results found for your query.[/yellow]")
        return

    if bot:
        context = "\n\n---\n\n".join(
            doc.to_markdown(distance=score) for doc, score in resp
        )
        if bot == "ollama":
            bot_client = OllamaBot()
        else:
            bot_client = VerdeBot()

        bot_response = bot_client.chat(question=qstn, context=context)
        console.print(
            Panel(
                Markdown(bot_response),
                title="[bold green]Response[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        for doc, score in resp:
            console.print(
                Panel(
                    Markdown(doc.to_markdown(distance=score)),
                    title=f"[bold blue]{doc.title}[/bold blue]",
                    border_style="green",
                    padding=(1, 2),
                )
            )


def main() -> None:
    """Entry point that runs the CLI group."""
    cli()


if __name__ == "__main__":
    main()
