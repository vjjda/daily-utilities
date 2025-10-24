# Path: scripts/internal/bootstrap/bootstrap_filler.py

"""
Template Filling logic for the Bootstrap module.
(Loads templates and formats them with code snippets)
"""

from typing import Dict, Any

from .bootstrap_helpers import load_template
from .bootstrap_builder import (
    build_config_constants, build_config_all_list, build_config_imports,
    build_typer_app_code, build_typer_path_expands, 
    build_typer_args_pass_to_core, build_typer_main_signature
)

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
    template = load_template("script_entrypoint.py.template")
    
    # --- MODIFIED: Hoàn tác logic, truyền module_name (thay vì config) ---
    config_imports_code = build_config_imports(config['module_name'], config)
    # --- END MODIFIED ---
    
    typer_app_code = build_typer_app_code(config)
    typer_main_sig = build_typer_main_signature(config)
    typer_path_expands = build_typer_path_expands(config)
    typer_args_pass = build_typer_args_pass_to_core(config)

    # --- MODIFIED: Hoàn tác, dùng 'module_name' (thay vì python_module_name) ---
    return template.format(
        script_file=config['meta']['script_file'],
        logger_name=config['meta']['logger_name'],
        module_name=config['module_name'], # <--- Hoàn tác
        config_imports=config_imports_code,
        typer_app_code=typer_app_code,
        typer_main_function_signature=typer_main_sig,
        typer_path_expands=typer_path_expands,
        typer_args_pass_to_core=typer_args_pass
    )
    # --- END MODIFIED ---

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