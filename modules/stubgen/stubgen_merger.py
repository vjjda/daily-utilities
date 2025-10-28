# Path: modules/stubgen/stubgen_merger.py
"""
Configuration Merging logic for the Stub Generator (sgen) module.
(Internal module, imported by stubgen_core.py)
"""

import logging
from typing import Dict, Any, List, Optional

# Import utils
from utils.core import (
    resolve_config_value, 
    resolve_config_list, 
    parse_comma_list
)

# Import config defaults
from .stubgen_config import (
    DEFAULT_IGNORE, 
    DEFAULT_RESTRICT, 
    DEFAULT_INCLUDE,
    DYNAMIC_IMPORT_INDICATORS,
    AST_MODULE_LIST_NAME,
    AST_ALL_LIST_NAME
)

__all__ = ["merge_stubgen_configs"]


def merge_stubgen_configs(
    logger: logging.Logger,
    cli_config: Dict[str, Optional[str]], 
    file_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Hợp nhất cấu hình từ CLI và File, trả về một dict chứa các giá trị "final".
    (Hàm này được chuyển từ stubgen_core.py)
    """
    
    # 2.1. Ignore (Âm)
    final_ignore_list = resolve_config_list(
        cli_str_value=cli_config.get('ignore'),
        file_list_value=file_config.get('ignore'), 
        default_set_value=DEFAULT_IGNORE
    )
    
    # 2.2. Restrict (Scan Roots)
    cli_restrict_str = cli_config.get('restrict')
    final_restrict_list: List[str]
    if cli_restrict_str is not None:
        final_restrict_list = list(parse_comma_list(cli_restrict_str))
        logger.debug("Sử dụng danh sách 'restrict' từ CLI.")
    elif file_config.get('restrict') is not None:
        final_restrict_list = file_config['restrict']
        logger.debug("Sử dụng danh sách 'restrict' từ file config.")
    else:
        final_restrict_list = DEFAULT_RESTRICT 
        logger.debug("Sử dụng danh sách 'restrict' (DEFAULT_RESTRICT) mặc định.")

    # 2.3. Include (Dương)
    default_include_set = DEFAULT_INCLUDE if DEFAULT_INCLUDE is not None else set()
    final_include_list = resolve_config_list(
        cli_str_value=cli_config.get('include'),
        file_list_value=file_config.get('include'),
        default_set_value=default_include_set
    )
    
    if final_include_list:
        logger.debug(f"Danh sách 'include' cuối cùng (đã merge): {final_include_list}")
    else:
        logger.debug("Không áp dụng bộ lọc 'include'.")

    # 2.4. AST/Dynamic Configs
    final_indicators = resolve_config_value(
        cli_value=None, 
        file_value=file_config.get('dynamic_import_indicators'),
        default_value=DYNAMIC_IMPORT_INDICATORS
    )
    final_module_list_name = resolve_config_value(
        cli_value=None,
        file_value=file_config.get('ast_module_list_name'),
        default_value=AST_MODULE_LIST_NAME
    )
    final_all_list_name = resolve_config_value(
        cli_value=None,
        file_value=file_config.get('ast_all_list_name'),
        default_value=AST_ALL_LIST_NAME
    )

    return {
        "ignore_list": final_ignore_list,
        "restrict_list": final_restrict_list,
        "include_list": final_include_list,
        "indicators": final_indicators,
        "module_list_name": final_module_list_name,
        "all_list_name": final_all_list_name
    }