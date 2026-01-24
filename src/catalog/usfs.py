from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from catalog.lib import clean_str, hash_string
import os
import json
# from rich.print import print as rprint

DATA_DIR = "./data/usfs"


class USFS:
    def __init__(self, output_dir: str = DATA_DIR) -> None:
        self.output_dir = Path(output_dir)

    def download_metadata(self) -> None:
        """Download USFS metadata files."""

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.download_fsgeodata()
        self.download_rda()
        self.download_gdd()

    def download_fsgeodata(self) -> None:
        """
        Docstring for download_fsgeodata

        :param self: Description
        """
        print("Downloading FSGeoData metadata...")
        fsgeodata = FSGeodataLoader(data_dir=self.output_dir / "fsgeodata")
        fsgeodata.download_all()

    def download_rda(self) -> None:
        """
        Docstring for download_rda

        :param self: Description
        """
        print("Downloading RDA metadata...")
        rda = RDALoader()
        rda.download()

    def download_gdd(self) -> None:
        """
        Docstring for download_gdd

        :param self: Description
        """
        print("Downloading GDD metadata...")
        gdd = GeospatialDataDiscovery()
        gdd.download_gdd_metadata()

    def build_metadata_catalog(self) -> None:
        pass

        # # Placeholder for actual download logic
        # metadata_file = self.output_dir / "usfs_metadata.json"
        # with open(metadata_file, "w", encoding="utf-8") as f:
        #     f.write('{"status": "metadata downloaded"}')


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
        # rprint(f"Fetching datasets page: {self.DATASETS_URL}")
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

    def download_file(self, url, output_path, description="file"):
        """Download a file from URL to output_path"""
        try:
            # rprint(f"  Downloading {description}: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)

            # rprint(f"  ✓ Saved to {output_path}")
            return True

        except requests.exceptions.RequestException as e:
            # rprint(f"  ✗ Failed to download {description}: {e}")
            return False

    def download_service_info(self, url, output_path):
        """Download service info (JSON format)"""
        try:
            # rprint(f"  Downloading service info: {url}")
            # Add ?f=json to get JSON response
            json_url = f"{url}?f=json"
            response = self.session.get(json_url, timeout=30)
            response.raise_for_status()

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            # rprint(f"  ✓ Saved to {output_path}")
            return True

        except requests.exceptions.RequestException as e:
            # rprint(f"  ✗ Failed to download service info: {e}")
            return False

    def download_all(self):
        """Main method to download all datasets"""
        # rprint("=" * 70)
        # rprint("FSGeodata Downloader")
        # rprint("=" * 70)
        # rprint()

        # Fetch and parse the datasets page
        html_content = self.fetch_datasets_page()
        datasets = self.parse_datasets(html_content)

        # rprint(f"\nFound {len(datasets)} datasets")
        # rprint("=" * 70)
        # rprint()

        stats = {
            "total": len(datasets),
            "metadata_success": 0,
            "metadata_failed": 0,
            "service_success": 0,
            "service_failed": 0,
        }

        # Download each dataset
        for i, dataset in enumerate(datasets, 1):
            # rprint(f"[{i}/{len(datasets)}] Processing: {dataset['name']}")

            # Download metadata
            metadata_path = self.metadata_dir / f"{dataset['name']}.xml"
            if self.download_file(dataset["metadata_url"], metadata_path, "metadata"):
                stats["metadata_success"] += 1
            else:
                stats["metadata_failed"] += 1

            # Download service info if available
            if dataset["service_url"]:
                service_path = self.services_dir / f"{dataset['name']}_service.json"
                if self.download_service_info(dataset["service_url"], service_path):
                    stats["service_success"] += 1
                else:
                    stats["service_failed"] += 1
            else:
                pass
                # rprint("  ! No service URL found")

            # rprint()

            # Be nice to the server
            time.sleep(0.5)

        # Print summary
        # rprint("=" * 70)
        # rprint("Download Summary")
        # rprint("=" * 70)
        # rprint(f"Total datasets:        {stats['total']}")
        # rprint(f"Metadata downloaded:   {stats['metadata_success']}")
        # rprint(f"Metadata failed:       {stats['metadata_failed']}")
        # rprint(f"Services downloaded:   {stats['service_success']}")
        # rprint(f"Services failed:       {stats['service_failed']}")
        # rprint()
        # rprint(f"Data saved to: {self.data_dir.absolute()}")

    def parse_metadata(self):
        """Parse metadata XML to extract title and abstract"""

        documents = []
        xml_path = "data/usfs/fsgeodata/metadata"
        xml_files = Path(xml_path)

        if xml_files.is_dir():
            xml_files = list(xml_files.glob("*.xml"))
        else:
            xml_files = [xml_files]

        try:
            for idx, file in enumerate(xml_files):
                with open(file, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f, "xml")

                    title = (
                        clean_str(soup.find("title").get_text())
                        if soup.find("title")
                        else ""
                    )

                    descript = soup.find("descript")
                    if descript:
                        abstract = (
                            clean_str(descript.find("abstract").get_text())
                            if descript.find("abstract")
                            else ""
                        )
                        purpose = (
                            clean_str(descript.find("purpose").get_text())
                            if descript.find("purpose")
                            else ""
                        )

                    lineage = []
                    if soup.find_all("dataqual"):
                        if len(soup.find_all("dataqual")):
                            dataqual = soup.find_all("dataqual")[0]
                            procsteps = dataqual.find_all("procstep")
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

        except Exception as e:
            # rprint(f"  ✗ Failed to parse metadata {xml_path}: {e}")
            return {"title": "N/A", "abstract": "N/A"}

        return documents


