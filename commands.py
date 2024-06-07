#!/usr/bin/env python
import os, json
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

    click.echo("Done!")

@click.command("show_stache_creds")
def show_stache_creds():
    url = os.environ.get("UA_STACHE_URL")
    headers = {
        "X-STACHE-KEY": os.environ.get("X_STACHE_KEY")
    }

    for i in range(100):
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            stache_entry = json.loads(resp.text)
            secret = json.loads(stache_entry["secret"])
            click.echo(f"{i}, {secret}")

@click.group(help="")
def cli():
    pass

if __name__ == "__main__":
    cli.add_command(load_seed_data)
    cli.add_command(show_stache_creds)
    cli()
