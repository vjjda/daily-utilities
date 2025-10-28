# Path: modules/zsh_wrapper/zsh_wrapper_config.py

"""
Configuration constants for zsh_wrapper (zrap).
"""

import os
from pathlib import Path
from typing import Dict, Any, Final

__all__ = [
    "DEFAULT_MODE", "DEFAULT_VENV", 
    "DEFAULT_WRAPPER_RELATIVE_DIR", "DEFAULT_WRAPPER_ABSOLUTE_PATH"
]

# --- Cấu hình Mặc định ---
DEFAULT_MODE: Final[str] = "relative"
DEFAULT_VENV: Final[str] = ".venv"

# Thư mục mặc định cho mode 'relative' (so với PROJECT_ROOT)
DEFAULT_WRAPPER_RELATIVE_DIR: Final[str] = "bin"

# Đường dẫn tuyệt đối mặc định cho mode 'absolute'
DEFAULT_WRAPPER_ABSOLUTE_PATH: Final[Path] = Path.home() / "bin"