# Path: modules/format_code/__init__.pyi
"""Statically declared API for format_code"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

CONFIG_FILENAME: Any
CONFIG_SECTION_NAME: Any
DEFAULT_EXTENSIONS: Any
DEFAULT_IGNORE: Any
DEFAULT_START_PATH: Any
FORC_DEFAULTS: Any
MODULE_DIR: Any
PROJECT_CONFIG_FILENAME: Any
TEMPLATE_FILENAME: Any
execute_format_code_action: Any
process_format_code_logic: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "DEFAULT_START_PATH",
    "FORC_DEFAULTS",
    "MODULE_DIR",
    "PROJECT_CONFIG_FILENAME",
    "TEMPLATE_FILENAME",
    "execute_format_code_action",
    "process_format_code_logic",
]