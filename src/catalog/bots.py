from openai import OpenAI
import os


class OpenAIBot:

    def __init__(self):
        self.LLM_API_KEY = os.getenv("LLM_API_KEY")
        self.LLM_BASE_URL = os.getenv("LLM_BASE_URL")
        self.LLM_MODEL = os.getenv("LLM_MODEL") or "Llama-3.2-11B-Vision-Instruct"
        self.model = self.LLM_MODEL
        self.client = OpenAI(api_key=self.LLM_API_KEY, base_url=self.LLM_BASE_URL)

    def discovery_chat(self, question: str, context: str) -> str:
        self.resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional data librarian specializing in dataset discovery. "
                        "Your role is to help researchers find relevant datasets in the catalog. "
                        "When answering discovery questions:\n"
                        "- List the relevant datasets found in the catalog\n"
                        "- Briefly explain why each dataset matches the user's query\n"
                        "- Highlight key characteristics (keywords, descriptions) that make them relevant\n"
                        "- If multiple datasets are found, organize them by relevance\n"
                        "- Be direct and concise - focus on what datasets ARE available\n"
                        "- If the query asks about existence (like 'is there'), give a clear yes/no answer first, then list the datasets\n"
                        "- If you don't know answers just say you don't know. Don't try to make up an answer.\n"
                        "Use the provided context from the catalog to give accurate, evidence-based responses."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context: {context}\n\nQuestion: {question}",
                },
            ],
        )

        return self.resp.choices[0].message.content
