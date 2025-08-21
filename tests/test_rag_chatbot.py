import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from catalog.rag.main import RAGChatBot

class TestRAGChatbot:

    def test_init(self):
        self.chatbot = RAGChatBot(model_name="test_model", rag_config={"param": "value"})
        assert self.chatbot.model_name == "test_model"
        assert self.chatbot.rag_config == {"param": "value"}

    # @pytest.fixture
    # def mock_rag_chatbot(self):
    #     with patch('rag_chatbot.RAGChatbot') as MockRAGChatbot:
    #         instance = MockRAGChatbot.return_value
    #         instance.get_response = Mock()
    #         yield instance

    # def test_get_response(self, mock_rag_chatbot):
    #     # Arrange
    #     mock_rag_chatbot.get_response.return_value = "Mocked response"
    #     user_input = "What is RAG?"

    #     # Act
    #     response = mock_rag_chatbot.get_response(user_input)

    #     # Assert
    #     assert response == "Mocked response"
    #     mock_rag_chatbot.get_response.assert_called_once_with(user_input)