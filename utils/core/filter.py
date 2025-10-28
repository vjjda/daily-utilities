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

# --- MODIFIED: Nâng cấp hàm biên dịch spec ---
def compile_spec_from_patterns(
    patterns: Set[str],
    scan_root: Path # <-- NEW: Thêm scan_root
) -> Optional['pathspec.PathSpec']:
    """
    Biên dịch một Set các pattern thành một đối tượng PathSpec.
    
    Mô phỏng hành vi của Git: Nếu một pattern (ví dụ: '.venv')
    không chứa '/' và khớp với một thư mục tại scan_root,
    nó sẽ được tự động xử lý như '.venv/'.
    """
    if pathspec is None or not patterns:
        return None
    
    # --- NEW: Logic mô phỏng Git ---
    processed_patterns: Set[str] = set()
    for pattern in patterns:
        # Nếu pattern không chứa '/' (ví dụ: '.venv', '__pycache__')
        # VÀ một thư mục có tên đó tồn tại trong thư mục gốc quét
        if '/' not in pattern and (scan_root / pattern).is_dir():
            # Thêm dấu / để đảm bảo pathspec bỏ qua toàn bộ thư mục
            processed_patterns.add(f"{pattern}/")
        else:
            processed_patterns.add(pattern)
    # --- END NEW ---
    
    try:
        # Sử dụng 'gitwildmatch' để có cú pháp giống .gitignore
        # Biên dịch các pattern đã được xử lý
        spec = pathspec.PathSpec.from_lines('gitwildmatch', list(processed_patterns))
        return spec
    except Exception:
        return None # (Có thể log lỗi nếu cần)
# --- END MODIFIED ---


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
        # --- MODIFIED: Xử lý lỗi nếu path không nằm trong start_dir ---
        # (Điều này xảy ra nếu start_dir là thư mục con,
        # nhưng path là file .gitignore ở thư mục cha)
        try:
            relative_path = path.relative_to(start_dir)
        except ValueError:
            # Nếu không thể tính tương đối, dùng đường dẫn tuyệt đối
            # (pathspec có thể xử lý cả hai)
            relative_path_str = path.as_posix()
        else:
            relative_path_str = relative_path.as_posix()
        # --- END MODIFIED ---
        
        # Thêm dấu / cho thư mục (nếu chưa có) để khớp chính xác
        if path.is_dir() and not relative_path_str.endswith('/'):
            relative_path_str += '/'
        
        if relative_path_str == './':
            return False

        return spec.match_file(relative_path_str) 
    except Exception:
        return False