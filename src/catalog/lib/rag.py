"""
RAG (Retrieval-Augmented Generation) implementation for natural language queries
against vector database containing catalog documents.
"""

import os
import logging
from typing import List, Dict, Optional, Tuple, Any
import psycopg2
from sentence_transformers import SentenceTransformer
import requests
import json
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries the system can handle."""
    VECTOR_SEARCH = "vector_search"
    KEYWORD_FREQUENCY = "keyword_frequency"
    DUPLICATE_TITLES = "duplicate_titles"
    DATA_SOURCE_FILTER = "data_source_filter"
    GENERAL = "general"


@dataclass
class RAGConfig:
    """Configuration for RAG system."""
    embedding_model: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.5
    max_results: int = 10
    llm_model: str = "ollama/llama3.2"
    llm_url: str = "http://lenny:4000"
    temperature: float = 0.7
    max_tokens: int = 1000


@dataclass
class Document:
    """Document representation for RAG results."""
    id: int
    doc_id: str
    title: str
    description: str
    chunk_text: str
    chunk_index: int
    data_source: str
    keywords: List[str]
    authors: List[str]
    similarity: float = 0.0


class DatabaseManager:
    """Handles database connections and queries."""

    def __init__(self):
        self.dbname = os.environ.get("PG_DBNAME", "postgres")
        self.dbuser = os.environ.get("POSTGRES_USER")
        self.dbpass = os.environ.get("POSTGRES_PASSWORD")
        self.connection_string = f"dbname={self.dbname} user={self.dbuser} password={self.dbpass} host='0.0.0.0'"

    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.connection_string)

    def count_documents(self) -> int:
        """Count total documents in database."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM documents")
            count = cur.fetchone()[0]
            cur.close()
            return count

    def get_data_sources(self) -> List[str]:
        """Get all available data sources."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT data_source FROM documents WHERE data_source IS NOT NULL")
            sources = [row[0] for row in cur.fetchall()]
            cur.close()
            return sources


class EmbeddingManager:
    """Handles text embeddings for vector search."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not self.model:
            raise RuntimeError("Embedding model not loaded")

        embedding = self.model.encode(text)
        return embedding.tolist()


class QueryClassifier:
    """Classifies user queries to determine appropriate handling strategy."""

    @staticmethod
    def classify_query(query: str) -> Tuple[QueryType, Dict[str, Any]]:
        """
        Classify the query and extract relevant parameters.

        Returns:
            Tuple of (QueryType, parameters_dict)
        """
        query_lower = query.lower()
        params = {}

        # Check for keyword frequency queries
        frequency_indicators = [
            "most frequent keyword", "most common keyword", "top keyword",
            "keyword frequency", "keyword frequencies", "popular keyword",
            "common keyword", "frequent keyword"
        ]
        if any(indicator in query_lower for indicator in frequency_indicators):
            return QueryType.KEYWORD_FREQUENCY, params

        # Check for duplicate title queries
        duplicate_indicators = [
            "duplicate title", "duplicate titles", "same title",
            "repeated title", "identical title", "title duplicate"
        ]
        if any(indicator in query_lower for indicator in duplicate_indicators):
            return QueryType.DUPLICATE_TITLES, params

        # Check for data source filtering
        source_indicators = ["from", "in", "source", "dataset", "data source"]
        if any(indicator in query_lower for indicator in source_indicators):
            # Try to extract data source name
            # This is a simple heuristic - could be improved with NER
            words = query.split()
            for i, word in enumerate(words):
                if word.lower() in source_indicators and i + 1 < len(words):
                    potential_source = words[i + 1].strip('.,!?')
                    params['data_source'] = potential_source
                    break
            return QueryType.DATA_SOURCE_FILTER, params

        # Default to vector search
        return QueryType.VECTOR_SEARCH, params


