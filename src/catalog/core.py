import os
import json
from rich import print as rprint
from catalog.lib import load_json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from catalog.schema import CatalogDocument, DataSource
from sentence_transformers import SentenceTransformer


class GenVectorData():

    def __init__(self):
        self.src_catalog_file = "data/catalog.json"
        self.documents = []

    def read_metadata(self):

        if not os.path.exists(self.src_catalog_file):
            rprint(f"[red]Source file {self.src_catalog_file} does not exist.[/red]")
            return

        json_data = load_json(self.src_catalog_file)
        rprint(f"Loaded {len(json_data)} raw documents from {self.src_catalog_file}")

        return json_data

    def process(self):
        model = SentenceTransformer("all-MiniLM-L6-v2")
        recursive_text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=65, chunk_overlap=0
        )

        raw_data = load_json(self.src_catalog_file)
        rprint(f"Loaded {len(raw_data)} raw documents from [cyan]{self.src_catalog_file}[/cyan]")

        documents = []
        for doc in raw_data:
            title = doc.get("title")
            description = doc.get("description")
            keywords = ",".join(kw for kw in doc.get("keywords")) or ""
            src = doc.get("src")
            combined_text = f"Title: {title}\nDescription: {description}\nKeywords: {keywords}\nSource: {src}"

            chunks = recursive_text_splitter.create_documents([combined_text])

            for idx, chunk in enumerate(chunks):

                metadata = {
                    "doc_id": idx,  # or fsdoc.doc_id if that's the field name
                    "chunk_type": "title+description+keywords+source",
                    "chunk_index": idx,
                    "chunk_text": chunk.page_content,
                    "title": title,
                    "description": description,
                    "keywords": keywords,
                    "src": src,  # or another source identifier
                }

                embedding = model.encode(chunk.page_content)

                documents.append(
                    {
                    "embedding": embedding,
                    "metadata": metadata,
                    "title": title,
                    "description": description,
                    }
                )

        rprint(f"Loaded {len(documents)} documents ready for embedding and saving to a database.")

if __name__ == "__main__":
    gvd = GenVectorData()
    gvd.process()

"""

class GenVectorData:
    def __init__(self):
        self.src_catalog_file = "data/catalog.json"
        self.documents = []

    def load_and_validate_documents(self):

        try:
            raw_data = load_json(self.src_catalog_file)
            rprint(f"Loaded {len(raw_data)} raw documents from [cyan]{self.src_catalog_file}[/cyan]")
        except FileNotFoundError:
            rprint(f"[red]Source file {self.src_catalog_file} does not exist.[/red]")
            rprint("[yellow]Hint: Run the 'get-docs' command first.[/yellow]")
            return

        validated_docs = []
        for item in raw_data:
            source = item.get("source")
            try:
                if source == DataSource.FSGEODATA:
                    doc = CatalogDocument.from_fsgeodata(item)
                elif source == DataSource.GDD:
                    doc = CatalogDocument.from_gdd(item)
                elif source == DataSource.RDA:
                    doc = CatalogDocument.from_rda(item)
                else:
                    continue  # Or handle unknown sources
                validated_docs.append(doc)
            except Exception as e:
                rprint(f"[yellow]Skipping a document due to validation error: {e}[/yellow]")
s
        self.documents = validated_docs
        rprint(f"Successfully validated {len(self.documents)} documents.")

    def process(self):

        self.load_and_validate_documents()
        if not self.documents:
            rprint("[red]No documents to process.[/red]")
            return

        # --- Chunking Strategy 1: Document-Level Chunks (Recommended to start) ---
        # Here, each "chunk" is the full text content of a single document.
        # This is great for keeping the context of each item together.
        document_chunks = []
        for doc in self.documents:
            # Using the `primary_description` property from your schema is a good choice.
            # We can enrich it with other metadata.
            text_content = (
                f"Title: {doc.title}\n"
                f"Description: {doc.primary_description}\n"
                f"Keywords: {', '.join(doc.keywords)}\n"
                f"Source: {doc.source.value}"
            )
            document_chunks.append(text_content)

        rprint(f"\nGenerated {len(document_chunks)} document-level chunks.")
        # You can now pass `document_chunks` to an embedding model.
        # Example: model.encode(document_chunks)

        # --- Chunking Strategy 2: Recursive Character Splitting ---
        # This is useful for very long documents.
        # The chunk_size should be tuned based on your embedding model's context window.
        recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512, chunk_overlap=50
        )
        split_chunks = recursive_splitter.split_text("\n\n".join(document_chunks))
        rprint(f"Split into {len(split_chunks)} recursive chunks (size=512, overlap=50).")


if __name__ == "__main__":
    gvd = GenVectorData()


"""