# Path: modules/zsh_wrapper/zsh_wrapper_config.py
import os
from pathlib import Path
from typing import Dict, Any, Final

__all__ = [
    "DEFAULT_MODE",
    "DEFAULT_VENV",
    "DEFAULT_WRAPPER_RELATIVE_DIR",
    "DEFAULT_WRAPPER_ABSOLUTE_PATH",
]


DEFAULT_MODE: Final[str] = "relative"
DEFAULT_VENV: Final[str] = ".venv"


DEFAULT_WRAPPER_RELATIVE_DIR: Final[str] = "bin"


DEFAULT_WRAPPER_ABSOLUTE_PATH: Final[Path] = Path.home() / "bin"
