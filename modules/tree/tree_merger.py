# Path: modules/tree/tree_core.py

"""
Logic nghiệp vụ cốt lõi cho module Tree (ctree).
(Các hàm thuần túy, không có I/O hoặc side-effect)
"""

from pathlib import Path
import logging
import argparse
# --- MODIFIED: Thêm TYPE_CHECKING, List, Iterable ---
from typing import Set, Optional, Dict, Any, TYPE_CHECKING, List, Iterable
# --- END MODIFIED ---

# --- MODIFIED: Tách biệt import cho runtime và type-checking ---
try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec
# --- END MODIFIED ---

# Import utilities
# --- MODIFIED: Import các helper mới ---
from utils.core import (
    get_submodule_paths,
    parse_gitignore, # Trả về List[str]
    resolve_config_value,
    resolve_config_list, # <-- Hàm này giờ trả về List
    compile_spec_from_patterns, # Nhận Iterable[str]
    parse_comma_list,
    resolve_set_modification # <-- NEW
)
# --- END MODIFIED ---

from .tree_config import (
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL, CONFIG_SECTION_NAME,
    FALLBACK_SHOW_SUBMODULES, FALLBACK_USE_GITIGNORE,
    DEFAULT_EXTENSIONS # <-- NEW
)

__all__ = ["merge_config_sources"]


