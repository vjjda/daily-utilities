# Path: utils/cli/reporting_root_resolver.py
"""
(Internal CLI Util)
Xác định Gốc Báo Cáo (Reporting Root) cho các tác vụ
cần tính toán đường dẫn tương đối.
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# Thiết lập sys.path để import utils.core
if not 'PROJECT_ROOT' in locals():
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.append(str(PROJECT_ROOT))

# Import hàm tìm Git từ utils.core
try:
    from utils.core import find_git_root
except ImportError as e:
    print(f"Lỗi: Không thể import utils.core trong reporting_root_resolver: {e}", file=sys.stderr)
    # Đây là lỗi nghiêm trọng, nhưng chúng ta có thể cho phép find_git_root = None
    find_git_root = None

__all__ = ["resolve_reporting_root"]


def _find_lca(logger: logging.Logger, paths: List[Path]) -> Path:
    """Tìm Tổ tiên Chung Gần nhất (LCA) của một danh sách đường dẫn."""
    if not paths:
        return Path.cwd()
    try:
        # Chuyển đổi thành chuỗi tuyệt đối để os.path.commonpath xử lý
        abs_path_strings = [str(p.resolve()) for p in paths]
        common_path_str = os.path.commonpath(abs_path_strings)
        lca = Path(common_path_str)
        # Đảm bảo kết quả là thư mục
        if lca.is_file():
            lca = lca.parent
        return lca
    except ValueError:
        # Xảy ra lỗi (ví dụ: C:\ và D:\ trên Windows)
        logger.debug("Không tìm thấy tổ tiên chung (ví dụ: khác ổ đĩa). Dùng CWD.")
        return Path.cwd()


def resolve_reporting_root(
    logger: logging.Logger,
    validated_paths: List[Path],
    cli_root_arg: Optional[str]
) -> Path:
    """
    Xác định Gốc Báo Cáo (Reporting Root) dựa trên logic ưu tiên:
    1. Cờ --root (Tường minh)
    2. Gốc Git (Tìm từ LCA của các đầu vào)
    3. LCA của các đầu vào (Fallback)
    """
    
    # 1. Ưu tiên 1: Cờ --root (Tường minh)
    if cli_root_arg:
        reporting_root = Path(cli_root_arg).expanduser().resolve()
        logger.info(f"Sử dụng gốc báo cáo tường minh (--root): {reporting_root.as_posix()}")
        return reporting_root

    # 2. Ưu tiên 2: Tìm Tổ tiên Chung (LCA)
    input_lca = _find_lca(logger, validated_paths)
    
    # 3. Ưu tiên 3: Tìm Gốc Git từ LCA
    git_root: Optional[Path] = None
    if find_git_root:
        git_root = find_git_root(input_lca)
    
    if git_root:
        reporting_root = git_root
        logger.info(f"Tự động phát hiện Gốc Git (từ đầu vào): {reporting_root.as_posix()}")
    else:
        # 4. Ưu tiên 4: Dùng LCA làm fallback
        reporting_root = input_lca
        logger.warning(f"⚠️ Không tìm thấy gốc Git. Sử dụng tổ tiên chung: {reporting_root.as_posix()}")
    
    return reporting_root