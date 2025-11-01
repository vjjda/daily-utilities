# Path: modules/bootstrap/__init__.pyi
"""Statically declared API for bootstrap"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

# --- THAY ĐỔI: Xóa các mục đã chuyển vào internal ---
CONFIG_SECTION_NAME: Any
DEFAULT_BIN_DIR_NAME: Any
DEFAULT_DOCS_DIR_NAME: Any
DEFAULT_MODULES_DIR_NAME: Any
DEFAULT_SCRIPTS_DIR_NAME: Any
TEMPLATE_DIR: Any
TYPE_HINT_MAP: Any
TYPING_IMPORTS: Any
execute_bootstrap_action: Any
# generate_bin_wrapper: Any # Đã chuyển
# generate_doc_file: Any # Đã chuyển
# generate_module_file: Any # Đã chuyển
# generate_module_init_file: Any # Đã chuyển
# generate_script_entrypoint: Any # Đã chuyển
# get_cli_args: Any # Đã chuyển
# load_bootstrap_config: Any # Đã chuyển
# load_spec_file: Any # Đã chuyển
# load_template: Any # Đã chuyển
process_bootstrap_logic: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "CONFIG_SECTION_NAME",
    "DEFAULT_BIN_DIR_NAME",
    "DEFAULT_DOCS_DIR_NAME",
    "DEFAULT_MODULES_DIR_NAME",
    "DEFAULT_SCRIPTS_DIR_NAME",
    "TEMPLATE_DIR",
    "TYPE_HINT_MAP",
    "TYPING_IMPORTS",
    "execute_bootstrap_action",
    # --- THAY ĐỔI: Xóa các mục đã chuyển vào internal ---
    # "generate_bin_wrapper",
    # "generate_doc_file",
    # "generate_module_file",
    # "generate_module_init_file",
    # "generate_script_entrypoint",
    # "get_cli_args",
    # "load_bootstrap_config",
    # "load_spec_file",
    # "load_template",
    "process_bootstrap_logic",
]