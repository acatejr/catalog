from dotenv import load_dotenv
import os
# from langchain_community.chat_models import ChatLiteLLM
from langchain_litellm import ChatLiteLLM

load_dotenv()

VERDE_API_KEY = os.getenv("VERDE_API_KEY")
VERDE_URL = os.getenv("VERDE_URL")
VERDE_MODEL = os.getenv("VERDE_MODEL")

class VerdeBot:
    def __init__(self):
        pass

    def chat(self, message):
        llm = ChatLiteLLM(
            model=f"litellm_proxy/{VERDE_MODEL}",
            api_key=VERDE_API_KEY,
            api_base=VERDE_URL)
        response = llm.invoke(message)
        return response


def main():
    print("Hello from verde!")
    bot = VerdeBot()
    resp = bot.chat("Tell me a joke.")
    print(resp.content)


if __name__ == "__main__":
    main()
