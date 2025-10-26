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
    resolve_config_list
)
# --- END MODIFIED ---

from .tree_config import (
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL, CONFIG_SECTION_NAME, 
    FALLBACK_SHOW_SUBMODULES, FALLBACK_USE_GITIGNORE
)

__all__ = ["merge_config_sources", "generate_dynamic_config"]


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
            "ignore_list": set(),
            "submodules": set(),
            "prune_list": set(),
            "dirs_only_list": set(),
            "is_in_dirs_only_zone": False,
            "global_dirs_only_flag": False,
            "gitignore_spec": None,
            "using_gitignore": False,
            "filter_lists": {
                "ignore": set(),
                "prune": set(),
                "dirs_only": set(),
                "submodules": set()
            }
        }

    # --- 3. Merge Configs (CLI > File > Default) ---
    
    # Level (Sử dụng helper mới)
    # --- MODIFIED: Sử dụng resolve_config_value ---
    final_level = resolve_config_value(
        cli_value=args.level,
        file_value=file_config.get('level'),
        default_value=DEFAULT_MAX_LEVEL
    )
    # --- END MODIFIED ---
    
    # Submodules (Giữ logic cũ, vì 'args.show_submodules' là cờ boolean Falsy)
    show_submodules = args.show_submodules if args.show_submodules else \
                      file_config.get('show-submodules', FALLBACK_SHOW_SUBMODULES)

    # Gitignore Logic (Giữ logic cũ, vì 'args.no_gitignore' là cờ boolean Inverted)
    use_gitignore_from_config = file_config.get(
        'use-gitignore', 
        FALLBACK_USE_GITIGNORE
    )
    final_use_gitignore = False if args.no_gitignore else use_gitignore_from_config
    
    gitignore_spec: Optional['pathspec.PathSpec'] = None 
    if is_git_repo and final_use_gitignore:
        logger.debug("Phát hiện kho Git. Đang tải .gitignore qua pathspec.")
        gitignore_spec = parse_gitignore(start_dir)
    elif is_git_repo and not final_use_gitignore:
        logger.debug("Phát hiện kho Git, nhưng bỏ qua .gitignore (do cờ hoặc cấu hình).")
    else:
        logger.debug("Không phải kho Git. Bỏ qua .gitignore.")

    # --- MODIFIED: Sử dụng logic "override" mới qua resolve_config_list ---
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
        # (Chỗ này cần import parse_comma_list - OK, tôi sẽ thêm lại)
        # --- RE-MODIFIED: Thêm lại import parse_comma_list ---
        from utils.core import parse_comma_list 
        # --- END RE-MODIFIED ---
        dirs_only_list_custom = parse_comma_list(final_dirs_only_mode)
        
    final_dirs_only_list = DEFAULT_DIRS_ONLY_LOGIC.union(dirs_only_list_custom)
    # --- END MODIFIED ---
    
    # Submodule Paths
    submodule_paths: Set[Path] = set()
    submodule_names: Set[str] = set()
    if not show_submodules: 
        submodule_paths = get_submodule_paths(start_dir, logger=logger)
        submodule_names = {p.name for p in submodule_paths}

    # 4. Return a dict
    return {
        "max_level": final_level,
        "ignore_list": final_ignore_list,
        "submodules": submodule_paths,
        "prune_list": final_prune_list,
        "dirs_only_list": final_dirs_only_list,
        "is_in_dirs_only_zone": global_dirs_only,
        "gitignore_spec": gitignore_spec,
        "using_gitignore": is_git_repo and final_use_gitignore and (gitignore_spec is not None),
        "global_dirs_only_flag": global_dirs_only,
        "filter_lists": {
            "ignore": final_ignore_list,
            "prune": final_prune_list,
            "dirs_only": final_dirs_only_list,
            "submodules": submodule_names
        }
    }


def generate_dynamic_config(template_content: str) -> str:
    """
    Chèn các giá trị mặc định vào chuỗi template .toml.
    """
    
    # --- MODIFIED: Helper mới cho TOML array ---
    def _format_set_to_toml_array(value_set: Set[str]) -> str:
        """Helper: Chuyển set thành chuỗi mảng TOML."""
        if not value_set:
            return "[]" # Mảng rỗng
        # Dùng repr() để tạo list string chuẩn: ['a', 'b']
        return repr(sorted(list(value_set)))
    # --- END MODIFIED ---

    # Format values for TOML
    toml_level = (
        f"level = {DEFAULT_MAX_LEVEL}" 
        if DEFAULT_MAX_LEVEL is not None 
        else f"# level = 3" # (Commented out)
    )
    toml_show_submodules = str(FALLBACK_SHOW_SUBMODULES).lower()
    toml_use_gitignore = str(FALLBACK_USE_GITIGNORE).lower()
    toml_ignore = _format_set_to_toml_array(DEFAULT_IGNORE)
    toml_prune = _format_set_to_toml_array(DEFAULT_PRUNE)
    toml_dirs_only = _format_set_to_toml_array(DEFAULT_DIRS_ONLY_LOGIC)

    # Format the template string
    try:
        # --- MODIFIED: Dùng placeholder của TOML ---
        dynamic_template = template_content.format(
            config_section_name=CONFIG_SECTION_NAME,
            toml_level=toml_level,
            toml_show_submodules=toml_show_submodules,
            toml_use_gitignore=toml_use_gitignore,
            toml_ignore=toml_ignore,
            toml_prune=toml_prune,
            toml_dirs_only=toml_dirs_only
        )
        return dynamic_template
    except KeyError as e:
        print(f"LỖI NGHIÊM TRỌNG: Template key không khớp: {e}")
        return "# LỖI: File template thiếu placeholder."
