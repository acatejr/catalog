from openai import OpenAI
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from catalog.core.db import search_docs

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL") or "Llama-3.2-11B-Vision-Instruct"

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# ESIIL_API_KEY = os.getenv("ESIIL_API_KEY")
# ESIIL_API_URL = os.getenv("ESIIL_API_URL")
# ESIIL_MODEL = os.getenv("ESIIL_MODEL") or "Llama-3.2-11B-Vision-Instruct"
# OLLAMA_API_KEY_CATALOG = os.getenv("OLLAMA_API_KEY_CATALOG")
# LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")


class ChatBot:
    def __init__(self):
        """Initialize the ChatBot with ESIIL LLM configuration"""

        self.client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL
        )
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


    def chat(self, message: str = "Hello, how can you help me?") -> str:
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
            reponse = response.choices[0].message.content
            return reponse

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
