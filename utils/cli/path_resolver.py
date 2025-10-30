# Path: utils/cli/path_resolver.py
"""
Tiện ích xử lý và xác thực danh sách đường dẫn đầu vào từ CLI.

Chuyển đổi danh sách chuỗi đường dẫn thô thành danh sách các "Tác vụ quét",
mỗi tác vụ chứa đường dẫn bắt đầu (start_path) và gốc quét
(scan_root, thường là gốc Git) tương ứng của nó.
"""

import logging
from pathlib import Path
from typing import List, Tuple, Set, NamedTuple, Optional

# Import tiện ích UI để xác thực gốc
from .ui_helpers import handle_project_root_validation

__all__ = ["ScanTask", "resolve_scan_tasks"]


class ScanTask(NamedTuple):
    """
    Đại diện cho một tác vụ quét đã được xác thực.
    Bao gồm đường dẫn mà người dùng chỉ định và gốc quét
    (thường là .git root) được tìm thấy cho đường dẫn đó.
    """
    start_path: Path   # Đường dẫn người dùng nhập (đã resolve)
    scan_root: Path    # Gốc Git (hoặc fallback) của đường dẫn đó


def resolve_scan_tasks(
    logger: logging.Logger,
    raw_paths: List[str],
    default_path_str: str,
    force_silent: bool = False
) -> Tuple[List[ScanTask], Set[str]]:
    """
    Xử lý danh sách đường dẫn thô từ CLI, xác thực gốc Git
    cho từng đường dẫn.

    Args:
        logger: Logger.
        raw_paths: Danh sách chuỗi đường dẫn thô từ argparse (nargs='*').
        default_path_str: Đường dẫn mặc định (dưới dạng chuỗi) nếu raw_paths rỗng.
        force_silent: True để bỏ qua các prompt xác thực (ví dụ: khi có --force).

    Returns:
        Một Tuple:
        (List[ScanTask]): Danh sách các tác vụ quét hợp lệ.
        (Set[str]): Một tập hợp các chuỗi cảnh báo Git (nếu có).
    """
    scan_tasks: List[ScanTask] = []
    git_warnings: Set[str] = set()

    # Nếu không có đường dẫn nào được cung cấp, sử dụng đường dẫn mặc định
    paths_to_process = raw_paths if raw_paths else [default_path_str]

    for path_str in paths_to_process:
        try:
            start_path = Path(path_str).expanduser().resolve()
        except Exception as e:
            logger.error(f"❌ Lỗi khi xử lý đường dẫn '{path_str}': {e}")
            continue # Bỏ qua đường dẫn này

        if not start_path.exists():
            logger.error(f"❌ Lỗi: Đường dẫn không tồn tại: {start_path}")
            continue  # Bỏ qua đường dẫn không hợp lệ

        # Xác định thư mục để bắt đầu tìm gốc (parent nếu là file)
        root_to_search = start_path.parent if start_path.is_file() else start_path

        # Gọi tiện ích xác thực gốc dùng chung
        effective_scan_root, git_warning = handle_project_root_validation(
            logger=logger,
            scan_root=root_to_search,
            force_silent=force_silent
        ) # 

        if effective_scan_root:
            # Nếu người dùng không "Quit", thêm tác vụ hợp lệ
            scan_tasks.append(ScanTask(start_path, effective_scan_root))
            if git_warning:
                git_warnings.add(git_warning) # [cite: 1163]
        # (Nếu effective_scan_root là None, người dùng đã 'Quit',
        #  hàm handle_project_root_validation đã log lỗi)

    return scan_tasks, git_warnings