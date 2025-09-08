from openai import OpenAI
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from catalog.db.main import search_docs

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ESIIL_API_KEY = os.getenv("ESIIL_API_KEY")
ESIIL_API_URL = os.getenv("ESIIL_API_URL")


class ChatBot():

    def __init__(self):
        """Initialize the ChatBot with ESIIL LLM configuration"""
        self.client = OpenAI(
            api_key=ESIIL_API_KEY or "dummy-key",
            base_url=ESIIL_API_URL or "https://llm-api.cyverse.ai/v1"
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
                model="Llama-3.2-11B-Vision-Instruct",
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


        # try:
        #     response = self.client.chat.completions.create(
        #         model=self.model,
        #         messages=[
        #             {
        #                 "role": "system",
        #                 "content": "You are a helpful assistant specialized in environmental science, data analysis, data cataloging and metadata."
        #             },
        #             {
        #                 "role": "user",
        #                 "content": message
        #             }
        #         ],
        #         max_tokens=1000,
        #         temperature=0.7
        #     )

        #     return response.choices[0].message.content

        # except Exception as e:
        #     print(f"Error calling ESIIL LLM: {e}")
        #     return f"Sorry, I encountered an error: {str(e)}"


def main():
    #print("Testing ESIIL ChatBot...")
    chatbot = ChatBot()

    # Test with a default message
    # response = chatbot.chat()
    # print(f"ChatBot Response: {response}")

    # Test with a custom message
    custom_message = "Describe what wildfire data is available in the data store."
    custom_response = chatbot.chat(custom_message)
    # print(f"\nCustom Message: {custom_message}")
    print(f"ChatBot Response: {custom_response}")

    custom_message = "Is there erosion data in NRM?"
    custom_response = chatbot.chat(custom_message)
    print(f"ChatBot Response: {custom_response}")

if __name__ == "__main__":
    main()


# import psycopg2
# import os
# from dotenv import load_dotenv
# from sentence_transformers import SentenceTransformer
# from openai import OpenAI
# import ollama

# load_dotenv()

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# # Database connection parameters
# dbname = os.environ.get("PG_DBNAME") or "postgres"
# dbuser = os.environ.get("POSTGRES_USER")
# dbpass = os.environ.get("POSTGRES_PASSWORD")


# class RAGChatBot:
#     def __init__(self, model_name: str, rag_config: dict):
#         self.model_name = model_name
#         self.rag_config = rag_config
#         self.client = OpenAI(api_key=OPENAI_API_KEY)
#         self.initialize_model()

#     def initialize_model(self):
#         # Placeholder for model initialization logic
#         # print(f"Initializing RAG model: {self.model_name} with config: {self.rag_config}")
#         pass

#     def chat(self, user_input: str) -> str:
#         # Placeholder for chat logic
#         print(f"User input: {user_input}")
#         return "This is a response from the RAG model."

#     def generate_llm_rag_response(self, prompt: str) -> str:
#         """
#         Generate a response using the LLM and the provided documents.

#         Args:
#             prompt: The user prompt/question
#             documents: List of relevant documents to use as context
#         Returns:
#             The generated response from the LLM
#         """

#         documents = []
#         reponse = None

#         if prompt and len(prompt):
#             # Generate the embeddings
#             encoder = SentenceTransformer("all-MiniLM-L6-v2")
#             query_embedding = encoder.encode(prompt).tolist()

#             if len(query_embedding) > 0:  # Should have embedding dimensions
#                 documents = self.search_docs(query_embedding)
#                 if len(documents) > 0:
#                     context = "\n\n".join(
#                         [
#                             f"Title: {doc['title']}\nDescription: {doc['description']}\nKeywords: {doc['keywords']}"
#                             for doc in documents
#                         ]
#                     )

#                     # Use the LLM to generate an answer
#                     response = self.client.chat.completions.create(
#                         # model="gpt-3.5-turbo",
#                         model="test",
#                         messages=[
#                             {
#                                 "role": "system",
#                                 "content": "You are a helpful assistant. Use the provided context to answer questions.",
#                             },
#                             {
#                                 "role": "user",
#                                 "content": f"Context: {context}\n\nQuestion: {prompt}",
#                             },
#                         ],
#                     )
#                     reponse = response.choices[0].message.content

#         return reponse

#     def search_docs(self, query_embedding: list[float], limit: int = 10) -> list:
#         """
#         Search documents using vector similarity with the query embedding.

#         Args:
#             query_embedding: The embedding vector to search with
#             limit: Maximum number of documents to return (default: 10)

#         Returns:
#             List of dictionaries containing document information and similarity scores
#         """

#         if not query_embedding:
#             return []

#         pg_connection_string = (
#             f"dbname={dbname} user={dbuser} password={dbpass} host='0.0.0.0'"
#         )

#         docs = []

#         try:
#             with psycopg2.connect(pg_connection_string) as conn:
#                 cur = conn.cursor()

#                 # SQL query using cosine similarity for vector search
#                 # The <=> operator computes cosine distance (1 - cosine similarity)
#                 # Lower distance means higher similarity
#                 if limit is None:
#                     sql_query = """
#                     SELECT id, title, description, keywords, 1 - (embedding <=> %s::vector) AS similarity_score
#                     FROM documents
#                     WHERE embedding IS NOT NULL
#                     ORDER BY embedding <=> %s::vector;
#                     """
#                 else:
#                     sql_query = """
#                     SELECT id, title, description, keywords, 1 - (embedding <=> %s::vector) AS similarity_score
#                     FROM documents
#                     WHERE embedding IS NOT NULL
#                     ORDER BY embedding <=> %s::vector
#                     LIMIT %s;
#                     """

#                 # Execute the query with the embedding vector
#                 cur.execute(sql_query, (query_embedding, query_embedding, limit))

#                 # Fetch results and convert to list of dictionaries
#                 columns = [desc[0] for desc in cur.description]
#                 rows = cur.fetchall()

#                 for row in rows:
#                     doc_dict = dict(zip(columns, row))
#                     docs.append(doc_dict)

#                 cur.close()

#         except Exception as e:
#             print(f"Error searching documents: {e}")
#             return []

#         return docs


# class OllamaChatBot:
#     def __init__(self, model_name: str, rag_config: dict):
#         self.model_name = model_name
#         self.rag_config = rag_config
#         self.initialize_model()

#     def initialize_model(self):
#         # Placeholder for model initialization logic
#         pass

#     def chat(self, user_input: str) -> str:
#         print(f"User input: {user_input}")
#         return "This is a response from the Ollama RAG model."

#     def generate_llm_rag_response(self, prompt: str) -> str:
#         """
#         Generate a response using Ollama and the provided documents.

#         Args:
#             prompt: The user prompt/question
#         Returns:
#             The generated response from the LLM
#         """

#         documents = []
#         response = None

#         if prompt and len(prompt):
#             encoder = SentenceTransformer("all-MiniLM-L6-v2")
#             query_embedding = encoder.encode(prompt).tolist()

#             if len(query_embedding) > 0:
#                 documents = self.search_docs(query_embedding)
#                 if len(documents) > 0:
#                     context = "\n\n".join(
#                         [
#                             f"Title: {doc['title']}\nDescription: {doc['description']}\nKeywords: {doc['keywords']}"
#                             for doc in documents
#                         ]
#                     )

#                     ollama_prompt = f"Context: {context}\n\nQuestion: {prompt}"
#                     result = ollama.chat(
#                         model=self.model_name,  # e.g., "llama3"
#                         messages=[
#                             {
#                                 "role": "system",
#                                 "content": "You are a helpful assistant. Use the provided context to answer questions.",
#                             },
#                             {
#                                 "role": "user",
#                                 "content": ollama_prompt,
#                             },
#                         ],
#                     )
#                     response = result["message"]["content"]

#         return response

#     def search_docs(self, query_embedding: list[float], limit: int = 10) -> list:
#         if not query_embedding:
#             return []

#         pg_connection_string = (
#             f"dbname={dbname} user={dbuser} password={dbpass} host='0.0.0.0'"
#         )

#         docs = []

#         try:
#             with psycopg2.connect(pg_connection_string) as conn:
#                 cur = conn.cursor()
#                 if limit is None:
#                     sql_query = """
#                     SELECT id, title, description, keywords, 1 - (embedding <=> %s::vector) AS similarity_score
#                     FROM documents
#                     WHERE embedding IS NOT NULL
#                     ORDER BY embedding <=> %s::vector;
#                     """
#                 else:
#                     sql_query = """
#                     SELECT id, title, description, keywords, 1 - (embedding <=> %s::vector) AS similarity_score
#                     FROM documents
#                     WHERE embedding IS NOT NULL
#                     ORDER BY embedding <=> %s::vector
#                     LIMIT %s;
#                     """
#                 cur.execute(sql_query, (query_embedding, query_embedding, limit))
#                 columns = [desc[0] for desc in cur.description]
#                 rows = cur.fetchall()
#                 for row in rows:
#                     doc_dict = dict(zip(columns, row))
#                     docs.append(doc_dict)
#                 cur.close()
#         except Exception as e:
#             print(f"Error searching documents: {e}")
#             return []

#         return docs



# """
# Simple Client for CyVerse LLM API using pydantic-ai
# """

# import asyncio
# import os
# from pydantic_ai import Agent
# from pydantic_ai.models.openai import OpenAIChatModel
# from dotenv import load_dotenv

# load_dotenv()

# VERDI_ESILL_API_KEY = os.getenv('VERDI_ESILL_API_KEY')
# VERDI_ESILL_URL = os.getenv('VERDI_ESILL_URL')


# async def main():
#     """
#     Main function to send a message to the LLM and print the response
#     """

#     # Get API key from environment or use dummy
#     api_key = os.getenv('VERDI_ESILL_API_KEY', 'dummy-key')

#     # Configure the OpenAI-compatible model using OpenAIChatModel
#     model = OpenAIChatModel(
#         model_name='anvilgpt/llama3.1:latest',
#         base_url='https://llm-api.cyverse.ai/v1',
#         api_key=api_key
#     )

#     # model = OpenAIChatModel(
#     #     model='anvilgpt/llama3.1:latest',
#     #     base_url='https://llm-api.cyverse.ai/v1',
#     #     api_key=api_key
#     # )

#     # Create an agent with the model
#     agent = Agent(
#         model=model,
#         result_type=str,
#         system_prompt="You are a helpful assistant."
#     )

#     try:
#         # Send the message and get the response
#         print("Sending message to LLM...")
#         result = await agent.run("hello")

#         # Print the response
#         print(f"\nLLM Response: {result.data}")

#     except Exception as e:
#         print(f"Error occurred: {e}")
#         print(f"Error type: {type(e).__name__}")

#         # If authentication is needed, provide guidance
#         if "401" in str(e) or "unauthorized" in str(e).lower():
#             print("\nNote: You may need to provide an API key.")
#             print("Set the CYVERSE_API_KEY environment variable with your API key.")


# if __name__ == "__main__":
#     asyncio.run(main())

# # # from pydantic import BaseModel, HttpUrl
# # # import requests
# # from dotenv import load_dotenv
# # import asyncio
# # import os
# # from typing import Optional
# # from pydantic_ai import Agent
# # from pydantic_ai.models.openai import OpenAIChatModel
# # from pydantic import BaseModel, Field
# # import httpx


# # load_dotenv()

# # VERDI_ESILL_API_KEY = os.getenv('VERDI_ESILL_API_KEY')
# # VERDI_ESILL_URL = os.getenv('VERDI_ESILL_URL')

# # """
# # Enhanced Client for CyVerse LLM API using pydantic-ai
# # """


# # class Config(BaseModel):
# #     """Configuration for the LLM client"""
# #     base_url: str = Field(default="https://llm-api.cyverse.ai/v1")
# #     model_name: str = Field(default="anvilgpt/llama3.1:latest")
# #     api_key: Optional[str] = Field(default=None)
# #     timeout: int = Field(default=30)


# # class LLMClient:
# #     """Client for interacting with the LLM API"""

# #     def __init__(self, config: Optional[Config] = None):
# #         """
# #         Initialize the LLM client

# #         Args:
# #             config: Configuration object, uses defaults if None
# #         """
# #         self.config = config or Config()

# #         # Check for API key in environment variable
# #         if not self.config.api_key:
# #             self.config.api_key = os.getenv('CYVERSE_API_KEY', 'dummy-key')

# #         # Setup HTTP client with custom timeout
# #         http_client = httpx.AsyncClient(timeout=self.config.timeout)

# #         # Configure the model
# #         self.model = OpenAIChatModel(
# #             self.config.model_name,
# #             base_url=self.config.base_url,
# #             api_key=self.config.api_key,
# #             http_client=http_client
# #         )

# #         # Create the agent
# #         self.agent = Agent(
# #             model=self.model,
# #             result_type=str,
# #             system_prompt="You are a helpful assistant."
# #         )

# #     async def send_message(self, message: str) -> str:
# #         """
# #         Send a message to the LLM and return the response

# #         Args:
# #             message: The message to send

# #         Returns:
# #             The LLM's response as a string
# #         """
# #         try:
# #             result = await self.agent.run(message)
# #             return result.data
# #         except Exception as e:
# #             raise Exception(f"Failed to get response from LLM: {e}")

# #     async def close(self):
# #         """Clean up resources"""
# #         if hasattr(self.model, 'http_client'):
# #             await self.model.http_client.aclose()


# # async def main():
# #     """
# #     Main function to demonstrate the client usage
# #     """
# #     # Create client with default configuration
# #     client = LLMClient()

# #     try:
# #         # Send "hello" message
# #         print("Sending message to LLM...")
# #         response = await client.send_message("hello")

# #         # Print the response
# #         print(f"\nLLM Response: {response}")

# #     except Exception as e:
# #         print(f"Error: {e}")

# #         # Provide helpful error messages
# #         if "401" in str(e) or "403" in str(e):
# #             print("\n💡 Tip: Authentication may be required.")
# #             print("   Set the CYVERSE_API_KEY environment variable or")
# #             print("   pass api_key to the Config object.")
# #         elif "404" in str(e):
# #             print("\n💡 Tip: The model or endpoint may not exist.")
# #             print(f"   Tried to access: {client.config.base_url}")
# #             print(f"   Model: {client.config.model_name}")
# #         elif "connection" in str(e).lower():
# #             print("\n💡 Tip: Could not connect to the API.")
# #             print("   Check your internet connection and the API URL.")

# #     finally:
# #         # Clean up
# #         await client.close()


# # if __name__ == "__main__":
# #     # Run the async main function
# #     asyncio.run(main())
