import pytest
from catalog.llm import ChatBot


class TestLLMClient:

    @pytest.fixture
    def chatbot(self):
        """Create a test chatbot."""

        return ChatBot()

    def test_init_client(self, chatbot):
        assert chatbot.client is not None
        assert chatbot.model == "Llama-3.2-11B-Vision-Instruct"


    def test_chat_method(self, chatbot):
        response = chatbot.chat("What is CyVerse?")
        assert isinstance(response, str)
        assert len(response) > 0

        chatbot = ChatBot()

    def test_chat_fire_message(self, chatbot):
        response = chatbot.chat("What fire data is available in the data store?")
        assert isinstance(response, str)
        assert len(response) > 0
        assert "fire" in response.lower()


# Test with a custom messages to possibly use later
# custom_message = "Describe what wildfire data is available in the data store."
# custom_message = "Is there erosion data in NRM?"
# custom_message = "I need to create a dashboard that shows recreational maintenance costs at a US National Forest.  What data sets should I consider?"

# custom_message = "How many datasets are in the catalog where the source is NRM?"
# custom_message = "How many datasets are in the catalog where the source is EDW?"
# custom_message = "What is the most frequent type in the src field in the catalog?"


