# Path: utils/core/parsing.py

"""
String Parsing Utilities
(Internal module, imported by utils/core.py)
"""

from typing import Union, Set

# --- NEW: Export list ---
__all__ = ["parse_comma_list"]

from typing import Union, Set

def parse_comma_list(value: Union[str, None]) -> Set[str]:
    """
    Converts a comma-separated string into a set of stripped items.
    (Code moved from utils/core.py)
    """
    if not value: 
        return set()
    return {item.strip() for item in value.split(',') if item.strip() != ''}