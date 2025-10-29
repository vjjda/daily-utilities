# Path: utils/cli/config_init/config_content_generator.py
"""
Generates the configuration file content string using tomlkit
to preserve template comments and correctly insert default values.
"""

import logging
from pathlib import Path
from typing import Dict, Any

try:
    import tomlkit
    from tomlkit.items import Comment, Item # Import Comment and Item
except ImportError:
    tomlkit = None
    # Dummy types if tomlkit is missing
    class Comment: pass
    class Item: pass

# Import necessary core utils
from utils.core import load_text_template # Still needed to load template initially

__all__ = ["generate_config_content"]


def generate_config_content(
    logger: logging.Logger,
    module_dir: Path,
    template_filename: str,
    config_section_name: str,
    effective_defaults: Dict[str, Any]
) -> str:
    """
    Parses the template with tomlkit, updates values based on defaults
    (uncommenting keys if necessary), and dumps back to a string.
    """
    if tomlkit is None:
        raise ImportError("Thư viện 'tomlkit' không được cài đặt.")

    template_path = module_dir / template_filename
    template_string = load_text_template(template_path, logger)

    try:
        # 1. Parse the template string with tomlkit
        doc = tomlkit.parse(template_string)

        # Check if the expected section exists in the parsed template
        if config_section_name not in doc:
            raise ValueError(
                f"Template '{template_filename}' is missing the primary section '[{config_section_name}]'."
            )

        # Get the target section table
        section_table = doc[config_section_name]
        if not isinstance(section_table, tomlkit.items.Table):
             raise ValueError(f"Section '[{config_section_name}]' in template is not a valid TOML table.")


        # 2. Iterate through defaults and update the tomlkit document
        for key, value in effective_defaults.items():
            # Skip None values - we want them commented out as per template logic
            if value is None:
                # Ensure the key exists but remains potentially commented
                if key not in section_table:
                     # Add the key commented out if completely missing
                     section_table.add(tomlkit.comment(f"{key} = "))
                continue # Skip updating value for None

            # Key exists in defaults and value is not None
            if key in section_table:
                # Update the value using tomlkit item factory
                section_table[key] = tomlkit.item(value)

                # --- Crucial: Uncomment the key if it was commented ---
                # Access the trivia (comments/whitespace) associated with the key
                key_obj = section_table.key(key)
                if key_obj and key_obj.trivia.comment_ws and key_obj.trivia.comment:
                    # Check if the comment starts with '# ' which indicates our placeholder comment
                    if key_obj.trivia.comment.startswith("# "):
                        logger.debug(f"Uncommenting key '{key}' in section '{config_section_name}'")
                        # Clear the preceding comment trivia
                        key_obj.trivia.comment_ws = ""
                        key_obj.trivia.comment = ""
                        # We might also need to adjust leading whitespace/newlines if the
                        # original template relied on the comment marker for indentation,
                        # but tomlkit usually handles this on dump. Let's try without first.

            else:
                # Key exists in defaults but not in template section - add it
                logger.debug(f"Adding missing key '{key}' to section '{config_section_name}'")
                section_table.add(key, tomlkit.item(value))

        # 3. Dump the modified document back to a string
        # Ensure trailing newline for consistency
        output_string = tomlkit.dumps(doc)
        if not output_string.endswith('\n'):
             output_string += '\n'
        return output_string

    except (tomlkit.exceptions.ParseError, ValueError, Exception) as e:
        logger.error(f"❌ Lỗi khi xử lý template TOML với tomlkit: {e}")
        # Log template content snippet for debugging if it's a parse error
        if isinstance(e, tomlkit.exceptions.ParseError):
             context = template_string.splitlines()
             line_num = getattr(e, '_line', 0) # Attempt to get line number
             if line_num > 0 and line_num <= len(context):
                 logger.error(f"   Lỗi gần dòng {line_num}: {context[line_num-1]}")
        raise # Re-raise the exception