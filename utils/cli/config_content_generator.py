# Path: utils/cli/config_content_generator.py
"""
Generates the configuration file content string from a template,
correctly handling None values and preserving comments.
"""

import logging
from pathlib import Path
from typing import Dict, Any
import re

# Import necessary core utils
from utils.core import load_text_template, format_value_to_toml

__all__ = ["generate_config_content"]


def generate_config_content(
    logger: logging.Logger,
    module_dir: Path,
    template_filename: str,
    config_section_name: str, # Still needed for context if errors occur elsewhere
    effective_defaults: Dict[str, Any]
) -> str:
    """
    Tải template, giữ comment, và chèn giá trị mặc định chỉ khi chúng không None.
    Nếu giá trị mặc định là None, comment out dòng key = value đó trong template.
    """
    template_path = module_dir / template_filename
    template_lines = load_text_template(template_path, logger).splitlines()

    output_lines = []
    # --- REMOVED: Redundant header check variables ---
    # section_header_expected = f"[{config_section_name}]"
    # header_found_in_template = False
    # --- END REMOVAL ---

    placeholder_pattern = re.compile(
        r"^(\s*)(#?\s*)([\w-]+)\s*=\s*\{toml_(\w+)\}\s*(?:#.*)?$"
    )

    for line in template_lines:
        match = placeholder_pattern.match(line)
        if match:
            indent, _, key_name_toml, placeholder_suffix = match.groups()
            key_name_dict = placeholder_suffix.replace('_', '-')

            if key_name_dict in effective_defaults:
                value = effective_defaults[key_name_dict]
                if value is not None:
                    value_str = format_value_to_toml(value)
                    output_lines.append(f"{indent}{key_name_toml} = {value_str}")
                else:
                    output_lines.append(f"{indent}# {key_name_toml} = ")
            else:
                 output_lines.append(line) # Keep template line if key missing in defaults
        else:
            # --- REMOVED: Redundant header check ---
            # if section_header_expected in line:
            #     header_found_in_template = True
            # --- END REMOVAL ---
            output_lines.append(line) # Keep non-placeholder lines

    # --- REMOVED: Redundant header validation block ---
    # if not header_found_in_template:
    #      raise ValueError(
    #          f"Template '{template_filename}' thiếu header section '{section_header_expected}'."
    #      )
    # --- END REMOVAL ---

    if output_lines and output_lines[-1].strip() != "":
        output_lines.append("")

    return "\n".join(output_lines)