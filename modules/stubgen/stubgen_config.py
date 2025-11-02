# Path: modules/stubgen/stubgen_config.py
from typing import List, Set, Final, Optional, Dict, Any
from pathlib import Path

__all__ = [
    "DEFAULT_IGNORE",
    "DEFAULT_INCLUDE",
    "DYNAMIC_IMPORT_INDICATORS",
    "AST_MODULE_LIST_NAME",
    "AST_ALL_LIST_NAME",
    "PROJECT_CONFIG_FILENAME",
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "MODULE_DIR",
    "TEMPLATE_FILENAME",
    "SGEN_DEFAULTS",
]


DEFAULT_IGNORE: Final[Set[str]] = {
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".git",
    "dist",
    "build",
    "out",
    "*.pyc",
    "*.pyo",
}


DEFAULT_INCLUDE: Final[Optional[Set[str]]] = None


DYNAMIC_IMPORT_INDICATORS: Final[List[str]] = [
    "globals()[name]",
    "globals().update",
]


AST_MODULE_LIST_NAME: Final[str] = "modules_to_export"

AST_ALL_LIST_NAME: Final[str] = "__all__"


PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".sgen.toml"
CONFIG_SECTION_NAME: Final[str] = "sgen"


MODULE_DIR: Final[Path] = Path(__file__).parent
TEMPLATE_FILENAME: Final[str] = "stubgen.toml.template"

SGEN_DEFAULTS: Final[Dict[str, Any]] = {
    "ignore": DEFAULT_IGNORE,
    "include": DEFAULT_INCLUDE or set(),
    "dynamic_import_indicators": DYNAMIC_IMPORT_INDICATORS,
    "ast_module_list_name": AST_MODULE_LIST_NAME,
    "ast_all_list_name": AST_ALL_LIST_NAME,
}
