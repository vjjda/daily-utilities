# Path: modules/pack_code/pack_code_loader.py

"""
File Loading logic for pack_code.
(Responsible for reading config files and source file content)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from utils.core import load_and_merge_configs
except ImportError:
    print("Lỗi: Không thể import utils.core.", file=sys.stderr)
    sys.exit(1)

from .pack_code_config import (
    PROJECT_CONFIG_FILENAME,
    CONFIG_FILENAME,
    CONFIG_SECTION_NAME
)

__all__ = ["load_files_content", "load_config_files"]

def load_config_files(
    start_dir: Path,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải và hợp nhất cấu hình từ .project.toml và .pcode.toml.

    Sử dụng logic chung từ `utils.core` để tìm `PROJECT_CONFIG_FILENAME`
    và `CONFIG_FILENAME`, sau đó trích xuất section `CONFIG_SECTION_NAME`.

    Args:
        start_dir: Thư mục bắt đầu quét config.
        logger: Logger để ghi log.

    Returns:
        Một dict chứa cấu hình [pcode] đã được hợp nhất (local ưu tiên hơn project).
    """
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME
    )

def load_files_content(
    logger: logging.Logger,
    file_paths: List[Path],
    base_dir: Path
) -> Dict[Path, str]:
    """
    Tải nội dung text của tất cả các file được yêu cầu.

    Bỏ qua các file không thể đọc (ví dụ: binary, encoding lỗi)
    và ghi log cảnh báo.

    Args:
        logger: Logger.
        file_paths: Danh sách các đối tượng Path đến file cần đọc.
        base_dir: Thư mục gốc (để tính đường dẫn tương đối khi log lỗi).

    Returns:
        Một dict ánh xạ từ Path đến nội dung (str) của file.
    """
    logger.info(f"Đang đọc nội dung từ {len(file_paths)} file...")
    content_map: Dict[Path, str] = {}
    skipped_count = 0

    for file_path in file_paths:
        try:
            # Đọc nội dung file với encoding utf-8
            content = file_path.read_text(encoding='utf-8')
            content_map[file_path] = content
        except UnicodeDecodeError:
            logger.warning(f"   -> Bỏ qua (lỗi encoding): {file_path.relative_to(base_dir).as_posix()}") #
            skipped_count += 1
        except IOError as e:
            logger.warning(f"   -> Bỏ qua (lỗi I/O: {e}): {file_path.relative_to(base_dir).as_posix()}") #
            skipped_count += 1
        except Exception as e:
            logger.warning(f"   -> Bỏ qua (lỗi không xác định: {e}): {file_path.relative_to(base_dir).as_posix()}") #
            skipped_count += 1

    if skipped_count > 0:
        logger.warning(f"Đã bỏ qua tổng cộng {skipped_count} file không thể đọc.")

    return content_map