class VectorSearchEngine:
    """Handles vector similarity search operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def search_similar_documents(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        data_source: Optional[str] = None,
        threshold: float = 0.5
    ) -> List[Document]:
        """
        Search for similar documents using vector similarity.
        Uses cosine similarity (1 - cosine distance).
        """
        with self.db_manager.get_connection() as conn:
            cur = conn.cursor()

            # Build the query with optional filters
            base_query = """
            SELECT
                id, doc_id, title, description, chunk_text, chunk_index,
                data_source, keywords, authors,
                1 - (embedding <=> %s::vector) as similarity
            FROM documents
            WHERE 1=1
            """

            params = [query_embedding]

            if data_source:
                base_query += " AND LOWER(data_source) LIKE LOWER(%s)"
                params.append(f"%{data_source}%")

            base_query += """
            AND 1 - (embedding <=> %s::vector) > %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """
            params.extend([query_embedding, threshold, query_embedding, top_k])

            cur.execute(base_query, params)

            documents = []
            for row in cur.fetchall():
                doc = Document(
                    id=row[0],
                    doc_id=row[1],
                    title=row[2] or "",
                    description=row[3] or "",
                    chunk_text=row[4] or "",
                    chunk_index=row[5] or 0,
                    data_source=row[6] or "",
                    keywords=row[7] or [],
                    authors=row[8] or [],
                    similarity=float(row[9])
                )
                documents.append(doc)

            cur.close()
            return documents

    def get_keyword_frequencies(
        self,
        top_k: int = 20,
        data_source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get the most frequent keywords from documents."""
        with self.db_manager.get_connection() as conn:
            cur = conn.cursor()

            query = """
            SELECT
                keyword,
                COUNT(*) as frequency
            FROM (
                SELECT unnest(keywords) as keyword
                FROM documents
                WHERE keywords IS NOT NULL
                AND array_length(keywords, 1) > 0
            """

            params = []
            if data_source:
                query += " AND LOWER(data_source) LIKE LOWER(%s)"
                params.append(f"%{data_source}%")

            query += """
            ) as keywords_unnested
            GROUP BY keyword
            ORDER BY frequency DESC
            LIMIT %s
            """
            params.append(top_k)

            cur.execute(query, params)

            results = []
            for row in cur.fetchall():
                results.append({"keyword": row[0], "frequency": row[1]})

            cur.close()
            return results


