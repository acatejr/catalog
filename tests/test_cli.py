"""Tests for catalog.cli Click commands."""

import pytest
import warnings
from click.testing import CliRunner


class TestHealthCommand:
    """Tests for health CLI command."""

    def test_health_returns_ok(self):
        """Test that health command returns OK status."""
        warnings.warn("TODO: Implement test for health command", UserWarning)


class TestDownloadFsMetadataCommand:
    """Tests for download_fs_metadata CLI command."""

    def test_download_fs_metadata_invokes_loaders(self):
        """Test that download_fs_metadata invokes all loaders."""
        warnings.warn("TODO: Implement test for download command", UserWarning)


class TestBuildFsCatalogCommand:
    """Tests for build_fs_catalog CLI command."""

    def test_build_fs_catalog_creates_json(self):
        """Test that build_fs_catalog creates catalog JSON."""
        warnings.warn("TODO: Implement test for build catalog command", UserWarning)


class TestBuildFsChromadbCommand:
    """Tests for build_fs_chromadb CLI command."""

    def test_build_fs_chromadb_loads_documents(self):
        """Test that build_fs_chromadb loads documents into ChromaDB."""
        warnings.warn("TODO: Implement test for ChromaDB build command", UserWarning)


class TestQueryFsChromadbCommand:
    """Tests for query_fs_chromadb CLI command."""

    def test_query_fs_chromadb_returns_results(self):
        """Test that query_fs_chromadb returns search results."""
        warnings.warn("TODO: Implement test for query command", UserWarning)


class TestOllamaChatCommand:
    """Tests for ollama_chat CLI command."""

    def test_ollama_chat_sends_query(self):
        """Test that ollama_chat sends query to LLM."""
        warnings.warn("TODO: Implement test for ollama chat command", UserWarning)
