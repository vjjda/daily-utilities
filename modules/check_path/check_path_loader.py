# Path: modules/check_path/check_path_loader.py

"""
Tiện ích tải file cho module Path Checker (cpath).
(Chịu trách nhiệm cho mọi hoạt động I/O đọc)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# --- MODIFIED: Import helper chung ---
try:
    from utils.core import load_and_merge_configs
except ImportError:
    print("Lỗi: Không thể import utils.core. Vui lòng chạy từ gốc dự án.", file=sys.stderr)
    sys.exit(1)
# --- END MODIFIED ---


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
    Tải file .project.toml VÀ .cpath.toml,
    trích xuất và merge section [cpath].
    
    Ưu tiên: .cpath.toml (cục bộ) sẽ ghi đè .project.toml (dự án).
    
    (Logic này đã được chuyển vào utils.core.load_and_merge_configs)
    """
    
    # --- MODIFIED: Tái sử dụng logic chung ---
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME
    )
    # --- END MODIFIED ---