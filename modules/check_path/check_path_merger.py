# Path: modules/check_path/check_path_merger.py
import logging
from typing import Dict, Any, List, Set, Optional

from utils.core import resolve_config_list, parse_comma_list, resolve_set_modification
from .check_path_config import DEFAULT_EXTENSIONS, DEFAULT_IGNORE

__all__ = ["merge_check_path_configs"]


def merge_check_path_configs(
    logger: logging.Logger,
    cli_extensions: Optional[str],
    cli_ignore: Optional[str],
    file_config_data: Dict[str, Any],
) -> Dict[str, Any]:

    file_extensions_value = file_config_data.get("extensions")

    file_ext_list: Optional[List[str]]
    if isinstance(file_extensions_value, str):

        file_ext_list = list(parse_comma_list(file_extensions_value))
    else:
        file_ext_list = file_extensions_value

    tentative_extensions: Set[str]
    if file_ext_list is not None:
        tentative_extensions = set(file_ext_list)
        logger.debug("Sử dụng danh sách 'extensions' từ file config làm cơ sở.")
    else:
        tentative_extensions = DEFAULT_EXTENSIONS
        logger.debug("Sử dụng danh sách 'extensions' mặc định làm cơ sở.")

    final_extensions_set = resolve_set_modification(
        tentative_set=tentative_extensions, cli_string=cli_extensions
    )

    if cli_extensions:
        logger.debug(
            f"Đã áp dụng logic CLI: '{cli_extensions}'. Set 'extensions' cuối cùng: {sorted(list(final_extensions_set))}"
        )
    else:
        logger.debug(
            f"Set 'extensions' cuối cùng (không có CLI): {sorted(list(final_extensions_set))}"
        )

    final_extensions_list = sorted(list(final_extensions_set))

    final_ignore_list = resolve_config_list(
        cli_str_value=cli_ignore,
        file_list_value=file_config_data.get("ignore"),
        default_set_value=DEFAULT_IGNORE,
    )
    logger.debug(
        f"Danh sách 'ignore' cuối cùng (đã merge, giữ trật tự): {final_ignore_list}"
    )

    return {
        "final_extensions_list": final_extensions_list,
        "final_ignore_list": final_ignore_list,
    }