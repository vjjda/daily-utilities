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
        # format_value_to_toml relies on tomlkit
        raise ImportError("Thư viện 'tomlkit' không được cài đặt.")

    template_path = module_dir / template_filename
    template_lines = load_text_template(template_path, logger).splitlines()

    output_lines: List[str] = []
    processed_keys: set[str] = set() # Track keys handled via placeholder

    # 1. Add Section Header
    output_lines.append(f"[{config_section_name}]")
    output_lines.append("") # Add a blank line after header

    # Regex to find potential key lines (commented or not) to extract comments
    # Groups: 1:indent, 2:comment_marker(#?), 3:key_name, 4:equals_part (= ...), 5:trailing_comment (#...)
    key_line_pattern = re.compile(r"^(\s*)(#?\s*)([\w-]+)(\s*=.*?)?\s*(#.*)?$")
    placeholder_pattern = re.compile(r"\{toml_(\w+)\}") # To find placeholders in value part

    # 2. Process Template Lines to extract comments and structure
    key_comments: Dict[str, str] = {} # Store comments associated with keys
    current_key_comment = ""

    in_section = False
    for line in template_lines:
        stripped_line = line.strip()

        # Find section start in template
        if stripped_line == f"[{config_section_name}]" or \
           stripped_line == "[{config_section_name}]":
            in_section = True
            continue # Skip header line itself

        # Stop processing if another section starts
        if in_section and stripped_line.startswith("[") and stripped_line.endswith("]"):
            in_section = False
            break # Stop after our target section

        if not in_section:
            continue # Only process lines within our section in the template

        # Capture comments preceding a key
        if stripped_line.startswith("#"):
            # Append multi-line comments
            if current_key_comment:
                current_key_comment += f"\n{line}"
            else:
                current_key_comment = line
            continue # Move to next line

        # Check if it's a key-value line (or potentially commented key-value)
        match = key_line_pattern.match(line)
        if match:
            key_name = match.group(3)
            # Store preceding comment (if any) and reset accumulator
            if current_key_comment:
                 # Check if placeholder name matches key
                 placeholder_suffix_in_val = ""
                 equals_part = match.group(4) or ""
                 placeholder_match = placeholder_pattern.search(equals_part)
                 if placeholder_match:
                     placeholder_suffix_in_val = placeholder_match.group(1).replace('_','-')

                 # Only associate comment if key matches placeholder variable name derived from key
                 if key_name == placeholder_suffix_in_val or not placeholder_match: # Or if it's just a commented key
                     key_comments[key_name] = current_key_comment
                 # else: Comment belongs to a different structure, ignore for now

            current_key_comment = "" # Reset comment accumulator

            # Also capture trailing comment on the same line
            trailing_comment = match.group(5)
            if trailing_comment and key_name not in key_comments:
                # If no preceding comment, use the trailing one as the primary
                 key_comments[key_name] = trailing_comment.strip()
            elif trailing_comment:
                 # Append trailing comment to preceding comment
                 key_comments[key_name] += f" {trailing_comment.strip()}"

        elif stripped_line == "":
             # If it's a blank line after comments, append it to the comment block
             if current_key_comment:
                 current_key_comment += "\n" # Keep blank line for spacing
        else:
            # Non-comment, non-key line, reset comment accumulator
            current_key_comment = ""


    # 3. Add default keys and values, preceded by extracted comments
    # Iterate through base_defaults to maintain a reasonable order
    for key in base_defaults.keys():
         if key in effective_defaults:
             value = effective_defaults[key]
             processed_keys.add(key) # Mark as processed

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

    # 4. Add any extra keys from effective_defaults not in base_defaults (rare)
    for key, value in effective_defaults.items():
        if key not in processed_keys:
             if key in key_comments:
                 output_lines.append(key_comments[key])
             if value is not None:
                 value_str = format_value_to_toml(value)
                 output_lines.append(f"{key} = {value_str}")
             else:
                 output_lines.append(f"# {key} = ")
             output_lines.append("")

    # Ensure trailing newline
    if not output_lines[-1] == "":
         output_lines.append("")

    final_content = "\n".join(output_lines)

    # Final basic validation (check if header is present)
    if f"[{config_section_name}]" not in final_content:
         # This should not happen with the new logic, but keep as safeguard
         raise ValueError(f"Generated content missing section header '[{config_section_name}]'.")

    return final_content