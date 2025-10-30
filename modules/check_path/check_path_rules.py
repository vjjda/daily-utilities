# Path: modules/check_path/check_path_rules.py

from typing import List, Dict, Any

__all__ = ["apply_line_comment_rule", "apply_block_comment_rule"]


def apply_line_comment_rule(
    lines: List[str], correct_path_comment: str, check_prefix: str, is_executable: bool
) -> List[str]:

    line1_is_shebang = lines[0].startswith("#!")

    if line1_is_shebang and not is_executable:
        lines.pop(0)

        if not lines:
            return lines

        line1_is_shebang = False

    line1_is_path = lines[0].startswith(f"{check_prefix} Path:")
    line2_is_path = False

    if len(lines) > 1 and lines[1].startswith(f"{check_prefix} Path:"):
        line2_is_path = True

    if line1_is_shebang:

        if line2_is_path:
            if lines[1] != correct_path_comment:
                lines[1] = correct_path_comment
        else:
            lines.insert(1, correct_path_comment)

    elif line1_is_path:

        if len(lines) > 1 and lines[1].startswith("#!"):
            if is_executable:
                lines[0], lines[1] = lines[1], lines[0]
                if lines[1] != correct_path_comment:
                    lines[1] = correct_path_comment
            else:
                lines.pop(1)
                if lines[0] != correct_path_comment:
                    lines[0] = correct_path_comment
        else:

            if lines[0] != correct_path_comment:
                lines[0] = correct_path_comment

    else:

        lines.insert(0, correct_path_comment)

    return lines


def apply_block_comment_rule(
    lines: List[str], correct_path_comment: str, rule: Dict[str, Any]
) -> List[str]:

    prefix = rule["comment_prefix"]
    padding = " " if rule.get("padding", False) else ""

    line1_is_path = lines[0].startswith(f"{prefix}{padding}Path:")

    if line1_is_path:
        if lines[0] != correct_path_comment:
            lines[0] = correct_path_comment
    else:
        lines.insert(0, correct_path_comment)

    return lines