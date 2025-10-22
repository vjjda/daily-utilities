#!/usr/bin/env python3
# Path: modules/path_checker/path_checker_config.py

"""
Configuration for the Path Checker module.

This file defines which file types are supported and which
commenting rules they use.
"""

from typing import Dict, Any

# --- 1. Định nghĩa các quy tắc (Rules) ---
# Đây là "khuôn mẫu" cho các loại comment.
# Sắp tới chúng ta sẽ thêm 'block_css' ở đây.
COMMENT_RULES: Dict[str, Dict[str, Any]] = {
    "hash_line": {
        "type": "line",
        "comment_prefix": "#",
    },
    "slash_line": {
        "type": "line",
        "comment_prefix": "//",
    }
}

# --- 2. Ánh xạ Đuôi file (Extensions) tới Quy tắc ---
# Đây là "bảng tra cứu" mà core logic sẽ sử dụng.
COMMENT_RULES_BY_EXT: Dict[str, Dict[str, Any]] = {
    # 'hash_line' users
    ".py":   COMMENT_RULES["hash_line"],
    ".zsh":  COMMENT_RULES["hash_line"],
    ".sh":   COMMENT_RULES["hash_line"],
    
    # 'slash_line' users
    ".js":   COMMENT_RULES["slash_line"],
    ".ts":   COMMENT_RULES["slash_line"],
    ".scss": COMMENT_RULES["slash_line"],
    
    # Sẽ sớm thêm .css tại đây
}