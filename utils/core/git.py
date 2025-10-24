# Path: utils/core/git.py

"""
Git and Filesystem Utilities
(Internal module, imported by utils/core.py)
"""

import logging
import configparser
from pathlib import Path
from typing import Set, Optional

# --- NEW: Export list ---
__all__ = ["is_git_repository", "find_git_root", "get_submodule_paths"]

# ----------------------------------------------------------------------
# FILE SYSTEM & CONFIG UTILITIES
# ----------------------------------------------------------------------

def is_git_repository(root: Path) -> bool:
    """Checks if the given root path is the root of a Git repository."""
    return (root / ".git").is_dir()

def find_git_root(start_path: Path, max_levels: int = 5) -> Optional[Path]:
    """
    Traverses up the directory tree to find the nearest Git repository root.
    (Code moved from utils/core.py)
    """
    current_path = start_path.resolve()
    for _ in range(max_levels):
        if is_git_repository(current_path):
            return current_path
        
        if current_path == current_path.parent:
            break
            
        current_path = current_path.parent
        
    return None

def get_submodule_paths(root: Path, logger: Optional[logging.Logger] = None) -> Set[Path]:
    """
    Gets submodule directory full paths based on the .gitmodules file.
    (Code moved from utils/core.py)
    """
    submodule_paths = set()
    gitmodules_path = root / ".gitmodules"
    if gitmodules_path.exists():
        try:
            config = configparser.ConfigParser()
            config.read(gitmodules_path)
            for section in config.sections():
                if config.has_option(section, "path"):
                    path_str = config.get(section, "path")
                    submodule_paths.add((root / path_str).resolve())
        except configparser.Error as e:
            warning_msg = f"Could not parse .gitmodules file: {e}"
            if logger:
                logger.warning(f"⚠️ {warning_msg}")
            else:
                print(f"Warning: {warning_msg}") 
    return submodule_paths