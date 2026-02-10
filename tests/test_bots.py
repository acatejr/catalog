"""Tests for catalog.bots."""

import pytest
from unittest.mock import patch, MagicMock
from catalog.bots import VerdeBot


class TestVerdeBot:
    """Tests for VerdeBot class."""

    def test_init_raises_without_env_vars(self):
        """Test that __init__ raises ValueError when env vars are missing."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="VERDE_API_KEY"):
                VerdeBot()

    def test_init_succeeds_with_env_vars(self):
        """Test that __init__ succeeds when all env vars are set."""
        env = {
            "VERDE_API_KEY": "test-key",
            "VERDE_URL": "http://localhost:8000",
            "VERDE_MODEL": "test-model",
        }
        with patch.dict("os.environ", env, clear=True):
            bot = VerdeBot()
            assert bot.VERDE_API_KEY == "test-key"
            assert bot.VERDE_URL == "http://localhost:8000"
            assert bot.VERDE_MODEL == "test-model"

    def test_chat_returns_response(self):
        """Test that chat sends correct request and returns content."""
        env = {
            "VERDE_API_KEY": "test-key",
            "VERDE_URL": "http://localhost:8000",
            "VERDE_MODEL": "test-model",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Here are some datasets."}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.dict("os.environ", env, clear=True):
            bot = VerdeBot()
            with patch("requests.post", return_value=mock_response) as mock_post:
                result = bot.chat(question="fire data", context="some context")

                assert result == "Here are some datasets."
                mock_post.assert_called_once()
