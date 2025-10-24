#!/usr/bin/env python3
# Path: utils/core/filter.py

"""
File Filtering and Path Matching Utilities
(Internal module, imported by utils/core.py)

GIAI ĐOẠN 1: Tích hợp gitignore-parser
- Xóa parse_gitignore() cũ.
- Đổi tên is_path_matched() -> _is_path_matched_custom()
- Thêm class PathFilter mới.
"""

import sys
import fnmatch
from pathlib import Path
from typing import Set, Optional, Callable

# --- 1. Thư viện Gitignore (Engine mới) ---
try:
    import gitignore_parser
    GITIGNORE_PARSER_AVAILABLE = True
except ImportError:
    # In ra stderr để không ảnh hưởng đến output của tool
    print(
        "Warning: 'gitignore-parser' not found. "
        "Run 'pip install gitignore-parser' to enable .gitignore negation.",
        file=sys.stderr
    )
    gitignore_parser = None
    GITIGNORE_PARSER_AVAILABLE = False


# --- 2. Logic fnmatch (Engine cũ) ---
# (Được giữ lại cho các pattern custom từ CLI/Config)

def _is_path_matched_custom(
    path: Path, 
    patterns: Set[str], 
    start_dir: Path
) -> bool:
    """
    Kiểm tra xem một đường dẫn có khớp với bất kỳ pattern custom
    nào (sử dụng logic fnmatch cũ).
    """
    if not patterns: 
        return False
    
    # Chúng ta cần try...except ở đây vì start_dir có thể không phải
    # là cha của path (ví dụ: khi kiểm tra path tuyệt đối)
    try:
        relative_path = path.relative_to(start_dir)
        relative_path_str = relative_path.as_posix()
        path_parts = relative_path.parts
    except ValueError:
        # Fallback về kiểm tra tên
        relative_path_str = path.name
        path_parts = (path.name,)

    for pattern in patterns: 
        # Check 1: Match full relative path
        if fnmatch.fnmatch(relative_path_str, pattern):
            return True
        
        # Check 2: Match just the name
        if fnmatch.fnmatch(path.name, pattern):
            return True

        # Check 3: Match any part of the path
        if any(fnmatch.fnmatch(part, pattern) for part in path_parts):
            return True
            
    return False


# --- 3. Bộ lọc chính (Class PathFilter) ---

class PathFilter:
    """
    Một class bao bọc logic lọc file, kết hợp cả .gitignore (với negation)
    và các pattern 'custom' (từ config, CLI).
    """
    def __init__(self, 
                 root_path: Path, 
                 custom_ignore_patterns: Set[str], 
                 use_gitignore: bool = True):
        
        self.root_path = root_path
        self.custom_patterns = custom_ignore_patterns
        self.gitignore_matcher: Optional[Callable] = None
        
        gitignore_file = root_path / ".gitignore"
        
        if use_gitignore and GITIGNORE_PARSER_AVAILABLE and gitignore_file.exists():
            try:
                # 'base_dir' rất quan trọng để xử lý các
                # pattern neo gốc (ví dụ: /build)
                self.gitignore_matcher = gitignore_parser.parse_gitignore(
                    str(gitignore_file), base_dir=str(root_path)
                )
            except Exception as e:
                print(f"Warning: Could not parse .gitignore file: {e}", file=sys.stderr)

    def matches(self, path_to_check: Path) -> bool:
        """
        Kiểm tra xem một đường dẫn có nên bị BỎ QUA hay không.
        Trả về True nếu path nên bị bỏ qua.
        """
        
        abs_path = path_to_check.resolve()

        # 1. Kiểm tra .gitignore trước (Engine mới, hỗ trợ negation !)
        if self.gitignore_matcher:
            # Thư viện này cần đường dẫn tuyệt đối
            if self.gitignore_matcher(abs_path):
                # .gitignore nói "Bỏ qua file này" (và không bị luật ! nào phủ định)
                return True 

        # 2. Kiểm tra các pattern custom (Engine cũ)
        # (Chúng ta giữ logic này tách biệt vì nó không hỗ trợ negation)
        if _is_path_matched_custom(
            abs_path, 
            self.custom_patterns, 
            self.root_path
        ):
            return True

        return False