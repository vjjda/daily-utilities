# Path: utils/cli/config_init/config_content_generator.py

import logging
from pathlib import Path
from typing import Dict, Any, List
import re

try:
    import tomlkit
except ImportError:
    tomlkit = None

from utils.core import load_text_template, format_value_to_toml

__all__ = ["generate_config_content"]


def generate_config_content(
    logger: logging.Logger,
    module_dir: Path,
    template_filename: str,
    config_section_name: str,
    effective_defaults: Dict[str, Any],
) -> str:
    if tomlkit is None:
        raise ImportError("Thư viện 'tomlkit' không được cài đặt.")

    template_path = module_dir / template_filename
    template_lines = load_text_template(template_path, logger).splitlines()

    output_lines: List[str] = []

    output_lines.append(f"[{config_section_name}]")
    output_lines.append("")

    key_line_pattern = re.compile(r"^(\s*)(#?\s*)([\w-]+)(\s*=.*?)?\s*(#.*)?$")
    placeholder_pattern = re.compile(r"\{toml_(\w+)\}")

    key_comments: Dict[str, str] = {}
    current_key_comment = ""
    in_section = False
    for line in template_lines:
        stripped_line = line.strip()
        if (
            stripped_line == f"[{config_section_name}]"
            or stripped_line == "[{config_section_name}]"
        ):
            in_section = True
            continue
        if in_section and stripped_line.startswith("[") and stripped_line.endswith("]"):
            in_section = False
            break
        if not in_section:
            continue

        if stripped_line.startswith("#"):
            current_key_comment = (
                f"{current_key_comment}\n{line}" if current_key_comment else line
            )
            continue

        match = key_line_pattern.match(line)
        if match:
            key_name = match.group(3)
            if current_key_comment:

                key_comments[key_name] = current_key_comment.strip()

            current_key_comment = ""

            trailing_comment = match.group(5)
            if trailing_comment:
                existing_comment = key_comments.get(key_name, "")

                separator = " " if existing_comment else ""
                key_comments[key_name] = (
                    f"{existing_comment}{separator}{trailing_comment.strip()}"
                )

        elif stripped_line == "":
            if current_key_comment:
                current_key_comment += "\n"
        else:
            current_key_comment = ""

    for key, value in effective_defaults.items():

        if key in key_comments:
            output_lines.append(key_comments[key])

        if value is not None:
            value_str = format_value_to_toml(value)
            output_lines.append(f"{key} = {value_str}")
        else:
            output_lines.append(f"# {key} = ")
        output_lines.append("")

    while output_lines and output_lines[-1] == "":
        output_lines.pop()

    if output_lines:
        output_lines.append("")

    final_content = "\n".join(output_lines)

    if f"[{config_section_name}]" not in final_content.splitlines()[0]:
        raise ValueError(
            f"Generated content missing section header '[{config_section_name}]'."
        )

    return final_content