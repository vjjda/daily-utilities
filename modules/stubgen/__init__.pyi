# Path: modules/stubgen/__init__.pyi
"""Statically declared API for stubgen"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

AST_ALL_LIST_NAME: Any
AST_MODULE_LIST_NAME: Any
CONFIG_FILENAME: Any
CONFIG_SECTION_NAME: Any
DEFAULT_IGNORE: Any
DEFAULT_INCLUDE: Any
DYNAMIC_IMPORT_INDICATORS: Any
MODULE_DIR: Any
PROJECT_CONFIG_FILENAME: Any
SGEN_DEFAULTS: Any
TEMPLATE_FILENAME: Any
execute_stubgen_action: Any
process_stubgen_logic: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "AST_ALL_LIST_NAME",
    "AST_MODULE_LIST_NAME",
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "DEFAULT_IGNORE",
    "DEFAULT_INCLUDE",
    "DYNAMIC_IMPORT_INDICATORS",
    "MODULE_DIR",
    "PROJECT_CONFIG_FILENAME",
    "SGEN_DEFAULTS",
    "TEMPLATE_FILENAME",
    "execute_stubgen_action",
    "process_stubgen_logic",
]