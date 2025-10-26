# Path: scripts/internal/bootstrap/bootstrap_builder/bootstrap_typer_builder.py

"""
Code snippet generation logic for the Bootstrap module.
(Builds code strings for Typer)
"""

from typing import Dict, Any, List

# --- MODIFIED: Import từ gateway cha (bootstrap) ---
from ..bootstrap_config import TYPE_HINT_MAP
from ..bootstrap_helpers import get_cli_args
# --- END MODIFIED ---

__all__ = [
    "build_typer_app_code", 
    "build_typer_path_expands", 
    "build_typer_args_pass_to_core",
    "build_typer_main_signature"
]

def build_typer_app_code(config: Dict[str, Any]) -> str:
    """Tạo code khởi tạo Typer App."""
    cli_config = config.get('cli', {})
    help_config = cli_config.get('help', {})
    
    desc = help_config.get('description', f"Mô tả cho {config['meta']['tool_name']}.")
    epilog = help_config.get('epilog', "")
    
    allow_interspersed = cli_config.get('allow_interspersed_args', False)
    allow_interspersed_str = str(allow_interspersed)
    
    code_lines = [
        f"app = typer.Typer(",
        f"    help=\"{desc}\",",
        f"    epilog=\"{epilog}\",",
        f"    add_completion=False,",
        f"    context_settings={{",
        f"        'help_option_names': ['--help', '-h'],",
        f"        'allow_interspersed_args': {allow_interspersed_str}",
        f"    }}",
        f")"
    ]
    return "\n".join(code_lines)

def build_typer_path_expands(config: Dict[str, Any]) -> str:
    """Tạo code expand Path cho Typer (dùng tên biến gốc)."""
    code_lines: List[str] = []
    path_args = [arg for arg in get_cli_args(config) if arg.get('type') == 'Path']
    if not path_args:
        code_lines.append("    # (No Path arguments to expand)")
        
    for arg in path_args:
        name = arg['name']
        var_name = f"{name}_expanded" # (VD: target_dir_expanded)
        
        if arg.get('is_argument') and 'default' not in arg:
             code_lines.append(f"    {var_name} = {name}.expanduser()")
        else:
             code_lines.append(f"    {var_name} = {name}.expanduser() if {name} else None")
            
    return "\n".join(code_lines)

def build_typer_args_pass_to_core(config: Dict[str, Any]) -> str:
    """Tạo code truyền args cho Typer (dùng tên biến gốc/expanded)."""
    code_lines: List[str] = []
    args = get_cli_args(config)
    if not args:
        code_lines.append("        # (No CLI args to pass)")
        
    for arg in args:
        name = arg['name']
        if arg.get('type') == 'Path':
            code_lines.append(f"        {name}={name}_expanded,")
        else:
            code_lines.append(f"        {name}={name},")
            
    return "\n".join(code_lines)


def build_typer_main_signature(config: Dict[str, Any]) -> str:
    """Tạo chữ ký hàm main() cho Typer."""
    code_lines: List[str] = [
        f"def main(",
        f"    ctx: typer.Context,"
    ]
    
    args = get_cli_args(config)
    
    for arg in args:
        name = arg['name']
        py_type = TYPE_HINT_MAP.get(arg['type'], 'str')
        help_str = arg.get('help', f"The {name} argument.")
        
        default_const = ""
        type_hint = py_type 

        if 'default' in arg:
            if py_type == 'bool':
                default_const = str(arg['default']).capitalize() 
            else:
                default_const = f"DEFAULT_{name.upper()}"
        else:
            if py_type == 'bool':
                default_const = "False"
            else:
                if arg.get('is_argument', False):
                    default_const = "..." 
                else:
                    default_const = "None" 
                    type_hint = f"Optional[{type_hint}]"
        
        if arg.get('is_argument', False):
            code_lines.append(f"    {name}: {type_hint} = typer.Argument(")
            code_lines.append(f"        {default_const},")
            code_lines.append(f"        help=\"{help_str}\"")
            code_lines.append(f"    ),")
        else:
            code_lines.append(f"    {name}: {type_hint} = typer.Option(")
            code_lines.append(f"        {default_const},")
            
            if 'short' in arg:
                code_lines.append(f"        \"{arg['short']}\",")
                
            code_lines.append(f"        \"--{name}\",")
            code_lines.append(f"        help=\"{help_str}\"")
            code_lines.append(f"    ),")

    code_lines.append(f"):")
    return "\n".join(code_lines)