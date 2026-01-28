from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from catalog.lib import clean_str, hash_string, save_json
import os
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("catalog")

DATA_DIR = "./data/usfs"


class USFS:
    def __init__(self, output_dir: str = DATA_DIR) -> None:
        self.output_dir = Path(output_dir)

    def build_chromadb(self) -> None:
        """Build ChromaDB vector store from USFS catalog"""

        print("Building USFS ChromaDB vector store...")
        from catalog.core import ChromaVectorDB

        db = ChromaVectorDB()
        db.batch_load_documents()

    def build_catalog(self, format: str = "json"):
        print("Building USFS catalog...")
        fsgeodata = FSGeodataLoader()
        gdd = GeospatialDataDiscovery()
        rda = RDALoader()

        fsgeo_docs = fsgeodata.parse_metadata()
        gdd_docs = gdd.parse_metadata()
        rda_docs = rda.parse_metadata()
        documents = fsgeo_docs + rda_docs + gdd_docs

        print(f"USFS Catalog Docs: {len(documents)}")

        if format == "json":
            save_json(documents, "./data/usfs/catalog.json")

    def download_metadata(self) -> None:
        """Download USFS metadata files."""

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.download_fsgeodata()
        self.download_rda()
        self.download_gdd()

    def download_fsgeodata(self) -> None:
        """
        Handles downloading of FSGeoData metadata
        """

        print("Downloading FSGeoData metadata...")
        fsgeodata = FSGeodataLoader(data_dir=self.output_dir / "fsgeodata")
        fsgeodata.download_all()

    def download_rda(self) -> None:
        """
        Downloads Research Data Archive (RDA) metadata
        """

        print("Downloading RDA metadata...")
        rda = RDALoader()
        rda.download()

    def download_gdd(self) -> None:
        """
        Downloads Geospatial Data Discovery (GDD) metadata
        """

        print("Downloading GDD metadata...")
        gdd = GeospatialDataDiscovery()
        gdd.download_gdd_metadata()


class FSGeodataLoader:
    """Downloads metadata and web services data from USFS Geodata Clearinghouse"""

    BASE_URL = "https://data.fs.usda.gov"
    METADATA_BASE_URL = f"{BASE_URL}/geodata/edw/edw_resources/meta/"

    DATASETS_URL = f"{BASE_URL}/geodata/edw/datasets.php"

    def __init__(self, data_dir="data/usfs/fsgeodata"):
        """Initialize downloader with data directory"""
        self.data_dir = Path(data_dir)
        self.metadata_dir = self.data_dir / "metadata"
        self.services_dir = self.data_dir / "services"

        # Create directories
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.services_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; FSGeodataDownloader/1.0)"}
        )

    def fetch_datasets_page(self):
        """Fetch the main datasets page"""
        response = self.session.get(self.DATASETS_URL)
        response.raise_for_status()
        return response.text

    def parse_datasets(self, html_content):
        """Parse the HTML and extract metadata and service URLs"""
        soup = BeautifulSoup(html_content, "html.parser")
        datasets = []

        # Find all links to metadata XML files
        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Look for metadata XML files
            if "/meta/" in href and href.endswith(".xml"):
                dataset_name = Path(href).stem
                metadata_url = urljoin(self.METADATA_BASE_URL, dataset_name + ".xml")

                # Try to find associated map service URL in nearby elements
                service_url = None
                parent = link.find_parent()
                if parent:
                    # Look for MapServer links in the same section
                    service_links = parent.find_all(
                        "a", href=lambda h: h and "MapServer" in h
                    )
                    if service_links:
                        service_url = service_links[0]["href"]

                datasets.append(
                    {
                        "name": dataset_name,
                        "metadata_url": metadata_url,
                        "service_url": service_url,
                    }
                )

        return datasets

    def download_file(self, url: str, output_path: Path, description: str = "file") -> bool:
        """Download a file from URL to output_path

        args:
            url (str): URL to download
            output_path (Path): Path to save the downloaded file
            description (str): Description of the file being downloaded
        returns:
            bool: True if download succeeded, False otherwise
        """

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            logger.error(f"Failed to download {description} from {url}: {e}")
            return False

        return True

    def download_service_info(self, url: str, output_path: Path) -> bool:
        """Download service info (JSON format)"""

        json_url = f"{url}?f=json"
        try:
            response = self.session.get(json_url, timeout=30)
            response.raise_for_status()
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(response.text)
        except Exception as e:
            logger.error(f"Failed to download service info from {json_url}: {e}")
            return False


        return True

    def download_all(self):
        """Main method to download all datasets"""

        # Fetch and parse the datasets page
        html_content = self.fetch_datasets_page()
        datasets = self.parse_datasets(html_content)

        stats = {
            "total": len(datasets),
            "metadata_success": 0,
            "metadata_failed": 0,
            "service_success": 0,
            "service_failed": 0,
        }

        # Download each dataset
        for i, dataset in enumerate(datasets, 1):
            # Download metadata
            metadata_path = self.metadata_dir / f"{dataset['name']}.xml"

            if not metadata_path.exists():
                if self.download_file(dataset["metadata_url"], metadata_path, "metadata"):
                    stats["metadata_success"] += 1
                else:
                    stats["metadata_failed"] += 1
            else:
                stats["metadata_success"] += 1

            # Download service info if available
            if dataset["service_url"]:
                service_path = self.services_dir / f"{dataset['name']}_service.json"
                if not service_path.exists():
                    if self.download_service_info(dataset["service_url"], service_path):
                        stats["service_success"] += 1
                    else:
                        stats["service_failed"] += 1
                else:
                    stats["service_success"] += 1

            # Be nice to the server
            time.sleep(0.25)

    def parse_metadata(self):
        """Parse metadata XML to extract title and abstract"""

        documents = []
        xml_path = "data/usfs/fsgeodata/metadata"
        xml_files = Path(xml_path)

        if xml_files.is_dir():
            xml_files = list(xml_files.glob("*.xml"))
        else:
            xml_files = [xml_files]

        for idx, xml_file in enumerate(xml_files):
            with open(xml_file, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "xml")
                abstract = ""
                purpose = ""
                keywords = []
                procdate = ""
                procdesc = ""

                title_elem = soup.find("title")
                title = clean_str(title_elem.get_text()) if title_elem else ""

                descript = soup.find("descript")
                if descript:
                    abstract_elem = descript.find("abstract")
                    abstract = (
                        clean_str(abstract_elem.get_text()) if abstract_elem else ""
                    )
                    purpose_elem = descript.find("purpose")
                    purpose = clean_str(purpose_elem.get_text()) if purpose_elem else ""

                lineage = []
                dataqual = soup.find_all("dataqual")
                if dataqual:
                    dq = dataqual[0]
                    procsteps = dq.find_all("procstep")
                    for step in procsteps:
                        if step.find("procdate"):
                            procdate = step.find("procdate").get_text()
                        if step.find("procdesc"):
                            procdesc = step.find("procdesc").get_text()

                        if procdate and procdesc:
                            procstep = {
                                "description": procdesc,
                                "date": procdate,
                            }
                            lineage.append(procstep)

                if soup.find_all("themekey") is not None:
                    themekeys = soup.find_all("themekey")
                    if len(themekeys) > 0:
                        keywords = [w.get_text() for w in themekeys]

                document = {
                    "id": hash_string(title.lower().strip()),
                    "title": title,
                    "lineage": lineage,
                    "abstract": abstract,
                    "purpose": purpose,
                    "keywords": keywords,
                    "src": "fsgeodata",
                }

                documents.append(document)

        return documents


