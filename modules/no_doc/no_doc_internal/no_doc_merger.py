# Path: modules/no_doc/no_doc_internal/no_doc_merger.py
import logging
from typing import Dict, Any, List, Set, Optional
import sys
from pathlib import Path

if not "PROJECT_ROOT" in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from utils.core import resolve_config_list, resolve_set_modification

# SỬA: Import thêm
from ..no_doc_config import (
    DEFAULT_EXTENSIONS, 
    DEFAULT_IGNORE, 
    DEFAULT_FORMAT_EXTENSIONS
)

__all__ = ["merge_ndoc_configs"]


def merge_ndoc_configs(
    logger: logging.Logger,
    cli_extensions: Optional[str],
    cli_ignore: Optional[str],
    file_config_data: Dict[str, Any],
) -> Dict[str, Any]:

    # 1. Hợp nhất Cấu hình 'extensions'
    file_extensions_value: Optional[List[str]] = file_config_data.get("extensions")
    default_ext_set: Set[str] = DEFAULT_EXTENSIONS
    tentative_extensions: Set[str]
    if file_extensions_value is not None:
        tentative_extensions = set(file_extensions_value)
    else:
        tentative_extensions = default_ext_set
        
    final_extensions_set = resolve_set_modification(
        tentative_set=tentative_extensions, cli_string=cli_extensions
    )
    final_extensions_list = sorted(list(final_extensions_set))
    logger.debug(f"Danh sách 'extensions' cuối cùng để quét: {final_extensions_list}")

    # 2. Hợp nhất Cấu hình 'ignore'
    final_ignore_list = resolve_config_list(
        cli_str_value=cli_ignore,
        file_list_value=file_config_data.get("ignore"),
        default_set_value=DEFAULT_IGNORE,
    )
    logger.debug(f"Danh sách 'ignore' cuối cùng: {final_ignore_list}")
    
    # 3. SỬA: Hợp nhất Cấu hình 'format_extensions'
    file_format_ext_list = file_config_data.get("format_extensions")
    default_format_ext_set = DEFAULT_FORMAT_EXTENSIONS
    
    format_extensions_set: Set[str]
    if file_format_ext_list is not None:
        format_extensions_set = set(file_format_ext_list)
        logger.debug("Sử dụng 'format_extensions' từ file config.")
    else:
        format_extensions_set = default_format_ext_set
        logger.debug("Sử dụng 'format_extensions' mặc định.")
        
    logger.debug(
        f"Set 'format_extensions' cuối cùng (để định dạng): {sorted(list(format_extensions_set))}"
    )

    return {
        "final_extensions_list": final_extensions_list,
        "final_ignore_list": final_ignore_list,
        "final_format_extensions_set": format_extensions_set, # SỬA: Thêm
    }