# Path: utils/core/filter.py

"""
File Filtering and Path Matching Utilities
(Internal module, imported by utils/core.py)

GIAI ĐOẠN 1: Chỉ chứa logic fnmatch.
(Logic gitignore đã được chuyển sang git.py)
"""

import fnmatch
import os
from pathlib import Path
from typing import Set

# --- MODIFIED: __all__ ---
__all__ = ["is_path_matched"]
# --- END MODIFIED ---

def is_path_matched(path: Path, patterns: Set[str], start_dir: Path) -> bool:
    """
    Checks if a path matches any pattern (using fnmatch for name or relative path).
    (Code moved from utils/core.py)
    """
    if not patterns: 
        return False
    
    relative_path = path.relative_to(start_dir)
    relative_path_str = relative_path.as_posix()
    
    path_parts = relative_path.parts 

    for pattern in patterns: 
        if fnmatch.fnmatch(relative_path_str, pattern):
            return True
        
        if fnmatch.fnmatch(path.name, pattern):
            return True

        if any(fnmatch.fnmatch(part, pattern) for part in path_parts):
            return True
            
    return False

# --- REMOVED: parse_gitignore ---
# (Logic này đã được chuyển sang utils/core/git.py và nâng cấp)
# --- END REMOVED ---