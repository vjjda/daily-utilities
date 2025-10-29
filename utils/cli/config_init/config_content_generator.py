# Path: utils/cli/config_init/config_content_generator.py
"""
Generates the configuration file content string by formatting defaults
and placing them under the correct section header, preserving comments
from the original template structure as hints.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
import re

try:
    import tomlkit # Still used for formatting individual values
except ImportError:
    tomlkit = None

from utils.core import load_text_template, format_value_to_toml

__all__ = ["generate_config_content"]


def generate_config_content(
    logger: logging.Logger,
    module_dir: Path,
    template_filename: str,
    config_section_name: str,
    effective_defaults: Dict[str, Any]
) -> str:
    """
    Loads template for comments, formats defaults, and combines them
    into a valid TOML section string.
    """
    if tomlkit is None:
        raise ImportError("Thư viện 'tomlkit' không được cài đặt.")

    template_path = module_dir / template_filename
    template_lines = load_text_template(template_path, logger).splitlines()

    output_lines: List[str] = []
    # --- REMOVED: processed_keys is no longer needed ---
    # processed_keys: set[str] = set()

    # 1. Add Section Header
    output_lines.append(f"[{config_section_name}]")
    output_lines.append("")

    key_line_pattern = re.compile(r"^(\s*)(#?\s*)([\w-]+)(\s*=.*?)?\s*(#.*)?$")
    placeholder_pattern = re.compile(r"\{toml_(\w+)\}")

    # 2. Process Template Lines to extract comments
    key_comments: Dict[str, str] = {}
    current_key_comment = ""
    in_section = False
    for line in template_lines:
        stripped_line = line.strip()
        if stripped_line == f"[{config_section_name}]" or \
           stripped_line == "[{config_section_name}]":
            in_section = True
            continue
        if in_section and stripped_line.startswith("[") and stripped_line.endswith("]"):
            in_section = False
            break
        if not in_section:
            continue

        if stripped_line.startswith("#"):
            current_key_comment = f"{current_key_comment}\n{line}" if current_key_comment else line
            continue

        match = key_line_pattern.match(line)
        if match:
            key_name = match.group(3)
            if current_key_comment:
                 placeholder_suffix_in_val = ""
                 equals_part = match.group(4) or ""
                 placeholder_match = placeholder_pattern.search(equals_part)
                 if placeholder_match:
                     placeholder_suffix_in_val = placeholder_match.group(1).replace('_','-')
                 if key_name == placeholder_suffix_in_val or not placeholder_match:
                     key_comments[key_name] = current_key_comment.strip() # Store stripped comment block

            current_key_comment = "" # Reset comment accumulator

            trailing_comment = match.group(5)
            if trailing_comment:
                existing_comment = key_comments.get(key_name, "")
                # Append trailing comment separated by a space if there was a preceding comment
                separator = " " if existing_comment else ""
                key_comments[key_name] = f"{existing_comment}{separator}{trailing_comment.strip()}"

        elif stripped_line == "":
             if current_key_comment:
                 current_key_comment += "\n" # Keep blank line for spacing
        else:
            current_key_comment = ""

    # --- FIX: Iterate directly over effective_defaults ---
    # 3. Add default keys and values, preceded by extracted comments
    for key, value in effective_defaults.items():
        # Add comment if found
        if key in key_comments:
            output_lines.append(key_comments[key])

        # Format value and add key-value line (or commented line for None)
        if value is not None:
            value_str = format_value_to_toml(value)
            output_lines.append(f"{key} = {value_str}")
        else:
            output_lines.append(f"# {key} = ") # Default commented for None
        output_lines.append("") # Add blank line for spacing
    # --- END FIX ---

    # --- REMOVED: Second loop for extra keys (already covered) ---

    # Ensure trailing newline
    # Remove potential multiple blank lines at the end
    while output_lines and output_lines[-1] == "":
        output_lines.pop()
    # Add a single trailing newline if there's content
    if output_lines:
        output_lines.append("")


    final_content = "\n".join(output_lines)

    if f"[{config_section_name}]" not in final_content.splitlines()[0]: # Check first line
         raise ValueError(f"Generated content missing section header '[{config_section_name}]'.")

    return final_content