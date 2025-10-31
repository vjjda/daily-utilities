# Path: utils/core/cleaners/cleaner_shell.py
import logging
import re
from typing import List

__all__ = ["clean_shell_code"]


def clean_shell_code(
    code_content: str, logger: logging.Logger, all_clean: bool = False
) -> str:
    logger.debug("Trình làm sạch Shell được gọi.")

    if not all_clean:
        logger.debug(
            "Chế độ all_clean=False, không thực hiện thay đổi nào cho Shell script."
        )
        return code_content

    lines = code_content.splitlines()
    cleaned_lines: List[str] = []
    shebang_line: str | None = None

    if not lines:
        return ""

    if lines[0].strip().startswith("#!"):
        shebang_line = lines[0]
        logger.debug(f"Đã giữ lại shebang: {shebang_line}")
        lines = lines[1:]

    cleaned_code_block = []
    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith("# Path:"):
            cleaned_code_block.append(line)
            continue

        in_single_quotes = False
        in_double_quotes = False
        comment_start_index = -1

        for i, char in enumerate(line):
            if char == "'" and (i == 0 or line[i - 1] != "\\"):
                in_single_quotes = not in_single_quotes
            elif char == '"' and (i == 0 or line[i - 1] != "\\"):
                in_double_quotes = not in_double_quotes
            elif char == "#" and not in_single_quotes and not in_double_quotes:

                comment_start_index = i
                break

        if comment_start_index != -1:
            cleaned_part = line[:comment_start_index].rstrip()
            if cleaned_part:
                cleaned_code_block.append(cleaned_part)
        else:
            if line.strip():
                cleaned_code_block.append(line)

    if shebang_line:
        cleaned_lines.append(shebang_line)

    cleaned_lines.extend(cleaned_code_block)

    final_content = "\n".join(cleaned_lines)
    if final_content:
        final_content += "\n"

    final_content = re.sub(r"\n{3,}", "\n\n", final_content)

    logger.debug("Hoàn tất làm sạch Shell script.")
    return final_content