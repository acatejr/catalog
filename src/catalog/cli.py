import typer
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import List, Dict, Any
import hashlib
from catalog.db import (
    empty_documents_table,
    load_documents_from_json,
    save_to_vector_db,
)
from catalog.schema import USFSDocument
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

cli = typer.Typer()

DEST_OUTPUT_DIR = "tmp/catalog"


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


create_output_dir()


def _download_fsgeodata_metadata():
    base_url = "https://data.fs.usda.gov/geodata/edw/datasets.php"
    metadata_urls = []
    file_count = 0

    resp = requests.get(base_url)
    soup = BeautifulSoup(resp.content, "html.parser")

    anchors = soup.find_all("a")
    for anchor in anchors:
        if anchor and anchor.get_text() == "metadata":
            metadata_urls.append(anchor["href"])

    for u in metadata_urls:
        url = f"https://data.fs.usda.gov/geodata/edw/{u}"
        outfile_name = f"{DEST_OUTPUT_DIR}/{u.split('/')[-1]}"

        if not os.path.exists(outfile_name):
            resp = requests.get(url)
            with open(outfile_name, "wb") as f:
                f.write(resp.content)
                file_count += 1


def _parse_fsgeodata_metadata():
    """Read all xml files in the DEST_OUTPUT_DIR and parse them into a list of metadata dictionaries.

    Returns:
        list: List of metadata dictionaries.
    """

    xml_files = [f for f in os.listdir(DEST_OUTPUT_DIR) if f.endswith(".xml")]

    assets = []

    for xml_file in xml_files:
        url = f"https://data.fs.usda.gov/geodata/edw/edw_resources/meta/{xml_file}"
        with open(f"{DEST_OUTPUT_DIR}/{xml_file}", "r") as f:
            soup = BeautifulSoup(f, "xml")
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
            keywords = [tk.get_text() for tk in themekeys]

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


def _fsgeodata():
    """Download all xml and json metadata from fsgeodata."""

    print("\tDownloading all fsgeodata metadata.")
    _download_fsgeodata_metadata()
    fsgeodata_assets = _parse_fsgeodata_metadata()
    print(f"\tFound {len(fsgeodata_assets)} fsgeodata assets.")
    print("\tDone downloading all fsgeodata metadata!")

    return fsgeodata_assets


def _download_datahub_metadata():
    """Download all json metadata from datahub and store in DEST_OUTPUT_DIR."""
    source_url = "https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json"

    response = requests.get(source_url)
    if response.status_code == 200:
        with open(f"{DEST_OUTPUT_DIR}/datahub_metadata.json", "w") as f:
            f.write(response.text)


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


def _datahub():
    """Download all json metadata from datahub."""

    print("\tDownloading all datahub metadata.")
    _download_datahub_metadata()
    datahub_assets = _parse_datahub_metadata()
    print(f"\tFound {len(datahub_assets)} datahub assets.")
    print("\tDone downloading all datahub metadata!")
    return datahub_assets


def _download_rda_metadata():
    """Download all json metadata from rda and store in DEST_OUTPUT_DIR."""

    source_url = "https://www.fs.usda.gov/rds/archive/webservice/datagov"

    response = requests.get(source_url)
    if response.status_code == 200:
        with open(f"{DEST_OUTPUT_DIR}/rda_metadata.json", "w") as f:
            f.write(response.text)


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


def _rda():
    """Download all xml and json metadata from rda."""

    print("\tDownloading all rda metadata.")
    _download_rda_metadata()
    rda_assets = _parse_rda_metadata()
    print(f"\tFound {len(rda_assets)} rda assets.")
    print("\tDone downloading all rda metadata!")
    return rda_assets


@cli.command()
def load_catalog_data():
    """Download all xml and json metadata, parse all dadta into a metadata dictionary.  Load the metadata
    dictionary into a documents table.
    """
    assets = []
    print("Loading all catalog data.")
    fsgeodata_assets = _fsgeodata()
    print("-----")
    datahub_assets = _datahub()
    print("-----")
    rda_assets = _rda()
    print("Done loading all catalog data!")

    assets = merge_docs(fsgeodata_assets, datahub_assets, rda_assets)
    print(f"Total unique assets: {len(assets)}")


@cli.command()
def run_api():
    """Run the catalog api."""

    print("Running catalog api.")


@cli.command()
def clear_docs_table():
    """Empty the documents table in the documents database table."""

    empty_documents_table()
    print("Emptied documents table in vector database.")


def _parse_all():
    """Parse all metadata files and return a list of metadata dictionaries.

    Returns:
        list: List of metadata dictionaries.
    """

    fsgeodata_assets = _parse_fsgeodata_metadata()
    datahub_assets = _parse_datahub_metadata()
    rda_assets = _parse_rda_metadata()

    all_assets = fsgeodata_assets + datahub_assets + rda_assets
    return all_assets


@cli.command()
def embed_and_store():
    """Embed all documents in the documents table and store the embeddings in the vector column."""

    model = SentenceTransformer("all-MiniLM-L6-v2")
    recursive_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=65, chunk_overlap=0
    )

    docs = merge_docs(_parse_all())
    fsdocs = [USFSDocument(**item) for item in docs]

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

            save_to_vector_db(
                embedding=embedding,
                metadata=metadata,
                title=title,
                desc=description,
            )


if __name__ == "__main__":
    cli()