class GeospatialDataDiscovery:
    """
    Harvests metadata from USFS Geospatial Data Discovery (GDD) portal
    https://data-usfs.hub.arcgis.com/pages/geospatial-data-discovery-gdd
    """

    def __init__(self):
        self.metadata_source_url = (
            "https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json"
        )
        self.dest_output_dir = "./data/usfs/gdd"
        self.dest_output_file = "gdd_metadata.json"

    def download_gdd_metadata(self):
        response = requests.get(self.metadata_source_url)

        # Make output dir if needed.
        os.makedirs(self.dest_output_dir, exist_ok=True)

        if response.status_code == 200:
            fpath = Path(self.dest_output_dir) / self.dest_output_file
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(response.text)
        else:
            logger.error(
                f"Failed to download GDD metadata: {response.status_code} {response.text}"
            )

    def parse_metadata(self) -> None:
        """
        Parses GDD metadata JSON file and returns list of documents

        :return: List of document dictionaries
        :rtype: list[dict]
        """

        documents = []

        src_file = Path(self.dest_output_dir) / self.dest_output_file

        if not os.path.exists(src_file):
            return []

        with open(src_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

            if "dataset" in json_data.keys():
                dataset = json_data.get("dataset")

                if dataset and len(dataset) > 0:
                    for item in dataset:
                        title = (
                            clean_str(item.get("title"))
                            if "title" in item.keys()
                            else ""
                        )
                        description = (
                            clean_str(item.get("description"))
                            if "description" in item.keys()
                            else ""
                        )
                        keyword = (
                            item.get("keyword") if "keyword" in item.keys() else []
                        )
                        theme = item.get("theme") if "theme" in item.keys() else []

                        document = {
                            "id": hash_string(title.lower().strip()),
                            "title": title,
                            "description": description,
                            "keywords": keyword,
                            "themes": theme,
                            "src": "gdd",
                        }

                        documents.append(document)

        return documents


class RDALoader:
    def __init__(self):
        self.source_url = "https://www.fs.usda.gov/rds/archive/webservice/datagov"
        self.dest_output_dir = "./data/usfs/rda"
        self.dest_output_file = "rda_metadata.json"

        os.makedirs(self.dest_output_dir, exist_ok=True)

    def download(self):
        response = requests.get(self.source_url)
        if response.status_code == 200:
            json_data = response.json()

            src_file = Path(self.dest_output_dir) / self.dest_output_file
            with open(src_file, "w", encoding="utf-8"
            ) as f:
                json.dump(json_data, f, indent=4)

    def parse_metadata(self):
        documents = []
        src_file = Path(self.dest_output_dir) / self.dest_output_file

        if not os.path.exists(src_file):
            return []

        with open(src_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            dataset = json_data.get("dataset", [])
            for item in dataset:
                title = clean_str(item.get("title"))
                description = clean_str(item.get("description"))
                keywords = item.get("keyword")

                doc = {
                    "id": hash_string(title.lower().strip()),
                    "title": title,
                    "description": description,
                    "keywords": keywords,
                    "src": "rda",
                }

                documents.append(doc)

        return documents
