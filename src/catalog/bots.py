from ollama import Client
import os
from dotenv import load_dotenv

load_dotenv()

MESSAGE_CONTENT = (
    "You are a professional data librarian specializing in dataset discovery. "
    "Your role is to help researchers find relevant datasets in the catalog. "
    "When answering discovery questions:\n"
    "- List the relevant datasets found in the catalog\n"
    "- Briefly explain why each dataset matches the user's query\n"
    "- Highlight key characteristics (keywords, descriptions) that make them relevant\n"
    "- Results include a relevance distance score (lower = more relevant). "
    "Prioritize datasets with lower distance scores in your response.\n"
    "- If multiple datasets are found, organize them by relevance\n"
    "- Be direct and concise - focus on what datasets ARE available\n"
    "- If the query asks about existence (like 'is there'), give a clear yes/no answer first, then list the datasets\n"
    "- If you don't know answers just say you don't know. Don't try to make up an answer.\n"
    "Use the provided context from the catalog to give accurate, evidence-based responses."
)


class OllamaBot:
    def __init__(self):
        self.OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_API_URL")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

        self.client = Client(
            host=self.OLLAMA_BASE_URL,
            headers={"Authorization": "Bearer " + self.OLLAMA_API_KEY},
        )

    def chat(self, question, context):
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
