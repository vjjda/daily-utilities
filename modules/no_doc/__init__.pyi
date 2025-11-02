# Path: modules/no_doc/__init__.pyi
"""Statically declared API for no_doc"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

CONFIG_FILENAME: Any
CONFIG_SECTION_NAME: Any
DEFAULT_EXTENSIONS: Any
DEFAULT_FORMAT_EXTENSIONS: Any
DEFAULT_IGNORE: Any
DEFAULT_START_PATH: Any
MODULE_DIR: Any
NDOC_DEFAULTS: Any
PROJECT_CONFIG_FILENAME: Any
TEMPLATE_FILENAME: Any
execute_ndoc_action: Any
process_no_doc_logic: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_FORMAT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "DEFAULT_START_PATH",
    "MODULE_DIR",
    "NDOC_DEFAULTS",
    "PROJECT_CONFIG_FILENAME",
    "TEMPLATE_FILENAME",
    "execute_ndoc_action",
    "process_no_doc_logic",
]