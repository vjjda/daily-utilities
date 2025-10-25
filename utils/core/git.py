# Path: utils/core/git.py

"""
Git and Filesystem Utilities
(Internal module, imported by utils/core.py)
"""

import logging
import configparser
from pathlib import Path
# --- MODIFIED: Thêm TYPE_CHECKING ---
from typing import Set, Optional, List, TYPE_CHECKING
# --- END MODIFIED ---

# --- MODIFIED: Tách biệt import cho runtime và type-checking ---
try:
    import pathspec
except ImportError:
    print("Warning: 'pathspec' library not found. .gitignore parsing will be basic.")
    print("Please run 'pip install pathspec' for full .gitignore support.")
    pathspec = None

if TYPE_CHECKING:
    import pathspec
# --- END MODIFIED ---

# --- MODIFIED: Thêm parse_gitignore ---
__all__ = ["is_git_repository", "find_git_root", "get_submodule_paths", "parse_gitignore"]
# --- END MODIFIED ---

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

# --- NEW: Nâng cấp parse_gitignore với pathspec ---
def parse_gitignore(root: Path) -> Optional['pathspec.PathSpec']:
    """
    Parses a .gitignore file using 'pathspec' and returns a compiled spec.
    """
    if pathspec is None:
        return None # Trả về None nếu thư viện không được cài đặt

    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return None # Không có file .gitignore

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Thêm các quy tắc mặc định mà Git luôn áp dụng
        lines.append(".git")
            
        spec = pathspec.PathSpec.from_lines('gitwildmatch', lines)
        return spec
        
    except Exception as e:
        print(f"Warning: Could not read or compile .gitignore file: {e}")
        return None
# --- END NEW ---