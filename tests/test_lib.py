import pytest
from src.catalog.lib import clean_str


class TestLib:
    def test_clean_str_basic(self):
        text = "  Hello World!  "
        expected = "Hello World!"
        assert clean_str(text) == expected

    def test_clean_str_newlines(self):
        text = "Line 1\n\nLine 2\nLine 3"
        expected = "Line 1 Line 2 Line 3"
        assert clean_str(text) == expected

    def test_clean_str_html(self):
        text = "<p>Some <b>HTML</b> text.</p>"
        expected = "Some HTML text."
        assert clean_str(text) == expected

    def test_clean_str_html_and_newlines(self):
        text = "  <p>First line.\n\nSecond line with <b>HTML</b>.</p>  "
        expected = "First line. Second line with HTML."
        assert clean_str(text) == expected

    def test_clean_str_empty(self):
        text = ""
        expected = ""
        assert clean_str(text) == expected

    def test_clean_str_only_newlines(self):
        text = "\n\n\n"
        expected = ""
        assert clean_str(text) == expected

    def test_clean_str_only_html(self):
        text = "<p></p>"
        expected = ""
        assert clean_str(text) == expected

    def test_strip_html_complex(self):
        text = "<div><h1>Title</h1><p>This is a <a href='#'>link</a>.</p></div>"
        expected = "TitleThis is a link."
        assert clean_str(text) == expected
