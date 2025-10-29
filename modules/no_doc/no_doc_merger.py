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
    # Fallback cho trường hợp chạy độc lập/test (nếu không có PROJECT_ROOT)
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    
from utils.core import (
    resolve_config_list,
    resolve_set_modification
)
from .no_doc_config import (
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
    
    Args:
        logger: Logger.
        cli_extensions: Chuỗi extensions thô từ CLI (ví dụ: "+py,~md").
        cli_ignore: Chuỗi ignore thô từ CLI (ví dụ: "*.log,build/").
        file_config_data: Dict cấu hình [ndoc] đã load từ file.
        
    Returns:
        Một dict chứa các danh sách "final" đã được hợp nhất.
    """
    
    # 1. Hợp nhất Cấu hình 'extensions' (hỗ trợ +/-/~)
    file_extensions_value: Optional[List[str]] = file_config_data.get('extensions')
        
    tentative_extensions: Set[str]
    if file_extensions_value is not None:
        tentative_extensions = set(file_extensions_value)
    else:
        tentative_extensions = DEFAULT_EXTENSIONS
    
    final_extensions_set = resolve_set_modification(
        tentative_set=tentative_extensions,
        cli_string=cli_extensions
    )
    final_extensions_list = sorted(list(final_extensions_set))
    
    logger.debug(f"Set 'extensions' cuối cùng: {final_extensions_list}")

    # 2. Hợp nhất Cấu hình 'ignore' (File GHI ĐÈ Default) + (CLI NỐI VÀO)
    final_ignore_list = resolve_config_list(
        cli_str_value=cli_ignore,
        file_list_value=file_config_data.get('ignore'), # Đây là List[str] hoặc None
        default_set_value=DEFAULT_IGNORE
    )
    logger.debug(f"Danh sách 'ignore' cuối cùng: {final_ignore_list}")

    return {
        "final_extensions_list": final_extensions_list,
        "final_ignore_list": final_ignore_list
    }