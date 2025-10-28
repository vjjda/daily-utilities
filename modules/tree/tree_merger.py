# Path: modules/tree/tree_merger.py

"""
Configuration Merging logic for the Tree (ctree) module.
(Internal module, imported by tree_core.py)

Chịu trách nhiệm hợp nhất các nguồn cấu hình (CLI, File, Default)
thành một bộ tham số "final" duy nhất.
"""

from pathlib import Path
import logging
import argparse
from typing import Set, Optional, Dict, Any, TYPE_CHECKING, List, Iterable, Tuple, Final

try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

from utils.core import (
    get_submodule_paths,
    parse_gitignore,
    resolve_config_value,
    resolve_config_list,
    compile_spec_from_patterns,
    parse_comma_list,
    resolve_set_modification
)

from .tree_config import (
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL,
    FALLBACK_SHOW_SUBMODULES, FALLBACK_USE_GITIGNORE,
    DEFAULT_EXTENSIONS
)

__all__ = ["merge_config_sources"]

# --- Helper Functions for Merging Specific Configs ---

def _resolve_simple_flags(
    args: argparse.Namespace,
    file_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Hợp nhất các cờ đơn giản: level, show_submodules, use_gitignore."""
    final_level = resolve_config_value(
        cli_value=args.level,
        file_value=file_config.get('level'),
        default_value=DEFAULT_MAX_LEVEL
    )
    show_submodules = args.show_submodules if args.show_submodules else \
                      file_config.get('show-submodules', FALLBACK_SHOW_SUBMODULES)
    
    use_gitignore_from_config = file_config.get(
         'use-gitignore',
        FALLBACK_USE_GITIGNORE
    )
    # Cờ CLI --no-gitignore luôn thắng
    final_use_gitignore = False if args.no_gitignore else use_gitignore_from_config

    return {
        "max_level": final_level,
        "show_submodules": show_submodules,
        "use_gitignore": final_use_gitignore
    }

def _resolve_filter_list(
    cli_str_value: Optional[str],
    file_list_value: Optional[List[str]],
    default_set_value: Set[str]
) -> List[str]:
    """
    Resolver chung cho các danh sách 'ignore' và 'prune'.
    Logic: (File GHI ĐÈ Default) + (CLI NỐI VÀO).
    """
    return resolve_config_list(
        cli_str_value=cli_str_value,
        file_list_value=file_list_value,
        default_set_value=default_set_value
    )

def _resolve_dirs_only(
    args: argparse.Namespace,
    file_config: Dict[str, Any]
) -> Tuple[Set[str], bool]:
    """
    Hợp nhất logic 'dirs_only'.
    
    Trả về:
        (Set[str]): Danh sách các pattern dirs_only cuối cùng.
        (bool): Cờ global_dirs_only (nếu -d hoặc _ALL_ được set).
    """
    dirs_only_cli = args.dirs_only
    dirs_only_file = file_config.get('dirs-only', None)
    
    # Ưu tiên CLI
    final_dirs_only_mode = dirs_only_cli if dirs_only_cli is not None else dirs_only_file

    global_dirs_only = final_dirs_only_mode == '_ALL_'
    dirs_only_list_custom: Set[str] = set()

    if isinstance(final_dirs_only_mode, list):
        dirs_only_list_custom = set(final_dirs_only_mode)
    elif final_dirs_only_mode is not None and not global_dirs_only:
        # Xử lý trường hợp chuỗi CLI (từ -D 'a,b')
        dirs_only_list_custom = parse_comma_list(final_dirs_only_mode)

    final_dirs_only_set = DEFAULT_DIRS_ONLY_LOGIC.union(dirs_only_list_custom)
    return final_dirs_only_set, global_dirs_only

def _resolve_extensions(
    logger: logging.Logger,
    args: argparse.Namespace,
    file_config: Dict[str, Any]
) -> Optional[Set[str]]:
    """
    Hợp nhất bộ lọc 'extensions' (hỗ trợ toán tử +/-/~).
    Trả về None nếu không có bộ lọc nào được áp dụng.
    """
    cli_ext_str = args.extensions
    file_ext_list: Optional[List[str]] = file_config.get('extensions')

    # 1. Xác định set cơ sở (tentative)
    tentative_extensions: Optional[Set[str]]
    if file_ext_list is not None:
        tentative_extensions = set(file_ext_list)
        logger.debug("Sử dụng danh sách 'extensions' từ file config làm cơ sở.")
    else:
        tentative_extensions = DEFAULT_EXTENSIONS # Default là None
        logger.debug("Sử dụng danh sách 'extensions' mặc định (None) làm cơ sở.")

    # 2. Áp dụng logic CLI
    extensions_filter: Optional[Set[str]]
    if cli_ext_str is None and tentative_extensions is None:
        # Đây là trường hợp phổ biến nhất: không lọc gì cả.
        extensions_filter = None
        logger.debug("Không áp dụng bộ lọc 'extensions'.")
    else:
        # Nếu 1 trong 2 có giá trị, chúng ta cần tính toán
        base_set = tentative_extensions if tentative_extensions is not None else set()
        extensions_filter = resolve_set_modification(
            tentative_set=base_set,
            cli_string=cli_ext_str
        )
        if cli_ext_str:
             logger.debug(f"Đã áp dụng logic 'extensions' CLI: '{cli_ext_str}'. Set cuối cùng: {extensions_filter}")
        else:
             logger.debug(f"Set 'extensions' cuối cùng (từ config/default): {extensions_filter}")
    return extensions_filter

def _compile_specs(
    start_dir: Path,
    ignore_list: List[str],
    prune_list: List[str],
    dirs_only_set: Set[str],
    gitignore_patterns: List[str]
) -> Dict[str, Optional['pathspec.PathSpec']]:
    """Biên dịch tất cả các danh sách filter thành đối tượng PathSpec."""
    
    # Giữ nguyên thứ tự: (Config/Default) + (Gitignore)
    all_ignore_patterns_list: List[str] = ignore_list + gitignore_patterns
    all_prune_patterns_list: List[str] = prune_list
    all_dirs_only_patterns_list: List[str] = sorted(list(dirs_only_set))

    return {
        "ignore_spec": compile_spec_from_patterns(all_ignore_patterns_list, start_dir),
        "prune_spec": compile_spec_from_patterns(all_prune_patterns_list, start_dir),
        "dirs_only_spec": compile_spec_from_patterns(all_dirs_only_patterns_list, start_dir)
    }

def _get_submodule_info(
    start_dir: Path,
    show_submodules: bool,
    logger: logging.Logger
) -> Tuple[Set[Path], Set[str]]:
    """Lấy đường dẫn và tên submodule (nếu show_submodules=False)."""
    submodule_paths: Set[Path] = set()
    submodule_names: Set[str] = set()
    if not show_submodules:
        submodule_paths = get_submodule_paths(start_dir, logger=logger)
        submodule_names = {p.name for p in submodule_paths}
    return submodule_paths, submodule_names


# --- Main Merging Function ---

def merge_config_sources(
    args: argparse.Namespace,
    file_config: Dict[str, Any],
    start_dir: Path,
    logger: logging.Logger,
    is_git_repo: bool
) -> Dict[str, Any]:
    """
    Hợp nhất cấu hình từ các nguồn (CLI, File, Default).

    Đây là trái tim logic của ctree, quyết định chính xác
    những gì sẽ được hiển thị hoặc ẩn đi.
    
    Args:
        args: Namespace các đối số từ CLI.
        file_config: Dict cấu hình đã load từ file .toml.
        start_dir: Thư mục gốc nơi quét (dùng để tìm .gitignore).
        logger: Logger.
        is_git_repo: True nếu start_dir là một kho Git.

    Returns:
        Một dict chứa tất cả các tham số đã được xử lý
        (ví dụ: max_level, ignore_spec, submodules, v.v.).
    """

    # Cờ --full-view sẽ ghi đè mọi thứ
    if args.full_view:
        logger.info("⚡ Chế độ xem đầy đủ. Bỏ qua mọi bộ lọc và giới hạn.")
        return {
            "max_level": None, "ignore_spec": None, "submodules": set(),
            "prune_spec": None, "dirs_only_spec": None, "extensions_filter": None,
            "is_in_dirs_only_zone": False, "global_dirs_only_flag": False,
            "using_gitignore": False,
            "filter_lists": {
                "ignore": set(), "prune": set(), "dirs_only": set(),
                "submodules": set(), "extensions": set()
            }
        }

    # 1. Hợp nhất các cờ đơn giản
    simple_flags = _resolve_simple_flags(args, file_config)
    final_level = simple_flags["max_level"]
    show_submodules = simple_flags["show_submodules"]
    final_use_gitignore = simple_flags["use_gitignore"]

    # 2. Tải .gitignore (nếu cần)
    gitignore_patterns: List[str] = []
    if is_git_repo and final_use_gitignore:
        logger.debug("Phát hiện kho Git. Đang tải patterns .gitignore.")
        gitignore_patterns = parse_gitignore(start_dir)
    elif is_git_repo and not final_use_gitignore:
        logger.debug("Phát hiện kho Git, nhưng bỏ qua .gitignore (do cờ hoặc cấu hình).")
    else:
        logger.debug("Không phải kho Git. Bỏ qua .gitignore.")

    # 3. Hợp nhất các danh sách filter
    final_ignore_list = _resolve_filter_list(
        args.ignore, file_config.get('ignore'), DEFAULT_IGNORE
    )
    final_prune_list = _resolve_filter_list(
         args.prune, file_config.get('prune'), DEFAULT_PRUNE
    )
    final_dirs_only_set, global_dirs_only_flag = _resolve_dirs_only(args, file_config)
    final_extensions_filter = _resolve_extensions(logger, args, file_config)

    # 4. Biên dịch các đối tượng PathSpec
    specs = _compile_specs(
        start_dir, final_ignore_list, final_prune_list,
        final_dirs_only_set, gitignore_patterns
    )

    # 5. Lấy thông tin Submodule
    submodule_paths, submodule_names = _get_submodule_info(start_dir, show_submodules, logger)

    # 6. Trả về dict kết quả cuối cùng
    return {
        "max_level": final_level,
        "ignore_spec": specs["ignore_spec"],
        "prune_spec": specs["prune_spec"],
        "dirs_only_spec": specs["dirs_only_spec"],
        "extensions_filter": final_extensions_filter,
        "submodules": submodule_paths,
        "is_in_dirs_only_zone": global_dirs_only_flag, # Trạng thái ban đầu cho generate_tree
        "using_gitignore": is_git_repo and final_use_gitignore and (len(gitignore_patterns) > 0),
        "global_dirs_only_flag": global_dirs_only_flag, # Dùng cho hàm in kết quả
        "filter_lists": { # Dùng cho hàm in header
            "ignore": set(final_ignore_list),
            "prune": set(final_prune_list),
            "dirs_only": final_dirs_only_set,
            "submodules": submodule_names,
            "extensions": final_extensions_filter if final_extensions_filter is not None else set()
        }
    }