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
        crawler = crawlers.DataDotGovCrawler()
        crawler.run()

        domain = Domain.objects.get(pk=1)
        for a in crawler.assets:
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
                    self.save_keywords(asset[0], keywords)

            except Exception as e:
                pass

    def load_fsgeodata(self):
        print("Loading metadata from fsgeodata.")
        crawler = crawlers.FSGeodataCrawler()
        crawler.run()

        domain = Domain.objects.get(pk=2)
        for a in crawler.assets:
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
                    self.save_keywords(asset[0], keywords)

            except Exception as e:
                pass

    def add_arguments(self, parser):
        parser.add_argument('--src_domain', nargs='+', type=str)

    def handle(self, *args, **options):
        if options["src_domain"]:
            if options["src_domain"][0] == "data.gov":
                self.load_data_dot_gov()
            elif options["src_domain"][0] == "fsgeodata":
                self.load_fsgeodata()
            elif options["src_domain"][0] == "all":
                self.load_data_dot_gov()
                self.load_fsgeodata()
