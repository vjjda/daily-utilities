# Path: utils/cli/config_init/config_writer_project.py
"""
Handles writing/updating a specific section within the project's main
configuration file (e.g., .project.toml) using tomlkit to preserve formatting.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import tomlkit
    # --- FIX: Import exceptions directly ---
    from tomlkit import ParseError, ConvertError
    # --- END FIX ---
except ImportError:
    tomlkit = None
    # Define dummy exceptions if tomlkit is not available to avoid NameError
    class ParseError(Exception): pass
    class ConvertError(Exception): pass


# Import UI helpers and logging utils from one level up
from ..ui_helpers import prompt_config_overwrite
from utils.logging_config import log_success

__all__ = ["write_project_config_section"]


def write_project_config_section(
    logger: logging.Logger,
    config_file_path: Path,
    config_section_name: str,
    new_section_content_string: str,
) -> Optional[Path]:
    """
    Handles I/O logic for 'project' scope using tomlkit.
    Parses the generated section string to get a TOML object with comments.
    Returns the path if written, None if cancelled.
    """
    if tomlkit is None:
        logger.error("❌ Thiếu thư viện 'tomlkit'. Không thể cập nhật file project.")
        raise ImportError("Thư viện 'tomlkit' không được cài đặt.")

    should_write = True
    try:
        content = config_file_path.read_text(encoding='utf-8') if config_file_path.exists() else ""
        main_doc = tomlkit.parse(content)

        section_existed = config_section_name in main_doc
        if section_existed:
            should_write = prompt_config_overwrite(
                logger, config_file_path, f"Section [{config_section_name}]"
            )

        if should_write is None:
            return None # User cancelled

        if should_write:
            try:
                # ParseError can happen here
                parsed_section_doc = tomlkit.parse(new_section_content_string)
                if config_section_name not in parsed_section_doc:
                     raise ValueError(
                         f"Generated content unexpectedly missing section [{config_section_name}] after parsing."
                     )
                new_section_object = parsed_section_doc[config_section_name]
            # --- FIX: Use direct exception names ---
            except (ParseError, ValueError, Exception) as e:
            # --- END FIX ---
                 logger.error(f"❌ Lỗi khi phân tích nội dung section đã tạo: {e}")
                 raise # Re-raise

            main_doc[config_section_name] = new_section_object

            # ConvertError can happen during dump if data is invalid
            with config_file_path.open('w', encoding='utf-8') as f:
                tomlkit.dump(main_doc, f)

            log_success(logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.")

    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi cập nhật file '{config_file_path.name}': {e}")
        raise
    # --- FIX: Use direct exception names ---
    except (ParseError, ConvertError, Exception) as e:
    # --- END FIX ---
        logger.error(f"❌ Lỗi không mong muốn khi cập nhật TOML (tomlkit): {e}")
        raise

    return config_file_path