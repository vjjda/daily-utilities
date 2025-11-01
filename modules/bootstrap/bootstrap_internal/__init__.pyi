# Path: modules/bootstrap/bootstrap_internal/__init__.pyi
"""Statically declared API for bootstrap_internal"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

# Liệt kê TẤT CẢ các hàm đã bị ẩn đi
# (Từ loader)
load_template: Any
load_bootstrap_config: Any
load_spec_file: Any
# (Từ generator)
generate_bin_wrapper: Any
generate_script_entrypoint: Any
generate_module_file: Any
generate_module_init_file: Any
generate_doc_file: Any
# (Từ utils)
get_cli_args: Any
# (Từ config_builder)
build_config_constants: Any
build_config_all_list: Any
build_config_imports: Any
# (Từ typer_builder)
build_typer_app_code: Any
build_typer_path_expands: Any
build_typer_args_pass_to_core: Any
build_typer_main_signature: Any
# (Từ argparse_builder)
build_argparse_arguments: Any
build_path_expands: Any
build_args_pass_to_core: Any

__all__: List[str] = [
    "load_template",
    "load_bootstrap_config",
    "load_spec_file",
    "generate_bin_wrapper",
    "generate_script_entrypoint",
    "generate_module_file",
    "generate_module_init_file",
    "generate_doc_file",
    "get_cli_args",
    "build_config_constants",
    "build_config_all_list",
    "build_config_imports",
    "build_typer_app_code",
    "build_typer_path_expands",
    "build_typer_args_pass_to_core",
    "build_typer_main_signature",
    "build_argparse_arguments",
    "build_path_expands",
    "build_args_pass_to_core",
]