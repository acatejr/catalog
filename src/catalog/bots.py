from ollama import Client
import os
from dotenv import load_dotenv
import requests
from langchain_litellm import ChatLiteLLM

load_dotenv()

MESSAGE_CONTENT = (
    "You are a professional data librarian specializing in dataset discovery. "
    "Your role is to help researchers find relevant datasets in the catalog. "
    "When answering discovery questions:\n"
    "- List the relevant datasets found in the catalog\n"
    "- Briefly explain why each dataset matches the user's query\n"
    "- Highlight key characteristics (keywords, descriptions) that make them relevant\n"
    "- Results include a relevance distance score (lower = more relevant). "
    "- Prioritize datasets with lower distance scores in your response.\n"
    "- If multiple datasets are found, organize them by relevance\n"
    "- Be direct and concise - focus on what datasets ARE available\n"
    "- If the query asks about existence (like 'is there'), give a clear yes/no answer first, then list the datasets\n"
    "- If you don't know answers just say you don't know. Don't try to make up an answer.\n"
    "Use the provided context from the catalog to give accurate, evidence-based responses."
)


class OllamaBot:
    def __init__(self):
        """Initializes the OllamaBot with API credentials from environment variables.
        """
        self.OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "")
        self.OLLAMA_BASE_URL = os.environ.get("OLLAMA_API_URL", "")
        self.OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "")

        if not self.OLLAMA_API_KEY:
            raise ValueError("OLLAMA_API_KEY environment variable is not set.")
        if not self.OLLAMA_BASE_URL:
            raise ValueError("OLLAMA_API_URL environment variable is not set.")
        if not self.OLLAMA_MODEL:
            raise ValueError("OLLAMA_MODEL environment variable is not set.")

        self.client = Client(
            host=self.OLLAMA_BASE_URL,
            headers={"Authorization": "Bearer " + self.OLLAMA_API_KEY},
        )

    def chat(self, question: str, context: str) -> str:
        """
        Sends a chat message to the Ollama model with the given question and context.

        :param question: The user's question.
        :param context: The context to provide to the model.
        :return: The model's response.
        """

        messages = [
            {
                "role": "system",
                "content": MESSAGE_CONTENT,
            },
            {
                "role": "user",
                "content": f"Context: {context}\n\nQuestion: {question}",
            },
        ]

        resp = self.client.chat(self.OLLAMA_MODEL, messages=messages, stream=False)
        return resp["message"]["content"]


class VerdeBot:
    def __init__(self):
        """Initializes the VerdeBot with API credentials from environment variables.
        """
        self.VERDE_API_KEY = os.environ.get("VERDE_API_KEY", "")
        self.VERDE_URL = os.environ.get("VERDE_URL", "")
        self.VERDE_MODEL = os.environ.get("VERDE_MODEL", "")

        if not self.VERDE_API_KEY:
            raise ValueError("VERDE_API_KEY environment variable is not set.")
        if not self.VERDE_URL:
            raise ValueError("VERDE_URL environment variable is not set.")
        if not self.VERDE_MODEL:
            raise ValueError("VERDE_MODEL environment variable is not set.")

    def chat(self, question: str, context: str) -> str:
        llm = ChatLiteLLM(
            model=f"litellm_proxy/{self.VERDE_MODEL}",
            api_key=self.VERDE_API_KEY,
            api_base=self.VERDE_URL
        )

        response = llm.invoke(question)
        return response.content
