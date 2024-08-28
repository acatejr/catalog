from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
import re
import arrow
from catalog.models import Asset, Domain, Keyword
from django.db.models import Q
from dotenv import load_dotenv
from crawlers import crawlers

load_dotenv()


class Command(BaseCommand):
    help = "Load seed metadata assets."

    def save_keywords(self, asset, keywords):
        for w in keywords:
            keyword = Keyword(word=w, asset_id=asset.id)
            keyword.save()

    def load_data_dot_gov(self):
        print("Loading metadata from data.gov.")
        assets = crawlers.data_dot_gov()

        domain = Domain.objects.get(pk=1)
        for a in assets[:]:
            asset = Asset.objects.update_or_create(
                title = a["title"],
                description = a["description"],
                modified = str(a["modified"]),
                metadata_url = a["metadata_url"],
                domain_id = domain.id
            )

            for kw in a["keywords"]:
                keyword = Keyword(word=kw)
                keyword.save()
                keyword.assets.add(asset[0])

    def load_fsgeodata(self):
        print("Loading metadata from fsgeodata.")

        assets = crawlers.fsgeodata()
        domain = Domain.objects.get(pk=2)

        for a in assets:

            try:
                asset = Asset.objects.update_or_create(
                    title = a["title"],
                    description = a["description"],
                    modified = str(a["modified"]),
                    metadata_url = a["metadata_url"],
                    domain_id = domain.id
                )

                keywords = a["keywords"]

                if keywords:
                    for kw in keywords:
                        keyword = Keyword(word=kw)
                        keyword.save()
                        keyword.assets.add(asset[0])

            except Exception as e:
                print(e)

    def load_crv_data(self):
        print("Loading metadata from CRV")
        assets = crawlers.climate_risk_viewer()

        domain = Domain.objects.get(pk=3)
        for a in assets:
            try:
                if a["modified"] == "":
                    modified = None
                else:
                    modified = str(a["modified"])
                asset = Asset.objects.update_or_create(
                    title = a["title"],
                    description = a["description"],
                    modified = modified,
                    metadata_url = a["metadata_url"],
                    domain_id = domain.id
                )

                keywords = a["keywords"]
                if keywords:
                    for kw in keywords:
                        keyword = Keyword(word=kw)
                        keyword.save()
                        keyword.assets.add(asset[0])

            except Exception as e:
                print(e)

    def add_arguments(self, parser):
        parser.add_argument('--src', nargs='+', type=str)

    def handle(self, *args, **options):
        if options["src"]:
            if options["src"][0] == "data.gov":
                self.load_data_dot_gov()
            elif options["src"][0] == "fsgeodata":
                self.load_fsgeodata()
            elif options["src"][0] == "crv":
                self.load_crv_data()
            elif options["src"][0] == "all":
                self.load_data_dot_gov()
                self.load_fsgeodata()
                self.load_crv_data()
