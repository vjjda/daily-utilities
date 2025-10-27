# Path: modules/bootstrap/bootstrap_builder/bootstrap_argparse_builder.py

"""
Code snippet generation logic for the Bootstrap module.
(Builds code strings for Argparse)
"""

# --- MODIFIED: Thêm Path và List ---
from typing import Dict, Any, List
from pathlib import Path
# --- END MODIFIED ---

# --- MODIFIED: Import từ ..bootstrap_utils ---
from ..bootstrap_utils import get_cli_args
# --- END MODIFIED ---

# --- MODIFIED: Cập nhật __all__ ---
__all__ = [
    "build_argparse_arguments",
    "build_path_expands", 
    "build_args_pass_to_core"
]
# --- END MODIFIED ---


def build_argparse_arguments(config: Dict[str, Any]) -> str:
    """
    Tạo các khối code parser.add_argument(...)
    dựa trên file .spec.toml.
    """
    code_lines: List[str] = []
    args = get_cli_args(config)
    
    if not args:
        # --- FIX: Thêm 4-space indent ---
        code_lines.append("    # (No CLI arguments defined in spec)")

    for arg in args:
        name = arg['name']
        py_type_str = arg.get('type', 'str')
        help_str = arg.get('help', f"Help text for {name}.")
        
        arg_params = []
        
        # 1. Name(s)
        if arg.get('is_argument', False):
            # --- FIX: Thêm 4-space indent (total 8) ---
            arg_params.append(f"        \"{name}\",")
        else:
            name_flags = [f"\"--{name}\""]
            if 'short' in arg:
                name_flags.insert(0, f"\"{arg['short']}\"")
            # --- FIX: Thêm 4-space indent (total 8) ---
            arg_params.append(f"        {', '.join(name_flags)},")

        # 2. Type / Action
        if py_type_str == 'bool':
            if arg.get('default', False) is True:
                # --- FIX: Thêm 4-space indent (total 8) ---
                arg_params.append(f"        action=\"store_false\",")
            else:
                # --- FIX: Thêm 4-space indent (total 8) ---
                arg_params.append(f"        action=\"store_true\",")
        else:
            arg_type = "int" if py_type_str == "int" else "str"
            # --- FIX: Thêm 4-space indent (total 8) ---
            arg_params.append(f"        type={arg_type},")

        # 3. Default / Nargs
        if arg.get('is_argument', False):
            if 'default' in arg:
                # --- FIX: Thêm 4-space indent (total 8) ---
                arg_params.append(f"        nargs=\"?\",")
                arg_params.append(f"        default={repr(arg['default'])},")
        else:
            if py_type_str != 'bool':
                if 'default' in arg:
                    # --- FIX: Thêm 4-space indent (total 8) ---
                    arg_params.append(f"        default={repr(arg['default'])},")
                else:
                    # --- FIX: Thêm 4-space indent (total 8) ---
                    arg_params.append(f"        default=None,")

        # 4. Help
        # --- FIX: Thêm 4-space indent (total 8) ---
        arg_params.append(f"        help={repr(help_str)}")

        # 5. Gộp lại
        # --- FIX: Thêm 4-space indent ---
        code_lines.append(f"    parser.add_argument(")
        code_lines.extend(arg_params)
        # --- FIX: Thêm 4-space indent ---
        code_lines.append(f"    )")
            
    return "\n".join(code_lines)

# --- NEW: Hàm (Di chuyển từ bootstrap_helpers.py) ---
def build_path_expands(config: Dict[str, Any]) -> str:
    """Tạo code để expanduser() cho các tham số loại Path (phiên bản Argparse)."""
    code_lines: List[str] = []
    path_args = [arg for arg in get_cli_args(config) if arg.get('type') == 'Path']
    if not path_args:
        # --- FIX: Thêm 4-space indent ---
        code_lines.append("    # (No Path arguments to expand)")
        
    for arg in path_args:
        name = arg['name']
        var_name = f"{name}_path" # (VD: target_dir_path)
        
        if arg.get('is_argument') and 'default' not in arg:
             # --- FIX: Thêm 4-space indent ---
             code_lines.append(f"    {var_name} = Path(args.{name}).expanduser()")
        else:
             # --- FIX: Thêm 4-space indent ---
             code_lines.append(f"    {var_name} = Path(args.{name}).expanduser() if args.{name} else None")
            
    return "\n".join(code_lines)
# --- END NEW ---

# --- NEW: Hàm (Di chuyển từ bootstrap_helpers.py) ---
def build_args_pass_to_core(config: Dict[str, Any]) -> str:
    """Tạo các dòng key=value để truyền args vào hàm core logic (phiên bản Argparse)."""
    code_lines: List[str] = []
    args = get_cli_args(config)
    if not args:
        code_lines.append("        # (No CLI args to pass)")
        
    for arg in args:
        name = arg['name']
        
        if arg.get('type') == 'Path':
            # (Indent 8-spaces là chính xác cho vị trí này)
            code_lines.append(f"        {name}={name}_path,")
        else:
            code_lines.append(f"        {name}=args.{name},")
            
    return "\n".join(code_lines)
# --- END NEW ---