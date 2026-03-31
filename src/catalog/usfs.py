import os
import requests
import json
from pathlib import Path
import click
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .lib import clean_str, hash_string


class USFS:
    def __init__(self):
        self.output_dir = "./data/usfs"

    def download_fsgeodata_metadata(self):
        BASE_URL = "https://data.fs.usda.gov"
        METADATA_BASE_URL = f"{BASE_URL}/geodata/edw/edw_resources/meta/"
        DATASETS_URL = f"{BASE_URL}/geodata/edw/datasets.php"

        output_dir = f"{self.output_dir}/fsgeodata"
        self.mkdir_output(output_dir)

        session = requests.Session()
        session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; FSGeodataDownloader/1.0)"}
        )
        response = session.get(DATASETS_URL)
        response.raise_for_status()
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")
        datasets = []

        # Find all links to metadata XML files
        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Look for metadata XML files
            if "/meta/" in href and href.endswith(".xml"):
                dataset_name = Path(href).stem
                metadata_url = urljoin(METADATA_BASE_URL, dataset_name + ".xml")

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

        click.echo(f"Found {len(datasets)} datasets with metadata links.")
        for dataset in datasets:
            meta_path = Path(output_dir) / f"{dataset['name']}.xml"
            if not os.path.exists(meta_path):
                click.echo(f"   Downloading metadata for {dataset['name']}...")
                try:
                    meta_response = session.get(dataset["metadata_url"])
                    meta_response.raise_for_status()
                    meta_path = Path(output_dir) / f"{dataset['name']}.xml"
                    with open(meta_path, "w", encoding="utf-8") as f:
                        f.write(meta_response.text)

                except requests.exceptions.RequestException as e:
                    click.echo(
                        f"   Failed to download metadata for {dataset['name']}: {e}"
                    )
            else:
                click.echo(
                    f"   Metadata for {dataset['name']} already exists. Skipping."
                )

    def download_gdd_metadata(self):

        source_url = "https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json"
        dest_output_dir = "./data/usfs/gdd"
        dest_output_file = "gdd_metadata.json"

        if os.path.exists(f"{dest_output_dir}/{dest_output_file}"):
            click.echo("   GDD metadata already exists. Skipping download.")
            return

        self.mkdir_output(dest_output_dir)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.fs.usda.gov/",
        }

        response = requests.get(source_url, headers=headers)
        response.raise_for_status()
        json_data = response.json()

        src_file = Path(dest_output_dir) / dest_output_file
        with open(src_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

    def download_rda_metadata(self):
        """
        Downloads Research Data Archive (RDA) metadata
        """

        source_url = "https://www.fs.usda.gov/rds/archive/webservice/datagov"
        dest_output_dir = "./data/usfs/rda"
        dest_output_file = "rda_metadata.json"

        if os.path.exists(f"{dest_output_dir}/{dest_output_file}"):
            click.echo("   RDA metadata already exists. Skipping download.")
            return

        self.mkdir_output(dest_output_dir)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.fs.usda.gov/",
        }
        response = requests.get(source_url, headers=headers)
        response.raise_for_status()
        json_data = response.json()

        src_file = Path(dest_output_dir) / dest_output_file
        with open(src_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

    def mkdir_output(self, dir_path: str = None) -> None:
        """Creates the output directory if it doesn't exist"""

        if dir_path is None:
            dir_path = self.output_dir

        os.makedirs(dir_path, exist_ok=True)

    def build_gdd_catalog(self):
        documents = []

        gdd_json_path = f"{self.output_dir}/gdd/gdd_metadata.json"
        if not os.path.exists(gdd_json_path):
            click.echo("\tGDD metadata not found.")
        else:
            with open(gdd_json_path, "r", encoding="utf-8") as f:
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

    def build_rda_catalog(self):
        documents = []

        rda_json_path = f"{self.output_dir}/rda/rda_metadata.json"
        if not os.path.exists(rda_json_path):
            click.echo("\tRDA metadata not found.")
        else:
            with open(rda_json_path, "r", encoding="utf-8") as f:
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

                            document = {
                                "id": hash_string(title.lower().strip()),
                                "title": title,
                                "description": description,
                                "keywords": keyword,
                                "themes": [],
                                "src": "rda",
                            }

                            documents.append(document)

        return documents

    def buld_fsgeodata_catalog(self):
        documents = []
        xml_path = f"{self.output_dir}/fsgeodata"
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

    def build_catalog(self):

        documents = []

        # FSGeodata
        fsgeodata_documents = self.buld_fsgeodata_catalog()
        documents.extend(fsgeodata_documents)

        # GDD
        gdd_documents = self.build_gdd_catalog()
        documents.extend(gdd_documents)

        # RDA
        rda_documents = self.build_rda_catalog()
        documents.extend(rda_documents)

        output_file = f"{self.output_dir}/usfs_catalog.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(documents, f, indent=4)
