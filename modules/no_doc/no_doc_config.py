# Path: modules/no_doc/no_doc_config.py
"""
Các hằng số cấu hình cho pack_code.
(Nguồn chân lý duy nhất - Single Source of Truth)
"""

from pathlib import Path
# THÊM Dict
from typing import Dict, Any, Optional, List, Final, Set

__all__ = [
    "DEFAULT_START_PATH", "DEFAULT_EXTENSIONS_MAP", "DEFAULT_IGNORE", # ĐỔI TÊN
    "PROJECT_CONFIG_FILENAME", "CONFIG_FILENAME", "CONFIG_SECTION_NAME"
]

# --- Giá trị Mặc định (sử dụng nếu không có CLI/Config) ---
DEFAULT_START_PATH: Final[str] = '.'

# THAY ĐỔI: Ánh xạ đuôi file (key) sang mã định danh ngôn ngữ (value)
# Dùng bởi Analyzer để gọi đúng cleaner.
# Các key cũng là danh sách extension mặc định dùng bởi Merger/Scanner.
DEFAULT_EXTENSIONS_MAP: Final[Dict[str, str]] = {
    "py": "python",
    # "js": "javascript", # Ví dụ: Thêm JS nếu có cleaner_js
    # "sh": "shell",      # Ví dụ: Thêm Shell nếu có cleaner_shell
}

# Dùng ignore mặc định của dự án cpath/pcode/tree để đảm bảo tính nhất quán
DEFAULT_IGNORE: Final[Set[str]] = {
    ".venv", "venv", "__pycache__", ".git", ".hg", ".svn",
    "node_modules", "dist", "build", "out", ".DS_Store"
}

# --- Tên File Cấu hình ---
PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".ndoc.toml"
CONFIG_SECTION_NAME: Final[str] = "ndoc"