# Path: modules/tree/tree_loader.py

"""
Tiện ích tải file cho module Tree (ctree).
(Chịu trách nhiệm cho mọi hoạt động I/O đọc)
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

try:
    from utils.core import load_and_merge_configs
except ImportError:
    print("Lỗi: Không thể import utils.core. Vui lòng chạy từ gốc dự án.", file=sys.stderr)
    sys.exit(1)

from .tree_config import (
    CONFIG_FILENAME, PROJECT_CONFIG_FILENAME, CONFIG_SECTION_NAME
)

# --- MODIFIED: Xóa load_config_template ---
__all__ = ["load_config_files"]
# --- END MODIFIED ---


def load_config_files(
    start_dir: Path, 
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải các file cấu hình .toml (.project.toml và .tree.toml).
    (Logic này đã được chuyển vào utils.core.load_and_merge_configs)
    """
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME
    )

# --- REMOVED: load_config_template ---
# (Hàm này đã bị xóa. utils.cli.config_writer sẽ
#  sử dụng 'load_text_template' chung của utils.core)
# --- END REMOVED ---