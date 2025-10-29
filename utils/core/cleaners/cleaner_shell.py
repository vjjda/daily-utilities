# Path: utils/core/cleaners/cleaner_shell.py
"""
Trình làm sạch (cleaner) cụ thể cho Shell/Bash.
(Module nội bộ, được import bởi code_cleaner.py)
"""

import logging
import re
from typing import List

__all__ = ["clean_shell_code"]

def clean_shell_code(
    code_content: str,
    logger: logging.Logger,
    all_clean: bool = False
) -> str:
    """Giả lập làm sạch comment Shell (cẩn thận với shebang)."""
    logger.debug("Trình làm sạch Shell (giả lập) được gọi.")
    
    lines = code_content.splitlines()
    cleaned_lines: List[str] = []

    if not lines:
        return ""

    # Giữ lại shebang (nếu có)
    if lines[0].strip().startswith("#!"):
        cleaned_lines.append(lines[0])
        lines = lines[1:]
    
    if all_clean:
        # Chỉ xóa comment nếu `all_clean` là True
        for line in lines:
            # Regex đơn giản: xóa comment # (trừ khi nó ở trong dấu ngoặc)
            cleaned_line = re.sub(r'(?<!\w)#.*', '', line).strip()
            if cleaned_line: # Bỏ qua các dòng trống
                cleaned_lines.append(cleaned_line)
    else:
        # Nếu không `all_clean`, chỉ ghép lại các dòng đã giữ
        cleaned_lines.extend(lines)

    return '\n'.join(cleaned_lines)