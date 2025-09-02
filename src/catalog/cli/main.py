import fire
import datetime
import os
from bs4 import BeautifulSoup
import requests

DEST_OUTPUT_DIR = "tmp/catalog"

def create_output_dir():
    if not os.path.exists(DEST_OUTPUT_DIR):
        os.makedirs(DEST_OUTPUT_DIR)


def health():
    """Prints health status."""
    now = datetime.datetime.now()
    print(f"Health check at {now.isoformat()}")


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

    _harvesest_fsgeodata(dl=dl)
    print("Harvesting data from fsgeodata...")


def _harvest_datahub():
    pass

def harvest_datahub():
    """Harvests data from datahub."""

    _harvest_datahub
    print("Harvesting data from datahub...")


def _harvest_rda(dl=False):

    source_url = "https://www.fs.usda.gov/rds/archive/webservice/datagov"

    if not os.path.exists(DEST_OUTPUT_DIR):
        os.makedirs(DEST_OUTPUT_DIR)

    response = requests.get(source_url)
    if response.status_code == 200:
        with open(f"{DEST_OUTPUT_DIR}/rda_metadata.json", "w") as f:
            f.write(response.text)
    else:
        print(f"Failed to download metadata files: {response.status_code}")


def harvest_rda(dl=False):
    """Harvests data from rda.

    Args:
        dl (bool): If True, download new data from fsgeodata. If False, use existing data.
    """

    _harvest_rda(dl=dl)


def _harvest_all():
    pass

def harvest_all():
    """Harvests data from all sources."""

    _harvest_all()
    print("Harvesting data from all sources...")


def main():
    fire.Fire(
        {
            "health": health,
            "harvest-fsgeodata": harvest_fsgeodata,
            "harvest-datahub": harvest_datahub,
            "harvest-rda": harvest_rda,
            "harvest-all": harvest_all,
        }
    )


if __name__ == "__main__":
    main()
