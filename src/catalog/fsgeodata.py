#!/usr/bin/env python3
"""
FSGeodata Downloader
Downloads metadata and web services information from USFS Geodata Clearinghouse
"""

import os
import requests
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
from rich import print as rprint


class FSGeodataDownloader:
    """Downloads metadata and web services data from USFS Geodata Clearinghouse"""

    BASE_URL = "https://data.fs.usda.gov"
    METADATA_BASE_URL = f"{BASE_URL}/geodata/edw/edw_resources/meta/"

    DATASETS_URL = f"{BASE_URL}/geodata/edw/datasets.php"

    def __init__(self, data_dir="data/fsgeodata"):
        """Initialize downloader with data directory"""
        self.data_dir = Path(data_dir)
        self.metadata_dir = self.data_dir / "metadata"
        self.services_dir = self.data_dir / "services"

        # Create directories
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.services_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; FSGeodataDownloader/1.0)"}
        )

    def fetch_datasets_page(self):
        """Fetch the main datasets page"""
        rprint(f"Fetching datasets page: {self.DATASETS_URL}")
        response = self.session.get(self.DATASETS_URL)
        response.raise_for_status()
        return response.text

    def parse_datasets(self, html_content):
        """Parse the HTML and extract metadata and service URLs"""
        soup = BeautifulSoup(html_content, "html.parser")
        datasets = []

        # Find all links to metadata XML files
        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Look for metadata XML files
            if "/meta/" in href and href.endswith(".xml"):
                dataset_name = Path(href).stem
                metadata_url = urljoin(self.METADATA_BASE_URL, dataset_name + ".xml")

                # Try to find associated map service URL in nearby elements
                service_url = None
                parent = link.find_parent()
                if parent:
                    # Look for MapServer links in the same section
                    service_links = parent.find_all(
                        "a", href=lambda h: h and "MapServer" in h
                    )
                    if service_links:
                        service_url = service_links[0]["href"]

                datasets.append(
                    {
                        "name": dataset_name,
                        "metadata_url": metadata_url,
                        "service_url": service_url,
                    }
                )

        return datasets

    def download_file(self, url, output_path, description="file"):
        """Download a file from URL to output_path"""
        try:
            rprint(f"  Downloading {description}: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)

            rprint(f"  ✓ Saved to {output_path}")
            return True

        except requests.exceptions.RequestException as e:
            rprint(f"  ✗ Failed to download {description}: {e}")
            return False

    def download_service_info(self, url, output_path):
        """Download service info (JSON format)"""
        try:
            rprint(f"  Downloading service info: {url}")
            # Add ?f=json to get JSON response
            json_url = f"{url}?f=json"
            response = self.session.get(json_url, timeout=30)
            response.raise_for_status()

            with open(output_path, "w") as f:
                f.write(response.text)

            rprint(f"  ✓ Saved to {output_path}")
            return True

        except requests.exceptions.RequestException as e:
            rprint(f"  ✗ Failed to download service info: {e}")
            return False

    def download_all(self):
        """Main method to download all datasets"""
        rprint("=" * 70)
        rprint("FSGeodata Downloader")
        rprint("=" * 70)
        rprint()

        # Fetch and parse the datasets page
        html_content = self.fetch_datasets_page()
        datasets = self.parse_datasets(html_content)

        rprint(f"\nFound {len(datasets)} datasets")
        rprint("=" * 70)
        rprint()

        stats = {
            "total": len(datasets),
            "metadata_success": 0,
            "metadata_failed": 0,
            "service_success": 0,
            "service_failed": 0,
        }

        # Download each dataset
        for i, dataset in enumerate(datasets, 1):
            rprint(f"[{i}/{len(datasets)}] Processing: {dataset['name']}")

            # Download metadata
            metadata_path = self.metadata_dir / f"{dataset['name']}.xml"
            if self.download_file(dataset["metadata_url"], metadata_path, "metadata"):
                stats["metadata_success"] += 1
            else:
                stats["metadata_failed"] += 1

            # Download service info if available
            if dataset["service_url"]:
                service_path = self.services_dir / f"{dataset['name']}_service.json"
                if self.download_service_info(dataset["service_url"], service_path):
                    stats["service_success"] += 1
                else:
                    stats["service_failed"] += 1
            else:
                rprint("  ! No service URL found")

            rprint()

            # Be nice to the server
            time.sleep(0.5)

        # Print summary
        rprint("=" * 70)
        rprint("Download Summary")
        rprint("=" * 70)
        rprint(f"Total datasets:        {stats['total']}")
        rprint(f"Metadata downloaded:   {stats['metadata_success']}")
        rprint(f"Metadata failed:       {stats['metadata_failed']}")
        rprint(f"Services downloaded:   {stats['service_success']}")
        rprint(f"Services failed:       {stats['service_failed']}")
        rprint()
        rprint(f"Data saved to: {self.data_dir.absolute()}")


def main():
    """Main entry point"""
    downloader = FSGeodataDownloader(data_dir="data")
    downloader.download_all()


if __name__ == "__main__":
    main()
