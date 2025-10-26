# Path: scripts/internal/bootstrap/bootstrap_filler.py

"""
Template Filling logic for the Bootstrap module.
(Loads templates and formats them with code snippets)
"""

from typing import Dict, Any

from .bootstrap_helpers import (
    load_template,
    # --- NEW: Import helpers dùng chung ---
    build_path_expands,
    build_args_pass_to_core
    # --- END NEW ---
)
from .bootstrap_builder import (
    build_config_constants, build_config_all_list, build_config_imports,
    build_typer_app_code, 
    # --- MODIFIED: Import các hàm builder riêng của Typer ---
    build_typer_path_expands, 
    build_typer_args_pass_to_core, 
    # --- END MODIFIED ---
    build_typer_main_signature
)
# --- NEW: Import Argparse builder ---
from .bootstrap_argparse_builder import (
    build_argparse_arguments
)
# --- END NEW ---


__all__ = [
    "generate_bin_wrapper", "generate_script_entrypoint", 
    "generate_module_file", "generate_module_init_file", "generate_doc_file"
]


def generate_bin_wrapper(config: Dict[str, Any]) -> str:
    # (Hàm này giữ nguyên)
    template = load_template("bin_wrapper.zsh.template")
    return template.format(
        tool_name=config['meta']['tool_name'],
        script_file=config['meta']['script_file']
    )

def generate_script_entrypoint(config: Dict[str, Any]) -> str:
    """Tạo nội dung cho file entrypoint Python trong /scripts/"""
    
    # --- MODIFIED: Đọc config từ cấp [cli] (Sửa lỗi của tôi) ---
    cli_config = config.get('cli', {})
    cli_help_config = cli_config.get('help', {})
    # Đọc 'interface' từ cấp [cli]
    interface_type = cli_config.get('interface', 'typer')
    # --- END MODIFIED ---
    
    # Imports config (dùng chung cho cả hai)
    config_imports_code = build_config_imports(config['module_name'], config)
    
    if interface_type == 'argparse':
        # --- 1. LOGIC CHO ARGPARSE ---
        template = load_template("script_entrypoint_argparse.py.template")
        
        # Build snippets
        argparse_args_code = build_argparse_arguments(config)
        
        # (Gọi các hàm dùng chung từ helpers.py)
        path_expands_code = build_path_expands(config)
        args_pass_code = build_args_pass_to_core(config)
        
        # Format
        return template.format(
            script_file=config['meta']['script_file'],
            logger_name=config['meta']['logger_name'],
            module_name=config['module_name'],
            config_imports=config_imports_code,
            
            # Placeholders của Argparse (Đọc từ cli_help_config)
            cli_description=cli_help_config.get('description', f"Mô tả cho {config['meta']['tool_name']}."),
            cli_epilog=cli_help_config.get('epilog', ""),
            argparse_arguments=argparse_args_code,
            argparse_path_expands=path_expands_code,
            argparse_args_pass_to_core=args_pass_code
        )
        
    else:
        # --- 2. LOGIC CHO TYPER (Mặc định) ---
        template = load_template("script_entrypoint.py.template")
        
        # Build snippets (Dùng các hàm riêng của Typer)
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
    # --- END NEW ---


def generate_module_file(config: Dict[str, Any], file_type: str) -> str:
    """Tạo nội dung cho các file _config, _core, _executor, _loader"""
    template_name_map = {
        "config": "module_config.py.template",
        "core": "module_core.py.template",
        "executor": "module_executor.py.template",
        "loader": "module_loader.py.template",
    }
    template_name = template_name_map[file_type]
    template = load_template(template_name)
    
    # --- MODIFIED: Hoàn tác, dùng 'module_name' (thay vì python_module_name) ---
    format_dict = {"module_name": config['module_name']} # <--- Hoàn tác
    # --- END MODIFIED ---
    
    if file_type == "config":
        config_constants_code = build_config_constants(config)
        config_all_code = build_config_all_list(config)
        format_dict["config_constants"] = config_constants_code
        format_dict["config_all_constants"] = config_all_code
    
    return template.format(**format_dict)

def generate_module_init_file(config: Dict[str, Any]) -> str:
    """Tạo file gateway __init__.py."""
    template = load_template("module_init.py.template")
    # --- MODIFIED: Hoàn tác, dùng 'module_name' (thay vì python_module_name) ---
    return template.format(module_name=config['module_name']) # <--- Hoàn tác
    # --- END MODIFIED ---

def generate_doc_file(config: Dict[str, Any]) -> str:
    # (Hàm này giữ nguyên)
    template = load_template("doc_file.md.template")
    
    return template.format(
        tool_name=config['meta']['tool_name'],
        short_description=config.get('docs', {}).get('short_description', f'Tài liệu cho {config["meta"]["tool_name"]}.')
    )