# Path: modules/tree/tree_core.py

from pathlib import Path
import logging 
import configparser
import argparse # <-- Vẫn giữ để type hint cho args object
from typing import Set, Optional, Dict, Any 
try:
    import pathspec
except ImportError:
    pathspec = None

from utils.core import get_submodule_paths, parse_comma_list, parse_gitignore

from .tree_config import (
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL, CONFIG_FILENAME, PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME, FALLBACK_SHOW_SUBMODULES,
    FALLBACK_USE_GITIGNORE
)

# --- MODIFIED: Thêm CONFIG_TEMPLATE vào __all__ ---
__all__ = ["load_and_merge_config", "CONFIG_TEMPLATE"]
# --- END MODIFIED ---


def load_and_merge_config(
    args: argparse.Namespace, 
    start_dir: Path, 
    logger: logging.Logger,
    is_git_repo: bool
) -> Dict[str, Any]:
    """
    Loads configuration from .ini files and merges them with CLI arguments.
    (This function is pure logic, no side-effects)
    """
    
    # 1. Check for Full View Override
    # (Logic này không đổi, cờ True sẽ override mọi thứ)
    if args.full_view:
        logger.info("⚡ Full View mode enabled. Bypassing all filters and limits.")
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

    # 2. Read Config from Files (Không thay đổi)
    config = configparser.ConfigParser()
    
    tree_config_path = start_dir / CONFIG_FILENAME
    project_config_path = start_dir / PROJECT_CONFIG_FILENAME

    files_to_read = []
    if project_config_path.exists():
        files_to_read.append(project_config_path)
    if tree_config_path.exists():
        files_to_read.append(tree_config_path)

    if files_to_read:
        try:
            config.read(files_to_read) 
            logger.debug(f"Loaded config from files: {[p.name for p in files_to_read]}")
        except Exception as e:
            logger.warning(logger, f"⚠️ Could not read config files: {e}")
    else:
        logger.debug("No .tree.ini or .project.ini config files found. Using defaults.")

    if CONFIG_SECTION_NAME not in config:
        config.add_section(CONFIG_SECTION_NAME)
        logger.debug(f"Added empty '{CONFIG_SECTION_NAME}' section for safe fallback.")

    # --- 3. Merge Configs (CLI > File > Default) ---
    
    # Level (Logic không đổi)
    level_from_config_file = config.getint(CONFIG_SECTION_NAME, 'level', fallback=DEFAULT_MAX_LEVEL)
    final_level = args.level if args.level is not None else level_from_config_file
    
    # --- MODIFIED: Submodules ---
    # Logic cũ: args.show_submodules is not None (chờ (None | True))
    # Logic mới: Typer trả về (False | True).
    # Nếu args.show_submodules là True (CLI flag) => Dùng True
    # Nếu args.show_submodules là False (Default) => Dùng config
    show_submodules = args.show_submodules if args.show_submodules else \
                      config.getboolean(CONFIG_SECTION_NAME, 'show-submodules', fallback=FALLBACK_SHOW_SUBMODULES)
    # --- END MODIFIED ---

    # --- MODIFIED: Gitignore Logic ---
    # (Logic này đã đúng, cờ True sẽ override)
    use_gitignore_from_config = config.getboolean(
        CONFIG_SECTION_NAME, 'use-gitignore', 
        fallback=FALLBACK_USE_GITIGNORE
    )
    # Nếu args.no_gitignore là True => final là False
    # Nếu args.no_gitignore là False (Default) => final là config
    final_use_gitignore = False if args.no_gitignore else use_gitignore_from_config
    # --- END MODIFIED ---
    
    gitignore_spec: Optional['pathspec.PathSpec'] = None
    if is_git_repo and final_use_gitignore:
        logger.debug("Git repository detected. Loading .gitignore patterns via pathspec.")
        gitignore_spec = parse_gitignore(start_dir)
    elif is_git_repo and not final_use_gitignore:
        logger.debug("Git repository detected, but skipping .gitignore (due to flag or config).")
    else:
        logger.debug("Not a Git repository. Skipping .gitignore.")

    # Ignore List (Không thay đổi)
    ignore_cli = parse_comma_list(args.ignore)
    ignore_file = parse_comma_list(config.get(CONFIG_SECTION_NAME, 'ignore', fallback=None))
    final_ignore_list = DEFAULT_IGNORE.union(ignore_file).union(ignore_cli)

    # Prune List (Không thay đổi)
    prune_cli = parse_comma_list(args.prune) 
    prune_file = parse_comma_list(config.get(CONFIG_SECTION_NAME, 'prune', fallback=None))
    final_prune_list = DEFAULT_PRUNE.union(prune_file).union(prune_cli)

    # Dirs Only List (Logic không đổi)
    dirs_only_cli = args.dirs_only
    dirs_only_file = config.get(CONFIG_SECTION_NAME, 'dirs-only', fallback=None)
    final_dirs_only_mode = dirs_only_cli if dirs_only_cli is not None else dirs_only_file
    
    global_dirs_only = final_dirs_only_mode == '_ALL_'
    dirs_only_list_custom = set()
    if final_dirs_only_mode is not None and not global_dirs_only:
        dirs_only_list_custom = parse_comma_list(final_dirs_only_mode)
    final_dirs_only_list = DEFAULT_DIRS_ONLY_LOGIC.union(dirs_only_list_custom)
    
    # Submodule Paths (Không thay đổi)
    submodule_paths: Set[Path] = set()
    submodule_names: Set[str] = set()
    if not show_submodules: 
        submodule_paths = get_submodule_paths(start_dir, logger=logger)
        submodule_names = {p.name for p in submodule_paths}

    # 4. Return a dict (Không thay đổi)
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


try:
    _CURRENT_DIR = Path(__file__).parent
    _TEMPLATE_PATH = _CURRENT_DIR / "tree.ini.template"
    CONFIG_TEMPLATE = _TEMPLATE_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    print("FATAL ERROR: Could not find 'tree.ini.template'.")
    CONFIG_TEMPLATE = "; ERROR: Template file missing."
except Exception as e:
    print(f"FATAL ERROR: Could not read 'tree.ini.template': {e}")
    CONFIG_TEMPLATE = "; ERROR: Template file could not be read."