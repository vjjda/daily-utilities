# Path: modules/forc/forc_config.py
"""
Các hằng số cấu hình cho forc (Format Code).
(Nguồn chân lý duy nhất - Single Source of Truth)
"""

from pathlib import Path
from typing import Any, Optional, List, Final, Set

__all__ = [
    "DEFAULT_START_PATH",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "PROJECT_CONFIG_FILENAME", "CONFIG_FILENAME", "CONFIG_SECTION_NAME"
]

# --- Giá trị Mặc định (sử dụng nếu không có CLI/Config) ---
DEFAULT_START_PATH: Final[str] = '.'

# Chỉ hỗ trợ Python (vì formatter của chúng ta mới chỉ có Black)
DEFAULT_EXTENSIONS: Final[Set[str]] = {"py"}

# Ignore mặc định
DEFAULT_IGNORE: Final[Set[str]] = {
    ".venv", "venv", "__pycache__", ".git", ".hg", ".svn",
    "node_modules", "dist", "build", "out", ".DS_Store"
}

# --- Tên File Cấu hình ---
PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".forc.toml"
CONFIG_SECTION_NAME: Final[str] = "forc"