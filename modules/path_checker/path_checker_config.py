# Path: modules/path_checker/path_checker_config.py

"""
Configuration for the Path Checker module.

This file defines which file types are supported and which
commenting rules they use.
"""

# --- MODIFIED: Thêm Set ---
from typing import Dict, Any, Set
# --- END MODIFIED ---

# --- NEW: Thêm DEFAULT_IGNORE ---
# Các pattern mặc định luôn bị bỏ qua khi quét
DEFAULT_IGNORE: Set[str] = {
    ".venv", "venv", "__pycache__", ".git", 
    "node_modules", "dist", "build", "out"
}
# --- END NEW ---

# --- NEW: Thêm DEFAULT_EXTENSIONS_STRING ---
DEFAULT_EXTENSIONS_STRING = "py,js,ts,css,scss,zsh,sh"
# --- END NEW ---


# --- 1. Định nghĩa các quy tắc (Rules) ---
COMMENT_RULES: Dict[str, Dict[str, Any]] = {
    # ... (Nội dung không đổi) ...
    "hash_line": {
        "type": "line",
        "comment_prefix": "#",
    },
    "slash_line": {
        "type": "line",
        "comment_prefix": "//",
    },
    "css_block": {
        "type": "block",
        "comment_prefix": "/*",
        "comment_suffix": "*/",
        "padding": True, 
    },
    "md_block": {
        "type": "block",
        "comment_prefix": "<!--",
        "comment_suffix": "-->",
        "padding": True, 
    }
}

# --- 2. Ánh xạ Đuôi file (Extensions) tới Quy tắc ---
COMMENT_RULES_BY_EXT: Dict[str, Dict[str, Any]] = {
    # ... (Nội dung không đổi) ...
    ".py":   COMMENT_RULES["hash_line"],
    ".zsh":  COMMENT_RULES["hash_line"],
    ".sh":   COMMENT_RULES["hash_line"],
    ".js":   COMMENT_RULES["slash_line"],
    ".ts":   COMMENT_RULES["slash_line"],
    ".scss": COMMENT_RULES["slash_line"],
    ".css":  COMMENT_RULES["css_block"],
    ".md":   COMMENT_RULES["md_block"],
}