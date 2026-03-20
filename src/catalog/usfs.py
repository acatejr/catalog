import os

class USFS:

    def __init__(self):
        self.output_dir = "./data/usfs"

    def download_fsgeodata_metadata(self):
        pass

    def download_gdd_metadata(self):
        pass

    def download_rda_metadata(self):
        self.mkdir_output()

    def mkdir_output(self):
        os.makedirs(self.output_dir, exist_ok=True)