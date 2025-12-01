import os
import requests
from rich import print as rprint

METADATA_SOURCE_URL = "https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json"
DEST_OUTPUT_DIR = "data/gdd"


def download_gdd_metadata():
    response = requests.get(METADATA_SOURCE_URL)

    os.makedirs(DEST_OUTPUT_DIR, exist_ok=True)

    if response.status_code == 200:
        rprint(
            f"Downloading {METADATA_SOURCE_URL} to {DEST_OUTPUT_DIR}/gdd_metadata.json"
        )

        with open(f"{DEST_OUTPUT_DIR}/gdd_metadata.json", "w") as f:
            f.write(response.text)
