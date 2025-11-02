# Path: modules/pack_code/__init__.pyi
"""Statically declared API for pack_code"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

CONFIG_FILENAME: Any
CONFIG_SECTION_NAME: Any
DEFAULT_CLEAN_EXTENSIONS: Any
DEFAULT_EXTENSIONS: Any
DEFAULT_FORMAT_EXTENSIONS: Any
DEFAULT_IGNORE: Any
DEFAULT_INCLUDE: Any
DEFAULT_OUTPUT_DIR: Any
DEFAULT_START_PATH: Any
MODULE_DIR: Any
PCODE_DEFAULTS: Any
PROJECT_CONFIG_FILENAME: Any
TEMPLATE_FILENAME: Any
execute_pack_code_action: Any
process_pack_code_logic: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "DEFAULT_CLEAN_EXTENSIONS",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_FORMAT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "DEFAULT_INCLUDE",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_START_PATH",
    "MODULE_DIR",
    "PCODE_DEFAULTS",
    "PROJECT_CONFIG_FILENAME",
    "TEMPLATE_FILENAME",
    "execute_pack_code_action",
    "process_pack_code_logic",
]