# Path: modules/check_path/__init__.pyi
"""Statically declared API for check_path"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

COMMENT_RULES: Any
COMMENT_RULES_BY_EXT: Any
CONFIG_FILENAME: Any
CONFIG_SECTION_NAME: Any
CPATH_DEFAULTS: Any
DEFAULT_EXTENSIONS: Any
DEFAULT_IGNORE: Any
MODULE_DIR: Any
PROJECT_CONFIG_FILENAME: Any
TEMPLATE_FILENAME: Any
execute_check_path_action: Any
process_check_path_logic: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "COMMENT_RULES",
    "COMMENT_RULES_BY_EXT",
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "CPATH_DEFAULTS",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "MODULE_DIR",
    "PROJECT_CONFIG_FILENAME",
    "TEMPLATE_FILENAME",
    "execute_check_path_action",
    "process_check_path_logic",
]