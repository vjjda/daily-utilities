# Path: modules/tree/tree_loader.py

"""
Tiện ích tải file cho module Tree (ctree).
(Chịu trách nhiệm cho mọi hoạt động I/O đọc)
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# --- MODIFIED: Import helper chung ---
try:
    from utils.core import load_and_merge_configs
except ImportError:
    print("Lỗi: Không thể import utils.core. Vui lòng chạy từ gốc dự án.", file=sys.stderr)
    sys.exit(1)
# --- END MODIFIED ---

from .tree_config import (
    CONFIG_FILENAME, PROJECT_CONFIG_FILENAME, CONFIG_SECTION_NAME
)

__all__ = ["load_config_files", "load_config_template"]


def load_config_files(
    start_dir: Path, 
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải các file cấu hình .toml (.project.toml và .tree.toml).
    Nó merge section [tree] từ cả hai file, ưu tiên .tree.toml.
    
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


def load_config_template() -> str:
    """
    Đọc nội dung thô của file template .toml.
    """
    try:
        current_dir = Path(__file__).parent
        template_path = current_dir / "tree.toml.template"
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("LỖI NGHIÊM TRỌNG: Không tìm thấy 'tree.toml.template'.")
        return "# LỖI: File template bị thiếu."
    except Exception as e:
        print(f"LỖI NGHIÊM TRỌNG: Không thể đọc 'tree.toml.template': {e}")
        return "# LỖI: Không thể đọc file template."