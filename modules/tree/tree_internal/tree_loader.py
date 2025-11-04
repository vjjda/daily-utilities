# Path: modules/tree/tree_internal/tree_loader.py
import logging
import sys
from pathlib import Path
from typing import Any, Dict

try:
    from utils.core import load_and_merge_configs
except ImportError:
    print(
        "Lỗi: Không thể import utils.core. Vui lòng chạy từ gốc dự án.", file=sys.stderr
    )
    sys.exit(1)


from ..tree_config import CONFIG_FILENAME, CONFIG_SECTION_NAME, PROJECT_CONFIG_FILENAME

__all__ = ["load_config_files"]


def load_config_files(start_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME,
    )
