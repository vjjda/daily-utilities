# Path: modules/bootstrap/__init__.pyi
"""Statically declared API for bootstrap"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

CONFIG_SECTION_NAME: Any
DEFAULT_BIN_DIR_NAME: Any
DEFAULT_DOCS_DIR_NAME: Any
DEFAULT_MODULES_DIR_NAME: Any
DEFAULT_SCRIPTS_DIR_NAME: Any
TEMPLATE_DIR: Any
TYPE_HINT_MAP: Any
TYPING_IMPORTS: Any
execute_bootstrap_action: Any
process_bootstrap_logic: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "CONFIG_SECTION_NAME",
    "DEFAULT_BIN_DIR_NAME",
    "DEFAULT_DOCS_DIR_NAME",
    "DEFAULT_MODULES_DIR_NAME",
    "DEFAULT_SCRIPTS_DIR_NAME",
    "TEMPLATE_DIR",
    "TYPE_HINT_MAP",
    "TYPING_IMPORTS",
    "execute_bootstrap_action",
    "process_bootstrap_logic",
]