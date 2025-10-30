# Path: modules/stubgen/stubgen_config.py
from typing import List, Set, Final, Optional
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
    "import_module",
    "globals()[name]",
    "globals()[name] = obj",
]


AST_MODULE_LIST_NAME: Final[str] = "modules_to_export"

AST_ALL_LIST_NAME: Final[str] = "__all__"


PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".sgen.toml"
CONFIG_SECTION_NAME: Final[str] = "sgen"