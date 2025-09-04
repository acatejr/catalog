"""
Simple Client for CyVerse LLM API using pydantic-ai
"""

import asyncio
import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from dotenv import load_dotenv

load_dotenv()

VERDI_ESILL_API_KEY = os.getenv('VERDI_ESILL_API_KEY')
VERDI_ESILL_URL = os.getenv('VERDI_ESILL_URL')


async def main():
    """
    Main function to send a message to the LLM and print the response
    """

    # Get API key from environment or use dummy
    api_key = os.getenv('VERDI_ESILL_API_KEY', 'dummy-key')

    # Configure the OpenAI-compatible model using OpenAIChatModel
    model = OpenAIChatModel(
        model_name='anvilgpt/llama3.1:latest',
        base_url='https://llm-api.cyverse.ai/v1',
        api_key=api_key
    )

    # model = OpenAIChatModel(
    #     model='anvilgpt/llama3.1:latest',
    #     base_url='https://llm-api.cyverse.ai/v1',
    #     api_key=api_key
    # )

    # Create an agent with the model
    agent = Agent(
        model=model,
        result_type=str,
        system_prompt="You are a helpful assistant."
    )

    try:
        # Send the message and get the response
        print("Sending message to LLM...")
        result = await agent.run("hello")

        # Print the response
        print(f"\nLLM Response: {result.data}")

    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"Error type: {type(e).__name__}")

        # If authentication is needed, provide guidance
        if "401" in str(e) or "unauthorized" in str(e).lower():
            print("\nNote: You may need to provide an API key.")
            print("Set the CYVERSE_API_KEY environment variable with your API key.")


if __name__ == "__main__":
    asyncio.run(main())

# # from pydantic import BaseModel, HttpUrl
# # import requests
# from dotenv import load_dotenv
# import asyncio
# import os
# from typing import Optional
# from pydantic_ai import Agent
# from pydantic_ai.models.openai import OpenAIChatModel
# from pydantic import BaseModel, Field
# import httpx


# load_dotenv()

# VERDI_ESILL_API_KEY = os.getenv('VERDI_ESILL_API_KEY')
# VERDI_ESILL_URL = os.getenv('VERDI_ESILL_URL')

# """
# Enhanced Client for CyVerse LLM API using pydantic-ai
# """


# class Config(BaseModel):
#     """Configuration for the LLM client"""
#     base_url: str = Field(default="https://llm-api.cyverse.ai/v1")
#     model_name: str = Field(default="anvilgpt/llama3.1:latest")
#     api_key: Optional[str] = Field(default=None)
#     timeout: int = Field(default=30)


# class LLMClient:
#     """Client for interacting with the LLM API"""

#     def __init__(self, config: Optional[Config] = None):
#         """
#         Initialize the LLM client

#         Args:
#             config: Configuration object, uses defaults if None
#         """
#         self.config = config or Config()

#         # Check for API key in environment variable
#         if not self.config.api_key:
#             self.config.api_key = os.getenv('CYVERSE_API_KEY', 'dummy-key')

#         # Setup HTTP client with custom timeout
#         http_client = httpx.AsyncClient(timeout=self.config.timeout)

#         # Configure the model
#         self.model = OpenAIChatModel(
#             self.config.model_name,
#             base_url=self.config.base_url,
#             api_key=self.config.api_key,
#             http_client=http_client
#         )

#         # Create the agent
#         self.agent = Agent(
#             model=self.model,
#             result_type=str,
#             system_prompt="You are a helpful assistant."
#         )

#     async def send_message(self, message: str) -> str:
#         """
#         Send a message to the LLM and return the response

#         Args:
#             message: The message to send

#         Returns:
#             The LLM's response as a string
#         """
#         try:
#             result = await self.agent.run(message)
#             return result.data
#         except Exception as e:
#             raise Exception(f"Failed to get response from LLM: {e}")

#     async def close(self):
#         """Clean up resources"""
#         if hasattr(self.model, 'http_client'):
#             await self.model.http_client.aclose()


# async def main():
#     """
#     Main function to demonstrate the client usage
#     """
#     # Create client with default configuration
#     client = LLMClient()

#     try:
#         # Send "hello" message
#         print("Sending message to LLM...")
#         response = await client.send_message("hello")

#         # Print the response
#         print(f"\nLLM Response: {response}")

#     except Exception as e:
#         print(f"Error: {e}")

#         # Provide helpful error messages
#         if "401" in str(e) or "403" in str(e):
#             print("\n💡 Tip: Authentication may be required.")
#             print("   Set the CYVERSE_API_KEY environment variable or")
#             print("   pass api_key to the Config object.")
#         elif "404" in str(e):
#             print("\n💡 Tip: The model or endpoint may not exist.")
#             print(f"   Tried to access: {client.config.base_url}")
#             print(f"   Model: {client.config.model_name}")
#         elif "connection" in str(e).lower():
#             print("\n💡 Tip: Could not connect to the API.")
#             print("   Check your internet connection and the API URL.")

#     finally:
#         # Clean up
#         await client.close()


# if __name__ == "__main__":
#     # Run the async main function
#     asyncio.run(main())