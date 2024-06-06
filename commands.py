#!/usr/bin/env python
import os
import click
import requests
from bs4 import BeautifulSoup
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.models import Document, Base
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
db_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432"
engine = create_engine(db_url)

def init_db():
    Base.metadata.create_all(engine)

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


@click.command("load_seed_data")
def load_seed_data():
    click.echo("Loading seed urls.")
    documents = []
    for url in SEED_URLS:
        resp = requests.get(url).json()
        description = resp["description"]
        type = ""

        if "@type" in resp.keys():
            type = resp["@type"]

        document = Document(
            metadata_url = url,
            description = description
        )

        documents.append(document)
        if documents and len(documents):
            with Session(engine) as session:
                session.add_all(documents)
                try:
                    session.commit()
                except IntegrityError as e:
                    # TODO: Need to add some logging here.
                    print(e)


    # id = Column(Integer, primary_key=True)
    # metadata_url = Column(String(250), unique=True, nullable=True)
    # description = Column(String(2500), unique=False, nullable=True)
    # created_at = Column(DateTime, default=datetime.now)
    # updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    click.echo("Done!")


@click.group(help="")
def cli():
    pass


if __name__ == "__main__":
    cli.add_command(load_seed_data)
    cli()

"""
class Command(BaseCommand):
    help = "Load seed data."

    def data_dot_gov_seeds(self):
        for url in SEED_URLS:
            resp = requests.get(url).json()
            description = resp["description"]
            type = ""
            if "@type" in resp.keys():
                type = resp["@type"]

            try:
                doc = Document(type=type, description=description, metadata_url=url)

                doc.save()
            except IntegrityError as err:
                pass

    def national_data_set(self):
        base_url = "https://data.fs.usda.gov/geodata/edw/datasets.php"
        resp = requests.get(base_url)
        soup = BeautifulSoup(resp.content, "html.parser")
        table = soup.find("table", class_="fcTable")
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            title = cells[0].find("strong").get_text()
            metadata_anchor = cells[1].find("a")
            metadata_href = None
            if metadata_anchor and metadata_anchor.get_text() == "metadata":
                metadata_href = (
                    f"https://data.fs.usda.gov/geodata/edw/{metadata_anchor['href']}"
                )

                resp = requests.get(metadata_href)
                soup = BeautifulSoup(resp.content, features="xml")
                desc = soup.find("descript")
                abstract = desc.find("abstract").get_text()
                try:
                    doc = Document(
                        metadata_url=metadata_href,
                        # title=title,
                        description=abstract,
                        type="USFS_NATIONAL_DATASET",
                    )
                    doc.save()
                except IntegrityError as err:
                    pass

    def add_arguments(self, parser):
        # parser.add_argument('sample', nargs='+')
        pass

    def handle(self, *args, **options):
        # self.data_dot_gov_seeds()
        self.national_data_set()

"""
