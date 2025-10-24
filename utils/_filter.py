#!/usr/bin/env python3
# Path: utils/_filter.py

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

def is_path_matched(path: Path, patterns: Set[str], start_dir: Path) -> bool:
    """Checks if a path matches any pattern (using fnmatch for name or relative path)."""
    if not patterns: 
        return False
    
    relative_path = path.relative_to(start_dir)
    relative_path_str = relative_path.as_posix()
    
    # --- FIX: Lấy tất cả các phần của đường dẫn ---
    # Ví dụ: Path('a/b/c.txt') -> ('a', 'b', 'c.txt')
    path_parts = relative_path.parts 

    for pattern in patterns: 
        # Check 1: Match full relative path (e.g., 'docs/drafts', 'build/')
        if fnmatch.fnmatch(relative_path_str, pattern):
            return True
        
        # Check 2: Match just the name (e.g., '.DS_Store', '*.log')
        if fnmatch.fnmatch(path.name, pattern):
            return True

        # Check 3 (FIX): Match any part of the path (e.g., '.venv', 'build')
        # Điều này xử lý khi 'build' nằm trong .gitignore và chúng ta đang kiểm tra 'build/main.py'
        if any(fnmatch.fnmatch(part, pattern) for part in path_parts):
            return True
            
    return False

def parse_gitignore(root: Path) -> Set[str]:
    """Parses a .gitignore file and returns a set of non-empty, non-comment patterns."""
    gitignore_path = root / ".gitignore"
    patterns = set()
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped_line = line.strip()
                    
                    # 1. Bỏ qua comment hoặc dòng trống
                    if not stripped_line or stripped_line.startswith('#'):
                        continue

                    # --- FIX: Chuẩn hóa pattern ---
                    # Xử lý trường hợp pattern bắt đầu bằng '/' (ví dụ: /build)
                    # Chúng ta loại bỏ nó để khớp với đường dẫn tương đối (ví dụ: build)
                    # vì is_path_matched luôn so sánh với đường dẫn tương đối.
                    if stripped_line.startswith('/'):
                        stripped_line = stripped_line[1:]
                    # --- END FIX ---

                    # 2. Thêm pattern đã chuẩn hóa (nếu nó không rỗng)
                    if stripped_line:
                        patterns.add(stripped_line)
                        
        except Exception as e:
            # We don't use logger here as this might be called before logging is set up
            print(f"Warning: Could not read .gitignore file: {e}")
    return patterns