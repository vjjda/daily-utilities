# Path: modules/bootstrap/bootstrap_filler.py

"""
Template Filling logic for the Bootstrap module.
(Loads templates and formats them with code snippets)
"""

from typing import Dict, Any

from .bootstrap_helpers import (
    load_template,
    # (Các hàm build_... đã bị xóa khỏi đây)
)

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
    
    cli_config = config.get('cli', {})
    cli_help_config = cli_config.get('help', {})
    interface_type = cli_config.get('interface', 'typer')
    
    config_imports_code = build_config_imports(config['module_name'], config)
    
    if interface_type == 'argparse':
        # --- 1. LOGIC CHO ARGPARSE ---
        template = load_template("script_entrypoint_argparse.py.template")
        
        # Build snippets
        argparse_args_code = build_argparse_arguments(config)
        
        # (Các hàm này giờ cũng được import từ .bootstrap_builder)
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
        
        # Build snippets (Các hàm này giờ cũng được import từ .bootstrap_builder)
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
    # (Hàm này giữ nguyên)
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
    # (Hàm này giữ nguyên)
    template = load_template("module_init.py.template")
    return template.format(module_name=config['module_name'])

def generate_doc_file(config: Dict[str, Any]) -> str:
    # (Hàm này giữ nguyên)
    template = load_template("doc_file.md.template")
    
    return template.format(
        tool_name=config['meta']['tool_name'],
        short_description=config.get('docs', {}).get('short_description', f'Tài liệu cho {config["meta"]["tool_name"]}.')
    )