# Path: modules/tree/tree_internal/__init__.pyi
"""Statically declared API for tree_internal"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

load_config_files: Any
merge_config_sources: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "load_config_files",
    "merge_config_sources",
]