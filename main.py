import os
import json
from dotenv import load_dotenv
import click
from db import empty_documents_table, count_documents, save_to_vector_db
from utils import load_docs_from_json, merge_docs, find_duplicate_documents
from crawlers import FSGeodataHarvester, DataHubHarvester, RDAHarvester
from sentence_transformers import SentenceTransformer
# from typing import List
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from harvester import (
     _harvest_datahub,
     _harvest_fsgeodata,
     _harvest_rda,
)

load_dotenv()
os.chdir(os.path.dirname(os.path.abspath(__file__)))

fsgeodata = FSGeodataHarvester()
datahub = DataHubHarvester()
rda = RDAHarvester()

@click.group()
def cli():
    """Command line interface for managing USFS documents."""
    pass


def _retrieve_and_save_docs(output_path = "./tmp/usfs_docs.json"):
    docs = []

    fsgeodata_docs = _harvest_fsgeodata()
    datahub_docs = _harvest_datahub()
    rda_docs = _harvest_rda()

    docs = merge_docs(fsgeodata_docs, datahub_docs, rda_docs)

    duplicates = find_duplicate_documents(docs)
    if duplicates:
        print(f"Found {len(duplicates)} duplicate documents based on title:")
        for dup in duplicates:
            print(f"- {dup['id']}: {dup['title']}, {dup['keywords']}")

    with open(output_path, "w") as f:
        json.dump(docs, f, indent=3)



@cli.command()
# @click.option("--json_path", type=click.Path(exists=True), default="./tmp/usfs_docs.json",
#               help="Path to the JSON file containing USFS documents.")
def retrieve_and_save_docs():
    """Retrieve documents from various sources."""
    _retrieve_and_save_docs()
    print("Documents retrieved and saved to ./tmp/usfs_docs.json.")


@cli.command()
def load_usfs_docs_into_pgdb():
    """Load USFS documents into the PostgreSQL database."""
    model = SentenceTransformer("all-MiniLM-L6-v2")

    fsdocs = load_docs_from_json("./tmp/usfs_docs.json")
    print(f"Loading USFS {len(fsdocs)} documents into PostgreSQL database...")

    recursive_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=65, chunk_overlap=0
    )  # ["\n\n", "\n", " ", ""] 65,450

    for fsdoc in fsdocs:
        title = fsdoc.title
        description = fsdoc.description
        keywords = ",".join(kw for kw in fsdoc.keywords) or []
        combined_text = (
            f"Title: {title}\nDescription: {description}\nKeywords: {keywords}"
        )

        chunks = recursive_text_splitter.create_documents([combined_text])
        for idx, chunk in enumerate(chunks):
            metadata = {
                "doc_id": fsdoc.id,  # or fsdoc.doc_id if that's the field name
                "chunk_type": "title+description+keywords",
                "chunk_index": idx,
                "chunk_text": chunk.page_content,
                "title": fsdoc.title,
                "description": fsdoc.description,
                "keywords": fsdoc.keywords,
                "src": fsdoc.src,  # or another source identifier
            }

            embedding = model.encode(chunk.page_content)
            save_to_vector_db(
                embedding=embedding,
                metadata=metadata,
                title=fsdoc.title,
                desc=fsdoc.description,
            )

    print("USFS documents loaded into PostgreSQL database.")


@cli.command()
def clear_documents():
    """Clear the documents table in the database."""
    empty_documents_table()
    print("Documents table cleared.")


@cli.command()
def document_count():
    """Count the number of documents in the documents table."""

    doc_count = count_documents()
    print(f"Total documents in the vector database: {doc_count}")


@cli.command()
# @click.argument('json_path', type=click.Path(exists=True))
def download_usfs_fsgeodata():
    """Download USFS documents from a JSON file."""

    print("Downloading USFS documents from FS Geodata...")
    count = fsgeodata.download_metadata_files()
    print(f"Downloaded {count} metadata files from FS Geodata.")


@cli.command()
def download_usfs_datahub():
    """Download USFS documents from DataHub."""

    print("Downloading USFS documents from DataHub...")
    datahub.download_metadata_files()
    print(f"Downloaded metadata file from DataHub.")


@cli.command()
def download_usfs_rda():
    """Download USFS documents from RDA."""

    print("Downloading USFS documents from RDA...")
    rda.download_metadata_files()
    print(f"Downloaded metadata file from RDA.")


def _download_usfs_all():
    """Download all USFS documents from FS Geodata, DataHub, and RDA."""
    fsgeodata.download_metadata_files()
    datahub.download_metadata_files()
    rda.download_metadata_files()


@cli.command()
def download_usfs_all():
    """Download all USFS documents."""
    _download_usfs_all()
    print(f"Downloaded metadata files.")


if __name__ == "__main__":
    cli()