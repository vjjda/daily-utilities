# Path: modules/stubgen/stubgen_config.py
"""
Configuration constants for stubgen.
"""

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
    "CONFIG_SECTION_NAME"
]

# --- Scanning Configuration ---

DEFAULT_IGNORE: Final[Set[str]] = {
    "__pycache__", ".venv", "venv", "node_modules", ".git", 
    "dist", "build", "out", "*.pyc", "*.pyo"
}

# Mặc định là None (không lọc)
DEFAULT_INCLUDE: Final[Optional[Set[str]]] = None

# --- AST Parsing Configuration ---

# Các chuỗi văn bản nhận diện __init__.py là "gateway động"
DYNAMIC_IMPORT_INDICATORS: Final[List[str]] = [
    "import_module", 
    "globals()[name]", 
    "globals()[name] = obj" 
]

# Tên biến (AST node name) chứa danh sách module cần import
AST_MODULE_LIST_NAME: Final[str] = 'modules_to_export'
# Tên biến (AST node name) chứa danh sách symbol __all__
AST_ALL_LIST_NAME: Final[str] = '__all__'

# --- Config File Names ---

PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".sgen.toml"
CONFIG_SECTION_NAME: Final[str] = "sgen"