# Path: utils/core/parsing.py

"""
Các tiện ích phân tích chuỗi (String Parsing).
(Module nội bộ, được import bởi utils/core)
"""

import re
from typing import Union, Set, Tuple

__all__ = ["parse_comma_list", "parse_cli_set_operators"]

def parse_comma_list(value: Union[str, None]) -> Set[str]:
    """
    Chuyển đổi một chuỗi ngăn cách bởi dấu phẩy thành một set các mục đã strip().

    Args:
        value: Chuỗi đầu vào hoặc None.

    Returns:
        Set các chuỗi đã được tách và làm sạch, hoặc set rỗng nếu đầu vào là None/rỗng.
    """
    if not value:
        return set()
    # Tách chuỗi bằng dấu phẩy, strip khoảng trắng và loại bỏ các mục rỗng
    return {item.strip() for item in value.split(',') if item.strip()}

def parse_cli_set_operators(cli_string: str) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    Phân tích chuỗi CLI thành các tập hợp Ghi đè (Overwrite), Thêm (Add), và Bớt (Subtract).
    Sử dụng '+' cho Thêm và '~' cho Bớt.

    Ví dụ:
    - `"a,b+x,y~z"` -> `({"a", "b"}, {"x", "y"}, {"z"})`
    - `"+x,y~z"`    -> `(set(), {"x", "y"}, {"z"})`
    - `"a,b"`       -> `({"a", "b"}, set(), set())`
    - `"+a,b"`      -> `(set(), {"a", "b"}, set())`
    - `"~a,b"`      -> `(set(), set(), {"a", "b"})`

    Args:
        cli_string: Chuỗi đầu vào từ CLI.

    Returns:
        Tuple chứa 3 set: (overwrite_set, add_set, subtract_set).
    """
    overwrite_set: Set[str] = set()
    add_set: Set[str] = set()
    subtract_set: Set[str] = set()

    if not cli_string:
        return overwrite_set, add_set, subtract_set

    # Regex: Tìm các đoạn bắt đầu bằng '+' hoặc '~' (hoặc không có gì)
    # `([+~]?)` : Bắt group 1: toán tử tùy chọn '+' hoặc '~'
    # `((?:[^~+]|\\.)+)`: Bắt group 2: một hoặc nhiều ký tự không phải là '+' hoặc '~',
    #                      hoặc bất kỳ ký tự nào nếu được escape bằng '\' (chưa hỗ trợ escape)
    matches = re.findall(r'([+~]?)((?:[^~+])+)', cli_string) # Đơn giản hóa regex

    if not matches:
        # Nếu không khớp regex nào (ví dụ: chuỗi chỉ chứa toán tử), trả về rỗng
        return overwrite_set, add_set, subtract_set

    # Xử lý match đầu tiên để xác định chế độ (Overwrite hay Modify)
    first_operator, first_items_str = matches[0]
    first_items_set = parse_comma_list(first_items_str)

    if not first_operator:
        # Không có toán tử ở đầu -> Chế độ Ghi đè
        overwrite_set.update(first_items_set)
    elif first_operator == '+':
        add_set.update(first_items_set)
    elif first_operator == '~':
        subtract_set.update(first_items_set)

    # Xử lý các match còn lại (luôn là Modify)
    for operator, items_str in matches[1:]:
        items_set = parse_comma_list(items_str)
        if operator == '+':
            add_set.update(items_set)
        elif operator == '~':
            subtract_set.update(items_set)
        # Bỏ qua nếu có toán tử không hợp lệ (không nên xảy ra với regex này)

    return overwrite_set, add_set, subtract_set