# Path: modules/format_code/format_code_internal/format_code_loader.py

import logging
import sys
from pathlib import Path
from typing import Dict, Any


if not "PROJECT_ROOT" in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

try:
    from utils.core import load_and_merge_configs
except ImportError as e:
    print(
        f"Lỗi: Không thể import utils.core: {e}. Vui lòng chạy từ gốc dự án.",
        file=sys.stderr,
    )
    sys.exit(1)


from ..format_code_config import (
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    CONFIG_FILENAME,
)

__all__ = ["load_config_files"]


def load_config_files(start_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME,
    )