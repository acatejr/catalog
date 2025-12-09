import click
from catalog.fsgeodata import FSGeodataLoader
from catalog.rda import RDALoader
from catalog.gdd import GeospatialDataDiscovery
from catalog.lib import save_json
from catalog.core import SqliteVectorDB
import os
from dotenv import load_dotenv

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

@cli.command("bsvdb")
def build_sqlite_vectordb() -> None:
    """Builds a SQLite3 based vector database of the catalog metadata.
    """
    slvdb = SqliteVectorDB()
    slvdb.bulk_insert_documents()

@cli.command()
@click.option('--qstn', '-q', required=True)
def sqlvdb_chat(qstn):

    click.secho(f"Asked: {qstn}", fg="green")

    slvdb = SqliteVectorDB()
    documents = slvdb.query_vector_table(query=qstn, limit=5)

    if len(documents) > 0:
        context = "\n\n".join(
            [
                f"Title: {doc['title']}\nDescription: {doc['abstract']}\nKeywords: {doc['keywords']}"
                for doc in documents
            ]
        )

        from openai import OpenAI
        LLM_API_KEY = os.getenv("LLM_API_KEY")
        LLM_BASE_URL = os.getenv("LLM_BASE_URL")
        LLM_MODEL = os.getenv("LLM_MODEL") or "Llama-3.2-11B-Vision-Instruct"
        model = LLM_MODEL

        client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional data librarian specializing in dataset discovery. "
                        "Your role is to help researchers find relevant datasets in the catalog. "
                        "When answering discovery questions:\n"
                        "- List the relevant datasets found in the catalog\n"
                        "- Briefly explain why each dataset matches the user's query\n"
                        "- Highlight key characteristics (keywords, descriptions) that make them relevant\n"
                        "- If multiple datasets are found, organize them by relevance\n"
                        "- Be direct and concise - focus on what datasets ARE available\n"
                        "- If the query asks about existence (like 'is there'), give a clear yes/no answer first, then list the datasets\n"
                        "- If you don't know answers just say you don't know. Don't try to make up an answer.\n"
                        "Use the provided context from the catalog to give accurate, evidence-based responses."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context: {context}\n\nQuestion: {qstn}",
                },
            ],
        )
        click.secho(f"Found {len(documents)} answers for query: {qstn}", fg="green")
        click.secho(f"Answer: {resp.choices[0].message.content}", fg="blue")

def main() -> None:
    """Entry point that runs the CLI group."""
    cli()


if __name__ == "__main__":
    main()
