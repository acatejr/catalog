import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.data_dir: str = os.environ.get("DATA_DIR", "data/usfs")
        self.chromadb_path: str = os.environ.get("CHROMADB_PATH", "./chromadb")
        self.ollama_api_key: str = os.environ.get("OLLAMA_API_KEY", "")
        self.ollama_api_url: str = os.environ.get("OLLAMA_API_URL", "")
        self.ollama_model: str = os.environ.get("OLLAMA_MODEL", "")
        self.verde_api_key: str = os.environ.get("VERDE_API_KEY", "")
        self.verde_url: str = os.environ.get("VERDE_URL", "")
        self.verde_model: str = os.environ.get("VERDE_MODEL", "")
