# Path: modules/tree/__init__.pyi
"""Statically declared API for tree"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

CONFIG_FILENAME: Any
CONFIG_SECTION_NAME: Any
DEFAULT_DIRS_ONLY_LOGIC: Any
DEFAULT_EXTENSIONS: Any
DEFAULT_IGNORE: Any
DEFAULT_MAX_LEVEL: Any
DEFAULT_PRUNE: Any
FALLBACK_SHOW_SUBMODULES: Any
FALLBACK_USE_GITIGNORE: Any
PROJECT_CONFIG_FILENAME: Any
generate_tree: Any
load_config_files: Any
merge_config_sources: Any
print_final_result: Any
print_status_header: Any
process_tree_logic: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "DEFAULT_DIRS_ONLY_LOGIC",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "DEFAULT_MAX_LEVEL",
    "DEFAULT_PRUNE",
    "FALLBACK_SHOW_SUBMODULES",
    "FALLBACK_USE_GITIGNORE",
    "PROJECT_CONFIG_FILENAME",
    "generate_tree",
    "load_config_files",
    "merge_config_sources",
    "print_final_result",
    "print_status_header",
    "process_tree_logic",
]