# Path: modules/check_path/check_path_config.py

"""
Configuration constants for the Path Checker (cpath) module.
(Single Source of Truth)
"""

from typing import Dict, Any, Set, Final

__all__ = [
    "DEFAULT_IGNORE",
    "DEFAULT_EXTENSIONS",
    "COMMENT_RULES",
    "COMMENT_RULES_BY_EXT",
    "PROJECT_CONFIG_FILENAME", 
    "CONFIG_SECTION_NAME",
    "CONFIG_FILENAME"
]

# --- 1. Scanning Defaults ---

# Các pattern mặc định luôn bị bỏ qua khi quét
DEFAULT_IGNORE: Final[Set[str]] = {
    ".venv", "venv", "__pycache__", ".git", 
    "node_modules", "dist", "build", "out"
}

# Các đuôi file mặc định sẽ được quét
DEFAULT_EXTENSIONS: Final[Set[str]] = {
    "py", "js", "ts", "css", "scss", "zsh", "sh", 
    "template.toml"
}

# --- 2. Config File Names ---
PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".cpath.toml"
CONFIG_SECTION_NAME: Final[str] = "cpath"


# --- 3. Comment Rule Definitions ---

# Định nghĩa các loại comment
COMMENT_RULES: Final[Dict[str, Dict[str, Any]]] = {
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
        "padding": True, # Thêm khoảng trắng: /* Path: ... */
    },
    "md_block": {
        "type": "block",
        "comment_prefix": "<!--",
        "comment_suffix": "-->",
        "padding": True
    }
}

# Ánh xạ Đuôi file (Extension) tới Quy tắc (Rule)
COMMENT_RULES_BY_EXT: Final[Dict[str, Dict[str, Any]]] = {
    ".py":   COMMENT_RULES["hash_line"],
    ".zsh":  COMMENT_RULES["hash_line"],
    ".sh":   COMMENT_RULES["hash_line"],
    ".js":   COMMENT_RULES["slash_line"],
    ".ts":   COMMENT_RULES["slash_line"],
    ".scss": COMMENT_RULES["slash_line"],
    ".css":  COMMENT_RULES["css_block"],
    ".md":   COMMENT_RULES["md_block"],
    ".py.template": COMMENT_RULES["hash_line"],
    ".template.toml": COMMENT_RULES["hash_line"],
}