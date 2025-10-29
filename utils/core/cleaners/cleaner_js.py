# Path: utils/core/cleaners/cleaner_js.py
"""
Trình làm sạch (cleaner) cụ thể cho JavaScript.
(Module nội bộ, được import bởi code_cleaner.py)

LƯU Ý: Đây chỉ là VÍ DỤ GIẢ LẬP (placeholder).
Một trình làm sạch thực thụ nên dùng JS parser (ví dụ: esprima, tree-sitter)
thay vì regex.
"""

import logging
import re
from typing import List

__all__ = ["clean_javascript_code"]

def clean_javascript_code(
    code_content: str,
    logger: logging.Logger,
    all_clean: bool = False
) -> str:
    """Giả lập làm sạch comment JS."""
    logger.debug("Trình làm sạch JavaScript (giả lập) được gọi.")
    if not all_clean:
        # Chỉ xóa docstring (ví dụ: JSDoc)
        # Regex này rất đơn giản và CHỈ là VÍ DỤ
        code_content = re.sub(r'/\*\*[\s\S]*?\*/', '', code_content)
    else:
        # Xóa tất cả comment
        code_content = re.sub(r'//.*', '', code_content)
        code_content = re.sub(r'/\*[\s\S]*?\*/', '', code_content)
    
    # Xóa các dòng trắng thừa
    cleaned_lines: List[str] = [line for line in code_content.splitlines() if line.strip()]
    return '\n'.join(cleaned_lines)