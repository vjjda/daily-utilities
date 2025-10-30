# Path: modules/zsh_wrapper/__init__.pyi
"""Statically declared API for zsh_wrapper"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

DEFAULT_MODE: Any
DEFAULT_VENV: Any
DEFAULT_WRAPPER_ABSOLUTE_PATH: Any
DEFAULT_WRAPPER_RELATIVE_DIR: Any
execute_zsh_wrapper_action: Any
resolve_output_path_interactively: Any
resolve_root_interactively: Any
run_zsh_wrapper: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "DEFAULT_MODE",
    "DEFAULT_VENV",
    "DEFAULT_WRAPPER_ABSOLUTE_PATH",
    "DEFAULT_WRAPPER_RELATIVE_DIR",
    "execute_zsh_wrapper_action",
    "resolve_output_path_interactively",
    "resolve_root_interactively",
    "run_zsh_wrapper",
]