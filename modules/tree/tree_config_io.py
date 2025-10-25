# Path: modules/tree/tree_config_io.py

"""
Logic thực thi cho các hoạt động File Config trong module Tree (ctree).
(Xử lý việc ghi file .tree.toml và .project.toml)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

import typer

# --- MODIFIED: Imports cho TOML ---
try:
    import tomllib 
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

try:
    import tomli_w # Thư viện để *ghi* TOML
except ImportError:
    print("Lỗi: Cần 'tomli-w'. Chạy 'pip install tomli-w'", file=sys.stderr)
    tomli_w = None
# --- END MODIFIED ---

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
    Ghi nội dung template cấu hình vào đường dẫn (dùng cho .tree.toml).
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log_msg = (
            f"Đã tạo thành công '{CONFIG_FILENAME}'." if not file_existed 
            else f"Đã ghi đè thành công '{CONFIG_FILENAME}'."
        )
        log_success(logger, log_msg)
    except IOError as e:
        logger.error(f"❌ Lỗi khi ghi file '{config_path}': {e}")
        raise 


def overwrite_or_append_project_config_section(
    config_path: Path, 
    new_section_content_str: str, # Đây là string TOML (ví dụ: "key = val")
    logger: logging.Logger
) -> None:
    """
    Đọc file .project.toml, ghi đè section [tree] nếu tồn tại 
    (và được xác nhận), hoặc nối thêm section [tree] vào.
    """
    if tomllib is None or tomli_w is None:
        logger.error("❌ Thiếu thư viện 'tomli' hoặc 'tomli-w'. Không thể ghi .project.toml.")
        raise typer.Exit(code=1)

    # 1. Đọc config hiện tại (nếu có)
    config_data: Dict[str, Any] = {}
    file_existed = config_path.exists()
    
    if file_existed:
        try:
            with open(config_path, 'rb') as f:
                config_data = tomllib.load(f)
            logger.debug(f"Đã đọc file config dự án: {config_path.name}")
        except Exception as e:
            logger.error(f"❌ Lỗi đọc file config dự án: {e}")
            raise typer.Exit(code=1)
    
    # 2. Phân tích nội dung section mới (từ template)
    try:
        # Chúng ta parse string (ví dụ: "level = 5\nignore = []")
        # bằng cách thêm header section tạm thời
        full_toml_string = f"[{CONFIG_SECTION_NAME}]\n{new_section_content_str}"
        new_data = tomllib.loads(full_toml_string)
        new_tree_section_dict = new_data.get(CONFIG_SECTION_NAME, {})
        
        if not new_tree_section_dict:
             raise ValueError("Nội dung section mới bị rỗng.")
             
    except Exception as e:
        logger.error(f"❌ Lỗi nội bộ: Không thể parse nội dung section [tree] mới: {e}")
        raise typer.Exit(code=1)

    # 3. Xử lý logic overwrite/append
    if CONFIG_SECTION_NAME in config_data:
        logger.warning(f"⚠️ Section [{CONFIG_SECTION_NAME}] đã tồn tại trong '{PROJECT_CONFIG_FILENAME}'.")
        try:
            should_overwrite = typer.confirm("   Ghi đè section hiện tại?", abort=True)
        except typer.Abort:
            logger.warning("Hoạt động bị hủy bởi người dùng.")
            raise typer.Exit(code=0)
            
        if not should_overwrite:
            logger.info("Section không bị ghi đè. Đang thoát.")
            raise typer.Exit(code=0)
        
        logger.debug("Đang ghi đè section [tree]...")
    else:
        logger.debug("Đang thêm mới section [tree]...")

    # 4. Thêm/Cập nhật section vào config data
    config_data[CONFIG_SECTION_NAME] = new_tree_section_dict

    # 5. Ghi config data trở lại file (dùng 'wb' cho tomli_w)
    try:
        with open(config_path, 'wb') as f:
            tomli_w.dump(config_data, f)
            
        log_msg = (
            f"✅ Đã tạo thành công '{PROJECT_CONFIG_FILENAME}' với section [{CONFIG_SECTION_NAME}]." if not file_existed
            else f"✅ Đã cập nhật thành công '{PROJECT_CONFIG_FILENAME}'."
        )
        log_success(logger, log_msg)
        
    except IOError as e:
        logger.error(f"❌ Lỗi khi ghi file config dự án: {e}")
        raise