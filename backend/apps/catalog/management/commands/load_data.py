from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from django.core.exceptions import ValidationError
import re
import arrow
from apps.catalog.models import Asset, Domain

SEED_URLS = [
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


class Command(BaseCommand):
    help = "Loads data into catalog database."

    def remove_html(self, text):
        txt = re.sub("<[^<]+?>", "", text).replace("\n", "")
        return txt

    def load_data_dot_gov(self):
        domain = Domain.objects.get(pk=1)
        for url in SEED_URLS:
            resp = requests.get(url).json()
            description = resp["description"]
            # desc = re.sub('<[^<]+?>', '', description).replace("\n", "")
            desc = self.remove_html(description)
            title = resp["title"]
            modified = arrow.get(resp["modified"])

            asset = Asset(
                title=title,
                metadata_url=url,
                description=desc,
                domain=domain,
                modified=str(modified),
            )
            asset.save()

    def load_nds_data(self):
        domain = Domain.objects.get(pk=2)
        base_url = "https://data.fs.usda.gov/geodata/edw/datasets.php"
        resp = requests.get(base_url)
        soup = BeautifulSoup(resp.content, "html.parser")
        table = soup.find("table", class_="fcTable")
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            title = self.remove_html(cells[0].find("strong").get_text())
            paragraphs = cells[0].find_all("p")

            if len(paragraphs) > 2:
                date_of_last_refresh = paragraphs[-1].get_text().replace("Date of last refresh: ", "").replace(",", "")
                date_of_last_refresh = arrow.get(date_of_last_refresh, "MMM D YYYY")

            metadata_anchor = cells[1].find("a")
            metadata_url = None
            if metadata_anchor and metadata_anchor.get_text() == "metadata":
                metadata_url = (
                    f"https://data.fs.usda.gov/geodata/edw/{metadata_anchor['href']}"
                )
                resp = requests.get(metadata_url)
                soup = BeautifulSoup(resp.content, features="xml")
                desc = soup.find("descript")
                abstract = self.remove_html(desc.find("abstract").get_text())

                asset = Asset(
                    metadata_url=metadata_url,
                    title=title,
                    description=abstract,
                    domain=domain,
                    modified=str(date_of_last_refresh),
                )

                asset.save()

    def add_arguments(self, parser):
        pass
        # parser.add_argument('sample', nargs='+')

    def handle(self, *args, **options):
        self.load_data_dot_gov()
        self.load_nds_data()
