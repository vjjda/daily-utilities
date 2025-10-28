# Path: modules/stubgen/stubgen_config.py

"""
Configuration constants for stubgen.
"""

# --- MODIFIED: Thêm Optional và Set ---
from typing import List, Set, Final, Optional
# --- END MODIFIED ---
from pathlib import Path

# --- MODIFIED: Cập nhật __all__ ---
__all__ = [
    # Defaults
    "DEFAULT_IGNORE", 
    "DEFAULT_RESTRICT",
    "DEFAULT_INCLUDE", # <-- NEW
    "DYNAMIC_IMPORT_INDICATORS",
    "AST_MODULE_LIST_NAME", 
    "AST_ALL_LIST_NAME",
    
    # Config File Names
    "PROJECT_CONFIG_FILENAME",
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME"
]
# --- END MODIFIED ---

# --- Scanning Configuration ---

DEFAULT_IGNORE: Final[Set[str]] = {
    "__pycache__", ".venv", "venv", "node_modules", ".git", 
    "dist", "build", "out", "*.pyc", "*.pyo"
}

# Các thư mục con (tương đối với scan_root) để tìm kiếm các module gateway.
DEFAULT_RESTRICT: Final[List[str]] = [
    "modules", 
    "utils",
]

# --- NEW: Inclusion Filter ---
# Mặc định là None (không lọc)
DEFAULT_INCLUDE: Final[Optional[Set[str]]] = None
# --- END NEW ---

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