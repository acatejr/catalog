# tests/test_query_classification.py
from src.catalog.api.query_classifier import classify_query


def test_classify_basic_keyword_list():
    result = classify_query("List all keywords")
    assert result["type"] == "list_keywords"
    assert not result["params"]["distinct"]


def test_classify_distinct_keywords():
    result = classify_query("Show me unique keywords")
    assert result["params"]["distinct"]


def test_classify_keywords_with_count():
    result = classify_query("How many distinct keywords are there?")
    assert result["params"]["distinct"]
    assert result["params"]["count"]


def test_classify_non_keyword_query():
    result = classify_query("Tell me about the weather")
    assert result["type"] == "llm_chat"
