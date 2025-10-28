# Path: modules/bootstrap/bootstrap_builder/bootstrap_argparse_builder.py
"""
Logic tạo các đoạn mã (code snippet) cho giao diện Argparse.
(Module nội bộ, được import bởi bootstrap_builder)
"""

from typing import Dict, Any, List
from pathlib import Path

# Import hàm helper từ module utils cùng cấp
from ..bootstrap_utils import get_cli_args

__all__ = [
    "build_argparse_arguments",
    "build_path_expands",
    "build_args_pass_to_core"
]


def build_argparse_arguments(config: Dict[str, Any]) -> str:
    """
    Tạo các khối code `parser.add_argument(...)` dựa trên cấu hình `[[cli.args]]`
    trong file `.spec.toml`.

    Args:
        config: Dict chứa nội dung đã parse của file `.spec.toml`.

    Returns:
        Chuỗi string chứa các dòng code `parser.add_argument(...)` đã được format.
    """
    code_lines: List[str] = []
    args = get_cli_args(config) # Lấy danh sách args từ config spec

    if not args:
        code_lines.append("    # (Không có đối số CLI nào được định nghĩa trong spec)") #
        return "\n".join(code_lines)

    for arg in args:
        name = arg['name']
        py_type_str = arg.get('type', 'str') # 'str', 'int', 'bool', 'Path'
        help_str = arg.get('help', f"Văn bản trợ giúp cho {name}.") #
        is_argument = arg.get('is_argument', False) # True nếu là positional argument

        arg_params: List[str] = [] # List chứa các dòng tham số cho add_argument

        # 1. Tên (positional hoặc optional)
        if is_argument:
            # Argument dạng positional: "target_dir"
            arg_params.append(f"        \"{name}\",")
        else:
            # Argument dạng optional: "--output", "-o"
            name_flags = [f"\"--{name}\""]
            if 'short' in arg:
                name_flags.insert(0, f"\"{arg['short']}\"")
            arg_params.append(f"        {', '.join(name_flags)},")

        # 2. Loại (type) hoặc Hành động (action)
        if py_type_str == 'bool':
            # Boolean flags dùng action store_true/store_false
            if arg.get('default', False) is True:
                # Nếu default là True, cờ sẽ làm nó thành False
                arg_params.append(f"        action=\"store_false\",")
            else:
                # Nếu default là False (hoặc không có), cờ sẽ làm nó thành True
                arg_params.append(f"        action=\"store_true\",")
        elif py_type_str == 'int':
             arg_params.append(f"        type=int,")
        # elif py_type_str == 'Path':
        #     # Path vẫn nhận vào là string, sẽ xử lý sau
        #     arg_params.append(f"        type=str,")
        else: # Mặc định là string
            arg_params.append(f"        type=str,")

        # 3. Giá trị mặc định (default) và Số lượng (nargs)
        if is_argument:
            # Positional argument
            if 'default' in arg:
                # Nếu có default, nó trở thành tùy chọn (nargs='?')
                arg_params.append(f"        nargs=\"?\",")
                arg_params.append(f"        default={repr(arg['default'])},")
            # else: không cần nargs='1' vì đó là mặc định cho positional
        else:
            # Optional argument
            if py_type_str != 'bool': # Boolean đã xử lý bằng action
                if 'default' in arg:
                    arg_params.append(f"        default={repr(arg['default'])},")
                else:
                    # Nếu không có default, mặc định là None cho optional
                    arg_params.append(f"        default=None,")

        # 4. Văn bản trợ giúp (help)
        arg_params.append(f"        help={repr(help_str)}")

        # 5. Ghép lại thành add_argument call
        code_lines.append(f"    parser.add_argument(")
        code_lines.extend(arg_params)
        code_lines.append(f"    )")

    return "\n".join(code_lines)

def build_path_expands(config: Dict[str, Any]) -> str:
    """
    Tạo code để gọi `Path(...).expanduser()` cho các tham số loại 'Path'
    (phiên bản Argparse).

    Args:
        config: Dict chứa nội dung đã parse của file `.spec.toml`.

    Returns:
        Chuỗi string chứa code xử lý Path.
    """
    code_lines: List[str] = []
    path_args = [arg for arg in get_cli_args(config) if arg.get('type') == 'Path']

    if not path_args:
        code_lines.append("    # (Không có đối số Path nào cần expand)") #
        return "\n".join(code_lines)

    for arg in path_args:
        name = arg['name']
        var_name = f"{name}_path" # Tạo biến mới, ví dụ: target_dir_path

        # `args.name` chứa giá trị string từ CLI
        # Nếu là positional bắt buộc, không cần kiểm tra None
        if arg.get('is_argument') and 'default' not in arg:
             code_lines.append(f"    {var_name} = Path(args.{name}).expanduser()")
        else:
             # Nếu là optional hoặc positional có default, cần kiểm tra args.name có phải None không
             code_lines.append(f"    {var_name} = Path(args.{name}).expanduser() if args.{name} else None")

    return "\n".join(code_lines)

def build_args_pass_to_core(config: Dict[str, Any]) -> str:
    """
    Tạo các dòng `key=value` để truyền các đối số đã xử lý
    vào hàm logic cốt lõi (phiên bản Argparse).

    Args:
        config: Dict chứa nội dung đã parse của file `.spec.toml`.

    Returns:
        Chuỗi string chứa các dòng `key=value,` đã được format.
    """
    code_lines: List[str] = []
    args = get_cli_args(config)

    if not args:
        code_lines.append("        # (Không có đối số CLI nào để truyền)") #
        return "\n".join(code_lines)

    for arg in args:
        name = arg['name']

        if arg.get('type') == 'Path':
            # Đối với Path, truyền biến đã expanduser()
            var_name = f"{name}_path"
            code_lines.append(f"        {name}={var_name},")
        else:
            # Các loại khác, truyền trực tiếp từ `args` namespace
            code_lines.append(f"        {name}=args.{name},")

    return "\n".join(code_lines)