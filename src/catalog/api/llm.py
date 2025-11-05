from openai import OpenAI
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from catalog.core.db import (
    search_docs,
    search_entity_by_name,
    get_field_lineage,
    get_dataset_relationships,
    list_all_datasets,
)
from enum import Enum
from typing import Optional

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL") or "Llama-3.2-11B-Vision-Instruct"


class QueryType(str, Enum):
    """Types of queries the system can handle"""

    GENERAL = "general"
    SCHEMA = "schema"
    LINEAGE = "lineage"
    RELATIONSHIPS = "relationships"
    QUALITY = "quality"
    DISCOVERY = "discovery"


class ChatBot:
    def __init__(self):
        """Initialize the ChatBot with ESIIL LLM configuration"""

        self.client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        self.model = LLM_MODEL

        # Initialize embedding model once during initialization for performance
        # This provides ~40-60x speedup for subsequent queries
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

    def get_documents(self, query: str) -> list:
        """
        Encode a text query using a SentenceTransformer model and retrieve matching documents.

        This method:
        - Uses the pre-loaded "all-MiniLM-L6-v2" SentenceTransformer encoder (initialized in __init__)
        - Computes the dense embedding for the provided query and converts it to a plain Python list
        - Calls search_docs(embedding: List[float]) to retrieve matching documents from the vector database
        - Returns the documents found, or an empty list if no valid embedding is produced

        Args:
            query (str): The natural-language query to encode and search for.

        Returns:
            list: A list of document dictionaries (search results) returned by search_docs.
                Each document typically contains: title, description, keywords, and other metadata.
                Returns an empty list if the encoder produces no embedding.

        Raises:
            RuntimeError: If the embedding cannot be computed or if the underlying encoder fails.
            Exception: Propagates exceptions raised by search_docs (e.g., connectivity or index errors).

        Notes:
            - The encoder is initialized once in __init__ and reused across all queries for performance
            - This provides ~40-60x speedup compared to loading the model on each query
            - The embedding model uses 384 dimensions to match the vector database schema
            - search_docs expects a list of floats representing the embedding

        Example:
            >>> chatbot = ChatBot()
            >>> docs = chatbot.get_documents("Find articles about distributed tracing")
            >>> if docs:
            ...     for doc in docs:
            ...         print(f"Title: {doc['title']}")
            ...         print(f"Description: {doc['description']}")
        """

        # Use pre-loaded encoder (MUCH faster than loading on each query)
        query_embedding = self.encoder.encode(query).tolist()

        # Validate embedding was generated
        if len(query_embedding) > 0:  # Should have 384 dimensions
            documents = search_docs(query_embedding)
            return documents
        else:
            return []

    def classify_query(self, query: str) -> QueryType:
        """
        Classify the user's query intent using the LLM.

        This routes queries to appropriate retrieval strategies.
        """
        classification_prompt = f"""Classify this data catalog query into ONE category:

1. SCHEMA - Asking about table/dataset structure, fields, data types, or schema definitions
   Examples: "What is the schema for X?", "What fields are in Y?", "Show me the structure of Z"

2. LINEAGE - Asking about data origins, transformations, or field derivation
   Examples: "Where does field X come from?", "What is the lineage of Y?", "How is Z calculated?"

3. RELATIONSHIPS - Asking about connections between datasets
   Examples: "What datasets reference X?", "How is Y related to Z?", "Show foreign keys"

4. QUALITY - Asking about data quality, completeness, or statistics
   Examples: "What is the quality of X?", "How complete is field Y?", "Show stats for Z"

5. DISCOVERY - Searching for datasets by characteristics
   Examples: "Find datasets with coordinates", "Show me spatial data", "What has timestamps?"

6. GENERAL - General questions or document search

Query: "{query}"

Respond with ONLY the category name."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": classification_prompt}],
                max_tokens=10,
            )
            classification = response.choices[0].message.content.strip().upper()
            return QueryType[classification]
        except (KeyError, Exception):
            return QueryType.GENERAL

    def chat(self, message: str = "Hello, how can you help me?") -> str:
        """
        Enhanced chat with query classification and specialized retrieval.

        Args:
            message: The message to send to the LLM

        Returns:
            The LLM's response as a string
        """
        # Classify the query
        query_type = self.classify_query(message)

        # Route to appropriate handler
        if query_type == QueryType.SCHEMA:
            return self._handle_schema_query(message)
        elif query_type == QueryType.LINEAGE:
            return self._handle_lineage_query(message)
        elif query_type == QueryType.RELATIONSHIPS:
            return self._handle_relationship_query(message)
        elif query_type == QueryType.QUALITY:
            return self._handle_quality_query(message)
        elif query_type == QueryType.DISCOVERY:
            return self._handle_discovery_query(message)
        else:
            return self._handle_general_query(message)

    def _handle_schema_query(self, message: str) -> str:
        """Handle schema-specific queries with structured retrieval."""
        # Extract dataset name using LLM
        extraction_prompt = f"""Extract the dataset/table name from this query.
