# Path: utils/core/filter.py

"""
File Filtering and Path Matching Utilities
(Internal module, imported by utils/core.py)

Đã refactor để sử dụng 'pathspec' làm engine thống nhất.
"""

# --- MODIFIED: Thêm imports ---
from pathlib import Path
from typing import Set, TYPE_CHECKING, Optional, Iterable # <-- Thêm Iterable
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
    patterns_iterable: Iterable[str], # <-- MODIFIED: Nhận Iterable (List, Set, ...)
    scan_root: Path
) -> Optional['pathspec.PathSpec']:
    """
    Biên dịch một Iterable các pattern thành một đối tượng PathSpec.

    Mô phỏng hành vi của Git: Nếu một pattern (ví dụ: '.venv')
    không chứa '/' và khớp với một thư mục tại scan_root,
    nó sẽ được tự động xử lý như '.venv/'.
    """
    if pathspec is None:
        return None

    # Chuyển đổi Iterable thành List để xử lý
    patterns = list(patterns_iterable)
    if not patterns:
        return None

    # --- NEW: Logic mô phỏng Git ---
    processed_patterns: List[str] = [] # Giữ thứ tự
    for pattern in patterns:
        # Nếu pattern không chứa '/' (ví dụ: '.venv', '__pycache__')
        # VÀ một thư mục có tên đó tồn tại trong thư mục gốc quét
        if '/' not in pattern and (scan_root / pattern).is_dir():
            # Thêm dấu / để đảm bảo pathspec bỏ qua toàn bộ thư mục
            processed_patterns.append(f"{pattern}/")
        else:
            processed_patterns.append(pattern)
    # --- END NEW ---

    try:
        # Sử dụng 'gitwildmatch' để có cú pháp giống .gitignore
        # Biên dịch các pattern đã được xử lý (giữ nguyên thứ tự)
        spec = pathspec.PathSpec.from_lines('gitwildmatch', processed_patterns)
        return spec
    except Exception as e: # Bắt lỗi cụ thể hơn nếu cần
        # Log lỗi nếu cần thiết
        # logger.error(f"Error compiling pathspec patterns: {e}")
        return None # (Có thể log lỗi nếu cần)
# --- END MODIFIED ---


def is_path_matched(
    path: Path,
    spec: Optional['pathspec.PathSpec'], # <-- MODIFIED: Nhận spec
    start_dir: Path # Giữ lại start_dir để tính relative path
) -> bool:
    """
    Kiểm tra xem một đường dẫn có khớp với 'PathSpec' đã biên dịch không.
    (Đã sửa để dùng pathspec)
    """
    if spec is None:
        return False

    try:
        # --- MODIFIED: Xử lý lỗi nếu path không nằm trong start_dir ---
        try:
            # pathspec hoạt động tốt nhất với đường dẫn tương đối từ gốc repo/quét
            relative_path = path.resolve().relative_to(start_dir.resolve())
        except ValueError:
            # Nếu không thể tính tương đối (ví dụ: path nằm ngoài start_dir),
            # sử dụng đường dẫn tuyệt đối POSIX. pathspec vẫn có thể xử lý.
            relative_path_str = path.resolve().as_posix()
        else:
            relative_path_str = relative_path.as_posix()
        # --- END MODIFIED ---

        # Thêm dấu / cho thư mục (nếu chưa có) để khớp chính xác
        if path.is_dir() and not relative_path_str.endswith('/'):
             # Chỉ thêm '/' nếu nó chưa phải là thư mục gốc tương đối '.'
             if relative_path_str != '.':
                 relative_path_str += '/'

        # Không khớp với thư mục gốc (tránh lỗi)
        if relative_path_str == '.' or relative_path_str == './':
            return False

        return spec.match_file(relative_path_str)
    except Exception as e:
         # Log lỗi nếu cần thiết
         # logger.debug(f"Error matching path '{path}' with spec: {e}")
        return False