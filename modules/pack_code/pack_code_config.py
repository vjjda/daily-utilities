# Path: modules/pack_code/pack_code_config.py
from pathlib import Path
from typing import Dict, Any, Optional, List, Final, Set

__all__ = [
    "DEFAULT_START_PATH",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "DEFAULT_CLEAN_EXTENSIONS",
    "DEFAULT_FORMAT_EXTENSIONS",
    "DEFAULT_OUTPUT_DIR",
    "PROJECT_CONFIG_FILENAME",
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
]

DEFAULT_START_PATH: Final[str] = "."
DEFAULT_EXTENSIONS: Final[str] = (
    "md,py,txt,json,xml,yaml,yml,ini,cfg,cfg.py,sh,bash,zsh,toml,template"
)
DEFAULT_IGNORE: Final[str] = ".venv,venv,__pycache__,.git,.hg,.svn,.DS_Store"
DEFAULT_OUTPUT_DIR: Final[str] = "~/Documents/code.context"

DEFAULT_CLEAN_EXTENSIONS: Final[Set[str]] = {"py", "zsh", "sh"}


DEFAULT_FORMAT_EXTENSIONS: Final[Set[str]] = {"py"}

PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".pcode.toml"
CONFIG_SECTION_NAME: Final[str] = "pcode"