def merge_config_sources(
    args: argparse.Namespace,
    file_config: Dict[str, Any], # <-- MODIFIED: Nhận Dict
    start_dir: Path,
    logger: logging.Logger,
    is_git_repo: bool
) -> Dict[str, Any]:
    """
    Hợp nhất cấu hình từ các nguồn: mặc định, file, và đối số CLI.
    """

    if args.full_view:
        # (Giữ nguyên)
        logger.info("⚡ Chế độ xem đầy đủ. Bỏ qua mọi bộ lọc và giới hạn.")
        return {
            "max_level": None,
            "ignore_spec": None,
            "submodules": set(),
            "prune_spec": None,
            "dirs_only_spec": None,
            "extensions_filter": None,
            "is_in_dirs_only_zone": False,
            "global_dirs_only_flag": False,
            "using_gitignore": False,
            "filter_lists": {
                "ignore": set(),
                "prune": set(),
                "dirs_only": set(),
                "submodules": set(),
                "extensions": set()
            }
        }

    # --- 3. Merge Configs (CLI > File > Default) ---

    # (Level, Submodules, Gitignore Logic giữ nguyên)
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
    final_use_gitignore = False if args.no_gitignore else use_gitignore_from_config

    # --- MODIFIED: parse_gitignore trả về List[str] ---
    gitignore_patterns: List[str] = []
    if is_git_repo and final_use_gitignore:
        logger.debug("Phát hiện kho Git. Đang tải patterns .gitignore.")
        gitignore_patterns = parse_gitignore(start_dir) # <-- List[str]
    elif is_git_repo and not final_use_gitignore:
        logger.debug("Phát hiện kho Git, nhưng bỏ qua .gitignore (do cờ hoặc cấu hình).")
    else:
        logger.debug("Không phải kho Git. Bỏ qua .gitignore.")
    # --- END MODIFIED ---


    # --- MODIFIED: Lấy danh sách pattern, gộp thành List, và biên dịch ---

    # --- MODIFIED: Cập nhật logic 'ignore' để nhận List ---
    final_ignore_list = resolve_config_list(
        cli_str_value=args.ignore,
        file_list_value=file_config.get('ignore'), # <-- Đây là List[str] hoặc None
        default_set_value=DEFAULT_IGNORE
    )
    # --- END MODIFIED ---

    # --- MODIFIED: Cập nhật logic 'prune' để nhận List ---
    final_prune_list = resolve_config_list(
        cli_str_value=args.prune,
        file_list_value=file_config.get('prune'), # <-- Đây là List[str] hoặc None
        default_set_value=DEFAULT_PRUNE
    )
    # --- END MODIFIED ---

    # (Logic 'dirs_only' giữ nguyên, vì nó không dùng resolve_config_list)
    dirs_only_cli = args.dirs_only
    dirs_only_file = file_config.get('dirs-only', None)
    final_dirs_only_mode = dirs_only_cli if dirs_only_cli is not None else dirs_only_file

    global_dirs_only = final_dirs_only_mode == '_ALL_'
    dirs_only_list_custom: Set[str] = set()

    if isinstance(final_dirs_only_mode, list):
        dirs_only_list_custom = set(final_dirs_only_mode)
    elif final_dirs_only_mode is not None and not global_dirs_only:
        dirs_only_list_custom = parse_comma_list(final_dirs_only_mode)

    final_dirs_only_set = DEFAULT_DIRS_ONLY_LOGIC.union(dirs_only_list_custom)


    # (Logic 'extensions' giữ nguyên)
    cli_ext_str = args.extensions
    file_ext_list: Optional[List[str]] = file_config.get('extensions')

    tentative_extensions: Optional[Set[str]]
    if file_ext_list is not None:
         tentative_extensions = set(file_ext_list)
         logger.debug("Sử dụng danh sách 'extensions' từ file config làm cơ sở.")
    else:
         tentative_extensions = DEFAULT_EXTENSIONS # Default là None
         logger.debug("Sử dụng danh sách 'extensions' mặc định (None) làm cơ sở.")

    extensions_filter: Optional[Set[str]]
    if cli_ext_str is None and tentative_extensions is None: 
        extensions_filter = None
        logger.debug("Không áp dụng bộ lọc 'extensions'.")
    else:
        base_set = tentative_extensions if tentative_extensions is not None else set()
        extensions_filter = resolve_set_modification(
            tentative_set=base_set,
            cli_string=cli_ext_str
        )
        if cli_ext_str:
             logger.debug(f"Đã áp dụng logic 'extensions' CLI: '{cli_ext_str}'. Set cuối cùng: {extensions_filter}")
        else:
             logger.debug(f"Set 'extensions' cuối cùng (từ config/default): {extensions_filter}")


    # --- MODIFIED: Gộp thành List (đã giữ trật tự) và Biên dịch ---
    # Ưu tiên: Config/CLI patterns -> Gitignore patterns
    all_ignore_patterns_list: List[str] = final_ignore_list + gitignore_patterns
    all_prune_patterns_list: List[str] = final_prune_list # Prune không dùng gitignore
    all_dirs_only_patterns_list: List[str] = sorted(list(final_dirs_only_set)) # Dirs-only (giữ sorted)

    final_ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, start_dir)
    final_prune_spec = compile_spec_from_patterns(all_prune_patterns_list, start_dir)
    final_dirs_only_spec = compile_spec_from_patterns(all_dirs_only_patterns_list, start_dir)
    # --- END MODIFIED ---

    # Submodule Paths (Giữ nguyên)
    submodule_paths: Set[Path] = set()
    submodule_names: Set[str] = set()
    if not show_submodules:
        submodule_paths = get_submodule_paths(start_dir, logger=logger)
        submodule_names = {p.name for p in submodule_paths}

    # 4. Return a dict
    return {
        "max_level": final_level,
        "ignore_spec": final_ignore_spec,
        "prune_spec": final_prune_spec,
        "dirs_only_spec": final_dirs_only_spec,
        "extensions_filter": extensions_filter,
        "submodules": submodule_paths,
        "is_in_dirs_only_zone": global_dirs_only,
        "using_gitignore": is_git_repo and final_use_gitignore and (len(gitignore_patterns) > 0),
        "global_dirs_only_flag": global_dirs_only,
        # Trả về Set để in status (không ảnh hưởng logic lọc)
        "filter_lists": {
             # --- MODIFIED: Chuyển đổi List (đã lọc) về Set (cho hiển thị) ---
            "ignore": set(final_ignore_list),
            "prune": set(final_prune_list),
            # --- END MODIFIED ---
            "dirs_only": final_dirs_only_set,
            "submodules": submodule_names,
            "extensions": extensions_filter if extensions_filter is not None else set()
        }
    }