import requests
from rich import print as rprint
import os

SOURCE_URL = "https://www.fs.usda.gov/rds/archive/webservice/datagov"
DEST_OUTPUT_DIR = "data/rda"

def download_rda_metadata():
    response = requests.get(SOURCE_URL)

    os.makedirs(DEST_OUTPUT_DIR, exist_ok=True)

    if response.status_code == 200:
        rprint(f"Downloading {SOURCE_URL} to {DEST_OUTPUT_DIR}/rda_metadata.json")

        with open(f"{DEST_OUTPUT_DIR}/rda_metadata.json", "w") as f:
            f.write(response.text)