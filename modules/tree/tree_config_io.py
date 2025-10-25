# Path: modules/tree/tree_config_io.py

"""
Execution logic for Config File operations in the Tree (ctree) module.
(Handles writing to .tree.ini and complex manipulation of .project.ini)
"""

import logging
import configparser
from pathlib import Path
from typing import Dict, Any, List

import typer

from utils.logging_config import log_success
from .tree_config import (
    CONFIG_FILENAME, PROJECT_CONFIG_FILENAME, CONFIG_SECTION_NAME
)

__all__ = [
    "write_config_file",
    "overwrite_or_append_project_config_section"
]


def write_config_file(
    config_path: Path, 
    content: str, 
    logger: logging.Logger,
    file_existed: bool
) -> None:
    """
    Writes the config template content to the specified path (used for .tree.ini).
    (Moved from tree_executor.py)
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log_msg = (
            f"Successfully created '{CONFIG_FILENAME}'." if not file_existed 
            else f"Successfully overwrote '{CONFIG_FILENAME}'."
        )
        log_success(logger, log_msg)
    except IOError as e:
        logger.error(f"❌ Failed to write file '{config_path}': {e}")
        # Re-raise to be caught by the entry point
        raise 


def overwrite_or_append_project_config_section(
    config_path: Path, 
    new_section_content: str, 
    logger: logging.Logger
) -> None:
    """
    Reads the .project.ini file, overwrites the [tree] section if it exists 
    and is confirmed by the user, or appends it otherwise.
    (This is the new complex logic for 'ctree init project').
    """
    
    # 1. Khởi tạo và đọc config hiện tại
    config = configparser.ConfigParser(allow_no_value=True)
    file_existed = config_path.exists()
    
    if file_existed:
        try:
            config.read(config_path)
            logger.debug(f"Read existing project config from: {config_path.name}")
        except Exception as e:
            logger.error(f"❌ Error reading project config file: {e}")
            raise typer.Exit(code=1)
    
    # 2. Phân tích nội dung section mới (từ template)
    # Tạm thời tạo một configparser từ nội dung mới để lấy [section]
    new_config = configparser.ConfigParser(allow_no_value=True)
    try:
        # Giả định new_section_content là một chuỗi INI hợp lệ
        new_config.read_string(f"[{CONFIG_SECTION_NAME}]\n{new_section_content}")
    except Exception as e:
        logger.error(f"❌ Internal Error: Cannot parse new tree section content: {e}")
        raise typer.Exit(code=1)

    # 3. Xử lý logic overwrite/append
    if CONFIG_SECTION_NAME in config:
        # Section đã tồn tại, hỏi người dùng
        logger.warning(f"⚠️ Section [{CONFIG_SECTION_NAME}] already exists in '{PROJECT_CONFIG_FILENAME}'.")
        try:
            should_overwrite = typer.confirm("   Overwrite this existing section?", abort=True)
        except typer.Abort:
            logger.warning("Operation cancelled by user.")
            raise typer.Exit(code=0)
            
        if not should_overwrite:
            logger.info("Section was not overwritten. Exiting.")
            raise typer.Exit(code=0)
            
        # Xóa section cũ và thay thế bằng section mới
        config.remove_section(CONFIG_SECTION_NAME)
        
    else:
        # Section chưa tồn tại, append.
        pass

    # 4. Thêm section mới vào config object
    config.add_section(CONFIG_SECTION_NAME)
    for option, value in new_config.items(CONFIG_SECTION_NAME):
        # Value sẽ là None cho các option không có giá trị
        config.set(CONFIG_SECTION_NAME, option, value)

    # 5. Ghi config object trở lại file
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
            
        log_msg = (
            f"✅ Successfully created '{PROJECT_CONFIG_FILENAME}' with section [{CONFIG_SECTION_NAME}]." if not file_existed
            else f"✅ Successfully updated '{PROJECT_CONFIG_FILENAME}'."
        )
        log_success(logger, log_msg)
        
    except IOError as e:
        logger.error(f"❌ Failed to write project config file: {e}")
        raise

# ... (Hết file)