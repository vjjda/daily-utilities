# Path: modules/bootstrap/bootstrap_internal/__init__.pyi
"""Statically declared API for bootstrap_internal"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

generate_bin_wrapper: Any
generate_doc_file: Any
generate_module_file: Any
generate_module_init_file: Any
generate_script_entrypoint: Any
get_cli_args: Any
load_bootstrap_config: Any
load_spec_file: Any
load_template: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "generate_bin_wrapper",
    "generate_doc_file",
    "generate_module_file",
    "generate_module_init_file",
    "generate_script_entrypoint",
    "get_cli_args",
    "load_bootstrap_config",
    "load_spec_file",
    "load_template",
]