# Path: modules/no_doc/no_doc_config.py
"""
Các hằng số cấu hình cho ndoc.
(Nguồn chân lý duy nhất - Single Source of Truth)
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Final, Set

__all__ = [
    "DEFAULT_START_PATH",
    "DEFAULT_EXTENSIONS", # <-- Đưa trở lại
    "EXTENSIONS_LANG_MAP", # <-- Đổi tên
    "DEFAULT_IGNORE",
    "PROJECT_CONFIG_FILENAME", "CONFIG_FILENAME", "CONFIG_SECTION_NAME"
]

# --- Giá trị Mặc định (sử dụng nếu không có CLI/Config) ---
DEFAULT_START_PATH: Final[str] = '.'

# DANH SÁCH mặc định các đuôi file cần xử lý
DEFAULT_EXTENSIONS: Final[Set[str]] = {"py", "sh", "bash", "zsh"}

# BẢN ĐỒ ÁNH XẠ: Đuôi file (key) sang mã định danh ngôn ngữ (value)
# Dùng bởi Analyzer để gọi đúng cleaner. Bao gồm TẤT CẢ các ánh xạ có thể.
EXTENSIONS_LANG_MAP: Final[Dict[str, str]] = {
    "py": "python",
    "js": "javascript", # Giữ lại ánh xạ dù không có trong DEFAULT_EXTENSIONS
    "sh": "shell",      # Giữ lại ánh xạ
    "bash": "shell",    # Giữ lại ánh xạ
    "zsh": "shell"      # Giữ lại ánh xạ
    }

# Ignore mặc định
DEFAULT_IGNORE: Final[Set[str]] = {
    ".venv", "venv", "__pycache__", ".git", ".hg", ".svn",
    "node_modules", "dist", "build", "out", ".DS_Store"
}

# --- Tên File Cấu hình ---
PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".ndoc.toml"
CONFIG_SECTION_NAME: Final[str] = "ndoc"