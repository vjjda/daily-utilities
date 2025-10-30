# Path: modules/stubgen/stubgen_internal/stubgen_formatter.py
"""
.pyi Content Formatting logic for the Stub Generator (sgen) module.
(Internal module, imported by stubgen_core.py)
"""

from pathlib import Path
from typing import Set

__all__ = ["format_stub_content"]


def format_stub_content(
    init_path: Path,
    project_root: Path,
    all_exported_symbols: Set[str],
    stub_template_str: str,
) -> str:
    """
    Tạo nội dung (string) cho file .pyi.
    Args:
        init_path: Đường dẫn đến file __init__.py nguồn.
        project_root: Gốc dự án (để tính đường dẫn tương đối).
        all_exported_symbols: Set các tên symbol cần export.
        stub_template_str: Nội dung file template .pyi.template.

    Returns:
        Một string chứa nội dung file .pyi hoàn chỉnh (không có header Path).
    """

    if not all_exported_symbols:
        # Nếu không có symbols, trả về template với __all__ rỗng
        return stub_template_str.format(
            module_name=init_path.parent.name,
            symbol_declarations="# (No symbols found)",
            all_list_repr="[]",
        )

    sorted_symbols = sorted(list(all_exported_symbols))

    # Tạo các dòng "symbol: Any"
    symbol_declarations = "\n".join(f"{symbol}: Any" for symbol in sorted_symbols)

    # SỬA: Dùng double quotes (") thay vì repr()
    quoted_symbols = [f'"{symbol}"' for symbol in sorted_symbols]

    # SỬA: Tạo nội dung list __all__ theo chuẩn Black
    all_list_body: str
    all_list_repr: str

    if not quoted_symbols:
        # Trường hợp list rỗng
        all_list_repr = "[]"
    else:
        # Tạo nội dung body
        all_list_body = ",\n".join(
            f"    {symbol_repr}" for symbol_repr in quoted_symbols
        )
        # SỬA: Thêm dấu phẩy cuối (trailing comma)
        all_list_body += ","
        # Đưa vào cặp ngoặc
        all_list_repr = f"[\n{all_list_body}\n]"

    module_name = init_path.parent.name

    # Điền vào template
    return stub_template_str.format(
        module_name=module_name,
        symbol_declarations=symbol_declarations,
        all_list_repr=all_list_repr,
    )