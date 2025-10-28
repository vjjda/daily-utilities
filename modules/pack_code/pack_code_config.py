# Path: modules/pack_code/pack_code_config.py

"""
Configuration constants for pack_code.
"""

import os
from pathlib import Path
# (Thêm Type Hint)
from typing import Dict, Any, Optional, List

# --- NEW: __all__ definition ---
__all__ = ["DEFAULT_START_PATH", "DEFAULT_EXTENSIONS", "DEFAULT_IGNORE"] # (Auto-generated)
# --- END NEW ---

# --- Constants generated from tool.spec.toml ---
DEFAULT_START_PATH = '.'
DEFAULT_EXTENSIONS = 'md,py,txt,json,xml,yaml,yml,ini,cfg,cfg.py,sh,bash,zsh'
DEFAULT_IGNORE = '.venv,venv,__pycache__,.git,.hg,.svn,.DS_Store'
# --- End generated constants ---

# (Ví dụ: DEFAULT_OUTPUT_DIR = Path.home() / 'Documents' / 'pack_code_output')