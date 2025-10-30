# Path: modules/stubgen/stubgen_internal/stubgen_merger.py

import logging
from typing import Dict, Any, List, Optional

from utils.core import resolve_config_value, resolve_config_list, parse_comma_list


from ..stubgen_config import (
    DEFAULT_IGNORE,
    DEFAULT_INCLUDE,
    DYNAMIC_IMPORT_INDICATORS,
    AST_MODULE_LIST_NAME,
    AST_ALL_LIST_NAME,
)

__all__ = ["merge_stubgen_configs"]


def merge_stubgen_configs(
    logger: logging.Logger,
    cli_config: Dict[str, Optional[str]],
    file_config: Dict[str, Any],
) -> Dict[str, Any]:

    final_ignore_list = resolve_config_list(
        cli_str_value=cli_config.get("ignore"),
        file_list_value=file_config.get("ignore"),
        default_set_value=DEFAULT_IGNORE,
    )

    default_include_set = DEFAULT_INCLUDE if DEFAULT_INCLUDE is not None else set()
    final_include_list = resolve_config_list(
        cli_str_value=cli_config.get("include"),
        file_list_value=file_config.get("include"),
        default_set_value=default_include_set,
    )

    if final_include_list:
        logger.debug(f"Danh sách 'include' cuối cùng (đã merge): {final_include_list}")
    else:
        logger.debug("Không áp dụng bộ lọc 'include'.")

    final_indicators = resolve_config_value(
        cli_value=None,
        file_value=file_config.get("dynamic_import_indicators"),
        default_value=DYNAMIC_IMPORT_INDICATORS,
    )
    final_module_list_name = resolve_config_value(
        cli_value=None,
        file_value=file_config.get("ast_module_list_name"),
        default_value=AST_MODULE_LIST_NAME,
    )
    final_all_list_name = resolve_config_value(
        cli_value=None,
        file_value=file_config.get("ast_all_list_name"),
        default_value=AST_ALL_LIST_NAME,
    )

    return {
        "ignore_list": final_ignore_list,
        "include_list": final_include_list,
        "indicators": final_indicators,
        "module_list_name": final_module_list_name,
        "all_list_name": final_all_list_name,
    }