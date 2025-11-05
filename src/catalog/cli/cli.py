import typer
from rich.console import Console
import requests
from bs4 import BeautifulSoup
import os
import json
from typing import List, Dict, Any
import hashlib
from catalog.core.db import (
    empty_documents_table,
    bulk_upsert_to_vector_db,
    count_documents,
    db_health_check,
)

from catalog.core.db import save_eainfo, empty_eainfo_tables
import uvicorn
from catalog.core.schema import USFSDocument
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.catalog.core.schema_parser import EAInfoParser


cli = typer.Typer(
    name="catalog-cli",
    no_args_is_help=True,
    help="Catalog CLI - Metadata catalog with AI-enhanced search",
)

console = Console()

DEST_OUTPUT_DIR = "./data/catalog"


def create_output_dir():
    if not os.path.exists(DEST_OUTPUT_DIR):
        os.makedirs(DEST_OUTPUT_DIR)


def hash_string(s):
    """Generate a SHA-256 hash of the input string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def strip_html_tags(text):
    soup = BeautifulSoup(text, "html.parser")
    stripped_text = soup.get_text()
    stripped_text = stripped_text.replace("\n", " ")
    return stripped_text


def get_keywords(item):
    """Extract keywords from the item."""
    keywords = []
    if "keywords" in item:
        keywords = [
            keyword.strip()
            for keyword in item["keywords"].split(",")
            if keyword.strip()
        ]
    return keywords


def merge_docs(*docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge multiple document lists, removing duplicates based on document ID.

    Args:
        *docs: Variable number of document lists to merge.

    Returns:
        A merged list of documents with duplicates removed.
    """
    documents = []
    document_ids = set()

    for doc_list in docs:
        for doc in doc_list:
            doc_id = doc.get("id")
            if doc_id and doc_id not in document_ids:
                documents.append(doc)
                document_ids.add(doc_id)

    return documents


def find_duplicate_documents(documents):
    seen = set()
    duplicates = []

    for doc in documents:
        id = doc.get("id")
        if id in seen:
            duplicates.append(doc)
        else:
            seen.add(id)

    return duplicates


def _download_fsgeodata_metadata():
    """Download all xml metadata from fsgeodata and store in DEST_OUTPUT_DIR."""

    create_output_dir()

    base_url = "https://data.fs.usda.gov/geodata/edw/datasets.php"
    metadata_urls = []
    file_count = 0

    resp = requests.get(base_url)
    soup = BeautifulSoup(resp.content, "html.parser")

    anchors = soup.find_all("a")
    for anchor in anchors:
        if anchor and anchor.get_text() == "metadata":
            metadata_urls.append(anchor["href"])

    for metadata_url in metadata_urls:
        url = f"https://data.fs.usda.gov/geodata/edw/{metadata_url}"

        outfile_name = f"{DEST_OUTPUT_DIR}/{url.split('/')[-1]}"
        console.print(
            f"Downloading {url} to {outfile_name} ({file_count + 1}/{len(metadata_urls)})"
        )
        if not os.path.exists(outfile_name):
            resp = requests.get(url)
            with open(outfile_name, "wb") as f:
                f.write(resp.content)
                file_count += 1


def _download_datahub_metadata():
    """Download all json metadata from datahub and store in DEST_OUTPUT_DIR."""

    source_url = "https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json"

    response = requests.get(source_url)
    console.print(
        f"Downloading {source_url} to {DEST_OUTPUT_DIR}/datahub_metadata.json"
    )
    if response.status_code == 200:
        with open(f"{DEST_OUTPUT_DIR}/datahub_metadata.json", "w") as f:
            f.write(response.text)


def _download_rda_metadata():
    """Download all json metadata from rda and store in DEST_OUTPUT_DIR."""

    source_url = "https://www.fs.usda.gov/rds/archive/webservice/datagov"

    response = requests.get(source_url)
    if response.status_code == 200:
        console.print(
            f"Downloading {source_url} to {DEST_OUTPUT_DIR}/rda_metadata.json"
        )
        with open(f"{DEST_OUTPUT_DIR}/rda_metadata.json", "w") as f:
            f.write(response.text)


def _parse_fsgeodata_metadata():
    """Read all xml files in the DEST_OUTPUT_DIR and parse them into a list of metadata dictionaries.

    Returns:
        list: List of metadata dictionaries.
    """

    xml_files = [f for f in os.listdir(DEST_OUTPUT_DIR) if f.endswith(".xml")]

    assets = []

    for xml_file in xml_files:
        url = f"https://data.fs.usda.gov/geodata/edw/edw_resources/meta/{xml_file}"
        with open(f"{DEST_OUTPUT_DIR}/{xml_file}", "r") as file_pointer:
            soup = BeautifulSoup(file_pointer, "xml")
            if soup.find("title"):
                title = strip_html_tags(soup.find("title").get_text())
            else:
                title = ""

            desc_block = ""
            abstract = ""
            if soup.find("descript"):
                desc_block = soup.find("descript")
                abstract = strip_html_tags(desc_block.find("abstract").get_text())
            themekeys = soup.find_all("themekey")
            keywords = [key.get_text() for key in themekeys]

            asset = {
                "id": hash_string(title.lower().strip()),
                "title": title,
                "description": abstract,
                "metadata_source_url": url,
                "keywords": keywords,
                "src": "fsgeodata",
            }

            assets.append(asset)

    return assets


