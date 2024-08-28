# from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
import re
import arrow
from dotenv import load_dotenv


def remove_html(text):
    txt = re.sub("<[^<]+?>", "", text).replace("\n", "")
    return txt


def data_dot_gov():
    metadata_urls = [
        "https://catalog.data.gov/harvest/object/203bed83-5da3-4a64-b156-ea016f277b07",
        "https://catalog.data.gov/harvest/object/04643a90-e5fd-4602-a8fa-e8195dd16c5e",
        "https://catalog.data.gov/harvest/object/abf916ec-6ddd-4030-8f5e-3b317a33ba1e",
        "https://catalog.data.gov/harvest/object/589436ca-1324-4773-9201-acecd5d83448",
        "https://catalog.data.gov/harvest/object/21392fa4-ff86-4ac8-9f38-33d67aef770c",
        "https://catalog.data.gov/harvest/object/9216c0ce-d083-48a6-b017-e0efc0fada37",
        "https://catalog.data.gov/harvest/object/0b20b4e4-34f8-4d1d-ae1c-7a405d0f6d36",
        "https://catalog.data.gov/harvest/object/36b9144a-dc24-43cf-85c3-49a08dbed762",
        "https://catalog.data.gov/harvest/object/9d60be08-5c3b-45a7-8ae6-017a4ca9433c",
        "https://catalog.data.gov/harvest/object/a4a75240-4fac-40f7-a327-6596becff636",
        "https://catalog.data.gov/harvest/object/8df82322-0812-46c7-b2b3-52829a8417e1",
        "https://catalog.data.gov/harvest/object/0419db56-01a4-4a97-a4f0-1fb903e77cdf",
        "https://catalog.data.gov/harvest/object/32d5b113-e83c-48f3-b05a-fd99ed7a3a92",
        "https://catalog.data.gov/harvest/object/f2e66a1c-10b6-4243-920a-0b64352b8c63",
        "https://catalog.data.gov/harvest/object/a0a63e30-b3cb-418b-8616-d89ee2e9e100",
    ]

    assets = []
    for url in metadata_urls:
        resp = requests.get(url).json()
        description = remove_html(resp["description"])
        title = resp["title"]
        modified = arrow.get(resp["modified"])
        keywords = resp["keyword"]

        asset = {
            "title": title,
            "description": description,
            "modified": modified,
            "metadata_url": url,
            "keywords": keywords,
        }

        assets.append(asset)

    return assets


def fsgeodata():
    base_url = "https://data.fs.usda.gov/geodata/edw/datasets.php"
    metadata_urls = []
    assets = []

    # Read the page that has the matedata links and cache locally
    resp = requests.get(base_url)
    soup = BeautifulSoup(resp.content, "html.parser")

    anchors = soup.find_all("a")
    for anchor in anchors:
        if anchor and anchor.get_text() == "metadata":
            metadata_urls.append(anchor["href"])

    for url in metadata_urls:
        url = f"https://data.fs.usda.gov/geodata/edw/{url}"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, features="xml")
        title = remove_html(soup.find("title").get_text())
        desc_block = soup.find("descript")
        abstract = remove_html(desc_block.find("abstract").get_text())
        themekeys = soup.find_all("themekey")
        keywords = [tk.get_text() for tk in themekeys]
        idinfo_citation_citeinfo_pubdate = soup.find("pubdate")
        if idinfo_citation_citeinfo_pubdate:
            modified = arrow.get(idinfo_citation_citeinfo_pubdate.get_text())
        else:
            modified = ""

        asset = {
            "title": title,
            "description": abstract,
            "modified": modified,
            "metadata_url": url,
            "keywords": keywords,
        }

        assets.append(asset)

    return assets


def climate_risk_viewer():
    assets = []

    metadata_urls = [
        "https://apps.fs.usda.gov/fsgisx05/rest/services/wo_nfs_gtac/EDW_ForestSystemBoundaries_01/MapServer?f=pjson",
        "https://apps.fs.usda.gov/fsgisx02/rest/services/wo_nfs_gstc/WO_OSC_GapAnalysis_Climate/MapServer?f=pjson",
        "https://services1.arcgis.com/gGHDlz6USftL5Pau/arcgis/rest/services/Firesheds_with_NFS_Lands_in_the_West_view/FeatureServer/0?f=pjson",
        "https://apps.fs.usda.gov/fsgisx02/rest/services/wo_nfs_gstc/WO_OSC_GapAnalysis_OldGrowthAndMatureForests/MapServer?f=pjson",
        "https://apps.fs.usda.gov/arcx/rest/services/wo_nrm_iweb/NRM_WCATTWatershedCondAssess/MapServer?f=pjson",
    ]

    for url in metadata_urls[:]:
        resp = requests.get(url)
        if resp.status_code == 200:
            content = resp.json()
            title = None
            description = remove_html(content["description"])
            if "documentInfo" in content.keys() and content["documentInfo"]:
                doc_info = content["documentInfo"]
                title = doc_info["Title"]
                keywords = [kw.strip() for kw in doc_info["Keywords"].split(" ")]
                # comments = remove_html(doc_info["Comments"])

                asset = {
                    "title": title,
                    "description": description,
                    "modified": "",
                    "metadata_url": url,
                    "keywords": keywords,
                }

                assets.append(asset)

    return assets


def main():
    import pprint

    assets = data_dot_gov()
    assets.extend(fsgeodata())
    assets.extend(climate_risk_viewer())

    pprint.pprint(assets)


if __name__ == "__main__":
    main()
