# Path: modules/no_doc/no_doc_merger.py
"""
Configuration Merging logic for the no_doc module.
(Internal module, imported by no_doc_core)
"""

import logging
from typing import Dict, Any, List, Set, Optional

# --- KHẮC PHỤC LỖI PYRIGHT/PYLANCE ---
import sys
from pathlib import Path
# -------------------------------------

# Thiết lập sys.path
if not 'PROJECT_ROOT' in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from utils.core import (
    resolve_config_list,
    resolve_set_modification
)
from .no_doc_config import (
    # SỬA: Import lại DEFAULT_EXTENSIONS và DEFAULT_IGNORE
    DEFAULT_EXTENSIONS,
    DEFAULT_IGNORE
)

__all__ = ["merge_ndoc_configs"]


def merge_ndoc_configs(
    logger: logging.Logger,
    cli_extensions: Optional[str],
    cli_ignore: Optional[str],
    file_config_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Hợp nhất các nguồn cấu hình (CLI, File, Default) cho ndoc.
    """

    # 1. Hợp nhất Cấu hình 'extensions' (hỗ trợ +/-/~)
    file_extensions_value: Optional[List[str]] = file_config_data.get('extensions')

    # SỬA: Sử dụng DEFAULT_EXTENSIONS làm default_ext_set
    default_ext_set: Set[str] = DEFAULT_EXTENSIONS

    tentative_extensions: Set[str]
    # Logic xác định tentative_extensions từ file_config hoặc default giữ nguyên
    if file_extensions_value is not None:
        tentative_extensions = set(file_extensions_value)
        logger.debug("Sử dụng danh sách 'extensions' từ file config làm cơ sở.")
    else:
        # Nếu không, dùng DEFAULT_EXTENSIONS làm cơ sở
        tentative_extensions = default_ext_set
        logger.debug("Sử dụng danh sách 'extensions' mặc định (từ config set) làm cơ sở.") # Sửa log message

    # Áp dụng logic CLI (+/-/~ hoặc ghi đè) vào tentative_extensions
    final_extensions_set = resolve_set_modification(
        tentative_set=tentative_extensions,
        cli_string=cli_extensions
    )
    # Kết quả cuối cùng là danh sách các đuôi file cần quét
    final_extensions_list = sorted(list(final_extensions_set))

    logger.debug(f"Danh sách 'extensions' cuối cùng để quét: {final_extensions_list}")

    # 2. Hợp nhất Cấu hình 'ignore' (Không đổi)
    final_ignore_list = resolve_config_list(
        cli_str_value=cli_ignore,
        file_list_value=file_config_data.get('ignore'),
        default_set_value=DEFAULT_IGNORE
    )
    logger.debug(f"Danh sách 'ignore' cuối cùng: {final_ignore_list}")

    return {
        "final_extensions_list": final_extensions_list,
        "final_ignore_list": final_ignore_list
    }