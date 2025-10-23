#!/usr/bin/env python3
# Path: modules/tree/tree_core.py

from pathlib import Path
import logging 
# --- NEW: Imports moved from old tree_config.py ---
import configparser
import argparse
# --- END NEW ---
from typing import List, Set, Optional, Dict, Any

# --- IMPORT UTILITIES FROM CENTRAL LOCATION ---
from utils.core import is_path_matched
# --- NEW: Imports moved from old tree_config.py ---
from utils.core import get_submodule_paths, parse_comma_list
# --- END NEW ---

# --- MODULE-SPECIFIC CONSTANTS (NOW IMPORTED) ---
# --- MODIFIED: Import from new SSOT config file ---
from .tree_config import (
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL, CONFIG_FILENAME, PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME, FALLBACK_SHOW_SUBMODULES
)
# --- END MODIFIED ---

# --- LOGIC MOVED FROM old tree_config.py ---
def load_and_merge_config(
    args: argparse.Namespace, 
    start_dir: Path, 
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Loads configuration from .ini files and merges them with CLI arguments.
    Priority order: CLI > .tree.ini > .project.ini > Defaults.
    """
    
    # 1. Read Config from Files
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

    # Ensure [tree] section exists
    if CONFIG_SECTION_NAME not in config:
        config.add_section(CONFIG_SECTION_NAME)
        logger.debug(f"Added empty '{CONFIG_SECTION_NAME}' section for safe fallback.")

    # 2. Merge Configs (CLI > File > Default)
    
    # Level
    # --- MODIFIED: Use imported constants ---
    level_from_config_file = config.getint(CONFIG_SECTION_NAME, 'level', fallback=DEFAULT_MAX_LEVEL)
    final_level = args.level if args.level is not None else level_from_config_file
    
    # Submodules
    show_submodules = args.show_submodules if args.show_submodules is not None else \
                      config.getboolean(CONFIG_SECTION_NAME, 'show-submodules', fallback=FALLBACK_SHOW_SUBMODULES)

    # Ignore List
    ignore_cli = parse_comma_list(args.ignore)
    ignore_file = parse_comma_list(config.get(CONFIG_SECTION_NAME, 'ignore', fallback=None))
    final_ignore_list = DEFAULT_IGNORE.union(ignore_file).union(ignore_cli)

    # Prune List
    prune_cli = parse_comma_list(args.prune) 
    prune_file = parse_comma_list(config.get(CONFIG_SECTION_NAME, 'prune', fallback=None))
    final_prune_list = DEFAULT_PRUNE.union(prune_file).union(prune_cli)

    # Dirs Only List
    dirs_only_cli = args.dirs_only
    dirs_only_file = config.get(CONFIG_SECTION_NAME, 'dirs-only', fallback=None)
    # --- END MODIFIED ---
    final_dirs_only_mode = dirs_only_cli if dirs_only_cli is not None else dirs_only_file
    
    global_dirs_only = final_dirs_only_mode == '_ALL_'
    dirs_only_list_custom = set()
    if final_dirs_only_mode is not None and not global_dirs_only:
        dirs_only_list_custom = parse_comma_list(final_dirs_only_mode)
    # --- MODIFIED: Use imported constant ---
    final_dirs_only_list = DEFAULT_DIRS_ONLY_LOGIC.union(dirs_only_list_custom)
    # --- END MODIFIED ---
    
    # Calculate Submodule Names
    submodule_names: Set[str] = set()
    if not show_submodules: 
        submodule_paths = get_submodule_paths(start_dir, logger=logger)
        submodule_names = {p.name for p in submodule_paths}

    # 3. Return a dict of processed settings
    return {
        "max_level": final_level,
        "ignore_list": final_ignore_list,
        "submodules": submodule_names,
        "prune_list": final_prune_list,
        "dirs_only_list": final_dirs_only_list,
        "is_in_dirs_only_zone": global_dirs_only,
        # Add other info for user printing
        "global_dirs_only_flag": global_dirs_only,
        "filter_lists": {
            "ignore": final_ignore_list,
            "prune": final_prune_list,
            "dirs_only": final_dirs_only_list,
            "submodules": submodule_names
        }
    }
# --- END MOVED LOGIC ---


# --- MAIN RECURSIVE LOGIC ---
# --- MODIFIED: Updated signature to use imported defaults ---
def generate_tree(
    directory: Path, 
    start_dir: Path, 
    prefix: str = "", 
    level: int = 0, 
    max_level: Optional[int] = DEFAULT_MAX_LEVEL, 
    ignore_list: Set[str] = DEFAULT_IGNORE, 
    submodules: Set[str] = None, # Submodules are calculated, so None is fine
    prune_list: Set[str] = DEFAULT_PRUNE,
    dirs_only_list: Set[str] = DEFAULT_DIRS_ONLY_LOGIC, 
    is_in_dirs_only_zone: bool = False, 
    counters: Dict[str, int] = None
):
# --- END MODIFIED ---
    """
    Recursive function to generate and print the directory tree.
    """
    if max_level is not None and level >= max_level: 
        return
    
    try: 
        # Get contents, ignoring hidden files/folders (starting with '.')
        contents = [path for path in directory.iterdir() if not path.name.startswith('.')]
    except (FileNotFoundError, NotADirectoryError): 
        return
        
    # Filter directories: exclude items in ignore_list
    dirs = sorted(
        [d for d in contents if d.is_dir() and not is_path_matched(d, ignore_list, start_dir)], 
        key=lambda p: p.name.lower()
    )
    
    files: List[Path] = []
    # Filter files: only show if NOT in a dirs-only zone
    if not is_in_dirs_only_zone: 
        files = sorted(
            [f for f in contents if f.is_file() and not is_path_matched(f, ignore_list, start_dir)], 
            key=lambda p: p.name.lower()
        )
        
    items_to_print = dirs + files
    pointers = ["├── "] * (len(items_to_print) - 1) + ["└── "]

    for pointer, path in zip(pointers, items_to_print):
        if path.is_dir(): 
            counters['dirs'] += 1
        else: 
            counters['files'] += 1

        is_submodule = path.is_dir() and path.name in submodules
        is_pruned = path.is_dir() and is_path_matched(path, prune_list, start_dir)
        
        # Check if this directory is the start of a dirs-only rule
        is_dirs_only_entry = (
            path.is_dir() and 
            is_path_matched(path, dirs_only_list, start_dir) and 
            not is_in_dirs_only_zone
        ) 
        
        line = f"{prefix}{pointer}{path.name}{'/' if path.is_dir() else ''}"
        
        # Add suffixes
        if is_submodule: 
            line += " [submodule]"
        elif is_pruned: 
            line += " [...]"
        elif is_dirs_only_entry: 
            line += " [dirs only]"
        
        print(line)

        # Recurse condition: is a directory AND not a submodule AND not pruned
        if path.is_dir() and not is_submodule and not is_pruned:
            extension = "│   " if pointer == "├── " else "    " 
            
            # Update flag: If already in a dirs-only zone OR this is a new dirs-only entry
            next_is_in_dirs_only_zone = is_in_dirs_only_zone or is_dirs_only_entry
            
            # Recurse
            generate_tree(
                path, start_dir, prefix + extension, level + 1, max_level, 
                ignore_list, submodules, prune_list, dirs_only_list, 
                next_is_in_dirs_only_zone, counters
            )

# --- CONFIG TEMPLATE CONTENT (Loaded from file) ---

try:
    # Get the directory containing this 'tree_core.py' file
    _CURRENT_DIR = Path(__file__).parent
    # Full path to the template file
    _TEMPLATE_PATH = _CURRENT_DIR / "tree.ini.template"
    # Read the content and assign to the variable
    CONFIG_TEMPLATE = _TEMPLATE_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    print("FATAL ERROR: Could not find 'tree.ini.template'.")
    CONFIG_TEMPLATE = "; ERROR: Template file missing."
except Exception as e:
    print(f"FATAL ERROR: Could not read 'tree.ini.template': {e}")
    CONFIG_TEMPLATE = "; ERROR: Template file could not be read."