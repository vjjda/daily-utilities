# Path: scripts/internal/bootstrap/bootstrap_builder.py

"""
Code snippet generation logic for the Bootstrap module.
(Builds config strings, Typer signatures, etc.)
"""

from typing import Dict, Any, List

from .bootstrap_config import TYPE_HINT_MAP
# --- MODIFIED: Import helper `get_cli_args` ---
from .bootstrap_helpers import get_cli_args
# --- END MODIFIED ---

__all__ = [
    "build_config_constants", "build_config_all_list", "build_config_imports",
    "build_typer_app_code", 
    # --- REMOVED: build_typer_path_expands, build_typer_args_pass_to_core ---
    "build_typer_main_signature",
    # --- NEW: Các hàm (giống tên) này là của Typer ---
    "build_typer_path_expands", "build_typer_args_pass_to_core"
]


def build_config_constants(config: Dict[str, Any]) -> str:
    """Tạo mã Python cho các hằng số DEFAULT_..."""
    code_lines: List[str] = []
    
    # --- MODIFIED: Áp dụng filter mới: phải có default VÀ type KHÔNG phải là bool ---
    default_args = [
        arg for arg in get_cli_args(config) 
        if 'default' in arg and arg.get('type') != 'bool'
    ]
    # --- END MODIFIED ---
    
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
    # --- MODIFIED: Áp dụng filter mới: phải có default VÀ type KHÔNG phải là bool ---
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

# --- MODIFIED: Hoàn tác lại logic cũ ---
def build_config_imports(module_name: str, config: Dict[str, Any]) -> str:
    # ... (Hàm này không đổi) ...
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

def build_typer_app_code(config: Dict[str, Any]) -> str:
    """Tạo code khởi tạo Typer App."""
    # --- MODIFIED: Tách biệt cli_config và help_config ---
    cli_config = config.get('cli', {})
    help_config = cli_config.get('help', {})
    # --- END MODIFIED ---
    
    desc = help_config.get('description', f"Mô tả cho {config['meta']['tool_name']}.")
    epilog = help_config.get('epilog', "")
    
    # --- MODIFIED: Đọc từ cli_config (cấp [cli]) ---
    # Đọc giá trị từ spec, mặc định là False (nếu không có trong file spec)
    allow_interspersed = cli_config.get('allow_interspersed_args', False)
    allow_interspersed_str = str(allow_interspersed) # Chuyển True/False thành chuỗi "True"/"False"
    # --- END MODIFIED ---
    
    code_lines = [
        f"app = typer.Typer(",
        f"    help=\"{desc}\",",
        f"    epilog=\"{epilog}\",",
        f"    add_completion=False,",
        f"    context_settings={{",
        f"        'help_option_names': ['--help', '-h'],",
        f"        'allow_interspersed_args': {allow_interspersed_str}" , # <--- LOGIC NÀY GIỜ ĐÃ ĐÚNG
        f"    }}",
        f")"
    ]
    return "\n".join(code_lines)

# --- MODIFIED: Hàm riêng của Typer ---
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
             # Tham số Path bắt buộc
             code_lines.append(f"    {var_name} = {name}.expanduser()")
        else:
             # Tham số Path tùy chọn (có default hoặc là --option)
             code_lines.append(f"    {var_name} = {name}.expanduser() if {name} else None")
            
    return "\n".join(code_lines)
# --- END MODIFIED ---

# --- MODIFIED: Hàm riêng của Typer ---
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
# --- END MODIFIED ---


def build_typer_main_signature(config: Dict[str, Any]) -> str:
    # (Hàm này giữ nguyên, không thay đổi)
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
            # --- MODIFIED LOGIC START ---
            if py_type == 'bool':
                # Cờ boolean dùng giá trị mặc định trực tiếp (VD: False)
                # str().capitalize() đảm bảo True/False được viết hoa chữ cái đầu
                default_const = str(arg['default']).capitalize() 
            else:
                # Các kiểu dữ liệu khác dùng hằng số đã được import
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