class GeospatialDataDiscovery:
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
            # rprint(
            #     f"Downloading {METADATA_SOURCE_URL} to {DEST_OUTPUT_DIR}/{DEST_OUTPUT_FILE}"
            # )

            with open(
                f"{self.dest_output_dir}/{self.dest_output_file}", "w", encoding="utf-8"
            ) as f:
                f.write(response.text)

    def parse_metadata(self) -> None:
        """_summary_"""

        documents = []

        src_file = f"{self.dest_output_dir}/{self.dest_output_file}"

        if not os.path.exists(src_file):
            # rprint(
            #     f"[red]Source file {src_file} does not exist. Please run download() first.[/red]"
            # )
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
    # SOURCE_URL = "https://www.fs.usda.gov/rds/archive/webservice/datagov"
    # DEST_OUTPUT_DIR = "data/rda"
    # DEST_OUTPUT_FILE = "rda_metadata.json"

    def __init__(self):
        self.source_url = "https://www.fs.usda.gov/rds/archive/webservice/datagov"
        self.dest_output_dir = "./data/usfs/rda"
        self.dest_output_file = "rda_metadata.json"

        os.makedirs(self.dest_output_dir, exist_ok=True)

    def download(self):
        response = requests.get(self.source_url)
        if response.status_code == 200:
            # rprint(f"Downloading {SOURCE_URL} to {DEST_OUTPUT_DIR}/{DEST_OUTPUT_FILE}")
            json_data = response.json()

            with open(
                f"{self.dest_output_dir}/{self.dest_output_file}", "w", encoding="utf-8"
            ) as f:
                json.dump(json_data, f, indent=4)

    def parse_metadata(self):
        documents = []
        src_file = f"{self.dest_output_dir}/{self.dest_outut_file}"

        if not os.path.exists(src_file):
            # rprint(
            #     f"[red]Source file {src_file} does not exist. Please run download() first.[/red]"
            # )
            return []

        with open(src_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            dataset = json_data["dataset"]
            for item in dataset:
                title = clean_str(item["title"])
                description = clean_str(item["description"])
                keywords = item["keyword"]

                doc = {
                    "id": hash_string(title.lower().strip()),
                    "title": title,
                    "description": description,
                    "keywords": keywords,
                    "src": "rda",
                }

                documents.append(doc)

        return documents
