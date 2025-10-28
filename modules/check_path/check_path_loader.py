# Path: modules/check_path/check_path_loader.py

"""
File Loading logic for the Path Checker (cpath) module.
(Responsible for all config read I/O)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

try:
    from utils.core import load_and_merge_configs
except ImportError:
    print("Lỗi: Không thể import utils.core. Vui lòng chạy từ gốc dự án.", file=sys.stderr)
    sys.exit(1)


from .check_path_config import (
    PROJECT_CONFIG_FILENAME, 
    CONFIG_SECTION_NAME,
    CONFIG_FILENAME
)

__all__ = ["load_config_files"]


def load_config_files(
    start_dir: Path, 
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải và hợp nhất cấu hình từ .project.toml và .cpath.toml.
    
    Sử dụng logic chung từ `utils.core` để tìm `PROJECT_CONFIG_FILENAME`
    và `CONFIG_FILENAME`, sau đó trích xuất section `CONFIG_SECTION_NAME`.
    
    Args:
        start_dir: Thư mục bắt đầu quét config.
        logger: Logger để ghi log.

    Returns:
        Một dict chứa cấu hình [cpath] đã được hợp nhất (local ưu tiên hơn project).
    """
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME
    )