Respond with ONLY the dataset name, nothing else.

Query: "{message}"

Dataset name:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": extraction_prompt}],
                max_tokens=20,
            )
            dataset_name = response.choices[0].message.content.strip()

            # Search for the dataset
            entity = search_entity_by_name(dataset_name)

            if not entity:
                return f"I couldn't find a dataset named '{dataset_name}' in the catalog. Would you like me to search for similar datasets?"

            # Format schema information
            schema_context = f"""Dataset: {entity.get("dataset_name") or entity["label"]}
Display Name: {entity.get("display_name", "N/A")}
Type: {entity.get("dataset_type", "N/A")}
Description: {entity.get("definition", "N/A")}
Source System: {entity.get("source_system", "N/A")}
Record Count: {entity.get("record_count", "Unknown")}

Schema (Fields):
"""

            for attr in entity.get("attributes", []):
                tech = attr.get("technical", {})
                schema_context += f"""
- {attr["label"]} ({tech.get("data_type", "Unknown")})
  Definition: {attr.get("definition", "N/A")}
  Nullable: {tech.get("is_nullable", "Yes")}
  Primary Key: {"Yes" if tech.get("is_primary_key") else "No"}
  Foreign Key: {"Yes" if tech.get("is_foreign_key") else "No"}
"""

                # Add domain constraints if present
                domain_values = attr.get("domain_values", [])
                if domain_values:
                    schema_context += (
                        f"  Domain: {len(domain_values)} constraint(s) defined\n"
                    )

            # Use LLM to format a natural response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional data librarian. Provide clear, well-organized information about dataset schemas.",
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{schema_context}\n\nQuestion: {message}\n\nProvide a clear, professional response about this dataset's schema.",
                    },
                ],
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error processing schema query: {str(e)}"

    def _handle_lineage_query(self, message: str) -> str:
        """Handle data lineage queries."""
        # Extract dataset and field name
        extraction_prompt = f"""Extract the dataset name and field name from this lineage query.
Respond in the format: "dataset_name|field_name"

Query: "{message}"

Answer:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": extraction_prompt}],
                max_tokens=50,
            )
            answer = response.choices[0].message.content.strip()

            dataset_name, field_name = answer.split("|")
            dataset_name = dataset_name.strip()
            field_name = field_name.strip()

            # Get lineage information
            lineage = get_field_lineage(dataset_name, field_name)

            if not lineage:
                return f"I couldn't find lineage information for field '{field_name}' in dataset '{dataset_name}'."

            # Format lineage context
            lineage_context = f"""Field: {lineage["entity_label"]}.{lineage["field"]}

Upstream Sources (where this field comes from):
"""

            if lineage["upstream_sources"]:
                for source in lineage["upstream_sources"]:
                    verified = " [VERIFIED]" if source["is_verified"] else ""
                    lineage_context += f"""
- Source: {source["source_dataset"]}.{source["source_field"]}{verified}
  Transformation: {source["transformation_type"]}
  Logic: {source.get("transformation_logic", "N/A")}
  Confidence: {source.get("confidence_score", "N/A")}
"""
                    if source.get("notes"):
                        lineage_context += f"  Notes: {source['notes']}\n"
            else:
                lineage_context += "  (No upstream sources - this is a source field)\n"

            lineage_context += "\nDownstream Dependents (what uses this field):\n"

            if lineage["downstream_dependents"]:
                for dep in lineage["downstream_dependents"]:
                    verified = " [VERIFIED]" if dep["is_verified"] else ""
                    lineage_context += f"""
- Target: {dep["target_dataset"]}.{dep["target_field"]}{verified}
  Transformation: {dep["transformation_type"]}
  Logic: {dep.get("transformation_logic", "N/A")}
"""
            else:
                lineage_context += "  (No downstream dependents recorded)\n"

            # Use LLM to format response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional data librarian specializing in data lineage and provenance.",
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{lineage_context}\n\nQuestion: {message}\n\nProvide a clear explanation of this field's data lineage.",
                    },
                ],
            )

            return response.choices[0].message.content

        except Exception as e:
            return "I couldn't identify the dataset and field name. Please ask like: 'What is the lineage of field OBJECTID in BrushDisposal?'"

    def _handle_relationship_query(self, message: str) -> str:
        """Handle dataset relationship queries."""
        # Extract dataset name
        extraction_prompt = f"""Extract the dataset/table name from this query.
