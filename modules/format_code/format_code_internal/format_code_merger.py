# Path: modules/format_code/format_code_internal/format_code_merger.py
import logging
from typing import Dict, Any, List, Set, Optional
import sys
from pathlib import Path


if not "PROJECT_ROOT" in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from utils.core import resolve_config_list, resolve_set_modification

from ..format_code_config import DEFAULT_EXTENSIONS, DEFAULT_IGNORE


__all__ = ["merge_format_code_configs"]


def merge_format_code_configs(
    logger: logging.Logger,
    cli_extensions: Optional[str],
    cli_ignore: Optional[str],
    file_config_data: Dict[str, Any],
) -> Dict[str, Any]:

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

    final_ignore_list = resolve_config_list(
        cli_str_value=cli_ignore,
        file_list_value=file_config_data.get("ignore"),
        default_set_value=DEFAULT_IGNORE,
    )
    logger.debug(f"Danh sách 'ignore' cuối cùng: {final_ignore_list}")

    return {
        "final_extensions_list": final_extensions_list,
        "final_ignore_list": final_ignore_list,
    }
