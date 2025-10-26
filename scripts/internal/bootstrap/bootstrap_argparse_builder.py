# Path: scripts/internal/bootstrap/bootstrap_argparse_builder.py

"""
Code snippet generation logic for the Bootstrap module.
(Builds code strings for Argparse)
"""

from typing import Dict, Any, List

# Import helpers
from .bootstrap_helpers import get_cli_args

__all__ = [
    "build_argparse_arguments"
]


def build_argparse_arguments(config: Dict[str, Any]) -> str:
    """
    Tạo các khối code parser.add_argument(...)
    dựa trên file .spec.toml.
    """
    code_lines: List[str] = []
    args = get_cli_args(config)
    
    if not args:
        code_lines.append("    # (No CLI arguments defined in spec)")

    for arg in args:
        name = arg['name']
        py_type_str = arg.get('type', 'str')
        help_str = arg.get('help', f"Help text for {name}.")
        
        arg_params = []
        
        # 1. Name(s): (VD: "target_dir" hoặc "-f", "--fix")
        if arg.get('is_argument', False):
            arg_params.append(f"        \"{name}\",")
        else:
            name_flags = [f"\"--{name}\""]
            if 'short' in arg:
                name_flags.insert(0, f"\"{arg['short']}\",")
            arg_params.append(f"        {', '.join(name_flags)},")

        # 2. Type / Action
        if py_type_str == 'bool':
            # Nếu default=True, dùng store_false. Ngược lại (kể cả ko có default), dùng store_true
            if arg.get('default', False) is True:
                arg_params.append(f"        action=\"store_false\",")
            else:
                arg_params.append(f"        action=\"store_true\",")
        else:
            # Ánh xạ 'Path' -> 'str', 'int' -> 'int'
            # (Template sẽ import Path và hàm main sẽ convert str -> Path)
            arg_type = "int" if py_type_str == "int" else "str"
            arg_params.append(f"        type={arg_type},")

        # 3. Default / Nargs (cho positionals)
        if arg.get('is_argument', False):
            if 'default' in arg:
                # Nếu có default, nó là tùy chọn (nargs=?)
                arg_params.append(f"        nargs=\"?\",")
                arg_params.append(f"        default={repr(arg['default'])},")
            # Nếu không có default, nó là bắt buộc (mặc định)
        else:
            # (Với optional flags, chỉ set default nếu không phải bool)
            if py_type_str != 'bool':
                if 'default' in arg:
                    arg_params.append(f"        default={repr(arg['default'])},")
                else:
                    # (Nếu không có default, nó là Optional[str] hoặc Optional[int])
                    arg_params.append(f"        default=None,")

        # 4. Help (luôn dùng repr để escape dấu ngoặc kép)
        arg_params.append(f"        help={repr(help_str)}")

        # 5. Gộp lại
        code_lines.append(f"    parser.add_argument(")
        code_lines.extend(arg_params)
        code_lines.append(f"    )")
            
    return "\n".join(code_lines)