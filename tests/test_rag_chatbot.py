import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from catalog.rag.main import RAGChatBot
from sentence_transformers import SentenceTransformer
from rich.console import Console

console = Console()

class TestRAGChatbot:

    @pytest.fixture()
    def rag_chatbot(self):
        self.chatbot = RAGChatBot(model_name="test_model", rag_config={"param": "value"})


    def test_init(self, rag_chatbot):
        # self.chatbot = RAGChatBot(model_name="test_model", rag_config={"param": "value"})
        assert self.chatbot.model_name == "test_model"
        assert self.chatbot.rag_config == {"param": "value"}


    def test_search_docs_with_empty_embedding(self, rag_chatbot):
        with pytest.raises(TypeError):
            self.chatbot.search_docs()

    def test_search_docs(self, rag_chatbot):
        search_string = "Find wildfire relevant documents."

        # Generate the embeddings
        encoder = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = encoder.encode(search_string).tolist()
        assert len(query_embedding) > 0  # Should have embedding dimensions

        # Test the search_docs method
        docs = self.chatbot.search_docs(query_embedding)
        assert isinstance(docs, list)

        for doc in docs:
            assert isinstance(doc, dict)
            assert "id" in doc
            assert "title" in doc
            assert "description" in doc
            assert "keywords" in doc
            assert "similarity_score" in doc
            assert 0 <= doc["similarity_score"] <= 1

    def test_generate_llm_rag_response(self, rag_chatbot):

        query = "Find datasets related to wildfires in California."

        # Generate the embeddings
        encoder = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = encoder.encode(query).tolist()
        assert len(query_embedding) > 0  # Should have embedding dimensions

        doocs = self.chatbot.search_docs(query_embedding, limit=5)
        assert isinstance(doocs, list)

        context = "\n\n".join([
            f"Title: {doc['title']}\nDescription: {doc['description']}\nKeywords: {doc['keywords']}"
            for doc in doocs
        ])

        # Librarian prompt
        prompt_messages = [
            {
                "role": "system",
                "content": """
                You are a helpful and knowledgeable data catalog librarian. Your role is to:
                1. Help users find the most relevant data assets for their needs
                2. Explain the contents and structure of data assets
                3. Provide guidance on data access and usage
                4. Suggest related datasets that might be useful
                5. Highlight important metadata like update frequency and data quality

                Be professional, thorough, and focus on helping users understand the data assets available to them.
                """
            },
            {
                "role": "user",
                "content": f"""
                User Query: {query}

                Available Data Assets:
                {context}

                Please provide a helpful response that:
                1. Addresses the user's specific query
                2. Describes the most relevant data assets
                3. Explains how the data could be used
                4. Mentions any important considerations (data quality, access levels, etc.)
                5. Suggests next steps or related datasets
                """
            }
        ]
