#!/usr/bin/env python3
# Path: modules/tree/tree_core.py

from pathlib import Path
import logging 
from typing import List, Set, Optional, Dict

# --- IMPORT UTILITIES FROM CENTRAL LOCATION ---
from utils.core import is_path_matched
# --------------------------------------------

# --- MODULE-SPECIFIC CONSTANTS ---
DEFAULT_IGNORE: Set[str] = {
    "__pycache__", ".venv", "venv", "node_modules", 
    ".git"
}
DEFAULT_PRUNE: Set[str] = {"dist", "build"}
DEFAULT_DIRS_ONLY: Set[str] = set()
DEFAULT_MAX_LEVEL: Optional[int] = None
CONFIG_FILENAME = ".tree.ini"
PROJECT_CONFIG_FILENAME = ".project.ini" 
CONFIG_SECTION_NAME = "tree" 

# --- MAIN RECURSIVE LOGIC ---

def generate_tree(
    directory: Path, 
    start_dir: Path, 
    prefix: str = "", 
    level: int = 0, 
    max_level: Optional[int] = None, 
    ignore_list: Set[str] = DEFAULT_IGNORE, 
    submodules: Set[str] = None, 
    prune_list: Set[str] = DEFAULT_PRUNE,
    dirs_only_list: Set[str] = DEFAULT_DIRS_ONLY, 
    is_in_dirs_only_zone: bool = False, 
    counters: Dict[str, int] = None
):
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