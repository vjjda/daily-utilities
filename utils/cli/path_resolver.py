# Path: utils/cli/path_resolver.py
"""
Tiện ích xử lý và xác thực danh sách đường dẫn đầu vào từ CLI.
Chuyển đổi danh sách chuỗi đường dẫn thô thành danh sách các đối tượng Path
đã được kiểm tra là tồn tại.
"""

import logging
from pathlib import Path
from typing import List, Set, Optional

__all__ = ["resolve_input_paths"]


def resolve_input_paths(
    logger: logging.Logger,
    raw_paths: List[str],
    default_path_str: str
) -> List[Path]:
    """
    Xử lý danh sách đường dẫn thô từ CLI (nargs='*').
    - Sử dụng default_path_str nếu raw_paths rỗng.
    - Mở rộng (expanduser) và resolve() từng đường dẫn.
    - Lọc ra các đường dẫn không tồn tại và log lỗi.

    Args:
        logger: Logger.
        raw_paths: Danh sách chuỗi đường dẫn thô từ argparse (nargs='*').
        default_path_str: Đường dẫn mặc định (dưới dạng chuỗi) nếu raw_paths rỗng.

    Returns:
        List[Path]: Danh sách các đường dẫn hợp lệ, đã được resolve.
    """
    validated_paths: List[Path] = []
    
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
            
        validated_paths.append(start_path)

    return validated_paths