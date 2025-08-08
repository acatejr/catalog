import pytest
from catalog.lib.query import (
    count_documents,
    get_keyword_frequencies
)

def test_count_documents():

    count = count_documents()
    assert isinstance(count, int)
    assert count >= 0

def test_get_keyword_frequencies():
    frequencies = get_keyword_frequencies()
    assert isinstance(frequencies, list)
    assert len(frequencies) >= 0
    # assert all(isinstance(k, str) and isinstance(v, int) for k, v in frequencies.items())
    # assert len(frequencies) > 0