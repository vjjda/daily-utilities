# Path: modules/tree/tree_config.py

"""
Configuration constants for the Tree (ctree) module.
(Single Source of Truth)
"""

from typing import Set, Optional

# --- 1. Logic Fallback Defaults ---
# Đây là giá trị mặc định "thực sự" của tool nếu không
# có cờ CLI hoặc file .ini nào được cấu hình.
DEFAULT_IGNORE: Set[str] = {
    "__pycache__", ".venv", "venv", "node_modules", ".git"
}
DEFAULT_PRUNE: Set[str] = {"dist", "build"}
DEFAULT_DIRS_ONLY_LOGIC: Set[str] = set()
FALLBACK_SHOW_SUBMODULES: bool = False
DEFAULT_MAX_LEVEL: Optional[int] = None

# --- 2. Argparse Defaults ---
# Các giá trị `None` này rất quan trọng để kích hoạt
# logic ưu tiên 3 tầng (CLI > .ini > Fallback).
DEFAULT_MAX_LEVEL_ARG: Optional[int] = DEFAULT_MAX_LEVEL
DEFAULT_SHOW_SUBMODULES_ARG: Optional[bool] = None
DEFAULT_DIRS_ONLY_ARG: Optional[str] = None

# --- 3. Config File Names ---
CONFIG_FILENAME: str = ".tree.ini"
PROJECT_CONFIG_FILENAME: str = ".project.ini"
CONFIG_SECTION_NAME: str = "tree"