# Path: utils/core/filter.py

"""
File Filtering and Path Matching Utilities
(Internal module, imported by utils/core.py)

GIAI ĐOẠN 0: Chứa logic fnmatch cũ.
GIAI ĐOẠN 1: Sẽ được thay thế bằng gitignore-parser.
"""

import fnmatch
import os
from pathlib import Path
from typing import Set

# --- NEW: Export list ---
__all__ = ["is_path_matched", "parse_gitignore"]

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

def parse_gitignore(root: Path) -> Set[str]:
    """
    Parses a .gitignore file and returns a set of non-empty, non-comment patterns.
    (Code moved from utils/core.py)
    """
    gitignore_path = root / ".gitignore"
    patterns = set()
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped_line = line.strip()
                    
                    if not stripped_line or stripped_line.startswith('#'):
                        continue

                    if stripped_line.startswith('/'):
                        stripped_line = stripped_line[1:]

                    if stripped_line:
                        patterns.add(stripped_line)
                        
        except Exception as e:
            print(f"Warning: Could not read .gitignore file: {e}")
    return patterns