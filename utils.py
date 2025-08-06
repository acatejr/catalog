import json
from schema import USFSDocument


def load_docs_from_json(json_path):
    """
    Loads documents from a JSON file and returns a list of USFSDocument instances.

    Args:
        json_path (str): The path to the JSON file containing the documents.

    Returns:
        list: A list of USFSDocument instances created from the JSON data.
    """

    with open(json_path, "r") as f:
        data = json.load(f)

    # If the JSON is a list of dicts:
    return [USFSDocument(**item) for item in data]


def merge_docs(*docs) -> list:
    documents = []
    document_ids = []

    for doc_list in docs:
        for doc in doc_list:
            doc_id = doc.get("id")
            if doc_id not in document_ids:
                documents.append(doc)
                document_ids.append(doc_id)

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