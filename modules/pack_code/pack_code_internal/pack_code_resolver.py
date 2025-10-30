# Path: modules/pack_code/pack_code_internal/pack_code_resolver.py
"""
Logic xác định đường dẫn và bộ lọc cho pack_code.
(Internal module, imported by pack_code_core)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING, Iterable, Tuple

if TYPE_CHECKING:
    import pathspec

from utils.core import (
    find_git_root,
    parse_gitignore,
    compile_spec_from_patterns,
    resolve_set_modification,
    get_submodule_paths,
    parse_comma_list,
    resolve_config_list,
    resolve_config_value
)

# SỬA: Import từ thư mục cha (..)
from ..pack_code_config import (
    DEFAULT_EXTENSIONS, DEFAULT_IGNORE, DEFAULT_START_PATH,
    DEFAULT_CLEAN_EXTENSIONS,
    DEFAULT_OUTPUT_DIR
)

__all__ = ["resolve_start_and_scan_paths", "resolve_filters", "resolve_output_path"]


def resolve_start_and_scan_paths(
    logger: logging.Logger,
    start_path_from_cli: Optional[Path],
) -> Tuple[Path, Path]:
    start_path: Path
    if start_path_from_cli:
        start_path = start_path_from_cli
    else:
        start_path = Path(DEFAULT_START_PATH).expanduser().resolve()
    scan_root: Path
    if start_path.is_file():
        scan_root = find_git_root(start_path.parent) or start_path.parent
    else:
        effective_start_dir = start_path if start_path.exists() else Path.cwd().resolve()
        scan_root = find_git_root(effective_start_dir) or effective_start_dir
    if not start_path.exists():
         raise FileNotFoundError(f"Đường dẫn bắt đầu không tồn tại: {start_path.as_posix()}")
    logger.debug(f"Gốc quét (cho quy tắc .gitignore): {scan_root.as_posix()}")
    logger.debug(f"Đường dẫn bắt đầu quét: {start_path.as_posix()}")
    return start_path, scan_root


def resolve_filters(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    scan_root: Path,
) -> Tuple[Set[str], Optional['pathspec.PathSpec'], Set[Path], Set[str]]:
    """
    Hợp nhất các cấu hình filter (extensions, ignore, submodules, clean_extensions).
    """

    # 1. Hợp nhất Extensions (để quét)
    file_ext_list = file_config.get('extensions')
    default_ext_set = parse_comma_list(DEFAULT_EXTENSIONS)
    tentative_extensions: Set[str]
    if file_ext_list is not None:
        tentative_extensions = set(file_ext_list)
    else:
        tentative_extensions = default_ext_set
    ext_filter_set = resolve_set_modification(
        tentative_extensions, cli_args.get("extensions") # String từ CLI -e
    )
    logger.debug(f"Set 'extensions' cuối cùng (để quét): {sorted(list(ext_filter_set))}")

    # 2. Hợp nhất Ignore
    default_ignore_set = parse_comma_list(DEFAULT_IGNORE)
    config_cli_ignore_list = resolve_config_list(
        cli_str_value=cli_args.get("ignore"), # String từ CLI -I
        file_list_value=file_config.get('ignore'),
        default_set_value=default_ignore_set
    )
    gitignore_patterns: List[str] = []
    if not cli_args.get("no_gitignore", False):
        gitignore_patterns = parse_gitignore(scan_root)
    all_ignore_patterns_list: List[str] = config_cli_ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)
    logger.debug(f"Tổng cộng {len(all_ignore_patterns_list)} quy tắc ignore đã biên dịch.")

    # 3. Lấy đường dẫn Submodules
    submodule_paths = get_submodule_paths(scan_root, logger)

    # 4. Hợp nhất Clean Extensions
    file_clean_ext_list = file_config.get('clean_extensions') # List[str] hoặc None
    default_clean_ext_set = DEFAULT_CLEAN_EXTENSIONS # Set[str]

    tentative_clean_extensions: Set[str]
    if file_clean_ext_list is not None:
        tentative_clean_extensions = set(file_clean_ext_list)
        logger.debug("Sử dụng 'clean_extensions' từ file config làm cơ sở.")
    else:
        tentative_clean_extensions = default_clean_ext_set
        logger.debug("Sử dụng 'clean_extensions' mặc định làm cơ sở.")

    clean_extensions_set = resolve_set_modification(
        tentative_set=tentative_clean_extensions,
        cli_string=cli_args.get("clean_extensions") # String từ CLI -x
    )
    logger.debug(f"Set 'clean_extensions' cuối cùng (để làm sạch): {sorted(list(clean_extensions_set))}")

    return ext_filter_set, ignore_spec, submodule_paths, clean_extensions_set


def resolve_output_path(
     logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    start_path: Path,
) -> Optional[Path]:
    if cli_args.get("stdout", False) or cli_args.get("dry_run", False): return None
    output_path_from_cli: Optional[Path] = cli_args.get("output")
    if output_path_from_cli: return output_path_from_cli
    default_output_dir_str = resolve_config_value(
        cli_value=None, file_value=file_config.get("output_dir"), default_value=DEFAULT_OUTPUT_DIR
    )
    default_output_dir_path = Path(default_output_dir_str)
    start_name = start_path.stem if start_path.is_file() else start_path.name
    final_output_path = default_output_dir_path / f"{start_name}_context.txt"
    logger.debug(f"Sử dụng đường dẫn output mặc định (chưa expand): {final_output_path.as_posix()}")
    return final_output_path