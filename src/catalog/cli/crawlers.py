import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import json
from catalog.lib.docs import get_keywords
from catalog.lib import strip_html_tags, hash_string
from typing import List, Dict, Any

load_dotenv()


class FSGeodataHarvester:
    def __init__(self):
        self.base_url = "https://data.fs.usda.gov/geodata/edw/datasets.php"
        self.temp_folder = "./tmp"

    def download_metadata_files(self):
        file_count = 0
        metadata_urls = []

        resp = requests.get(self.base_url)
        soup = BeautifulSoup(resp.content, "html.parser")

        anchors = soup.find_all("a")
        for anchor in anchors:
            if anchor and anchor.get_text() == "metadata":
                metadata_urls.append(anchor["href"])

        # Download the metadata files
        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)

        for u in metadata_urls:
            url = f"https://data.fs.usda.gov/geodata/edw/{u}"
            outfile_name = f"{self.temp_folder}/{u.split('/')[-1]}"

            if not os.path.exists(outfile_name):
                resp = requests.get(url)
                with open(outfile_name, "wb") as f:
                    f.write(resp.content)
                    file_count += 1

        return file_count

    def parse_metadata(self):
        xml_files = [f for f in os.listdir(self.temp_folder) if f.endswith(".xml")]

        assets = []

        for xml_file in xml_files:
            url = f"https://data.fs.usda.gov/geodata/edw/edw_resources/meta/{xml_file}"
            with open(f"{self.temp_folder}/{xml_file}", "r") as f:
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


class DataHubHarvester:
    def __init__(self):
        self.source_url = "https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json"
        self.temp_folder = "./tmp"

    def download_metadata_files(self):
        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)

        response = requests.get(self.source_url)
        if response.status_code == 200:
            with open(f"{self.temp_folder}/datahub_metadata.json", "w") as f:
                f.write(response.text)
        else:
            print(f"Failed to download metadata files: {response.status_code}")

    def read_json_file(self):
        """Parse the JSON file and return its content."""
        with open(f"{self.temp_folder}/datahub_metadata.json", "r") as f:
            return json.load(f)

    def parse_metadata(self):
        assets = []

        json_data = self.read_json_file()

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


class RDAHarvester:
    def __init__(self):
        self.source_url = "https://www.fs.usda.gov/rds/archive/webservice/datagov"
        self.temp_folder = "./tmp"

    def download_metadata_files(self):
        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)

        response = requests.get(self.source_url)
        if response.status_code == 200:
            with open(f"{self.temp_folder}/rda_metadata.json", "w") as f:
                f.write(response.text)
        else:
            print(f"Failed to download metadata files: {response.status_code}")

    def read_json_file(self):
        """Parse the JSON file and return its content."""
        with open(f"{self.temp_folder}/rda_metadata.json", "r") as f:
            return json.load(f)

    def parse_metadata(self):
        assets = []

        json_data = self.read_json_file()

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
