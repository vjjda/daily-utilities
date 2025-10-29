# Path: utils/cli/config_writer_local.py
"""
Handles writing the configuration content to a local config file (e.g., .<tool>.toml).
Overwrites the entire file.
"""

import logging
from pathlib import Path
from typing import Optional

# Import UI helpers and logging utils
from .ui_helpers import prompt_config_overwrite
from utils.logging_config import log_success

__all__ = ["write_local_config"]


def write_local_config(
    logger: logging.Logger,
    config_file_path: Path,
    content_from_template: str,
) -> Optional[Path]:
    """
    Handles I/O logic for 'local' scope.
    (Checks existence, prompts, overwrites file)
    Returns the path if written, None if cancelled.
    """
    file_existed = config_file_path.exists()
    should_write = True

    if file_existed:
        should_write = prompt_config_overwrite(
            logger, config_file_path, f"File '{config_file_path.name}'"
        )

    if should_write is None:
        return None # User cancelled

    if should_write:
        try:
            config_file_path.write_text(content_from_template, encoding="utf-8")
            log_msg = (
                f"Đã tạo thành công '{config_file_path.name}'." if not file_existed
                else f"Đã ghi đè thành công '{config_file_path.name}'."
            )
            log_success(logger, log_msg)
        except IOError as e:
            logger.error(f"❌ Lỗi I/O khi ghi file '{config_file_path.name}': {e}")
            raise # Re-raise for the orchestrator to catch

    return config_file_path