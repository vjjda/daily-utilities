# Path: modules/bootstrap/bootstrap_builder/bootstrap_config_builder.py

"""
Code snippet generation logic for the Bootstrap module.
(Builds config strings: constants, __all__, imports)
"""

from typing import Dict, Any, List

# --- MODIFIED: Import từ gateway cha (bootstrap) ---
from ..bootstrap_helpers import get_cli_args
# --- END MODIFIED ---

__all__ = [
    "build_config_constants", "build_config_all_list", "build_config_imports"
]


def build_config_constants(config: Dict[str, Any]) -> str:
    """Tạo mã Python cho các hằng số DEFAULT_..."""
    code_lines: List[str] = []
    
    default_args = [
        arg for arg in get_cli_args(config) 
        if 'default' in arg and arg.get('type') != 'bool'
    ]
    
    if not default_args:
        code_lines.append("# (No default constants defined in tool.spec.toml)")
        
    for arg in default_args:
        name = arg['name']
        const_name = f"DEFAULT_{name.upper()}"
        const_value = repr(arg['default'])
        code_lines.append(f"{const_name} = {const_value}")
            
    return "\n".join(code_lines)

def build_config_all_list(config: Dict[str, Any]) -> str:
    """Tạo chuỗi cho __all__ trong file config."""
    default_args = [
        arg for arg in get_cli_args(config) 
        if 'default' in arg and arg.get('type') != 'bool'
    ]
    if not default_args:
        return "" 
        
    const_names: List[str] = []
    for arg in default_args:
        const_name = f"DEFAULT_{arg['name'].upper()}"
        const_names.append(f'"{const_name}"') 
            
    return ", ".join(const_names)

def build_config_imports(module_name: str, config: Dict[str, Any]) -> str:
    """Tạo code import các hằng số config cho file entrypoint."""
    default_args = [
        arg for arg in get_cli_args(config) 
        if 'default' in arg and arg.get('type') != 'bool'
    ]
    
    if not default_args:
        return "# (No default constants to import)"
        
    const_names: List[str] = []
    for arg in default_args:
        const_name = f"DEFAULT_{arg['name'].upper()}"
        const_names.append(const_name)
        
    import_list = ", ".join(const_names)
    return f"from modules.{module_name}.{module_name}_config import {import_list}"