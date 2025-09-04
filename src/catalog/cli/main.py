import fire
import datetime
import os
import json
from bs4 import BeautifulSoup
import requests
from catalog.utils.main import hash_string, strip_html_tags, get_keywords, merge_docs
from typing import List
from catalog.db.schema import USFSDocument
from catalog.db.main import save_to_vector_db
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from catalog.db.main import empty_documents_table
import uvicorn


DEST_OUTPUT_DIR = "tmp/catalog"


def create_output_dir():
    if not os.path.exists(DEST_OUTPUT_DIR):
        os.makedirs(DEST_OUTPUT_DIR)


def health():
    """Prints health status."""
    now = datetime.datetime.now()
    print(f"Health check at {now.isoformat()}")


def _parse_fsgeodata_metadata():
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
            # idinfo_citation_citeinfo_pubdate = soup.find("pubdate")

            # if idinfo_citation_citeinfo_pubdate:
            #     modified = str(
            #         arrow.get(idinfo_citation_citeinfo_pubdate.get_text())
            #     )
            # else:
            #     modified = ""

            asset = {
                "id": hash_string(title.lower().strip()),
                "title": title,
                "description": abstract,
                # "modified": modified,
                "metadata_source_url": url,
                "keywords": keywords,
                "src": "fsgeodata",
            }

            assets.append(asset)

    return assets


def _harvesest_fsgeodata(dl=False):
    base_url = "https://data.fs.usda.gov/geodata/edw/datasets.php"
    metadata_urls = []
    file_count = 0

    create_output_dir()

    resp = requests.get(base_url)
    soup = BeautifulSoup(resp.content, "html.parser")

    anchors = soup.find_all("a")
    for anchor in anchors:
        if anchor and anchor.get_text() == "metadata":
            metadata_urls.append(anchor["href"])

    # Download the metadata files if specified at cli switch
    if dl:
        for u in metadata_urls:
            url = f"https://data.fs.usda.gov/geodata/edw/{u}"
            outfile_name = f"{DEST_OUTPUT_DIR}/{u.split('/')[-1]}"

            if not os.path.exists(outfile_name):
                resp = requests.get(url)
                with open(outfile_name, "wb") as f:
                    f.write(resp.content)
                    file_count += 1


def harvest_fsgeodata(dl=False):
    """Harvests data from fsgeodata.

    Args:
        dl (bool): If True, download new data from fsgeodata. If False, use existing data.
    """

    print("Harvesting data from fsgeodata...")
    _harvesest_fsgeodata(dl=dl)
    assets = _parse_fsgeodata_metadata()
    return assets


def _parse_datahub_metadata():
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


def _harvest_datahub(dl):
    source_url = "https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json"

    create_output_dir()

    if dl:
        response = requests.get(source_url)
        if response.status_code == 200:
            with open(f"{DEST_OUTPUT_DIR}/datahub_metadata.json", "w") as f:
                f.write(response.text)


def harvest_datahub(dl=False):
    """Harvests data from datahub."""

    _harvest_datahub(dl=dl)
    assets = _parse_datahub_metadata()
    return assets


def _harvest_rda(dl=False):
    source_url = "https://www.fs.usda.gov/rds/archive/webservice/datagov"

    if not os.path.exists(DEST_OUTPUT_DIR):
        os.makedirs(DEST_OUTPUT_DIR)

    if dl:
        response = requests.get(source_url)
        if response.status_code == 200:
            with open(f"{DEST_OUTPUT_DIR}/rda_metadata.json", "w") as f:
                f.write(response.text)


def _parse_rda_metadata():
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


def harvest_rda(dl=False):
    """Harvests data from rda.

    Args:
        dl (bool): If True, download new data from fsgeodata. If False, use existing data.
    """

    _harvest_rda(dl=dl)
    assets = _parse_rda_metadata()
    print(f"Harvested {len(assets)} assets from RDA.")


def _parse_all():
    fsgeodata_assets = _parse_fsgeodata_metadata()
    datahub_assets = _parse_datahub_metadata()
    rda_assets = _parse_rda_metadata()

    all_assets = fsgeodata_assets + datahub_assets + rda_assets
    return all_assets


def parse_all():
    """Parse data from all sources."""

    assets = _parse_all()
    print(f"Total assets parsed: {len(assets)}")

    documents = merge_docs(assets)
    print(f"Total unique documents after merging: {len(documents)}")


def clear_docs_table():

    empty_documents_table()
    print("Emptied documents table in vector database.")


def embed_and_store():

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
        combined_text = (
            f"Title: {title}\nDescription: {description}\nKeywords: {keywords}"
        )

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


def run_api(host="127.0.0.1", port=8000, reload=True):
    """Run the FastAPI server.

    Args:
        host (str): Host to bind the server to. Defaults to "127.0.0.1".
        port (int): Port to bind the server to. Defaults to 8000.
        reload (bool): Enable auto-reload for development. Defaults to True.
    """
    print(f"Starting Catalog API server on {host}:{port}")
    uvicorn.run(
        "catalog.api.main:app",
        host=host,
        port=port,
        reload=reload
    )


def main():
    fire.Fire(
        {
            "health": health,
            "harvest-fsgeodata": harvest_fsgeodata,
            "harvest-datahub": harvest_datahub,
            "harvest-rda": harvest_rda,
            "parse-all": parse_all,
            "embed-and-store": embed_and_store,
            "clear-docs-table": clear_docs_table,
            "run-api": run_api,
        }
    )


if __name__ == "__main__":
    main()
