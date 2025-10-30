# Path: modules/forc/forc_internal/forc_loader.py
"""
File Loading logic for the forc module.
(Internal module, imported by forc_core)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Thiết lập sys.path
if not 'PROJECT_ROOT' in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

try:
    from utils.core import load_and_merge_configs
except ImportError as e:
    print(f"Lỗi: Không thể import utils.core: {e}. Vui lòng chạy từ gốc dự án.", file=sys.stderr)
    sys.exit(1)

# SỬA: Import config của forc
from ..forc_config import (
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
    Tải và hợp nhất cấu hình từ .project.toml và .forc.toml.
    """
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME
    )