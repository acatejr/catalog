import hashlib
from bs4 import BeautifulSoup
from typing import List, Dict, Any


def hash_string(s):
    """Generate a SHA-256 hash of the input string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def strip_html_tags(text):
    soup = BeautifulSoup(text, "html.parser")
    stripped_text = soup.get_text()
    stripped_text = stripped_text.replace("\n", " ")
    return stripped_text


def get_keywords(item):
    """Extract keywords from the item."""
    keywords = []
    if "keywords" in item:
        keywords = [
            keyword.strip()
            for keyword in item["keywords"].split(",")
            if keyword.strip()
        ]
    return keywords


def merge_docs(*docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge multiple document lists, removing duplicates based on document ID.

    Args:
        *docs: Variable number of document lists to merge.

    Returns:
        A merged list of documents with duplicates removed.
    """
    documents = []
    document_ids = set()

    for doc_list in docs:
        for doc in doc_list:
            doc_id = doc.get("id")
            if doc_id and doc_id not in document_ids:
                documents.append(doc)
                document_ids.add(doc_id)

    return documents


def find_duplicate_documents(documents):
    seen = set()
    duplicates = []

    for doc in documents:
        id = doc.get("id")
        if id in seen:
            duplicates.append(doc)
        else:
            seen.add(id)

    return duplicates


# def load_docs_from_json(json_path):
#     """
#     Loads documents from a JSON file and returns a list of USFSDocument instances.

#     Args:
#         json_path (str): The path to the JSON file containing the documents.

#     Returns:
#         list: A list of USFSDocument instances created from the JSON data.
#     """

#     with open(json_path, "r") as f:
#         data = json.load(f)

#     # If the JSON is a list of dicts:
#     return [USFSDocument(**item) for item in data]