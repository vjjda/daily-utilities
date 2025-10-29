# Path: utils/cli/config_init/config_content_generator.py
"""
Generates the configuration file content string from a template,
correctly handling None values and preserving comments.
"""

import logging
from pathlib import Path
from typing import Dict, Any
import re

# Import necessary core utils
# Renamed import to avoid potential namespace collision if format_value_to_toml is used elsewhere
from utils.core import load_text_template, format_value_to_toml as _format_single_value_to_toml

__all__ = ["generate_config_content"]


def generate_config_content(
    logger: logging.Logger,
    module_dir: Path,
    template_filename: str,
    config_section_name: str, # Used for replacing header placeholder
    effective_defaults: Dict[str, Any]
) -> str:
    """
    Tải template, giữ comment, chèn giá trị mặc định (commenting out None),
    và thay thế placeholder header section.
    """
    template_path = module_dir / template_filename
    template_lines = load_text_template(template_path, logger).splitlines()

    output_lines = []
    section_header_placeholder = "[{config_section_name}]" # Placeholder like in template
    section_header_correct = f"[{config_section_name}]"   # Correct header string

    placeholder_pattern = re.compile(
        r"^(\s*)(#?\s*)([\w-]+)\s*=\s*\{toml_(\w+)\}\s*(?:#.*)?$"
    )

    for line in template_lines:
        # --- FIX: Explicitly replace header placeholder ---
        if section_header_placeholder in line:
            processed_line = line.replace(section_header_placeholder, section_header_correct)
            output_lines.append(processed_line)
            continue # Header processed, move to next line
        # --- END FIX ---

        match = placeholder_pattern.match(line)
        if match:
            indent, _, key_name_toml, placeholder_suffix = match.groups()
            key_name_dict = placeholder_suffix.replace('_', '-')

            if key_name_dict in effective_defaults:
                value = effective_defaults[key_name_dict]
                if value is not None:
                    # Use the imported helper function
                    value_str = _format_single_value_to_toml(value)
                    output_lines.append(f"{indent}{key_name_toml} = {value_str}")
                else:
                    output_lines.append(f"{indent}# {key_name_toml} = ")
            else:
                 # Keep template line if key missing in defaults
                 output_lines.append(line)
        else:
            # Keep other lines (comments, blank lines, already correct headers if any)
            output_lines.append(line)

    # Add trailing newline if needed
    if output_lines and output_lines[-1].strip() != "":
        output_lines.append("")

    # The final validation happens when tomlkit tries to parse this string
    return "\n".join(output_lines)