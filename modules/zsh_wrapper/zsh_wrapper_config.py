#!/usr/bin/env python3
# Path: modules/zsh_wrapper/zsh_wrapper_config.py

"""
Configuration constants for zsh_wrapper.
"""

import os
from pathlib import Path
from typing import Dict, Any

# --- Constants generated from tool.spec.toml ---
DEFAULT_MODE = "relative"
DEFAULT_VENV = ".venv"
# --- End generated constants ---

# --- NEW: Thư mục mặc định cho wrapper ---
DEFAULT_WRAPPER_DIR = "to_run"
# --- END NEW ---

# (Ví dụ: DEFAULT_OUTPUT_DIR = Path.home() / 'Documents' / 'zsh_wrapper_output')