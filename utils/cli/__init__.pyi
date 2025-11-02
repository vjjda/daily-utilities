# Path: utils/cli/__init__.pyi
"""Statically declared API for cli"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

handle_config_init_request: Any
handle_project_root_validation: Any
launch_editor: Any
print_grouped_report: Any
prompt_config_overwrite: Any
resolve_input_paths: Any
resolve_reporting_root: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "handle_config_init_request",
    "handle_project_root_validation",
    "launch_editor",
    "print_grouped_report",
    "prompt_config_overwrite",
    "resolve_input_paths",
    "resolve_reporting_root",
]