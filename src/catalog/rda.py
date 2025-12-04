import requests
from rich import print as rprint
import os
import json
from catalog.lib import clean_str

SOURCE_URL = "https://www.fs.usda.gov/rds/archive/webservice/datagov"
DEST_OUTPUT_DIR = "data/rda"
DEST_OUTPUT_FILE = "rda_metadata.json"


class RDALoader:
    def __init__(self):
        os.makedirs(DEST_OUTPUT_DIR, exist_ok=True)

    def download(self):
        response = requests.get(SOURCE_URL)
        if response.status_code == 200:
            rprint(f"Downloading {SOURCE_URL} to {DEST_OUTPUT_DIR}/{DEST_OUTPUT_FILE}")
            json_data = response.json()

            with open(f"{DEST_OUTPUT_DIR}/{DEST_OUTPUT_FILE}", "w") as f:
                json.dump(json_data, f, indent=4)

    def parse_metadata(self):
        documents = []
        src_file = f"{DEST_OUTPUT_DIR}/{DEST_OUTPUT_FILE}"

        if not os.path.exists(src_file):
            rprint(
                f"[red]Source file {src_file} does not exist. Please run download() first.[/red]"
            )
            return []

        with open(src_file, "r") as f:
            json_data = json.load(f)
            dataset = json_data["dataset"]
            for item in dataset:
                title = clean_str(item["title"])
                description = clean_str(item["description"])
                keywords = item["keyword"]

                doc = {"title": title, "description": description, "keywords": keywords, "src": "rda"}

                documents.append(doc)

        return documents


if __name__ == "__main__":
    rda = RDALoader()
    rda.parse()
