# catalog/api/query_classifier.py
"""
Query classification for natural language keyword queries.
Inspired by the pattern matching approach in api.py (lines 77-146).
"""

# from typing import Dict, Optional, List
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class QueryType(Enum):
    LIST_KEYWORDS = "list_keywords"
    LLM_CHAT = "llm_chat"


# Pattern definitions
# Patterns from reference code lines 82-93
KEYWORD_LIST_PATTERNS = [
    "list keywords",
    "keyword list",
    "show keywords",
    "all keywords",
    "all the keywords",
    "keywords in the catalog",
    "keywords catalog",
    "all unique keywords",
    "unique keywords",
    "distinct keywords",
    "keywords list",
]

# Patterns from reference code lines 97-98
DISTINCT_PATTERNS = ["unique", "distinct", "no duplicates", "without duplicates"]

# Patterns from reference code lines 102-111
COUNT_PATTERNS = [
    "how many",
    "number of",
    "count of",
    "total",
    "top",
    "count",
    "most frequent",
    "frequent",
    "frequencies",
]

# Mapping for written numbers to digits
WORD_TO_NUM = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "hundred": 100,
}


def extract_limit(query: str) -> int | None:
    """
    Extract numeric limit from a natural language query.

    Handles patterns like:
    - "top 10 keywords"
    - "first 20"
    - "show me 5 keywords"
    - "limit 30"
    - "top ten" (written numbers)

    Args:
        query: Lowercased query string

    Returns:
        int: Extracted limit value, or None if no limit found
    """
    # Pattern 1: "top/first/last/show N" or "limit N"
    pattern1 = r"\b(?:top|first|last|show|limit)\s+(\d+)\b"
    match = re.search(pattern1, query)
    if match:
        return int(match.group(1))

    # Pattern 2: "N keywords/items/results"
    pattern2 = r"\b(\d+)\s+(?:keywords?|items?|results?)\b"
    match = re.search(pattern2, query)
    if match:
        return int(match.group(1))

    # Pattern 3: Written numbers like "top ten", "first five"
    pattern3 = (
        r"\b(?:top|first|last|show|limit)\s+(" + "|".join(WORD_TO_NUM.keys()) + r")\b"
    )
    match = re.search(pattern3, query)
    if match:
        word = match.group(1)
        if word in WORD_TO_NUM:
            return WORD_TO_NUM[word]

    return None


def classify_query(query: str) -> dict:
    """
    Classify a natural language query into structured parameters.

    Improves upon the reference implementation (api.py lines 79-122) by:
    - Separating classification logic into a dedicated function
    - Using clear variable names
    - Returning consistent structure

    Returns:
        dict: {
            "type": "list_keywords" | "llm_chat",
            "params": {
                "distinct": bool,
                "count": bool,
                "limit": Optional[int]
            }
        }
    """
    q_lower = query.lower()

    # Step 1: Check if it's a keyword-related query (ref: lines 79-93)
    is_keyword_query = any(pattern in q_lower for pattern in KEYWORD_LIST_PATTERNS)

    if not is_keyword_query:
        return {"type": "llm_chat", "params": {}}

    # Step 2: Determine if distinct/unique is requested (ref: lines 95-98)
    distinct = any(pattern in q_lower for pattern in DISTINCT_PATTERNS)

    # Step 3: Determine if counts/frequencies are requested (ref: lines 99-111)
    count = any(pattern in q_lower for pattern in COUNT_PATTERNS)

    # Step 4: Extract limit if specified (e.g., "top 10", "first 20")
    # This extends the reference code's logic
    limit = extract_limit(q_lower)

    result = {
        "type": "list_keywords",
        "params": {"distinct": distinct, "count": count, "limit": limit},
    }

    logger.info(f"Query classified: '{query[:50]}' --> {result}")
    return result


def format_keyword_response(keywords_data, params: dict) -> str:
    """
    Format keyword data into a natural language response.

    Improves upon the reference code's inline formatting (lines 128-142) by:
    - Extracting formatting into a testable function
    - Handling all combinations of distinct/count correctly
    - Providing consistent response structure

    Args:
        keywords_data: List of keywords or list of dicts with counts
        params: Classification parameters (distinct, count, limit)

    Returns:
        str: Formatted natural language response
    """
    if params.get("count", False):
        # Format with counts - keywords_data should be list of dicts with 'keyword' and 'count' keys
        # Format: "There are X unique keywords. Top keywords: keyword1 (5), keyword2 (3)..."
        total = len(keywords_data)
        formatted_items = [
            f"{kw['keyword']} ({kw['count']})" for kw in keywords_data[:10]
        ]
        return f"There are {total} unique keywords in the catalog. Top keywords: {', '.join(formatted_items)}"

    elif params.get("distinct", False):
        # Format distinct keywords without counts
        # Format: "Here are the X unique keywords: keyword1, keyword2, ..."
        return f"There are {len(keywords_data)} unique keywords: {', '.join(keywords_data)}"

    else:
        # All keywords including duplicates (no counts)
        return f"Here are {len(keywords_data)} keywords: {', '.join(keywords_data)}"
