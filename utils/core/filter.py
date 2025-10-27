# Path: utils/core/filter.py

"""
File Filtering and Path Matching Utilities
(Internal module, imported by utils/core.py)

Đã refactor để sử dụng 'pathspec' làm engine thống nhất.
"""

# --- MODIFIED: Thêm imports ---
from pathlib import Path
from typing import Set, TYPE_CHECKING, Optional
# --- END MODIFIED ---

# --- NEW: Import pathspec ---
try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec
# --- END NEW ---

# --- MODIFIED: __all__ ---
__all__ = ["is_path_matched", "compile_spec_from_patterns"]
# --- END MODIFIED ---

# --- NEW: Hàm biên dịch spec ---
def compile_spec_from_patterns(
    patterns: Set[str]
) -> Optional['pathspec.PathSpec']:
    """Biên dịch một Set các pattern thành một đối tượng PathSpec."""
    if pathspec is None or not patterns:
        return None
    
    try:
        # Sử dụng 'gitwildmatch' để có cú pháp giống .gitignore
        spec = pathspec.PathSpec.from_lines('gitwildmatch', list(patterns))
        return spec
    except Exception:
        return None # (Có thể log lỗi nếu cần)
# --- END NEW ---


def is_path_matched(
    path: Path, 
    spec: Optional['pathspec.PathSpec'], # <-- MODIFIED: Nhận spec
    start_dir: Path
) -> bool:
    """
    Kiểm tra xem một đường dẫn có khớp với 'PathSpec' đã biên dịch không.
    (Đã sửa để dùng pathspec)
    """
    if spec is None: 
        return False
    
    try:
        relative_path = path.relative_to(start_dir)
        relative_path_str = relative_path.as_posix()
        
        # Thêm dấu / cho thư mục (nếu chưa có) để khớp chính xác
        if path.is_dir() and not relative_path_str.endswith('/'):
            relative_path_str += '/'
        
        if relative_path_str == './':
            return False

        return spec.match_file(relative_path_str) 
    except Exception:
        return False