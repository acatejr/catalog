from pathlib import Path
import chromadb
import json
from catalog.schema import USFSDocument


class ChromaVectorDB:
    def __init__(self, src_catalog_file="data/usfs/catalog.json"):
        self.src_catalog_file = src_catalog_file
        self.client = chromadb.PersistentClient(path="./chromadb")
        self.collection = self.client.create_collection("documents", get_or_create=True)
        self.documents = []

    def load_document_metadata(self):
        json_file = Path(self.src_catalog_file)
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.documents = [USFSDocument.model_validate(doc) for doc in data]

    def extract_lineage_info(self, lineage_list: list) -> str:

        lineage = ""
        for item in lineage_list:
            desc = item.get("description", "")
            date = item.get("date", "")
            lineage += f"{desc} ({date}),"

        return lineage

    def load_documents(self):
        if not self.documents:
            self.load_document_metadata()

        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name, get_or_create=True
        )

        documents = []
        ids = []
        metadatas = []

        for idx, doc in enumerate(self.documents):
            title = doc.title or ""
            abstract = doc.abstract or ""
            purpose = doc.purpose or ""
            source = doc.src or ""

            lineage_str = ""
            if doc.lineage:
                lineage_str = self.extract_lineage_info(doc.lineage)

            ids.append(f"doc_{idx}")
            documents.append(
                f"Title: {title}\nAbstract: {abstract}\nPurpose: {purpose}\nSource: {source}\nKeywords: {', '.join(doc.keywords) if doc.keywords else ''}\nLineage: {lineage_str}\n"
            )
            metadatas.append(
                {
                    "id": doc.id,
                    "title": title,
                    "src": doc.src or "unknown",
                    "purpose": doc.purpose or "",
                    "keywords": ",".join(doc.keywords) if doc.keywords else "",
                }
            )

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def query(self, qstn: str = None, nresults=5, k: int = None) -> None:
        """Query the collection. Supports both nresults and k parameters."""
        if k is not None:
            nresults = k
        if qstn is None:
            return None

        results = None

        if self.collection and self.collection.count() > 0:
            results = self.collection.query(
                query_texts=[qstn],  # Chroma will embed this for you
                n_results=nresults,  # how many results to return
            )

            if results:
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]

                for doc, meta in zip(docs, metas):
                    # print(f"Title: {meta.get('title')}")
                    print(doc)
                    print("-" * 40)

        return results


# ids = results.get("ids", [[]])[0]
# documents = results.get("documents", [[]])[0]
# metadatas = results.get("metadatas", [[]])[0]
# distances = results.get("distances", [[]])[0]

# for i, (doc_id, document, metadata, distance) in enumerate(
#     zip(ids, documents, metadatas, distances), 1
# ):
#     # print(f"\n--- Result {i} ---")
#     # print(f"ID: {doc_id}")
#     # print(f"Distance: {distance:.4f}")
#     # print(f"Title: {metadata.get('title', 'N/A')}")
#     # print(f"Source: {metadata.get('src', 'N/A')}")
#     print(f"Document:\n{document}")
