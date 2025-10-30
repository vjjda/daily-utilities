# Path: utils/core/cleaners/cleaner_js.py
import logging
import re
from typing import List, Final

__all__ = ["clean_javascript_code"]


SAFE_JS_CLEANER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'("(\\"|[^"])*")'
    r"|('(\\'|[^'])*')"
    r"|(`(\\`|[^`])*`)"
    r"|(/\*\*[\s\S]*?\*/)"
    r"|(/\*[\s\S]*?\*/)"
    r"|(//.*)"
)


def clean_javascript_code(
    code_content: str, logger: logging.Logger, all_clean: bool = False
) -> str:
    logger.debug(
        f"Trình làm sạch JavaScript (Regex an toàn) được gọi (all_clean={all_clean})."
    )

    def replacer(match: re.Match[str]) -> str:

        if match.group(1) or match.group(2) or match.group(3):
            return match.group(0)

        if all_clean:

            if match.group(4) or match.group(5) or match.group(6):
                return ""
        else:

            if match.group(4):
                return ""

            if match.group(5) or match.group(6):
                return match.group(0)

        return match.group(0)

    try:
        cleaned_content: str = SAFE_JS_CLEANER_PATTERN.sub(replacer, code_content)

        cleaned_lines: List[str] = [
            line for line in cleaned_content.splitlines() if line.strip()
        ]

        if not cleaned_lines:
            return ""

        final_content = "\n".join(cleaned_lines)

        return final_content + "\n"

    except Exception as e:
        logger.warning(f"Lỗi khi xử lý regex cleaner cho JavaScript: {e}")

        return code_content