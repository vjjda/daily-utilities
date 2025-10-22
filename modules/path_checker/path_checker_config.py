#!/usr/bin/env python3
# Path: modules/path_checker/path_checker_config.py

"""
Configuration for the Path Checker module.

This file defines which file types are supported and which
commenting rules they use.
"""

from typing import Dict, Any

# --- 1. Định nghĩa các quy tắc (Rules) ---
COMMENT_RULES: Dict[str, Dict[str, Any]] = {
    "hash_line": {
        "type": "line",
        "comment_prefix": "#",
    },
    "slash_line": {
        "type": "line",
        "comment_prefix": "//",
    },
    # --- NEW: Thêm quy tắc block comment ---
    "css_block": {
        "type": "block",
        "comment_prefix": "/*",
        "comment_suffix": "*/",
        "padding": True, # Thêm space: /* Path: ... */
    },
    "md_block": {
        "type": "block",
        "comment_prefix": "<!--",
        "comment_suffix": "-->",
        "padding": True, 
    }
    # --- END NEW ---
}

# --- 2. Ánh xạ Đuôi file (Extensions) tới Quy tắc ---
COMMENT_RULES_BY_EXT: Dict[str, Dict[str, Any]] = {
    # 'hash_line' users
    ".py":   COMMENT_RULES["hash_line"],
    ".zsh":  COMMENT_RULES["hash_line"],
    ".sh":   COMMENT_RULES["hash_line"],
    
    # 'slash_line' users
    ".js":   COMMENT_RULES["slash_line"],
    ".ts":   COMMENT_RULES["slash_line"],
    ".scss": COMMENT_RULES["slash_line"],
    
    # --- NEW: 'block' users ---
    ".css":  COMMENT_RULES["css_block"],
    ".md":   COMMENT_RULES["md_block"],
    # --- END NEW ---
}