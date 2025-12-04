import json
from pathlib import Path
from bs4 import BeautifulSoup

soup = BeautifulSoup()


def save_json(
    data: dict | list,
    file_path: str | Path,
    indent: int = 2,
    ensure_ascii: bool = False,
    create_dirs: bool = True,
) -> None:
    """
    Save a dictionary or list to a JSON file.

    Args:
        data: Dictionary or list to save as JSON
        file_path: Path to the output JSON file
        indent: Number of spaces for indentation (default: 2). Set to None for compact output
        ensure_ascii: If True, escape non-ASCII characters (default: False)
        create_dirs: If True, create parent directories if they don't exist (default: True)

    Raises:
        TypeError: If data is not JSON serializable
        IOError: If file cannot be written

    Example:
        >>> data = {"title": "Example", "keywords": ["test", "demo"]}
        >>> save_json(data, "output/data.json")

        >>> documents = [{"title": "Doc 1"}, {"title": "Doc 2"}]
        >>> save_json(documents, "output/documents.json", indent=4)
    """
    file_path = Path(file_path)

    # Create parent directories if needed
    if create_dirs and not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON to file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)


def load_json(file_path: str | Path) -> dict | list:
    """
    Load a JSON file and return the parsed data.

    Args:
        file_path: Path to the JSON file to load

    Returns:
        Parsed JSON data as a dictionary or list

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON

    Example:
        >>> data = load_json("output/data.json")
        >>> print(data["title"])

        >>> documents = load_json("output/documents.json")
        >>> for doc in documents:
        ...     print(doc["title"])
    """
    file_path = Path(file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


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