class LLMManager:
    """Handles interactions with Language Models."""

    def __init__(self, config: RAGConfig):
        self.config = config

    def generate_response(
        self,
        query: str,
        context_documents: List[Document],
        query_type: QueryType = QueryType.VECTOR_SEARCH
    ) -> str:
        """
        Generate a response using the LLM with retrieved context.
        """
        try:
            if query_type == QueryType.VECTOR_SEARCH:
                return self._generate_vector_search_response(query, context_documents)
            elif query_type == QueryType.KEYWORD_FREQUENCY:
                return self._generate_keyword_frequency_response(query, context_documents)
            else:
                return self._generate_general_response(query, context_documents)

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return f"Error generating response: {str(e)}"

    def _generate_vector_search_response(
        self,
        query: str,
        documents: List[Document]
    ) -> str:
        """Generate response for vector search results."""
        if not documents:
            return "No relevant documents found for your query."

        # Prepare context from retrieved documents
        context_text = "\n\n".join([
            f"Document {i + 1} (Similarity: {doc.similarity:.3f}):\n"
            f"Title: {doc.title}\n"
            f"Description: {doc.description}\n"
            f"Content: {doc.chunk_text}\n"
            f"Data Source: {doc.data_source}\n"
            f"Keywords: {', '.join(doc.keywords) if doc.keywords else 'None'}"
            for i, doc in enumerate(documents)
        ])

        prompt = f"""You are a helpful assistant that answers questions based on catalog document data.
Use the following documents to answer the user's question. If the answer cannot be found in the context, say so.
Focus on providing specific information about datasets, data sources, and relevant details.

Context:
{context_text}

User Question: {query}

Please provide a comprehensive answer based on the above context. Include relevant details and cite which documents you're drawing information from."""

        return self._call_llm(prompt)

    def _generate_keyword_frequency_response(
        self,
        query: str,
        keyword_data: List[Dict[str, Any]]
    ) -> str:
        """Generate response for keyword frequency queries."""
        if not keyword_data:
            return "No keyword frequency data available."

        keyword_context = "\n".join([
            f"{i + 1}. '{kw['keyword']}' - appears {kw['frequency']} times"
            for i, kw in enumerate(keyword_data[:10])
        ])

        prompt = f"""Based on the keyword frequency data, answer the user's question.

Keyword Frequency Data (top 10):
{keyword_context}

User Question: {query}

Provide a natural language response about the keyword frequencies."""

        return self._call_llm(prompt)

    def _generate_general_response(
        self,
        query: str,
        documents: List[Document]
    ) -> str:
        """Generate general response with document context."""
        return self._generate_vector_search_response(query, documents)

    def _call_llm(self, prompt: str) -> str:
        """Make API call to LLM service."""
        try:
            response = requests.post(
                f"{self.config.llm_url}/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get('LITELLM_MASTER_KEY', '')}",
                },
                json={
                    "model": self.config.llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that analyzes catalog document data.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error querying LLM: {response.status_code} - {response.text}"

        except requests.exceptions.RequestException as e:
            return f"Error connecting to LLM: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"


class RAGSystem:
    """Main RAG system that orchestrates all components."""

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.db_manager = DatabaseManager()
        self.embedding_manager = EmbeddingManager(self.config.embedding_model)
        self.search_engine = VectorSearchEngine(self.db_manager)
        self.llm_manager = LLMManager(self.config)
        self.query_classifier = QueryClassifier()

    def query(
        self,
        user_query: str,
        top_k: Optional[int] = None,
        data_source: Optional[str] = None,
        use_llm: bool = True,
        similarity_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Main query method that handles natural language queries.

        Args:
            user_query: The natural language query from the user
            top_k: Number of results to return (defaults to config.max_results)
            data_source: Optional data source filter
            use_llm: Whether to use LLM for response generation
            similarity_threshold: Similarity threshold for vector search

        Returns:
            Dictionary containing query results and metadata
        """
        try:
            # Set defaults
            top_k = top_k or self.config.max_results
            similarity_threshold = similarity_threshold or self.config.similarity_threshold

            # Classify the query
            query_type, extracted_params = self.query_classifier.classify_query(user_query)

            # Override data_source if extracted from query
            if 'data_source' in extracted_params and not data_source:
                data_source = extracted_params['data_source']

            logger.info(f"Query type: {query_type}, Data source: {data_source}")

            # Handle different query types
            if query_type == QueryType.KEYWORD_FREQUENCY:
                return self._handle_keyword_frequency_query(
                    user_query, top_k, data_source, use_llm
                )
            elif query_type == QueryType.DUPLICATE_TITLES:
                return self._handle_duplicate_titles_query(
                    user_query, data_source, use_llm
                )
            else:
                # Vector search (default for most queries)
                return self._handle_vector_search_query(
                    user_query, top_k, data_source, use_llm, similarity_threshold
                )

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "query": user_query,
                "query_type": "error",
                "documents": [],
                "response": f"Error processing query: {str(e)}",
                "metadata": {"error": str(e)}
            }

    def _handle_vector_search_query(
        self,
        query: str,
        top_k: int,
        data_source: Optional[str],
        use_llm: bool,
        similarity_threshold: float
    ) -> Dict[str, Any]:
        """Handle vector similarity search queries."""
        # Generate embedding for the query
        query_embedding = self.embedding_manager.get_embedding(query)

        # Search for similar documents
        documents = self.search_engine.search_similar_documents(
            query_embedding, top_k, data_source, similarity_threshold
        )

        # Generate LLM response if requested
        response = ""
        if use_llm:
            response = self.llm_manager.generate_response(
                query, documents, QueryType.VECTOR_SEARCH
            )
        else:
            response = f"Found {len(documents)} relevant documents."

        return {
            "query": query,
            "query_type": QueryType.VECTOR_SEARCH.value,
            "documents": [self._document_to_dict(doc) for doc in documents],
            "response": response,
            "metadata": {
                "total_results": len(documents),
                "similarity_threshold": similarity_threshold,
                "data_source": data_source
            }
        }

    def _handle_keyword_frequency_query(
        self,
        query: str,
        top_k: int,
        data_source: Optional[str],
        use_llm: bool
    ) -> Dict[str, Any]:
        """Handle keyword frequency queries."""
        keyword_data = self.search_engine.get_keyword_frequencies(top_k, data_source)

        response = ""
        if use_llm and keyword_data:
            response = self.llm_manager._generate_keyword_frequency_response(
                query, keyword_data
            )
        else:
            response = f"Found {len(keyword_data)} keywords."

        return {
            "query": query,
            "query_type": QueryType.KEYWORD_FREQUENCY.value,
            "documents": [],
            "response": response,
            "metadata": {
                "keyword_frequencies": keyword_data,
                "total_keywords": len(keyword_data),
                "data_source": data_source
            }
        }

    def _handle_duplicate_titles_query(
        self,
        query: str,
        data_source: Optional[str],
        use_llm: bool
    ) -> Dict[str, Any]:
        """Handle duplicate titles queries."""
        # This would need to be implemented similar to keyword frequencies
        # For now, return a placeholder
        return {
            "query": query,
            "query_type": QueryType.DUPLICATE_TITLES.value,
            "documents": [],
            "response": "Duplicate titles functionality not yet implemented.",
            "metadata": {"data_source": data_source}
        }

    def _document_to_dict(self, doc: Document) -> Dict[str, Any]:
        """Convert Document object to dictionary."""
        return {
            "id": doc.id,
            "doc_id": doc.doc_id,
            "title": doc.title,
            "description": doc.description,
            "chunk_text": doc.chunk_text,
            "chunk_index": doc.chunk_index,
            "data_source": doc.data_source,
            "keywords": doc.keywords,
            "authors": doc.authors,
            "similarity": doc.similarity
        }

    def get_available_data_sources(self) -> List[str]:
        """Get list of available data sources."""
        return self.db_manager.get_data_sources()

    def get_document_count(self) -> int:
        """Get total document count."""
        return self.db_manager.count_documents()


# Convenience functions for backward compatibility
def get_query_embedding(query: str, model_name: str = "all-MiniLM-L6-v2") -> List[float]:
    """Generate embedding for the query text."""
    embedding_manager = EmbeddingManager(model_name)
    return embedding_manager.get_embedding(query)


def search_similar_documents(
    query_embedding: List[float],
    top_k: int = 5,
    data_source: Optional[str] = None,
    threshold: float = 0.5,
) -> List[Dict]:
    """Search for similar documents using vector similarity."""
    db_manager = DatabaseManager()
    search_engine = VectorSearchEngine(db_manager)
    documents = search_engine.search_similar_documents(
        query_embedding, top_k, data_source, threshold
    )

    # Convert to dict format for backward compatibility
    return [
        {
            "id": doc.id,
            "doc_id": doc.doc_id,
            "title": doc.title,
            "description": doc.description,
            "chunk_text": doc.chunk_text,
            "chunk_index": doc.chunk_index,
            "data_source": doc.data_source,
            "keywords": doc.keywords,
            "authors": doc.authors,
            "similarity": doc.similarity,
        }
        for doc in documents
    ]


def run_natural_language_query(
    query: str,
    top_k: int = 5,
    data_source: Optional[str] = None,
    use_llm: bool = True,
    similarity_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Main function to run natural language queries against the catalog.

    Examples:
        - "Show me all the forest fire related data sets"
        - "Find all records related to erosion"
        - "What datasets are available from USGS?"
        - "Most frequent keywords in the database"
    """
    rag_system = RAGSystem()
    return rag_system.query(
        user_query=query,
        top_k=top_k,
        data_source=data_source,
        use_llm=use_llm,
        similarity_threshold=similarity_threshold
    )
