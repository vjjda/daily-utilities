# Path: modules/check_path/check_path_merger.py
"""
Configuration Merging logic for the Path Checker (cpath) module.
(Internal module, imported by check_path_core.py)
"""

import logging
from typing import Dict, Any, List, Set, Optional

from utils.core import (
    resolve_config_list,
    parse_comma_list,
    resolve_set_modification
)
from .check_path_config import (
    DEFAULT_EXTENSIONS,
    DEFAULT_IGNORE
)

__all__ = ["merge_check_path_configs"]


def merge_check_path_configs(
    logger: logging.Logger,
    cli_extensions: Optional[str],
    cli_ignore: Optional[str],
    file_config_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Hợp nhất các nguồn cấu hình (CLI, File, Default) cho cpath.

    Logic hợp nhất:
    - extensions: Dùng `resolve_set_modification` (hỗ trợ +/-/~).
    - ignore: Dùng `resolve_config_list` (File GHI ĐÈ Default) + (CLI NỐI VÀO).

    Args:
        logger: Logger.
        cli_extensions: Chuỗi extensions thô từ CLI (ví dụ: "+py,~md").
        cli_ignore: Chuỗi ignore thô từ CLI (ví dụ: "*.log,build/").
        file_config_data: Dict cấu hình [cpath] đã load từ file.

    Returns:
        Một dict chứa các danh sách "final" đã được hợp nhất:
        {
            "final_extensions_list": List[str],
            "final_ignore_list": List[str]
        }
    """
    
    # --- 1. Hợp nhất Cấu hình 'extensions' ---
    file_extensions_value = file_config_data.get('extensions')
    
    file_ext_list: Optional[List[str]]
    if isinstance(file_extensions_value, str):
        # Hỗ trợ trường hợp file config dùng string thay vì list
        file_ext_list = list(parse_comma_list(file_extensions_value))
    else:
        file_ext_list = file_extensions_value # Giữ nguyên (List hoặc None)
        
    tentative_extensions: Set[str]
    if file_ext_list is not None:
        tentative_extensions = set(file_ext_list)
        logger.debug("Sử dụng danh sách 'extensions' từ file config làm cơ sở.")
    else:
        tentative_extensions = DEFAULT_EXTENSIONS
        logger.debug("Sử dụng danh sách 'extensions' mặc định làm cơ sở.")
    
    final_extensions_set = resolve_set_modification(
        tentative_set=tentative_extensions,
        cli_string=cli_extensions
    )
    
    if cli_extensions:
        logger.debug(f"Đã áp dụng logic CLI: '{cli_extensions}'. Set 'extensions' cuối cùng: {sorted(list(final_extensions_set))}")
    else:
        logger.debug(f"Set 'extensions' cuối cùng (không có CLI): {sorted(list(final_extensions_set))}")

    final_extensions_list = sorted(list(final_extensions_set))

    # --- 2. Hợp nhất Cấu hình 'ignore' ---
    final_ignore_list = resolve_config_list(
        cli_str_value=cli_ignore,
        file_list_value=file_config_data.get('ignore'), # Đây là List[str] hoặc None
        default_set_value=DEFAULT_IGNORE
    )
    logger.debug(f"Danh sách 'ignore' cuối cùng (đã merge, giữ trật tự): {final_ignore_list}")

    return {
        "final_extensions_list": final_extensions_list,
        "final_ignore_list": final_ignore_list
    }