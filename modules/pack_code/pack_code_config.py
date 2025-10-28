# Path: modules/pack_code/pack_code_config.py

"""
Các hằng số cấu hình cho pack_code.
(Nguồn chân lý duy nhất - Single Source of Truth)
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Final

__all__ = [
    "DEFAULT_START_PATH", "DEFAULT_EXTENSIONS", "DEFAULT_IGNORE",
    "DEFAULT_OUTPUT_DIR",
    "PROJECT_CONFIG_FILENAME", "CONFIG_FILENAME", "CONFIG_SECTION_NAME"
]

# --- Giá trị Mặc định (sử dụng nếu không có CLI/Config) ---
DEFAULT_START_PATH: Final[str] = '.'
DEFAULT_EXTENSIONS: Final[str] = 'md,py,txt,json,xml,yaml,yml,ini,cfg,cfg.py,sh,bash,zsh,toml' # Chuỗi ngăn cách bởi dấu phẩy
DEFAULT_IGNORE: Final[str] = '.venv,venv,__pycache__,.git,.hg,.svn,.DS_Store' # Chuỗi ngăn cách bởi dấu phẩy
DEFAULT_OUTPUT_DIR: Final[str] = "~/Documents/code.context" # Chuỗi đường dẫn, có thể chứa '~'

# --- Tên File Cấu hình ---
PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".pcode.toml"
CONFIG_SECTION_NAME: Final[str] = "pcode"