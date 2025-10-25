# Path: modules/path_checker/path_checker_loader.py

"""
Tiện ích tải file cho module Path Checker (cpath).
(Chịu trách nhiệm cho mọi hoạt động I/O đọc)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

try:
    import tomllib 
except ImportError:
    try:
        import toml as tomllib # Fallback
    except ImportError:
        print("Lỗi: Cần 'tomli'. Chạy 'pip install tomli'", file=sys.stderr)
        tomllib = None

from .path_checker_config import (
    PROJECT_CONFIG_FILENAME, CONFIG_SECTION_NAME
)

__all__ = ["load_config_files"]


def load_config_files(
    start_dir: Path, 
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải file .project.toml và trích xuất section [cpath].
    """
    if tomllib is None:
        logger.error("❌ Thư viện 'tomli' (cho Python < 3.11) chưa được cài đặt.")
        return {} # Trả về config rỗng

    project_config_path = start_dir / PROJECT_CONFIG_FILENAME
    config_data: Dict[str, Any] = {}

    try:
        if project_config_path.exists():
            with open(project_config_path, 'rb') as f:
                config_data = tomllib.load(f)
            logger.debug(f"Đã tải cấu hình từ: {project_config_path.name}")
        else:
            logger.debug(f"Không tìm thấy file {PROJECT_CONFIG_FILENAME}.")
            
    except Exception as e:
        logger.warning(f"⚠️ Không thể đọc file cấu hình {PROJECT_CONFIG_FILENAME}: {e}")

    # Trả về section [cpath] hoặc dict rỗng nếu không có
    return config_data.get(CONFIG_SECTION_NAME, {})