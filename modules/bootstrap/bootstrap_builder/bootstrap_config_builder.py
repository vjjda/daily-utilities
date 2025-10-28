# Path: modules/bootstrap/bootstrap_builder/bootstrap_config_builder.py
"""
Logic tạo các đoạn mã (code snippet) liên quan đến file config của module mới.
(Module nội bộ, được import bởi bootstrap_builder)
"""

from typing import Dict, Any, List

from ..bootstrap_utils import get_cli_args

__all__ = [
    "build_config_constants", "build_config_all_list", "build_config_imports"
]


def build_config_constants(config: Dict[str, Any]) -> str:
    """
    Tạo mã Python cho các hằng số `DEFAULT_...` trong file `*_config.py`.

    Chỉ tạo hằng số cho các đối số có `default` và không phải `bool`.

    Args:
        config: Dict chứa nội dung đã parse của file `.spec.toml`.

    Returns:
        Chuỗi string chứa các dòng định nghĩa hằng số.
    """
    code_lines: List[str] = []

    default_args = [
        arg for arg in get_cli_args(config)
        if 'default' in arg and arg.get('type') != 'bool'
    ]

    if not default_args:
        code_lines.append("# (Không có hằng số mặc định nào được định nghĩa trong tool.spec.toml)") #
        return "\n".join(code_lines)

    for arg in default_args:
        name = arg['name']
        const_name = f"DEFAULT_{name.upper()}" # Ví dụ: DEFAULT_OUTPUT_DIR
        const_value = repr(arg['default']) # Dùng repr để có dấu ngoặc kép cho string
        code_lines.append(f"{const_name} = {const_value}")

    return "\n".join(code_lines)

def build_config_all_list(config: Dict[str, Any]) -> str:
    """
    Tạo chuỗi cho danh sách `__all__` trong file `*_config.py`.

    Bao gồm tên các hằng số `DEFAULT_...` đã tạo.

    Args:
        config: Dict chứa nội dung đã parse của file `.spec.toml`.

    Returns:
        Chuỗi string dạng `"CONST1", "CONST2", ...` hoặc chuỗi rỗng.
    """
    default_args = [
        arg for arg in get_cli_args(config)
        if 'default' in arg and arg.get('type') != 'bool'
    ]
    if not default_args:
        return "" # Trả về chuỗi rỗng nếu không có hằng số

    const_names: List[str] = []
    for arg in default_args:
        const_name = f"DEFAULT_{arg['name'].upper()}"
        const_names.append(f'"{const_name}"') # Thêm dấu ngoặc kép

    return ", ".join(const_names)

def build_config_imports(module_name: str, config: Dict[str, Any]) -> str:
    """
    Tạo dòng code `from ... import ...` để import các hằng số config
    vào file entrypoint (ví dụ: `scripts/new_tool.py`).

    Args:
        module_name: Tên module (ví dụ: "new_tool").
        config: Dict chứa nội dung đã parse của file `.spec.toml`.

    Returns:
        Chuỗi string chứa dòng `import` hoặc comment nếu không có gì để import.
    """
    default_args = [
        arg for arg in get_cli_args(config)
        if 'default' in arg and arg.get('type') != 'bool'
    ]

    if not default_args:
        return "# (Không có hằng số mặc định nào để import)" #

    const_names: List[str] = []
    for arg in default_args:
        const_name = f"DEFAULT_{arg['name'].upper()}"
        const_names.append(const_name)

    import_list = ", ".join(const_names)
    # Ví dụ: from modules.new_tool.new_tool_config import DEFAULT_OUTPUT_DIR
    return f"from modules.{module_name}.{module_name}_config import {import_list}"