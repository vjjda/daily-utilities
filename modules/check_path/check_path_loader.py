# Path: modules/check_path/check_path_loader.py

"""
Tiện ích tải file cho module Path Checker (cpath).
(Chịu trách nhiệm cho mọi hoạt động I/O đọc)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List # <-- Thêm List

try:
    import tomllib 
except ImportError:
    # ... (fallback giữ nguyên)
    tomllib = None

from .check_path_config import (
    PROJECT_CONFIG_FILENAME, 
    CONFIG_SECTION_NAME,
    CONFIG_FILENAME # <-- MỚI: Import file config cục bộ
)

__all__ = ["load_config_files"]


def load_config_files(
    start_dir: Path, 
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải file .project.toml VÀ .cpath.toml,
    trích xuất và merge section [cpath].
    
    Ưu tiên: .cpath.toml (cục bộ) sẽ ghi đè .project.toml (dự án).
    """
    if tomllib is None:
        logger.error("❌ Thư viện 'tomli' (cho Python < 3.11) chưa được cài đặt.")
        return {} # Trả về config rỗng

    project_config_path = start_dir / PROJECT_CONFIG_FILENAME
    local_config_path = start_dir / CONFIG_FILENAME # <-- MỚI

    project_data: Dict[str, Any] = {}
    local_data: Dict[str, Any] = {} # <-- MỚI
    files_loaded: List[str] = [] # <-- MỚI

    try:
        if project_config_path.exists():
            with open(project_config_path, 'rb') as f:
                project_data = tomllib.load(f)
            files_loaded.append(project_config_path.name)
            
        # --- MỚI: Đọc file .cpath.toml ---
        if local_config_path.exists():
            with open(local_config_path, 'rb') as f:
                local_data = tomllib.load(f)
            files_loaded.append(local_config_path.name)
        # --- KẾT THÚC MỚI ---
            
    except Exception as e:
        logger.warning(f"⚠️ Không thể đọc file cấu hình: {e}")

    if files_loaded:
        logger.debug(f"Đã tải cấu hình từ: {files_loaded}")
    else:
        logger.debug(f"Không tìm thấy file config. Dùng mặc định.")


    # Lấy section [cpath] từ mỗi file
    project_cpath_section = project_data.get(CONFIG_SECTION_NAME, {})
    local_cpath_section = local_data.get(CONFIG_SECTION_NAME, {}) # <-- MỚI

    # Merge: local (cục bộ) sẽ ghi đè project (dự án)
    final_config_section = {**project_cpath_section, **local_cpath_section}
        
    return final_config_section