# Path: modules/stubgen/stubgen_config.py

"""
Configuration constants for stubgen.
"""

from typing import List, Set, Final
from pathlib import Path

# --- NEW: __all__ definition ---
__all__ = [
    # Defaults
    "DEFAULT_IGNORE", 
    "DEFAULT_RESTRICT", # <-- MODIFIED: Đổi tên
    "DYNAMIC_IMPORT_INDICATORS",
    "AST_MODULE_LIST_NAME",
    "AST_ALL_LIST_NAME",
    
    # Config File Names
    "PROJECT_CONFIG_FILENAME",
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME"
]
# --- END NEW ---

# --- Scanning Configuration ---

DEFAULT_IGNORE: Final[Set[str]] = {
    "__pycache__", ".venv", "venv", "node_modules", ".git", 
    "dist", "build", "out", "*.pyc", "*.pyo"
}

# --- MODIFIED: Đổi tên SCAN_ROOTS ---
# Các thư mục con (tương đối với scan_root) để tìm kiếm các module gateway.
DEFAULT_RESTRICT: Final[List[str]] = [
    "modules", 
    "utils",
]
# --- END MODIFIED ---

DYNAMIC_IMPORT_INDICATORS: Final[List[str]] = [
    "import_module", 
    "globals()[name]", 
    "globals()[name] = obj" 
]

AST_MODULE_LIST_NAME: Final[str] = 'modules_to_export'
AST_ALL_LIST_NAME: Final[str] = '__all__'

PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".sgen.toml"
CONFIG_SECTION_NAME: Final[str] = "sgen"