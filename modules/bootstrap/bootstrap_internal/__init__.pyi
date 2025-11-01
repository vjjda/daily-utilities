# Path: modules/bootstrap/bootstrap_internal/__init__.pyi
"""Statically declared API for bootstrap_internal"""

from typing import Any, List, Optional, Set, Dict, Union, Tuple
from pathlib import Path
import logging
import argparse

# --- From bootstrap_loader ---
load_template: Any
load_bootstrap_config: Any
load_spec_file: Any

# --- From bootstrap_utils ---
get_cli_args: Any

# --- From bootstrap_generator ---
generate_bin_wrapper: Any
generate_script_entrypoint: Any
generate_module_file: Any
generate_module_init_file: Any
generate_doc_file: Any

# --- From bootstrap_orchestrator ---
process_bootstrap_logic: Any


# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    # from bootstrap_loader
    "load_template",
    "load_bootstrap_config",
    "load_spec_file",
    # from bootstrap_utils
    "get_cli_args",
    # from bootstrap_generator
    "generate_bin_wrapper",
    "generate_script_entrypoint",
    "generate_module_file",
    "generate_module_init_file",
    "generate_doc_file",
    # from bootstrap_orchestrator
    "process_bootstrap_logic",
]