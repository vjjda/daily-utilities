# Path: modules/tree/tree_config.py

"""
Configuration constants for the Tree (ctree) module.
(Single Source of Truth)
"""

from typing import Set, Optional

# --- MODIFIED: __all__ definition ---
__all__ = [
    # Logic Fallbacks
    "DEFAULT_IGNORE", "DEFAULT_PRUNE", "DEFAULT_DIRS_ONLY_LOGIC",
    "DEFAULT_EXTENSIONS", # <-- NEW
    "FALLBACK_SHOW_SUBMODULES", "DEFAULT_MAX_LEVEL",
    "FALLBACK_USE_GITIGNORE",
    
    # Config File Names
    "CONFIG_FILENAME", "PROJECT_CONFIG_FILENAME", "CONFIG_SECTION_NAME"
]
# --- END MODIFIED ---


# --- 1. Logic Fallback Defaults ---
# Đây là giá trị mặc định "thực sự" của tool nếu không
# có cờ CLI hoặc file .ini nào được cấu hình.
DEFAULT_IGNORE: Set[str] = {
    "__pycache__", ".venv", "venv", "node_modules", ".git"
}
DEFAULT_PRUNE: Set[str] = {"dist", "build"}
DEFAULT_DIRS_ONLY_LOGIC: Set[str] = set()

# --- NEW: Extension Filter Default ---
# Mặc định là None, có nghĩa là "không lọc", hiển thị tất cả file.
DEFAULT_EXTENSIONS: Optional[Set[str]] = None
# --- END NEW ---

FALLBACK_SHOW_SUBMODULES: bool = False
DEFAULT_MAX_LEVEL: Optional[int] = None

# --- NEW: Gitignore Fallback ---
# Mặc định là 'True' (luôn tôn trọng .gitignore nếu có)
FALLBACK_USE_GITIGNORE: bool = True
# --- END NEW ---

# --- REMOVED: Argparse Defaults ---
# (Toàn bộ section 2 đã bị xóa)
# --- END REMOVED ---

# --- 3. Config File Names ---
# --- MODIFIED: Chuyển sang .toml ---
CONFIG_FILENAME: str = ".tree.toml"
PROJECT_CONFIG_FILENAME: str = ".project.toml"
# --- END MODIFIED ---
CONFIG_SECTION_NAME: str = "tree"