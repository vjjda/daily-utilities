# Path: utils/core/cleaners/cleaner_shell.py
"""
Trình làm sạch (cleaner) cụ thể cho Shell/Bash.
Loại bỏ các comment '#' trong khi cố gắng giữ lại shebang và các ký tự '#'
bên trong dấu ngoặc kép hoặc đơn.
(Module nội bộ, được import bởi code_cleaner.py)
"""

import logging
import re
from typing import List

__all__ = ["clean_shell_code"]

def clean_shell_code(
    code_content: str,
    logger: logging.Logger,
    all_clean: bool = False # Parameter remains for interface consistency
) -> str:
    """
    Loại bỏ comments '#' khỏi mã nguồn Shell/Bash.

    Hiện tại, chức năng này chỉ hoạt động khi `all_clean` được đặt thành True,
    vì khái niệm "docstring" không áp dụng trực tiếp cho shell scripts.
    Nó cố gắng bảo tồn shebang và các ký tự '#' bên trong dấu ngoặc.
    """
    logger.debug("Trình làm sạch Shell được gọi.")

    if not all_clean:
        logger.debug("Chế độ all_clean=False, không thực hiện thay đổi nào cho Shell script.")
        return code_content # Shell scripts don't have docstrings in the Python sense

    lines = code_content.splitlines()
    cleaned_lines: List[str] = []
    shebang_line: str | None = None

    if not lines:
        return ""

    # 1. Preserve Shebang
    if lines[0].strip().startswith("#!"):
        shebang_line = lines[0]
        logger.debug(f"Đã giữ lại shebang: {shebang_line}")
        lines = lines[1:] # Process remaining lines

    # 2. Process remaining lines to remove comments
    # This regex tries to find '#' that is NOT preceded by an odd number of quotes
    # It's not perfect for complex cases but covers simple ones.
    # It looks for '#' possibly preceded by spaces, ensuring it's not inside simple quotes.
    # A more robust regex would need lookbehind/lookahead for different quote types.
    # Let's try a simpler approach: find the first '#' NOT inside quotes.
    cleaned_code_block = []
    for line in lines:
        in_single_quotes = False
        in_double_quotes = False
        comment_start_index = -1

        for i, char in enumerate(line):
            if char == "'" and (i == 0 or line[i-1] != '\\'):
                in_single_quotes = not in_single_quotes
            elif char == '"' and (i == 0 or line[i-1] != '\\'):
                in_double_quotes = not in_double_quotes
            elif char == '#' and not in_single_quotes and not in_double_quotes:
                # Found the first '#' not inside quotes
                comment_start_index = i
                break # Stop searching on this line

        if comment_start_index != -1:
            # Keep the part before the comment, stripping trailing whitespace
            cleaned_part = line[:comment_start_index].rstrip()
            # Only add the line if the part before the comment is not empty
            if cleaned_part:
                cleaned_code_block.append(cleaned_part)
            # If the cleaned part is empty, the whole line was effectively a comment, skip it.
        else:
            # No comment found, keep the line if it's not just whitespace
            if line.strip():
                cleaned_code_block.append(line)

    # 3. Reconstruct the script
    if shebang_line:
        cleaned_lines.append(shebang_line)

    cleaned_lines.extend(cleaned_code_block)

    # Join lines, ensuring a single trailing newline if there's content
    final_content = '\n'.join(cleaned_lines)
    if final_content:
        final_content += '\n'

    # Remove potential multiple blank lines introduced
    final_content = re.sub(r'\n{3,}', '\n\n', final_content)


    logger.debug("Hoàn tất làm sạch Shell script.")
    return final_content