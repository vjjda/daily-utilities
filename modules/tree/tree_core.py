# Path: modules/tree/tree_core.py

"""
Core business logic for the Tree (ctree) module.
(Pure functions, no I/O or side-effects)
"""

from pathlib import Path
import logging 
import configparser
import argparse
from typing import Set, Optional, Dict, Any 

try:
    import pathspec
except ImportError:
    pathspec = None

# Import utilities
from utils.core import get_submodule_paths, parse_comma_list, parse_gitignore

# Import defaults
from .tree_config import (
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL, CONFIG_SECTION_NAME, 
    FALLBACK_SHOW_SUBMODULES, FALLBACK_USE_GITIGNORE
)

__all__ = ["merge_config_sources", "generate_dynamic_config"]


def merge_config_sources(
    args: argparse.Namespace, 
    file_config: configparser.ConfigParser,
    start_dir: Path, 
    logger: logging.Logger,
    is_git_repo: bool
) -> Dict[str, Any]:
    """
    Merges configuration from defaults, files, and CLI arguments.
    (Pure logic, moved from old load_and_merge_config)
    """
    
    # 1. Check for Full View Override
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

    # 2. Get config section (already loaded by loader)
    config_section = file_config[CONFIG_SECTION_NAME]

    # --- 3. Merge Configs (CLI > File > Default) ---
    
    # Level
    level_from_config_file = config_section.getint('level', fallback=DEFAULT_MAX_LEVEL)
    final_level = args.level if args.level is not None else level_from_config_file
    
    # Submodules
    show_submodules = args.show_submodules if args.show_submodules else \
                      config_section.getboolean('show-submodules', fallback=FALLBACK_SHOW_SUBMODULES)

    # Gitignore Logic
    use_gitignore_from_config = config_section.getboolean(
        'use-gitignore', 
        fallback=FALLBACK_USE_GITIGNORE
    )
    final_use_gitignore = False if args.no_gitignore else use_gitignore_from_config
    
    gitignore_spec: Optional['pathspec.PathSpec'] = None
    if is_git_repo and final_use_gitignore:
        logger.debug("Git repository detected. Loading .gitignore patterns via pathspec.")
        gitignore_spec = parse_gitignore(start_dir)
    elif is_git_repo and not final_use_gitignore:
        logger.debug("Git repository detected, but skipping .gitignore (due to flag or config).")
    else:
        logger.debug("Not a Git repository. Skipping .gitignore.")

    # Ignore List
    ignore_cli = parse_comma_list(args.ignore)
    ignore_file = parse_comma_list(config_section.get('ignore', fallback=None))
    final_ignore_list = DEFAULT_IGNORE.union(ignore_file).union(ignore_cli)

    # Prune List
    prune_cli = parse_comma_list(args.prune) 
    prune_file = parse_comma_list(config_section.get('prune', fallback=None))
    final_prune_list = DEFAULT_PRUNE.union(prune_file).union(prune_cli)

    # Dirs Only List
    dirs_only_cli = args.dirs_only
    dirs_only_file = config_section.get('dirs-only', fallback=None)
    final_dirs_only_mode = dirs_only_cli if dirs_only_cli is not None else dirs_only_file
    
    global_dirs_only = final_dirs_only_mode == '_ALL_'
    dirs_only_list_custom = set()
    if final_dirs_only_mode is not None and not global_dirs_only:
        dirs_only_list_custom = parse_comma_list(final_dirs_only_mode)
    final_dirs_only_list = DEFAULT_DIRS_ONLY_LOGIC.union(dirs_only_list_custom)
    
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
    Injects default values into the .ini template string.
    (Pure logic, moved from scripts/tree.py)
    """
    
    def _format_set_to_ini(value_set: Set[str]) -> str:
        """Helper to convert a set to a comma-separated INI string."""
        if not value_set:
            return "" # Return empty string if set is empty
        return ", ".join(sorted(list(value_set)))

    # Format values for INI
    ini_level = (
        f"level = {DEFAULT_MAX_LEVEL}" 
        if DEFAULT_MAX_LEVEL is not None 
        else f"; level = "
    )
    ini_show_submodules = str(FALLBACK_SHOW_SUBMODULES).lower()
    ini_use_gitignore = str(FALLBACK_USE_GITIGNORE).lower()
    ini_ignore = _format_set_to_ini(DEFAULT_IGNORE)
    ini_prune = _format_set_to_ini(DEFAULT_PRUNE)
    ini_dirs_only = _format_set_to_ini(DEFAULT_DIRS_ONLY_LOGIC)

    # Format the template string
    try:
        dynamic_template = template_content.format(
            config_section_name=CONFIG_SECTION_NAME,
            ini_level=ini_level,
            ini_show_submodules=ini_show_submodules,
            ini_use_gitignore=ini_use_gitignore,
            ini_ignore=ini_ignore,
            ini_prune=ini_prune,
            ini_dirs_only=ini_dirs_only
        )
        return dynamic_template
    except KeyError as e:
        print(f"FATAL ERROR: Template key mismatch: {e}")
        return "; ERROR: Template file is missing a placeholder."