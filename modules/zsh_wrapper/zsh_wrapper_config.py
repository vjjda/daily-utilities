# Path: modules/zsh_wrapper/zsh_wrapper_config.py

"""
Configuration constants for zsh_wrapper.
"""

import os
from pathlib import Path
from typing import Dict, Any

# --- NEW: __all__ definition ---
__all__ = ["DEFAULT_MODE", "DEFAULT_VENV", "DEFAULT_WRAPPER_DIR"]
# --- END NEW ---

# --- Constants generated from tool.spec.toml ---
DEFAULT_MODE = "relative"
DEFAULT_VENV = ".venv"
# --- End generated constants ---

# --- NEW: Thư mục mặc định cho wrapper ---
DEFAULT_WRAPPER_DIR = "to_run"
# --- END NEW ---

# (Ví dụ: DEFAULT_OUTPUT_DIR = Path.home() / 'Documents' / 'zsh_wrapper_output')