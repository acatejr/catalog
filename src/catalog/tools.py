"""Tool definitions and executors for agentic search."""

from catalog.core import ChromaVectorDB
from catalog.schema import USFSDocument

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_vector_db",
            "description": (
                "Search the USFS dataset catalog using semantic similarity. "
                "Use this for conceptual or natural language queries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hybrid",
            "description": (
                "Search the catalog using hybrid BM25 keyword + semantic vector search "
                "with Reciprocal Rank Fusion. Best for mixed or keyword-heavy queries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_by_source",
            "description": (
                "Search the catalog filtered to a specific data source. "
                "Sources are: fsgeodata, gdd, rda."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "source": {
                        "type": "string",
                        "description": "Data source to filter by: fsgeodata, gdd, or rda",
                        "enum": ["fsgeodata", "gdd", "rda"],
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query", "source"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_document_details",
            "description": "Retrieve full details for a specific dataset by its document ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "description": "The document ID to retrieve",
                    }
                },
                "required": ["doc_id"],
            },
        },
    },
]


def _format_results(results: list[tuple[USFSDocument, float]]) -> str:
    if not results:
        return "No results found."
    return "\n\n---\n\n".join(
        doc.to_markdown(distance=score) for doc, score in results
    )


def _meta_to_doc(meta: dict) -> USFSDocument:
    keywords_str = meta.get("keywords", "")
    return USFSDocument(
        id=meta.get("id", ""),
        title=meta.get("title"),
        abstract=meta.get("abstract"),
        description=meta.get("description"),
        purpose=meta.get("purpose"),
        src=meta.get("source") or meta.get("src"),
        keywords=keywords_str.split(",") if keywords_str else [],
        lineage=None,
    )


def execute_tool(name: str, args: dict, db: ChromaVectorDB, hs) -> str:
    """Route a tool call to the appropriate executor and return result as a string."""

    if name == "search_vector_db":
        results = db.query(qstn=args["query"], nresults=args.get("n_results", 5))
        return _format_results(results)

    if name == "search_hybrid":
        results = hs.query(qstn=args["query"], nresults=args.get("n_results", 5))
        return _format_results(results)

    if name == "filter_by_source":
        try:
            raw = db.collection.query(
                query_texts=[args["query"]],
                n_results=args.get("n_results", 5),
                where={"source": args["source"]},
            )
            metadatas = raw.get("metadatas", [[]])[0]
            distances = raw.get("distances", [[]])[0]
            results = [(_meta_to_doc(m), d) for m, d in zip(metadatas, distances)]
            return _format_results(results)
        except Exception as e:
            return f"Error filtering by source: {e}"

    if name == "get_document_details":
        try:
            raw = db.collection.get(
                ids=[args["doc_id"]], include=["metadatas", "documents"]
            )
            if not raw["ids"]:
                return f"No document found with ID: {args['doc_id']}"
            doc = _meta_to_doc(raw["metadatas"][0])
            return doc.to_markdown()
        except Exception as e:
            return f"Error retrieving document: {e}"

    return f"Unknown tool: {name}"
