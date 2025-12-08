import os
import requests
import json
from rich import print as rprint
from catalog.lib import clean_str, hash_string

METADATA_SOURCE_URL = "https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json"
DEST_OUTPUT_DIR = "data/gdd"
DEST_OUTPUT_FILE = "gdd_metadata.json"


class GeospatialDataDiscovery:
    def __init__(self):
        pass

    def download_gdd_metadata(self):
        response = requests.get(METADATA_SOURCE_URL)

        # Make output dir if needed.
        os.makedirs(DEST_OUTPUT_DIR, exist_ok=True)

        if response.status_code == 200:
            rprint(
                f"Downloading {METADATA_SOURCE_URL} to {DEST_OUTPUT_DIR}/{DEST_OUTPUT_FILE}"
            )

            with open(f"{DEST_OUTPUT_DIR}/{DEST_OUTPUT_FILE}", "w") as f:
                f.write(response.text)

    def parse_metadata(self) -> None:
        """_summary_"""

        documents = []

        src_file = f"{DEST_OUTPUT_DIR}/{DEST_OUTPUT_FILE}"

        if not os.path.exists(src_file):
            rprint(
                f"[red]Source file {src_file} does not exist. Please run download() first.[/red]"
            )
            return []

        with open(src_file, "r") as f:
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

        """dict_keys(['@type', 'identifier', 'landingPage', 'title', 'description', 'keyword',
        'issued', 'modified', 'publisher', 'contactPoint', 'accessLevel', 'spatial', 'license',
        'programCode', 'bureauCode', 'theme', 'progressCode', 'distribution'])
        """