def _parse_datahub_metadata():
    """Parse the datahub metadata json file and return a list of metadata dictionaries.

    Returns:
        list: List of metadata dictionaries.
    """
    assets = []

    with open(f"{DEST_OUTPUT_DIR}/datahub_metadata.json", "r") as f:
        json_data = json.load(f)

        for item in json_data.get("dataset", []):
            title = item.get("title", "").strip().lower()
            keywords = get_keywords(item.get("keyword", []))
            data = {
                "id": hash_string(title),
                "title": item.get("title"),
                "identifier": item.get("identifier"),
                "description": strip_html_tags(item.get("description")),
                "url": item.get("url"),
                "keywords": keywords,
                "src": "datahub",
            }
            assets.append(data)

    return assets


def _parse_rda_metadata():
    """Parse the rda metadata json file and return a list of metadata dictionaries.

    Returns:
        list: List of metadata dictionaries.
    """

    assets = []

    with open(f"{DEST_OUTPUT_DIR}/rda_metadata.json", "r") as f:
        json_data = json.load(f)

        for item in json_data.get("dataset", []):
            title = item.get("title", "").strip().lower()
            keywords = get_keywords(item.get("keyword", []))
            data = {
                "id": hash_string(title),
                "title": item.get("title"),
                "identifier": item.get("identifier"),
                "description": strip_html_tags(item.get("description")),
                "url": item.get("url"),
                "keywords": keywords,
                "src": "rda",
            }
            assets.append(data)

    return assets


def _parse_all_metadata():
    """Parses all downloaded metadata and stores into one json file."""

    fsgeodata_assets = _parse_fsgeodata_metadata()
    datahub_assets = _parse_datahub_metadata()
    rda_assets = _parse_rda_metadata()

    assets = merge_docs(fsgeodata_assets, datahub_assets, rda_assets)

    save_path = f"{DEST_OUTPUT_DIR}/all_usfs_metadata.json"
    with open(save_path, "w") as f:
        json.dump(assets, f, indent=4)

    return assets


@cli.command()
def clear_docs_table():
    """
    Clear the documents table in the vector database.
    """
    console.print("[red]Clearing documents table...[/red]")
    empty_documents_table()
    console.print("[green]Documents table cleared![/green]")


@cli.command(name="download-all", short_help="Download all metadata from the catalog")
def download_all_metadata():
    """
    Download all metadata from the catalog.
    """
    console.print("[blue]Downloading all metadata...[/blue]")
    # Placeholder for actual download logic
    _download_fsgeodata_metadata()
    _download_datahub_metadata()
    _download_rda_metadata()
    console.print("[green]All metadata downloaded successfully![/green]")


@cli.command()
def embed_and_store():
    """Embed all documents in the documents table and store the embeddings in the vector column."""

    model = SentenceTransformer("all-MiniLM-L6-v2")
    recursive_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=65, chunk_overlap=0
    )

    docs = merge_docs(_parse_all_metadata())
    fsdocs = [USFSDocument(**item) for item in docs]

    # Collect all records for bulk insert
    records = []

    for doc in fsdocs:
        title = doc.title
        description = doc.description
        keywords = ",".join(kw for kw in doc.keywords) or []
        src = doc.src
        combined_text = f"Title: {title}\nDescription: {description}\nKeywords: {keywords}\nSource: {src}"

        chunks = recursive_text_splitter.create_documents([combined_text])

        for idx, chunk in enumerate(chunks):
            metadata = {
                "doc_id": doc.id,  # or fsdoc.doc_id if that's the field name
                "chunk_type": "title+description+keywords",
                "chunk_index": idx,
                "chunk_text": chunk.page_content,
                "title": title,
                "description": description,
                "keywords": doc.keywords,
                "src": doc.src,  # or another source identifier
            }

            embedding = model.encode(chunk.page_content)

            records.append(
                {
                    "embedding": embedding,
                    "metadata": metadata,
                    "title": title,
                    "description": description,
                }
            )

    # Perform bulk upsert
    bulk_upsert_to_vector_db(records)
    console.print(
        f"[green]Successfully upserted {len(records)} document chunks![/green]"
    )


@cli.command()
def run_api():
    """Run the FastAPI server."""

    console.print("[blue]Starting API server...[/blue]")
    uvicorn.run("api:api", host="0.0.0.0", port=8000, reload=True, workers=2)


@cli.command(
    name="doc-count", short_help="Get the count of documents in the vector database"
)
def doc_count():
    """Get the count of documents in the vector database."""

    count = count_documents()
    console.print(f"[green]Document count: {count}[/green]")


@cli.command(name="db-health", short_help="Check the health of the database connection")
def db_health():
    healthy = db_health_check()
    if healthy:
        console.print("[green]Database connection is healthy![/green]")
    else:
        console.print("[red]Database connection is not healthy![/red]")


@cli.command()
def parse_all_schema():
    xml_src_path = f"{DEST_OUTPUT_DIR}"

    xml_files = [f for f in os.listdir(xml_src_path) if f.endswith(".xml")]
    for xml_file in xml_files:
        # Parse XML file
        parser = EAInfoParser()
        in_file = f"{xml_src_path}/{xml_file}"
        eainfo = parser.parse_xml_file(in_file)

        id = save_eainfo(eainfo)
        # console.print(f"[cyan]Parsed schema for {xml_file} (ID: {id}):[/cyan] {eainfo}")


@cli.command()
def clear_eainfo():
    empty_eainfo_tables()


if __name__ == "__main__":
    cli()
