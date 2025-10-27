# Path: modules/tree/tree_core.py

"""
Logic nghiệp vụ cốt lõi cho module Tree (ctree).
(Các hàm thuần túy, không có I/O hoặc side-effect)
"""

from pathlib import Path
import logging 
import argparse
# --- MODIFIED: Thêm TYPE_CHECKING ---
from typing import Set, Optional, Dict, Any, TYPE_CHECKING 
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
# --- MODIFIED: Import các helper mới, xóa parse_comma_list ---
from utils.core import (
    get_submodule_paths, 
    parse_gitignore, 
    resolve_config_value, 
    resolve_config_list,
    compile_spec_from_patterns, # <-- MỚI
    parse_comma_list # <-- THÊM LẠI (cho dirs-only)
)
# --- END MODIFIED ---

from .tree_config import (
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL, CONFIG_SECTION_NAME, 
    FALLBACK_SHOW_SUBMODULES, FALLBACK_USE_GITIGNORE
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
        logger.info("⚡ Chế độ xem đầy đủ. Bỏ qua mọi bộ lọc và giới hạn.")
        return {
            "max_level": None,
            # --- MODIFIED: Trả về None spec ---
            "ignore_spec": None,
            "submodules": set(),
            "prune_spec": None,
            "dirs_only_spec": None,
            # --- END MODIFIED ---
            "is_in_dirs_only_zone": False,
            "global_dirs_only_flag": False,
            "using_gitignore": False, # (Sửa)
            "filter_lists": {
                "ignore": set(),
                "prune": set(),
                "dirs_only": set(),
                "submodules": set()
            }
        }

    # --- 3. Merge Configs (CLI > File > Default) ---
    
    # (Level, Submodules, Gitignore Logic giữ nguyên)
    # ...
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
    
    # --- MODIFIED: Lấy patterns, không lấy spec ---
    gitignore_patterns: Set[str] = set()
    if is_git_repo and final_use_gitignore:
        logger.debug("Phát hiện kho Git. Đang tải patterns .gitignore.")
        # parse_gitignore giờ trả về Set[str]
        gitignore_patterns = parse_gitignore(start_dir) 
    elif is_git_repo and not final_use_gitignore:
        logger.debug("Phát hiện kho Git, nhưng bỏ qua .gitignore (do cờ hoặc cấu hình).")
    else:
        logger.debug("Không phải kho Git. Bỏ qua .gitignore.")
    # --- END MODIFIED ---


    # --- MODIFIED: Lấy danh sách pattern (như cũ), nhưng gộp và biên dịch ---
    
    # Ignore List
    final_ignore_list = resolve_config_list(
        cli_str_value=args.ignore,
        file_list_value=file_config.get('ignore'),
        default_set_value=DEFAULT_IGNORE
    )

    # Prune List
    final_prune_list = resolve_config_list(
        cli_str_value=args.prune,
        file_list_value=file_config.get('prune'),
        default_set_value=DEFAULT_PRUNE
    )

    # Dirs Only List (Giữ logic cũ vì phức tạp: _ALL_, list, hoặc string)
    dirs_only_cli = args.dirs_only
    dirs_only_file = file_config.get('dirs-only', None) 
    final_dirs_only_mode = dirs_only_cli if dirs_only_cli is not None else dirs_only_file
    
    global_dirs_only = final_dirs_only_mode == '_ALL_'
    dirs_only_list_custom: Set[str] = set()
    
    if isinstance(final_dirs_only_mode, list): 
        dirs_only_list_custom = set(final_dirs_only_mode)
    elif final_dirs_only_mode is not None and not global_dirs_only: 
        # (parse_comma_list đã được import lại ở trên)
        dirs_only_list_custom = parse_comma_list(final_dirs_only_mode)
        
    final_dirs_only_list = DEFAULT_DIRS_ONLY_LOGIC.union(dirs_only_list_custom)
    
    # --- NEW: Gộp và Biên dịch Specs ---
    # Gộp ignore từ config và .gitignore
    all_ignore_patterns = final_ignore_list.union(gitignore_patterns)
    
    final_ignore_spec = compile_spec_from_patterns(all_ignore_patterns)
    final_prune_spec = compile_spec_from_patterns(final_prune_list)
    final_dirs_only_spec = compile_spec_from_patterns(final_dirs_only_list)
    # --- END NEW ---
    
    # Submodule Paths
    submodule_paths: Set[Path] = set()
    submodule_names: Set[str] = set()
    if not show_submodules: 
        submodule_paths = get_submodule_paths(start_dir, logger=logger)
        submodule_names = {p.name for p in submodule_paths}

    # 4. Return a dict
    return {
        "max_level": final_level,
        # --- MODIFIED: Trả về specs ---
        "ignore_spec": final_ignore_spec,
        "prune_spec": final_prune_spec,
        "dirs_only_spec": final_dirs_only_spec,
        # --- END MODIFIED ---
        "submodules": submodule_paths,
        "is_in_dirs_only_zone": global_dirs_only,
        # (Sửa logic: dùng len(gitignore_patterns) thay vì (spec is not None))
        "using_gitignore": is_git_repo and final_use_gitignore and (len(gitignore_patterns) > 0),
        "global_dirs_only_flag": global_dirs_only,
        "filter_lists": {
            "ignore": final_ignore_list, # Giữ lại để in status
            "prune": final_prune_list,
            "dirs_only": final_dirs_only_list,
            "submodules": submodule_names
        }
    }
