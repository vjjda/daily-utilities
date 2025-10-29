# Path: modules/pack_code/pack_code_resolver.py
"""
Logic xác định đường dẫn và bộ lọc cho pack_code.
(Module nội bộ, được import bởi pack_code_core)
"""

import logging
from pathlib import Path
# THÊM Tuple
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

from .pack_code_config import (
    DEFAULT_EXTENSIONS, DEFAULT_IGNORE, DEFAULT_START_PATH,
    DEFAULT_CLEAN_EXTENSIONS, # <-- THÊM IMPORT
    DEFAULT_OUTPUT_DIR
)

__all__ = ["resolve_start_and_scan_paths", "resolve_filters", "resolve_output_path"]


# ... (resolve_start_and_scan_paths không đổi) ...
def resolve_start_and_scan_paths(
    logger: logging.Logger,
    start_path_from_cli: Optional[Path],
) -> Tuple[Path, Path]:
    start_path: Path
    if start_path_from_cli:
        start_path = start_path_from_cli
        logger.debug(f"Sử dụng đường dẫn bắt đầu từ CLI: {start_path.as_posix()}")
    else:
        start_path = Path(DEFAULT_START_PATH).expanduser().resolve()
        logger.debug(f"Sử dụng đường dẫn bắt đầu mặc định: {start_path.as_posix()}")
    scan_root: Path
    if start_path.is_file():
        scan_root = find_git_root(start_path.parent) or start_path.parent
    else:
        effective_start_dir = start_path if start_path.exists() else Path.cwd().resolve()
        scan_root = find_git_root(effective_start_dir) or effective_start_dir
    if not start_path.exists():
         logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path.as_posix()}")
         raise FileNotFoundError(f"Đường dẫn bắt đầu không tồn tại: {start_path.as_posix()}")
    logger.debug(f"Gốc quét (cho quy tắc .gitignore): {scan_root.as_posix()}")
    logger.debug(f"Đường dẫn bắt đầu quét: {start_path.as_posix()}")
    return start_path, scan_root


def resolve_filters(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    scan_root: Path,
# SỬA: Kiểu trả về bao gồm clean_extensions_set
) -> Tuple[Set[str], Optional['pathspec.PathSpec'], Set[Path], Set[str]]:
    """
    Hợp nhất các cấu hình filter (extensions, ignore, submodules, clean_extensions).
    """

    # 1. Hợp nhất Extensions (để quét) (Không đổi)
    file_ext_list = file_config.get('extensions')
    default_ext_set = parse_comma_list(DEFAULT_EXTENSIONS)
    tentative_extensions: Set[str]
    if file_ext_list is not None:
        tentative_extensions = set(file_ext_list)
        logger.debug("Sử dụng 'extensions' từ file config làm cơ sở.")
    else:
        tentative_extensions = default_ext_set
        logger.debug("Sử dụng 'extensions' mặc định làm cơ sở.")
    ext_filter_set = resolve_set_modification(
        tentative_extensions, cli_args.get("extensions")
    )
    logger.debug(f"Set 'extensions' cuối cùng (để quét): {sorted(list(ext_filter_set))}")

    # 2. Hợp nhất Ignore (Không đổi)
    default_ignore_set = parse_comma_list(DEFAULT_IGNORE)
    config_cli_ignore_list = resolve_config_list(
        cli_str_value=cli_args.get("ignore"),
        file_list_value=file_config.get('ignore'),
        default_set_value=default_ignore_set
    )
    gitignore_patterns: List[str] = []
    if not cli_args.get("no_gitignore", False):
        gitignore_patterns = parse_gitignore(scan_root)
        if gitignore_patterns: logger.debug(f"Đã tải {len(gitignore_patterns)} quy tắc từ .gitignore")
        else: logger.debug("Không tìm thấy .gitignore hoặc không thể đọc.")
    else:
        logger.info("Bỏ qua .gitignore do cờ --no-gitignore.")
    all_ignore_patterns_list: List[str] = config_cli_ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)
    logger.debug(f"Tổng cộng {len(all_ignore_patterns_list)} quy tắc ignore đã biên dịch.")

    # 3. Lấy đường dẫn Submodules (Không đổi)
    submodule_paths = get_submodule_paths(scan_root, logger)
    if submodule_paths: logger.debug(f"Tìm thấy {len(submodule_paths)} submodule. Sẽ bỏ qua nội dung của chúng.")

    # 4. THÊM MỚI: Hợp nhất Clean Extensions
    # Logic đơn giản: File config ghi đè Default. CLI chỉ bật/tắt tính năng.
    file_clean_ext_list = file_config.get('clean_extensions') # Có thể là List[str] hoặc None
    clean_extensions_set: Set[str]
    if file_clean_ext_list is not None:
        clean_extensions_set = set(file_clean_ext_list)
        logger.debug(f"Sử dụng 'clean_extensions' từ file config: {sorted(list(clean_extensions_set))}")
    else:
        clean_extensions_set = DEFAULT_CLEAN_EXTENSIONS
        logger.debug(f"Sử dụng 'clean_extensions' mặc định: {sorted(list(clean_extensions_set))}")

    # SỬA: Trả về clean_extensions_set
    return ext_filter_set, ignore_spec, submodule_paths, clean_extensions_set

# ... (resolve_output_path không đổi) ...
def resolve_output_path(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    start_path: Path,
) -> Optional[Path]:
    if cli_args.get("stdout", False) or cli_args.get("dry_run", False):
        return None
    output_path_from_cli: Optional[Path] = cli_args.get("output")
    if output_path_from_cli:
        logger.debug(f"Sử dụng đường dẫn output từ CLI: {output_path_from_cli.as_posix()}")
        return output_path_from_cli
    default_output_dir_str = resolve_config_value(
        cli_value=None,
        file_value=file_config.get("output_dir"),
        default_value=DEFAULT_OUTPUT_DIR
    )
    default_output_dir_path = Path(default_output_dir_str)
    start_name = start_path.stem if start_path.is_file() else start_path.name
    final_output_path = default_output_dir_path / f"{start_name}_context.txt"
    logger.debug(f"Sử dụng đường dẫn output mặc định (chưa expand): {final_output_path.as_posix()}")
    return final_output_path