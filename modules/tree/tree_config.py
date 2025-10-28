# Path: modules/tree/tree_config.py

"""
Configuration constants for the Tree (ctree) module.
(Single Source of Truth)
"""

from typing import Set, Optional, Final

__all__ = [
    "DEFAULT_IGNORE", "DEFAULT_PRUNE", "DEFAULT_DIRS_ONLY_LOGIC",
    "DEFAULT_EXTENSIONS",
    "FALLBACK_SHOW_SUBMODULES", "DEFAULT_MAX_LEVEL",
    "FALLBACK_USE_GITIGNORE",
    "CONFIG_FILENAME", "PROJECT_CONFIG_FILENAME", "CONFIG_SECTION_NAME"
]


# --- 1. Logic Fallback Defaults ---
# Các giá trị này được sử dụng khi không có file config
# hoặc cờ CLI nào được chỉ định.

DEFAULT_IGNORE: Final[Set[str]] = {
    "__pycache__", ".venv", "venv", "node_modules", ".git"
}
DEFAULT_PRUNE: Final[Set[str]] = {"dist", "build"}
DEFAULT_DIRS_ONLY_LOGIC: Final[Set[str]] = set()

# Mặc định là None (không lọc), có nghĩa là hiển thị tất cả file.
DEFAULT_EXTENSIONS: Final[Optional[Set[str]]] = None

FALLBACK_SHOW_SUBMODULES: Final[bool] = False
DEFAULT_MAX_LEVEL: Final[Optional[int]] = None

# Mặc định là 'True' (luôn tôn trọng .gitignore nếu có)
FALLBACK_USE_GITIGNORE: Final[bool] = True

# --- 2. Config File Names ---
CONFIG_FILENAME: Final[str] = ".tree.toml"
PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_SECTION_NAME: Final[str] = "tree"