# from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
import re
import arrow
from dotenv import load_dotenv


class BaseCrawler:

    def __init__(self, name=None, assets=[], metadata_urls=[]):
        self.name = name
        self.assets = assets
        self.metadata_urls = metadata_urls

    def run(self):
        pass

    def remove_html(self, text):
        txt = re.sub("<[^<]+?>", "", text).replace("\n", "")
        return txt


class DataDotGovCrawler(BaseCrawler):

    def __init__(self, name=None):

        super().__init__(name)

        self.metadata_urls = [
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

    def __str__(self) -> str:
        return f"{self.name}"

    def run(self):
        super().run()

        if self.metadata_urls:
            for url in self.metadata_urls:
                resp = requests.get(url).json()
                description = self.remove_html(resp["description"])
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

                self.assets.append(asset)


class FSGeodataCrawler(BaseCrawler):

    def __str__(self) -> str:
        return f"{self.name}"

    def run(self):
        super().run()
        base_url = "https://data.fs.usda.gov/geodata/edw/datasets.php"

        # Read the page that has the matedata links and cache locally
        resp = requests.get(base_url)
        soup = BeautifulSoup(resp.content, "html.parser")

        anchors = soup.find_all("a")
        for anchor in anchors:
            if anchor and anchor.get_text() == "metadata":
                self.metadata_urls.append(anchor["href"])

        for url in self.metadata_urls:
            url = f"https://data.fs.usda.gov/geodata/edw/{url}"
            resp = requests.get(url)
            soup = BeautifulSoup(resp.content, features="xml")
            title = self.remove_html(soup.find("title").get_text())
            desc_block = soup.find("descript")
            abstract = self.remove_html(desc_block.find("abstract").get_text())
            themekeys = soup.find_all("themekey")
            keywords = [tk.get_text() for tk in themekeys]
            idinfo_citation_citeinfo_pubdate = soup.find("pubdate")
            if idinfo_citation_citeinfo_pubdate:
                modified = arrow.get(idinfo_citation_citeinfo_pubdate.get_text())
            else:
                modified = ''

            asset = {
                "title": title,
                "description": abstract,
                "modified": modified,
                "metadata_url": url,
                "keywords": keywords,
            }

            self.assets.append(asset)


# def main():
#     fsgdc = FSGeodataCrawler(name="fsgeodata")
#     fsgdc.run()

#     import pprint
#     for asset in fsgdc.assets:
#         pprint.pprint(asset)

# if __name__ == "__main__":
#     main()
