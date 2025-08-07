import hashlib
from bs4 import BeautifulSoup


def hash_string(s):
    """Generate a SHA-256 hash of the input string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def strip_html_tags(text):
    soup = BeautifulSoup(text, "html.parser")
    stripped_text = soup.get_text()
    stripped_text = stripped_text.replace("\n", " ")
    return stripped_text
