# Path: modules/bootstrap/bootstrap_builder/bootstrap_typer_builder.py
"""
Logic tạo các đoạn mã (code snippet) cho giao diện Typer.
(Module nội bộ, được import bởi bootstrap_builder)
"""

from typing import Dict, Any, List, Optional as TypingOptional # Đổi tên để tránh trùng

# Import config và utils từ gateway cha (bootstrap)
from ..bootstrap_config import TYPE_HINT_MAP, TYPING_IMPORTS
from ..bootstrap_utils import get_cli_args

__all__ = [
    "build_typer_app_code",
    "build_typer_path_expands",
    "build_typer_args_pass_to_core",
    "build_typer_main_signature"
]

def build_typer_app_code(config: Dict[str, Any]) -> str:
    """
    Tạo code khởi tạo `typer.Typer(...)`.

    Lấy thông tin `description` và `epilog` từ `[cli.help]` trong spec.

    Args:
        config: Dict chứa nội dung đã parse của file `.spec.toml`.

    Returns:
        Chuỗi string chứa code khởi tạo Typer app.
    """
    cli_config = config.get('cli', {})
    help_config = cli_config.get('help', {})

    desc = help_config.get('description', f"Mô tả cho {config['meta']['tool_name']}.") #
    epilog = help_config.get('epilog', "")

    # Typer không hỗ trợ allow_interspersed_args trực tiếp trong Typer()
    # Nó nằm trong context_settings
    # allow_interspersed = cli_config.get('allow_interspersed_args', False)
    # allow_interspersed_str = str(allow_interspersed)

    code_lines = [
        f"app = typer.Typer(",
        f"    help={repr(desc)},", # Dùng repr để xử lý dấu ngoặc kép trong chuỗi
        f"    epilog={repr(epilog)},",
        f"    add_completion=False,", # Tắt tính năng auto-completion mặc định
        f"    context_settings={{",
        f"        'help_option_names': ['--help', '-h'],", # Thêm -h làm alias cho --help
        # f"        'allow_interspersed_args': {allow_interspersed_str}", # Không hỗ trợ
        f"    }}",
        f")"
    ]
    return "\n".join(code_lines)

def build_typer_path_expands(config: Dict[str, Any]) -> str:
    """
    Tạo code để gọi `.expanduser()` cho các tham số loại 'Path'
    (phiên bản Typer).

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
        var_name = f"{name}_expanded" # Tạo biến mới, ví dụ: target_dir_expanded

        # Typer truyền trực tiếp Path object vào hàm main
        # Nếu là Argument bắt buộc, không cần kiểm tra None
        if arg.get('is_argument') and 'default' not in arg:
             code_lines.append(f"    {var_name} = {name}.expanduser()")
        else:
             # Nếu là Option hoặc Argument có default, cần kiểm tra None
             # (Typer sẽ truyền None nếu Option không được cung cấp và không có default)
             code_lines.append(f"    {var_name} = {name}.expanduser() if {name} else None")

    return "\n".join(code_lines)

def build_typer_args_pass_to_core(config: Dict[str, Any]) -> str:
    """
    Tạo các dòng `key=value` để truyền các đối số đã xử lý
    vào hàm logic cốt lõi (phiên bản Typer).

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
            var_name = f"{name}_expanded"
            code_lines.append(f"        {name}={var_name},")
        else:
            # Các loại khác, truyền trực tiếp biến từ signature hàm main
            code_lines.append(f"        {name}={name},")

    return "\n".join(code_lines)


def build_typer_main_signature(config: Dict[str, Any]) -> str:
    """
    Tạo chữ ký (signature) cho hàm `main()` được decorate bởi `@app.command()`.

    Args:
        config: Dict chứa nội dung đã parse của file `.spec.toml`.

    Returns:
        Chuỗi string chứa toàn bộ chữ ký hàm `main()`, bao gồm type hints
        và các giá trị mặc định `typer.Argument`/`typer.Option`.
    """
    code_lines: List[str] = [
        f"def main(",
        f"    ctx: typer.Context," # Tham số context bắt buộc
    ]

    args = get_cli_args(config)

    # Kiểm tra xem có cần import Optional không
    needs_optional = any(
        not arg.get('is_argument', False) and 'default' not in arg and arg.get('type') != 'bool'
        for arg in args
    )
    if needs_optional:
        # Thêm Optional vào đầu danh sách import nếu cần
        # (Template entrypoint sẽ xử lý việc import thực tế)
        pass # Template sẽ thêm `from typing import Optional` nếu cần

    for arg in args:
        name = arg['name']
        spec_type = arg['type'] # 'str', 'int', 'bool', 'Path'
        py_type = TYPE_HINT_MAP.get(spec_type, 'str') # Lấy type hint Python tương ứng
        help_str = arg.get('help', f"Tham số {name}.") #

        default_repr: str = "..." # Giá trị mặc định cho Typer
        type_hint = py_type # Type hint cuối cùng

        is_argument = arg.get('is_argument', False)

        if 'default' in arg:
            # Nếu có default trong spec
            if py_type == 'bool':
                # Typer xử lý bool khác: default=True/False
                default_repr = str(arg['default']).capitalize() # True hoặc False
            else:
                # Dùng hằng số DEFAULT_ đã tạo trong file config
                default_repr = f"DEFAULT_{name.upper()}"
        else:
            # Nếu không có default trong spec
            if py_type == 'bool':
                default_repr = "False" # Mặc định cho cờ bool là False
            else:
                if is_argument:
                    # Argument positional bắt buộc, dùng ...
                    default_repr = "..."
                else:
                    # Option tùy chọn, mặc định là None
                    default_repr = "None"
                    type_hint = f"TypingOptional[{type_hint}]" # Thêm Optional[...]

        # Xác định dùng typer.Argument hay typer.Option
        if is_argument:
            code_lines.append(f"    {name}: {type_hint} = typer.Argument(")
            code_lines.append(f"        {default_repr},") # Giá trị mặc định
            code_lines.append(f"        help={repr(help_str)}") # Help text
            code_lines.append(f"    ),")
        else: # Là Option
            code_lines.append(f"    {name}: {type_hint} = typer.Option(")
            code_lines.append(f"        {default_repr},") # Giá trị mặc định

            option_names: List[str] = []
            # Thêm short flag (ví dụ: "-o") nếu có
            if 'short' in arg:
                option_names.append(f"\"{arg['short']}\"")
            # Thêm long flag (ví dụ: "--output")
            option_names.append(f"\"--{name}\"")
            code_lines.append(f"        {', '.join(option_names)},") # Các tên flag

            code_lines.append(f"        help={repr(help_str)}") # Help text
            code_lines.append(f"    ),")

    code_lines.append(f"):") # Kết thúc signature
    return "\n".join(code_lines)