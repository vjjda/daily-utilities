# Path: modules/stubgen/stubgen_config.py

"""
Configuration constants for stubgen.
"""

from typing import List, Set, Final
from pathlib import Path

# --- NEW: __all__ definition ---
__all__ = [
    "DEFAULT_IGNORE", 
    "SCAN_ROOTS", 
    "DYNAMIC_IMPORT_INDICATORS",
    "AST_MODULE_LIST_NAME",
    "AST_ALL_LIST_NAME"
]
# --- END NEW ---

# --- Scanning Configuration ---

# Các pattern FNMATCH mặc định luôn bị bỏ qua.
# Kế thừa từ .gitignore và path_checker_config.
DEFAULT_IGNORE: Final[Set[str]] = {
    "__pycache__", ".venv", "venv", "node_modules", ".git", 
    "dist", "build", "out", "*.pyc", "*.pyo"
}

# --- MODIFIED: Xóa 'scripts/internal/bootstrap' ---
# Các thư mục con (tương đối với scan_root) để tìm kiếm các module gateway.
# Đây là giá trị mặc định cho cờ --restrict.
SCAN_ROOTS: Final[List[str]] = [
    "modules", 
    "utils",
    # "scripts/internal/bootstrap" # <-- ĐÃ XÓA (giờ nằm trong 'modules')
]
# --- END MODIFIED ---

# Các chuỗi code dùng để xác định file __init__.py có phải là dynamic gateway không
DYNAMIC_IMPORT_INDICATORS: Final[List[str]] = [
    "import_module", 
    "globals()[name]", 
    "globals()[name] = obj" 
]

# Tên biến AST để trích xuất
AST_MODULE_LIST_NAME: Final[str] = 'modules_to_export'
AST_ALL_LIST_NAME: Final[str] = '__all__'