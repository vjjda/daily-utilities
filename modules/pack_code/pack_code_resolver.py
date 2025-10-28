# Path: modules/pack_code/pack_code_resolver.py
"""
Logic for resolving paths and filters for pack_code.
(Internal module, imported by pack_code_core)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING, Iterable, Tuple

# Import pathspec for type checking
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
    DEFAULT_OUTPUT_DIR
)

__all__ = ["resolve_start_and_scan_paths", "resolve_filters", "resolve_output_path"]


def resolve_start_and_scan_paths(
    logger: logging.Logger,
    start_path_from_cli: Optional[Path],
) -> Tuple[Path, Path]:
    """
    Xác định start_path và scan_root (Git root hoặc fallback).
    Ném FileNotFoundError nếu start_path cuối cùng không tồn tại.
    """
    
    # 1. Xác định Start Path
    start_path: Path
    if start_path_from_cli:
        start_path = start_path_from_cli
    else:
        start_path = Path(DEFAULT_START_PATH).expanduser().resolve()

    # 2. Xác định Scan Root
    scan_root: Path
    if start_path.is_file():
        scan_root = find_git_root(start_path.parent) or start_path.parent
    else:
        effective_start_dir = start_path if start_path.exists() else Path.cwd()
        scan_root = find_git_root(effective_start_dir) or effective_start_dir

    # 3. Validation
    if not start_path.exists():
         logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path.as_posix()}")
         raise FileNotFoundError(f"Start path not found: {start_path.as_posix()}")

    logger.debug(f"Scan Root (cho quy tắc .gitignore): {scan_root.as_posix()}")
    logger.debug(f"Start Path (nơi bắt đầu quét): {start_path.as_posix()}")
    
    return start_path, scan_root


def resolve_filters(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    scan_root: Path,
) -> Tuple[Set[str], Optional['pathspec.PathSpec'], Set[Path]]:
    """Hợp nhất các cấu hình filter (extensions, ignore, submodules)."""
    
    # 1. Hợp nhất Extensions
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

    # 2. Hợp nhất Ignore
    default_ignore_set = parse_comma_list(DEFAULT_IGNORE)
    
    final_ignore_list = resolve_config_list(
        cli_str_value=cli_args.get("ignore"),
        file_list_value=file_config.get('ignore'), 
        default_set_value=default_ignore_set
    )
    
    gitignore_patterns: List[str] = []
    if not cli_args.get("no_gitignore", False):
        gitignore_patterns = parse_gitignore(scan_root)
        logger.debug(f"Đã tải {len(gitignore_patterns)} quy tắc từ .gitignore")

    all_ignore_patterns_list: List[str] = final_ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)

    # 3. Submodules
    submodule_paths = get_submodule_paths(scan_root, logger)
    
    return ext_filter_set, ignore_spec, submodule_paths


def resolve_output_path(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    start_path: Path,
) -> Optional[Path]:
    """
    Xác định đường dẫn output cuối cùng.
    Trả về None nếu là stdout hoặc dry_run.
    KHÔNG expanduser ('~'), đó là việc của Executor.
    """
    if cli_args.get("stdout", False) or cli_args.get("dry_run", False):
        return None
        
    output_path_from_cli: Optional[Path] = cli_args.get("output")
    if output_path_from_cli:
        return output_path_from_cli

    # Hợp nhất Default Output Dir (File > Default)
    default_output_dir_str = resolve_config_value(
        cli_value=None,
        file_value=file_config.get("output_dir"),
        default_value=DEFAULT_OUTPUT_DIR
    )
    
    default_output_dir_path = Path(default_output_dir_str)
    
    # Tính toán tên file
    start_name = start_path.stem if start_path.is_file() else start_path.name
    final_output_path = default_output_dir_path / f"{start_name}_context.txt"

    logger.debug(f"Sử dụng đường dẫn output mặc định (chưa expand): {final_output_path.as_posix()}")
    return final_output_path