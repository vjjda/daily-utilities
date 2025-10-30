# Path: modules/pack_code/pack_code_internal/pack_code_builder.py
"""
Logic ghép nối chuỗi nội dung đóng gói cuối cùng.
(Module nội bộ, được import bởi pack_code_core)
"""

from pathlib import Path
from typing import Dict, Any, List, Optional

__all__ = ["assemble_packed_content"]


def assemble_packed_content(
    files_to_pack: List[Path],
    files_content: Dict[Path, str],
    scan_root: Path,
    tree_str: str,
    no_header: bool,
    dry_run: bool,
) -> str:
    """
    Xây dựng chuỗi nội dung output cuối cùng từ các phần đã thu thập.

    Args:
        files_to_pack: Danh sách Path các file (đã sắp xếp).
        files_content: Dict ánh xạ Path -> nội dung file (str).
        scan_root: Gốc quét (để tính đường dẫn tương đối cho header).
        tree_str: Chuỗi cây thư mục (có thể rỗng).
        no_header: True nếu không cần in header "===== Path: ... =====".
        dry_run: True nếu đang ở chế độ dry-run (sẽ không thêm nội dung file).

    Returns:
        Chuỗi string chứa toàn bộ nội dung đã đóng gói.
    """

    final_content_lines: List[str] = []

    # 1. Thêm cây thư mục (nếu có)
    if tree_str:
        final_content_lines.append(tree_str)
        final_content_lines.append("\n" + ("=" * 80) + "\n")

    # 2. Thêm nội dung file (chỉ khi không phải dry_run)
    if not dry_run:
        for file_path in files_to_pack:
            content = files_content.get(file_path)
            if content is None:
                # Bỏ qua file không đọc được (đã log trong loader)
                continue

            try:
                # Tính đường dẫn tương đối cho header
                rel_path_str = file_path.relative_to(scan_root).as_posix()
            except ValueError:
                 rel_path_str = file_path.as_posix() # Fallback nếu không cùng cây

            # Thêm header (nếu cần)
            if not no_header:
                header = f"===== Path: {rel_path_str} ====="
                final_content_lines.append(header)

            # Thêm nội dung file
            final_content_lines.append(content)

            # Thêm dòng trống sau nội dung (nếu có header)
            if not no_header:
                final_content_lines.append("\n")

    return "\n".join(final_content_lines)