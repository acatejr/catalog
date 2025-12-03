from bs4 import BeautifulSoup

soup = BeautifulSoup()


def clean_str(text: str) -> str:
    cleaned_str = text.strip().replace("\n\n", " ")
    clean_str = strip_html(cleaned_str)

    return clean_str


def strip_html(text: str) -> str:
    """_summary_

    Args:
        text (_type_): _description_

    Returns:
        _type_: _description_
    """

    soup = BeautifulSoup(text, "html.parser")
    stripped_text = soup.get_text()
    stripped_text = stripped_text.replace("\n", " ")
    return stripped_text
