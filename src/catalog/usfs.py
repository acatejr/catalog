from pathlib import Path

class USFS:

    def __init__(self, output_dir: str = "./data/usfs") -> None:
        self.output_dir = Path(output_dir)

    def download_metadata(self) -> None:
        """Download USFS metadata files."""

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.download_fsgeodata()
        self.download_rda()
        self.download_gdd()

    def download_fsgeodata(self) -> None:
        """
        Docstring for download_fsgeodata

        :param self: Description
        """
        print("Downloading FSGeoData metadata...")
        pass

    def download_rda(self) -> None:
        """
        Docstring for download_rda

        :param self: Description
        """
        print("Downloading RDA metadata...")
        pass

    def download_gdd(self) -> None:
        """
        Docstring for download_gdd

        :param self: Description
        """
        print("Downloading GDD metadata...")
        pass

    def build_metadata_catalog(self) -> None:
        pass

        # # Placeholder for actual download logic
        # metadata_file = self.output_dir / "usfs_metadata.json"
        # with open(metadata_file, "w", encoding="utf-8") as f:
        #     f.write('{"status": "metadata downloaded"}')
