from pathlib import Path
import chromadb
import json
from catalog.schema import USFSDocument


class ChromaVectorDB:
    def __init__(self, db_path: str = "./chromadb", src_catalog_file: str = "data/usfs/catalog.json"):
        self.db_path = db_path
        self.src_catalog_file = src_catalog_file
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.create_collection("documents", get_or_create=True)
        self.documents = []

    def load_document_metadata(self):
        """
        Loads the document metadata from the JSON file.
        """

        json_file = Path(self.src_catalog_file)
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            docs = [USFSDocument.model_validate(doc) for doc in data]
            self.documents = list({doc.id: doc for doc in docs}.values())

    def extract_lineage_info(self, lineage_list: list[dict]) -> str:
        """
        Extracts lineage information from the lineage list.

        :param lineage_list: List of lineage dictionaries.
        :type lineage_list: list[dict]
        :return: Formatted lineage string.
        :rtype: str
        """

        lineage = ""
        for item in lineage_list:
            desc = item.get("description", "")
            date = item.get("date", "")
            lineage += f"{desc} ({date}),"

        return lineage

    def batch_load_documents(self, batch_size: int = 100) -> None:
        """
        Loads the documents into the ChromaDB collection in batches.
        :param batch_size: Number of documents to process in each batch.
        :type batch_size: int
        :return: None
        """

        if not self.documents:
            self.load_document_metadata()

        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name, get_or_create=True
        )

        for i in range(0, len(self.documents), batch_size):
            batch = self.documents[i : i + batch_size]
            ids = []
            documents = []
            metadatas = []

            for doc in batch:
                title = doc.title or ""
                abstract = doc.abstract or ""
                purpose = doc.purpose or ""
                source = doc.src or ""
                lineage_str = (
                    self.extract_lineage_info(doc.lineage) if doc.lineage else ""
                )

                ids.append(doc.id)
                documents.append(
                    f"Title: {title}\n"
                    f"Abstract: {abstract}\n"
                    f"Purpose: {purpose}\n"
                    f"Source: {source}\n"
                    f"Keywords: {', '.join(doc.keywords) if doc.keywords else ''}\n"
                    f"Lineage: {lineage_str}\n"
                )
                metadatas.append(
                    {
                        "id": doc.id,
                        "title": title,
                        "abstract": abstract,
                        "source": source,
                        "purpose": purpose,
                        "keywords": ",".join(doc.keywords) if doc.keywords else "",
                        "lineage": lineage_str,
                    }
                )

            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def query(
        self, qstn: str = None, nresults=5
    ) -> list[tuple[USFSDocument, float]]:
        """Query the collection. Returns list of (USFSDocument, distance) tuples.
        :param qstn: The question or query text.
        :type qstn: str
        :param nresults: Number of results to return.
        :type nresults: int
        :return: List of tuples containing USFSDocument and distance.
        """

        if qstn is None:
            return []

        results_list = []
        if self.collection and self.collection.count() > 0:
            results = self.collection.query(query_texts=[qstn], n_results=nresults)
            if results:
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                for meta, distance in zip(metadatas, distances):
                    keywords_str = meta.get("keywords", "")
                    doc = USFSDocument(
                        id=meta.get("id", ""),
                        title=meta.get("title"),
                        abstract=meta.get("abstract"),
                        purpose=meta.get("purpose"),
                        src=meta.get("source") or meta.get("src"),
                        keywords=keywords_str.split(",") if keywords_str else [],
                        lineage=None,
                    )
                    results_list.append((doc, distance))

        return results_list
