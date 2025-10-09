from openai import OpenAI
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from catalog.db import search_docs

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ESIIL_API_KEY = os.getenv("ESIIL_API_KEY")
ESIIL_API_URL = os.getenv("ESIIL_API_URL")
ESIIL_MODEL = os.getenv("ESIIL_MODEL") or "Llama-3.2-11B-Vision-Instruct"


class ChatBot:
    def __init__(self):
        """Initialize the ChatBot with ESIIL LLM configuration"""
        self.client = OpenAI(
            api_key=ESIIL_API_KEY or "dummy-key",
            base_url=ESIIL_API_URL or "https://llm-api.cyverse.ai/v1",
        )
        self.model = ESIIL_MODEL

    def get_documents(self, query: str) -> str:
        """
        Placeholder for RAG query method
        """

        encoder = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = encoder.encode(query).tolist()

        if len(query_embedding) > 0:  # Should have embedding dimensions
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
                model="Llama-3.2-11B-Vision-Instruct",  # Slow
                # model="Llama-3.3-70B-Instruct-quantized", # A little faster
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