Respond with ONLY the dataset name.

Query: "{message}"

Dataset name:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": extraction_prompt}],
                max_tokens=20,
            )
            dataset_name = response.choices[0].message.content.strip()

            # Get relationships
            relationships = get_dataset_relationships(dataset_name)

            if not relationships:
                return f"I couldn't find the dataset '{dataset_name}' in the catalog."

            # Format relationships context
            rel_context = f"""Dataset: {relationships["dataset"]}

Outgoing Relationships (this dataset references):
"""

            if relationships["outgoing_relationships"]:
                for rel in relationships["outgoing_relationships"]:
                    enforced = " [ENFORCED]" if rel["is_enforced"] else ""
                    rel_context += f"""
- {rel["from_field"]} → {rel["to_dataset"]}.{rel["to_field"]}{enforced}
  Type: {rel["relationship_type"]}
  Name: {rel.get("relationship_name", "N/A")}
"""
            else:
                rel_context += "  (No outgoing relationships)\n"

            rel_context += (
                "\nIncoming Relationships (other datasets reference this one):\n"
            )

            if relationships["incoming_relationships"]:
                for rel in relationships["incoming_relationships"]:
                    enforced = " [ENFORCED]" if rel["is_enforced"] else ""
                    rel_context += f"""
- {rel["from_dataset"]}.{rel["from_field"]} → {rel["to_field"]}{enforced}
  Type: {rel["relationship_type"]}
  Name: {rel.get("relationship_name", "N/A")}
"""
            else:
                rel_context += "  (No incoming relationships)\n"

            # Use LLM to format response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional data librarian explaining dataset relationships.",
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{rel_context}\n\nQuestion: {message}\n\nExplain this dataset's relationships.",
                    },
                ],
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error processing relationship query: {str(e)}"

    def _handle_quality_query(self, message: str) -> str:
        """Handle data quality queries."""
        return "Quality query handling is not yet implemented. Please ask about dataset schemas, lineage, or relationships."

    def _handle_discovery_query(self, message: str) -> str:
        """Handle dataset discovery queries."""
        return "Discovery query handling is not yet implemented. Please ask about specific datasets."

    def _handle_general_query(self, message: str) -> str:
        """Handle general queries using existing RAG approach."""
        documents = self.get_documents(message)

        if len(documents) > 0:
            context = "\n\n".join(
                [
                    f"Title: {doc['title']}\nDescription: {doc['description']}\nKeywords: {doc['keywords']}"
                    for doc in documents
                ]
            )
            # Use the LLM to generate an answer
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional data librarian specializing in scientific data discovery and metadata curation. "
                            "Your role is to help researchers and scientists find, understand, and evaluate datasets based on their needs. "
                            "When answering questions:\n"
                            "- Provide clear, organized summaries of available datasets\n"
                            "- Highlight key metadata like titles, descriptions, keywords, and relevant attributes\n"
                            "- Explain how datasets relate to the user's query\n"
                            "- Suggest related datasets or complementary resources when appropriate\n"
                            "- Use professional library science terminology when helpful\n"
                            "- If information is incomplete or uncertain, acknowledge this transparently\n"
                            "- Cite specific dataset titles when making recommendations\n"
                            "Use the provided context from the catalog to give accurate, evidence-based responses."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Context: {context}\n\nQuestion: {message}",
                    },
                ],
            )
            return response.choices[0].message.content
        else:
            return "I couldn't find any relevant information in the catalog for your query."

    def keyword_chat(
        self, message: str = "Hello, how can you help me?", params=None
    ) -> str:
        """
        Send a message to the ESIIL LLM and return the response

        Args:
            message: The message to send to the LLM

        Returns:
            The LLM's response as a string
        """

        documents = self.get_documents(message)

        if len(documents) > 0:
            context = "\n\n".join(
                [
                    f"Title: {doc['title']}\nDescription: {doc['description']}\nKeywords: {doc['keywords']}"
                    for doc in documents
                ]
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional data librarian specializing in scientific data discovery and metadata curation. "
                            "Your role is to help researchers and scientists find, understand, and evaluate datasets based on their needs. "
                            "When answering questions:\n"
                            "- Provide at list of unique keywords from the context provided\n"
                            "- Use professional library science terminology when helpful\n"
                            "- If information is incomplete or uncertain, acknowledge this transparently\n"
                            "Use the provided context from the catalog to give accurate, evidence-based responses."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Context: {context}\n\nQuestion: {message}",
                    },
                ],
            )

            reponse = response.choices[0].message.content
            return reponse
