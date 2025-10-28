# Path: modules/bootstrap/bootstrap_core.py
"""
Logic điền template (Template Filling) cho module Bootstrap.
(Logic thuần túy, không I/O ghi)

Chịu trách nhiệm tải các file template và điền vào đó các đoạn code snippet
được tạo bởi các builder.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

# Import các thành phần cần thiết
from .bootstrap_loader import load_template
from .bootstrap_utils import get_cli_args
from .bootstrap_builder import (
    # Config builders
    build_config_constants,
    build_config_all_list,
    build_config_imports,
    # Typer builders
    build_typer_app_code,
    build_typer_path_expands,
    build_typer_args_pass_to_core,
    build_typer_main_signature,
    # Argparse builders
    build_argparse_arguments,
    build_path_expands as build_argparse_path_expands, # Đổi tên để tránh trùng
    build_args_pass_to_core as build_argparse_args_pass_to_core # Đổi tên
)

__all__ = [
    "generate_bin_wrapper", "generate_script_entrypoint",
    "generate_module_file", "generate_module_init_file", "generate_doc_file",
    "process_bootstrap_logic" # Hàm điều phối chính
]


def generate_bin_wrapper(config: Dict[str, Any]) -> str:
    """Tạo nội dung cho file wrapper Zsh trong thư mục `bin/`."""
    template = load_template("bin_wrapper.zsh.template")
    return template.format(
        tool_name=config['meta']['tool_name'],
        script_file=config['meta']['script_file']
    )

def generate_script_entrypoint(config: Dict[str, Any]) -> str:
    """Tạo nội dung cho file entrypoint Python trong thư mục `scripts/`."""
    cli_config = config.get('cli', {})
    cli_help_config = cli_config.get('help', {})
    interface_type = cli_config.get('interface', 'typer') # Mặc định là Typer

    # Tạo dòng import hằng số config
    config_imports_code = build_config_imports(config['module_name'], config)

    if interface_type == 'argparse':
        # --- Logic cho ARGPARSE ---
        template = load_template("script_entrypoint_argparse.py.template")

        # Tạo các code snippet
        argparse_args_code = build_argparse_arguments(config)
        path_expands_code = build_argparse_path_expands(config) # Dùng hàm builder argparse
        args_pass_code = build_argparse_args_pass_to_core(config) # Dùng hàm builder argparse

        # Điền vào template
        return template.format(
            script_file=config['meta']['script_file'],
            logger_name=config['meta']['logger_name'],
            module_name=config['module_name'],
            config_imports=config_imports_code,
            cli_description=cli_help_config.get('description', f"Mô tả cho {config['meta']['tool_name']}."), #
            cli_epilog=cli_help_config.get('epilog', ""),
            argparse_arguments=argparse_args_code,
            argparse_path_expands=path_expands_code,
            argparse_args_pass_to_core=args_pass_code
        )

    else:
        # --- Logic cho TYPER (mặc định) ---
        template = load_template("script_entrypoint.py.template")

        # Tạo các code snippet
        typer_app_code = build_typer_app_code(config)
        typer_main_sig = build_typer_main_signature(config)
        typer_path_expands = build_typer_path_expands(config)
        typer_args_pass = build_typer_args_pass_to_core(config)

        # Điền vào template
        return template.format(
            script_file=config['meta']['script_file'],
            logger_name=config['meta']['logger_name'],
            module_name=config['module_name'],
            config_imports=config_imports_code,
            typer_app_code=typer_app_code,
            typer_main_function_signature=typer_main_sig,
            typer_path_expands=typer_path_expands,
            typer_args_pass_to_core=typer_args_pass
        )


def generate_module_file(config: Dict[str, Any], file_type: str) -> str:
    """
    Tạo nội dung cho các file bên trong module (`*_config.py`, `*_core.py`, etc.).

    Args:
        config: Dict config spec.
        file_type: Loại file cần tạo ('config', 'core', 'executor', 'loader').

    Returns:
        Nội dung file đã được điền.
    """
    template_name_map = {
        "config": "module_config.py.template",
        "core": "module_core.py.template",
        "executor": "module_executor.py.template",
        "loader": "module_loader.py.template",
    }
    template_name = template_name_map[file_type]
    template = load_template(template_name)

    format_dict = {"module_name": config['module_name']}

    # Điền thêm thông tin cho file config
    if file_type == "config":
        config_constants_code = build_config_constants(config)
        config_all_code = build_config_all_list(config)
        format_dict["config_constants"] = config_constants_code
        format_dict["config_all_constants"] = config_all_code

    return template.format(**format_dict)

def generate_module_init_file(config: Dict[str, Any]) -> str:
    """Tạo nội dung cho file `__init__.py` của module."""
    template = load_template("module_init.py.template")
    return template.format(module_name=config['module_name'])

def generate_doc_file(config: Dict[str, Any]) -> str:
    """Tạo nội dung ban đầu cho file tài liệu Markdown của tool."""
    template = load_template("doc_file.md.template")

    return template.format(
        tool_name=config['meta']['tool_name'],
        short_description=config.get('docs', {}).get('short_description', f'Tài liệu cho {config["meta"]["tool_name"]}.') #
    )

def process_bootstrap_logic(
    logger: logging.Logger,
    config: Dict[str, Any],
    configured_paths: Dict[str, Path]
) -> Tuple[Dict[str, str], Dict[str, Path], Path]:
    """
    Hàm điều phối logic chính (Orchestrator).
    Thực hiện xác thực config, tạo nội dung các file, và xác định đường dẫn đích.
    (Logic thuần túy)

    Args:
        logger: Logger.
        config: Dict config spec đã load.
        configured_paths: Dict chứa các đường dẫn thư mục chính (BIN_DIR, SCRIPTS_DIR,...).

    Returns:
        Tuple chứa:
            - generated_content (Dict[str, str]): Ánh xạ loại file ('bin', 'script', ...) -> nội dung.
            - target_paths (Dict[str, Path]): Ánh xạ loại file -> đường dẫn đích tuyệt đối.
            - module_path (Path): Đường dẫn tuyệt đối đến thư mục module mới.

    Raises:
        SystemExit: Nếu config thiếu key bắt buộc trong [meta].
        Exception: Nếu có lỗi nghiêm trọng khi tạo nội dung code.
    """

    BIN_DIR = configured_paths["BIN_DIR"]
    SCRIPTS_DIR = configured_paths["SCRIPTS_DIR"]
    MODULES_DIR = configured_paths["MODULES_DIR"]
    DOCS_DIR = configured_paths["DOCS_DIR"]

    # 1. Xác thực config [meta]
    try:
        tool_name = config['meta']['tool_name']
        script_file = config['meta']['script_file']
        module_name = config['meta']['module_name']
        # Đảm bảo key 'module_name' tồn tại ở cấp gốc config để các hàm khác sử dụng
        config['module_name'] = module_name
        # Thêm logger_name vào meta nếu chưa có
        if 'logger_name' not in config['meta']:
             config['meta']['logger_name'] = tool_name.capitalize() # Ví dụ: MyTool

        logger.debug(f"Tên Tool: {tool_name}") #
        logger.debug(f"File Script: {script_file}") #
        logger.debug(f"Tên Module: {module_name}") #
        logger.debug(f"Tên Logger: {config['meta']['logger_name']}") #

    except KeyError as e:
        logger.error(f"❌ File spec thiếu key bắt buộc trong [meta]: {e}") #
        sys.exit(1)

    # Xác định đường dẫn thư mục module
    module_path = MODULES_DIR / module_name

    # 2. Tạo nội dung các file
    try:
        mod_name = config['module_name'] # Lấy lại module_name từ config

        generated_content = {
            "bin": generate_bin_wrapper(config),
            "script": generate_script_entrypoint(config),
            "config": generate_module_file(config, "config"),
            "loader": generate_module_file(config, "loader"),
            "core": generate_module_file(config, "core"),
            "executor": generate_module_file(config, "executor"),
            "init": generate_module_init_file(config),
        }

        # Xác định đường dẫn đích cho từng file
        target_paths = {
            "bin": BIN_DIR / tool_name,
            "script": SCRIPTS_DIR / script_file,
            "config": module_path / f"{mod_name}_config.py",
            "loader": module_path / f"{mod_name}_loader.py",
            "core": module_path / f"{mod_name}_core.py",
            "executor": module_path / f"{mod_name}_executor.py",
            "init": module_path / "__init__.py",
        }

        # Thêm file tài liệu nếu được bật trong spec
        if config.get('docs', {}).get('enabled', False):
            generated_content["docs"] = generate_doc_file(config)
            target_paths["docs"] = DOCS_DIR / "tools" / f"{tool_name}.md"

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng khi tạo nội dung code: {e}") #
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    return generated_content, target_paths, module_path