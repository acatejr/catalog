from openai import OpenAI
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from catalog.db import search_docs

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ESIIL_API_KEY = os.getenv("ESIIL_API_KEY")
ESIIL_API_URL = os.getenv("ESIIL_API_URL")


class ChatBot:
    def __init__(self):
        """Initialize the ChatBot with ESIIL LLM configuration"""
        self.client = OpenAI(
            api_key=ESIIL_API_KEY or "dummy-key",
            base_url=ESIIL_API_URL or "https://llm-api.cyverse.ai/v1",
        )
        self.model = "Llama-3.2-11B-Vision-Instruct"
        # self.model = "anvilgpt/llama2:latest"

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
                # model="Llama-3.2-11B-Vision-Instruct", # Slow
                # model="Llama-3.3-70B-Instruct-quantized", # A little faster
                # model = "anvilgpt/llama3.3:70b",
                # model = "anvilgpt/llama3.2:latest", # Worked but poor response
                # model = "anvilgpt/codegemma:latest", # Worked but could not deal with context
                # model="anvilgpt/gemma:latest", # Worked but could not deal with context
                # model="anvilgpt/deepseek-r1:70b", # Speed is decent and has real potential
                # model="anvilgpt/mistral:latest", # Speed seems decent and has real potential.  Interesting, after adding src field to context, made a python code suggestion.
                # model="js2/llama-4-scout", # Speed was decent and results had potential.  After adding src field to context, made interesting response inferences.
                # model="js2/DeepSeek-R1", # Speed was good and results were very interesting.  Still interesting results after adding src field to context.
                # model="nrp/phi3", # Speed good, not sure about results.  Same results after adding src field to context.
                # model = "nrp/gorilla", # Speed needs to be reviewed, but results were very interesting.  Same results after adding src field to context.  Still interesting.
                model="nrp/olmo",  # *** Speed good and results were very interesting
                # model="gemma-3-12b-it", # Fast but no response
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Use the provided context to answer questions.",
                    },
                    {
                        "role": "user",
                        "content": f"Context: {context}\n\nQuestion: {message}",
                    },
                ],
            )
            reponse = response.choices[0].message.content
            return reponse
