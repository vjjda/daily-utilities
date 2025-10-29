# Path: modules/no_doc/no_doc_config.py
"""
Các hằng số cấu hình cho ndoc.
(Nguồn chân lý duy nhất - Single Source of Truth)
"""

from pathlib import Path
# SỬA: Bỏ Dict
from typing import Any, Optional, List, Final, Set

__all__ = [
    "DEFAULT_START_PATH",
    "DEFAULT_EXTENSIONS",
    # "EXTENSIONS_LANG_MAP", # <-- XÓA DÒNG NÀY
    "DEFAULT_IGNORE",
    "PROJECT_CONFIG_FILENAME", "CONFIG_FILENAME", "CONFIG_SECTION_NAME"
]

# --- Giá trị Mặc định (sử dụng nếu không có CLI/Config) ---
DEFAULT_START_PATH: Final[str] = '.'
DEFAULT_EXTENSIONS: Final[Set[str]] = {"py"}

# XÓA: Không cần định nghĩa EXTENSIONS_LANG_MAP ở đây nữa
# EXTENSIONS_LANG_MAP: Final[Dict[str, str]] = { ... }

# Ignore mặc định
DEFAULT_IGNORE: Final[Set[str]] = {
    ".venv", "venv", "__pycache__", ".git", ".hg", ".svn",
    "node_modules", "dist", "build", "out", ".DS_Store"
}

# --- Tên File Cấu hình ---
PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".ndoc.toml"
CONFIG_SECTION_NAME: Final[str] = "ndoc"