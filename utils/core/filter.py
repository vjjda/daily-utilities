# Path: utils/core/filter.py

"""
Các tiện ích lọc file và khớp đường dẫn sử dụng thư viện 'pathspec'.
(Module nội bộ, được import bởi utils/core)
"""

from pathlib import Path
from typing import List, TYPE_CHECKING, Optional, Iterable
import logging # Thêm logging

# Import pathspec để kiểm tra type và sử dụng
try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

__all__ = ["is_path_matched", "compile_spec_from_patterns"]

# Khởi tạo logger cho module này (nếu cần log lỗi biên dịch)
logger = logging.getLogger(__name__)

def compile_spec_from_patterns(
    patterns_iterable: Iterable[str],
    scan_root: Path
) -> Optional['pathspec.PathSpec']:
    """
    Biên dịch một Iterable (List, Set, ...) các pattern thành đối tượng PathSpec.

    Mô phỏng hành vi của Git: Nếu một pattern (ví dụ: '.venv')
    không chứa '/' và khớp với một thư mục tại `scan_root`,
    nó sẽ được tự động xử lý như một pattern thư mục (`.venv/`).

    Args:
        patterns_iterable: Iterable chứa các chuỗi pattern (giống .gitignore).
        scan_root: Thư mục gốc dùng làm cơ sở để kiểm tra sự tồn tại của thư mục.

    Returns:
        Đối tượng `pathspec.PathSpec` đã biên dịch, hoặc None nếu `pathspec`
        không được cài đặt hoặc không có pattern nào.
    """
    if pathspec is None:
        logger.warning("Thư viện 'pathspec' không được cài đặt. Việc lọc file sẽ bị hạn chế.") #
        return None

    # Chuyển đổi Iterable thành List để xử lý
    patterns = list(patterns_iterable)
    if not patterns:
        return None # Không có gì để biên dịch

    # Xử lý các pattern thư mục giống Git
    processed_patterns: List[str] = [] # Giữ thứ tự gốc
    for pattern in patterns:
        # Bỏ qua pattern rỗng
        if not pattern:
            continue
        # Nếu pattern không chứa '/' và khớp với thư mục tại gốc quét
        if '/' not in pattern and (scan_root / pattern).is_dir():
            # Thêm dấu '/' để pathspec hiểu là bỏ qua toàn bộ thư mục
            processed_patterns.append(f"{pattern}/")
        else:
            processed_patterns.append(pattern)

    if not processed_patterns:
        return None

    try:
        # Sử dụng 'gitwildmatch' để có cú pháp giống .gitignore
        spec = pathspec.PathSpec.from_lines('gitwildmatch', processed_patterns)
        return spec
    except Exception as e:
        logger.error(f"Lỗi khi biên dịch các pattern pathspec: {e}") #
        logger.debug(f"Patterns gây lỗi: {processed_patterns}") #
        return None

def is_path_matched(
    path: Path,
    spec: Optional['pathspec.PathSpec'],
    start_dir: Path
) -> bool:
    """
    Kiểm tra xem một đường dẫn có khớp với 'PathSpec' đã biên dịch không.

    Args:
        path: Đường dẫn cần kiểm tra (có thể là file hoặc thư mục).
        spec: Đối tượng `pathspec.PathSpec` đã biên dịch (từ `compile_spec_from_patterns`).
        start_dir: Thư mục gốc được sử dụng khi biên dịch `spec` (để tính đường dẫn tương đối).

    Returns:
        True nếu đường dẫn khớp với `spec`, False nếu không khớp,
        `spec` là None, hoặc có lỗi xảy ra.
    """
    if spec is None:
        return False

    try:
        # pathspec hoạt động tốt nhất với đường dẫn tương đối từ gốc quét
        relative_path: Path
        try:
            relative_path = path.resolve().relative_to(start_dir.resolve())
        except ValueError:
            # Nếu không thể tính tương đối (ví dụ: path nằm ngoài start_dir),
            # sử dụng đường dẫn tuyệt đối dạng POSIX. pathspec vẫn có thể xử lý.
            relative_path_str = path.resolve().as_posix()
        else:
            relative_path_str = relative_path.as_posix()

        # Thêm dấu '/' cho thư mục (nếu chưa có) để khớp chính xác pattern thư mục
        if path.is_dir() and not relative_path_str.endswith('/'):
             # Chỉ thêm '/' nếu nó không phải là thư mục gốc tương đối '.'
             if relative_path_str != '.':
                 relative_path_str += '/'

        # Không khớp với chính thư mục gốc (tránh lỗi)
        if relative_path_str == '.' or relative_path_str == './':
            return False

        return spec.match_file(relative_path_str)
    except Exception as e:
         logger.debug(f"Lỗi khi khớp đường dẫn '{path}' với spec: {e}") #
         return False