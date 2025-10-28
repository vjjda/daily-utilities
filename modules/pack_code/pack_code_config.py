# Path: modules/pack_code/pack_code_config.py

"""
Configuration constants for pack_code.
"""

import os # <-- XÓA DÒNG NÀY
from pathlib import Path
# (Thêm Type Hint)
from typing import Dict, Any, Optional, List, Final # <-- MODIFIED: Thêm Final

# --- NEW: __all__ definition ---
__all__ = [
    "DEFAULT_START_PATH", "DEFAULT_EXTENSIONS", "DEFAULT_IGNORE",
    "DEFAULT_OUTPUT_DIR",
    # --- NEW ---
    "PROJECT_CONFIG_FILENAME", "CONFIG_FILENAME", "CONFIG_SECTION_NAME"
    # --- END NEW ---
]
# --- END NEW ---

# --- Constants generated from tool.spec.toml ---
DEFAULT_START_PATH = '.'
DEFAULT_EXTENSIONS = 'md,py,txt,json,xml,yaml,yml,ini,cfg,cfg.py,sh,bash,zsh'

# --- MODIFIED: Hoàn tác về trạng thái gốc (không có /) ---
DEFAULT_IGNORE = '.venv,venv,__pycache__,.git,.hg,.svn,.DS_Store'
# --- END MODIFIED ---

DEFAULT_OUTPUT_DIR: str = "~/Documents/code.context"
# --- KẾT THÚC SỬA ĐỔI ---

# --- NEW: Config File Constants ---
PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".pcode.toml"
CONFIG_SECTION_NAME: Final[str] = "pcode"
# --- END NEW ---