# Path: modules/bootstrap/bootstrap_core.py

"""
Template Filling logic for the Bootstrap module.
(Loads templates and formats them with code snippets)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

# --- MODIFIED: Import từ _loader và _utils ---
from .bootstrap_loader import load_template
from .bootstrap_utils import get_cli_args
# --- END MODIFIED ---

# --- MODIFIED: Import từ gateway 'bootstrap_builder' mới ---
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
    build_path_expands, # (Hàm chung của argparse)
    build_args_pass_to_core # (Hàm chung của argparse)
)
# --- END MODIFIED ---


__all__ = [
    "generate_bin_wrapper", "generate_script_entrypoint", 
    "generate_module_file", "generate_module_init_file", "generate_doc_file",
    "process_bootstrap_logic" # <-- NEW
]


def generate_bin_wrapper(config: Dict[str, Any]) -> str:
    # (Hàm này giữ nguyên)
    template = load_template("bin_wrapper.zsh.template")
    return template.format(
        tool_name=config['meta']['tool_name'],
        script_file=config['meta']['script_file']
    )

def generate_script_entrypoint(config: Dict[str, Any]) -> str:
    # (Hàm này giữ nguyên, chỉ di chuyển)
    """Tạo nội dung cho file entrypoint Python trong /scripts/"""
    
    cli_config = config.get('cli', {})
    cli_help_config = cli_config.get('help', {})
    interface_type = cli_config.get('interface', 'typer')
    
    config_imports_code = build_config_imports(config['module_name'], config)
    
    if interface_type == 'argparse':
        # --- 1. LOGIC CHO ARGPARSE ---
        template = load_template("script_entrypoint_argparse.py.template")
        
        # Build snippets
        argparse_args_code = build_argparse_arguments(config)
        path_expands_code = build_path_expands(config)
        args_pass_code = build_args_pass_to_core(config)
        
        # Format
        return template.format(
            script_file=config['meta']['script_file'],
            logger_name=config['meta']['logger_name'],
            module_name=config['module_name'],
            config_imports=config_imports_code,
            
            cli_description=cli_help_config.get('description', f"Mô tả cho {config['meta']['tool_name']}."),
            cli_epilog=cli_help_config.get('epilog', ""),
            argparse_arguments=argparse_args_code,
            argparse_path_expands=path_expands_code,
            argparse_args_pass_to_core=args_pass_code
        )
        
    else:
        # --- 2. LOGIC CHO TYPER (Mặc định) ---
        template = load_template("script_entrypoint.py.template")
        
        # Build snippets
        typer_app_code = build_typer_app_code(config)
        typer_main_sig = build_typer_main_signature(config)
        typer_path_expands = build_typer_path_expands(config)
        typer_args_pass = build_typer_args_pass_to_core(config)

        # Format
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
    # (Hàm này giữ nguyên, chỉ di chuyển)
    template_name_map = {
        "config": "module_config.py.template",
        "core": "module_core.py.template",
        "executor": "module_executor.py.template",
        "loader": "module_loader.py.template",
    }
    template_name = template_name_map[file_type]
    template = load_template(template_name)
    
    format_dict = {"module_name": config['module_name']}
    
    if file_type == "config":
        config_constants_code = build_config_constants(config)
        config_all_code = build_config_all_list(config)
        format_dict["config_constants"] = config_constants_code
        format_dict["config_all_constants"] = config_all_code
    
    return template.format(**format_dict)

def generate_module_init_file(config: Dict[str, Any]) -> str:
    # (Hàm này giữ nguyên, chỉ di chuyển)
    template = load_template("module_init.py.template")
    return template.format(module_name=config['module_name'])

def generate_doc_file(config: Dict[str, Any]) -> str:
    # (Hàm này giữ nguyên, chỉ di chuyển)
    template = load_template("doc_file.md.template")
    
    return template.format(
        tool_name=config['meta']['tool_name'],
        short_description=config.get('docs', {}).get('short_description', f'Tài liệu cho {config["meta"]["tool_name"]}.')
    )

# --- NEW: Hàm điều phối logic (chuyển từ bootstrap_tool.py) ---
def process_bootstrap_logic(
    logger: logging.Logger,
    config: Dict[str, Any],
    configured_paths: Dict[str, Path]
) -> Tuple[Dict[str, str], Dict[str, Path], Path]:
    """
    Điều phối việc tạo nội dung, xác thực config và tạo dict đường dẫn.
    (Logic thuần túy)
    """
    
    BIN_DIR = configured_paths["BIN_DIR"]
    SCRIPTS_DIR = configured_paths["SCRIPTS_DIR"]
    MODULES_DIR = configured_paths["MODULES_DIR"]
    DOCS_DIR = configured_paths["DOCS_DIR"]

    # 1. Xác thực config (chuyển từ bootstrap_tool.py)
    try:
        tool_name = config['meta']['tool_name']
        script_file = config['meta']['script_file']
        module_name = config['meta']['module_name']
        config['module_name'] = module_name # Đảm bảo key này tồn tại
        
        logger.debug(f"Tool Name: {tool_name}")
        logger.debug(f"Script File: {script_file}")
        logger.debug(f"Module Name: {module_name}")
        
    except KeyError as e:
        logger.error(f"❌ File spec thiếu key bắt buộc trong [meta]: {e}")
        sys.exit(1)
    
    # Xác định đường dẫn module
    module_path = MODULES_DIR / module_name

    # 2. Tạo nội dung (chuyển từ bootstrap_tool.py)
    try:
        mod_name = config['module_name']
        
        generated_content = {
            "bin": generate_bin_wrapper(config),
            "script": generate_script_entrypoint(config),
            "config": generate_module_file(config, "config"),
            "loader": generate_module_file(config, "loader"), 
            "core": generate_module_file(config, "core"),
            "executor": generate_module_file(config, "executor"),
            "init": generate_module_init_file(config), 
        }
        
        target_paths = {
            "bin": BIN_DIR / tool_name,
            "script": SCRIPTS_DIR / script_file,
            "config": module_path / f"{mod_name}_config.py",
            "loader": module_path / f"{mod_name}_loader.py", 
            "core": module_path / f"{mod_name}_core.py",
            "executor": module_path / f"{mod_name}_executor.py",
            "init": module_path / "__init__.py", 
        }
        
        if config.get('docs', {}).get('enabled', False):
            generated_content["docs"] = generate_doc_file(config)
            target_paths["docs"] = DOCS_DIR / "tools" / f"{tool_name}.md"

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng khi tạo nội dung code: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    return generated_content, target_paths, module_path