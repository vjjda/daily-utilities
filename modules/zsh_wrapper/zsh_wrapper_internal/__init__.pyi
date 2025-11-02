# Path: modules/zsh_wrapper/zsh_wrapper_internal/__init__.pyi
"""Statically declared API for zsh_wrapper_internal"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

execute_zsh_wrapper_action: Any
find_project_root: Any
generate_wrapper_content: Any
resolve_default_output_path: Any
resolve_output_path_interactively: Any
resolve_root_interactively: Any
resolve_wrapper_inputs: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "execute_zsh_wrapper_action",
    "find_project_root",
    "generate_wrapper_content",
    "resolve_default_output_path",
    "resolve_output_path_interactively",
    "resolve_root_interactively",
    "resolve_wrapper_inputs",
]