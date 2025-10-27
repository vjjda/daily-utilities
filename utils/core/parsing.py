# Path: utils/core/parsing.py

"""
String Parsing Utilities
(Internal module, imported by utils/core.py)
"""

# --- MODIFIED: Thêm re và Tuple ---
import re
from typing import Union, Set, Tuple
# --- END MODIFIED ---


# --- MODIFIED: Cập nhật __all__ ---
__all__ = ["parse_comma_list", "parse_cli_set_operators"]
# --- END MODIFIED ---

def parse_comma_list(value: Union[str, None]) -> Set[str]:
    """
    Converts a comma-separated string into a set of stripped items.
    (Code moved from utils/core.py)
    """
    if not value: 
        return set()
    return {item.strip() for item in value.split(',') if item.strip() != ''}

# --- MODIFIED: Hàm phân tích toán tử set (Dùng ~ thay vì -) ---
def parse_cli_set_operators(cli_string: str) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    Phân tích chuỗi CLI thành các tập hợp Ghi đè, Thêm, và Bớt.
    Ví dụ: "a,b+x,y~z" -> ({"a", "b"}, {"x", "y"}, {"z"})
    Ví dụ: "+x,y~z" -> (set(), {"x", "y"}, {"z"})
    """
    overwrite_set: Set[str] = set()
    add_set: Set[str] = set()
    subtract_set: Set[str] = set()

    if not cli_string:
        return overwrite_set, add_set, subtract_set

    # Regex: Tìm các đoạn bắt đầu bằng + hoặc ~
    # --- MODIFIED: Thay thế - bằng ~ trong regex ---
    matches = re.findall(r'([+~]?)((?:[^~+]|\\.)+)', cli_string)
    # --- END MODIFIED ---
    
    if not matches:
        return overwrite_set, add_set, subtract_set
    
    # Xử lý match đầu tiên
    first_operator, first_items_str = matches[0]
    first_items_set = parse_comma_list(first_items_str)
    
    if not first_operator:
        # Trường hợp Ghi đè (không có toán tử ở đầu)
        overwrite_set.update(first_items_set)
    elif first_operator == '+':
        add_set.update(first_items_set)
    # --- MODIFIED: Thay thế - bằng ~ ---
    elif first_operator == '~':
        subtract_set.update(first_items_set)
    # --- END MODIFIED ---
        
    # Xử lý các match còn lại (nếu có)
    for operator, items_str in matches[1:]:
        items_set = parse_comma_list(items_str)
        if operator == '+':
            add_set.update(items_set)
        # --- MODIFIED: Thay thế - bằng ~ ---
        elif operator == '~':
            subtract_set.update(items_set)
        # --- END MODIFIED ---
    
    return overwrite_set, add_set, subtract_set
# --- END MODIFIED ---