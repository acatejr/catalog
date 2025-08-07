from typing import List, Dict, Any


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
