# Path: utils/cli/config_writer_project.py
"""
Handles writing/updating a specific section within the project's main
configuration file (e.g., .project.toml) using tomlkit to preserve formatting.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import tomlkit
except ImportError:
    tomlkit = None

# Import UI helpers and logging utils
from .ui_helpers import prompt_config_overwrite
from utils.logging_config import log_success

__all__ = ["write_project_config_section"]


def write_project_config_section(
    logger: logging.Logger,
    config_file_path: Path,
    config_section_name: str,
    # Receive the already generated section content string
    new_section_content_string: str,
) -> Optional[Path]:
    """
    Handles I/O logic for 'project' scope using tomlkit.
    Parses the generated section string to get a TOML object with comments.
    Returns the path if written, None if cancelled.
    """
    if tomlkit is None:
        # This check should ideally be in the orchestrator, but double-check here.
        logger.error("❌ Thiếu thư viện 'tomlkit'. Không thể cập nhật file project.")
        raise ImportError("Thư viện 'tomlkit' không được cài đặt.")

    should_write = True
    try:
        # 1. Read the main project file using tomlkit
        content = config_file_path.read_text(encoding='utf-8') if config_file_path.exists() else ""
        main_doc = tomlkit.parse(content)

        # 2. Check if section exists and prompt if needed
        section_existed = config_section_name in main_doc
        if section_existed:
            should_write = prompt_config_overwrite(
                logger, config_file_path, f"Section [{config_section_name}]"
            )

        if should_write is None:
            return None # User cancelled

        if should_write:
            # 3. Parse the generated section string to get a TOML Table object
            try:
                parsed_section_doc = tomlkit.parse(new_section_content_string)
                if config_section_name not in parsed_section_doc:
                     raise ValueError(
                         f"Generated content unexpectedly missing section [{config_section_name}] after parsing."
                     )
                new_section_object = parsed_section_doc[config_section_name]
            except (tomlkit.exceptions.ParseError, ValueError, Exception) as e:
                 logger.error(f"❌ Lỗi khi phân tích nội dung section đã tạo: {e}")
                 raise # Re-raise

            # 4. Assign the new Table object (with comments) to the main doc
            main_doc[config_section_name] = new_section_object

            # 5. Write back the main document
            with config_file_path.open('w', encoding='utf-8') as f:
                tomlkit.dump(main_doc, f)

            log_success(logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.")

    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi cập nhật file '{config_file_path.name}': {e}")
        raise
    except (tomlkit.exceptions.ParseError, tomlkit.exceptions.ConvertError, Exception) as e:
        # Catch potential errors during parsing or dumping
        logger.error(f"❌ Lỗi không mong muốn khi cập nhật TOML (tomlkit): {e}")
        raise

    return config_file_path