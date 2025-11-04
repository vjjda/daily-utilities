# Path: modules/check_path/check_path_internal/check_path_analyzer.py
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..check_path_config import COMMENT_RULES_BY_EXT
from .check_path_rules import apply_block_comment_rule, apply_line_comment_rule

__all__ = ["analyze_single_file_for_path_comment"]

FileResult = Dict[str, Any]


def analyze_single_file_for_path_comment(
    file_path: Path, scan_root: Path, logger: logging.Logger
) -> Optional[FileResult]:
    try:
        relative_path = file_path.relative_to(scan_root)
    except ValueError:

        relative_path = file_path.relative_to(file_path.parent)

    file_ext = "".join(file_path.suffixes)
    rule = COMMENT_RULES_BY_EXT.get(file_ext)

    if not rule:
        logger.debug(f"Bỏ qua kiểu file không hỗ trợ: {relative_path.as_posix()}")
        return None

    try:
        try:
            original_lines = file_path.read_text(encoding="utf-8").splitlines(True)
            lines = list(original_lines)
        except UnicodeDecodeError:
            logger.warning(f"Bỏ qua file lỗi encoding: {relative_path.as_posix()}")
            return None
        except IOError as e:
            logger.error(f"Không thể đọc file {relative_path.as_posix()}: {e}")
            return None

        if not lines:
            return None

        try:
            is_executable = os.access(file_path, os.X_OK)
        except Exception:
            is_executable = False

        first_line_content = lines[0].strip()
        new_lines: List[str] = []
        correct_comment_str = ""
        rule_type = rule["type"]

        if rule_type == "line":
            prefix = rule["comment_prefix"]
            correct_comment = f"{prefix} Path: {relative_path.as_posix()}\n"
            correct_comment_str = correct_comment
            new_lines = apply_line_comment_rule(
                lines, correct_comment, prefix, is_executable
            )
        elif rule_type == "block":
            prefix = rule["comment_prefix"]
            suffix = rule["comment_suffix"]
            padding = " " if rule.get("padding", False) else ""
            correct_comment = (
                f"{prefix}{padding}Path: {relative_path.as_posix()}{padding}{suffix}\n"
            )
            correct_comment_str = correct_comment
            new_lines = apply_block_comment_rule(lines, correct_comment, rule)
        else:
            logger.warning(
                f"Bỏ qua file: Kiểu quy tắc không rõ '{rule_type}' cho {relative_path.as_posix()}"
            )
            return None

        if new_lines != original_lines:
            fix_preview_str = correct_comment_str.strip()
            if first_line_content.startswith("#!") and not is_executable:
                fix_preview_str = f"(Đã xóa Shebang) -> {fix_preview_str}"

            return {
                "path": file_path,
                "line": first_line_content,
                "new_lines": new_lines,
                "fix_preview": fix_preview_str,
            }

    except Exception as e:
        logger.error(f"Lỗi xử lý file {relative_path.as_posix()}: {e}")
        logger.debug("Traceback:", exc_info=True)

    return None
