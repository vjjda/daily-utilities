# Path: modules/pack_code/pack_code_config.py

"""
Configuration constants for pack_code.
(Single Source of Truth)
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Final

__all__ = [
    "DEFAULT_START_PATH", "DEFAULT_EXTENSIONS", "DEFAULT_IGNORE",
    "DEFAULT_OUTPUT_DIR",
    "PROJECT_CONFIG_FILENAME", "CONFIG_FILENAME", "CONFIG_SECTION_NAME"
]

# --- Default Values (used if no CLI/Config) ---
DEFAULT_START_PATH: Final[str] = '.'
DEFAULT_EXTENSIONS: Final[str] = 'md,py,txt,json,xml,yaml,yml,ini,cfg,cfg.py,sh,bash,zsh' # Comma-separated string
DEFAULT_IGNORE: Final[str] = '.venv,venv,__pycache__,.git,.hg,.svn,.DS_Store' # Comma-separated string
DEFAULT_OUTPUT_DIR: Final[str] = "~/Documents/code.context" # Path string, potentially with '~'

# --- Config File Names ---
PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".pcode.toml"
CONFIG_SECTION_NAME: Final[str] = "pcode"