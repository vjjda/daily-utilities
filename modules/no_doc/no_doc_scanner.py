# Path: modules/no_doc/no_doc_scanner.py

"""
File Scanning logic for the no_doc module.
(Internal module, imported by no_doc_core)
"""

import logging
from pathlib import Path
import sys
from typing import List, Set, Optional, TYPE_CHECKING, Iterable

# Thiết lập sys.path
if not 'PROJECT_ROOT' in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

from utils.core import (
    get_submodule_paths,
    parse_gitignore,
    is_path_matched,
    compile_spec_from_patterns
)

__all__ = ["scan_files"]

def scan_files(
    logger: logging.Logger,
    start_path: Path,
    ignore_list: List[str],
    extensions: List[str],
    scan_root: Path,
    script_file_path: Path
) -> List[Path]:
    """
    Quét thư mục dự án, lọc file, và trả về danh sách file sạch.
    
    Args:
        logger: Logger.
        start_path: Đường dẫn bắt đầu quét (file hoặc thư mục).
        ignore_list: Danh sách pattern (đã hợp nhất) để bỏ qua.
        extensions: Danh sách đuôi file (đã hợp nhất) để quét.
        scan_root: Gốc dự án (để tính .gitignore và submodule).
        script_file_path: Đường dẫn của chính script ndoc (để bỏ qua, DÙNG TRONG CODE GỐC).

    Returns:
        List[Path]: Danh sách các file cần phân tích.
    """

    # Xác định đường dẫn bắt đầu quét (rglob)
    scan_path = start_path.resolve()
    
    if not scan_path.exists():
         logger.warning(f"Thư mục quét không tồn tại: {scan_path.as_posix()}")
         return []

    submodule_paths = get_submodule_paths(scan_root, logger)

    # Tải .gitignore (luôn tôn trọng trong logic này)
    gitignore_patterns: List[str] = parse_gitignore(scan_root)
    all_ignore_patterns_list: List[str] = ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)

    all_files: List[Path] = []
    
    # Chỉ quét nếu là thư mục
    if scan_path.is_dir():
        for ext in extensions:
            all_files.extend(scan_path.rglob(f"*.{ext}"))
    elif scan_path.is_file():
        # Nếu là file, kiểm tra extension có hợp lệ không
        file_ext = "".join(scan_path.suffixes).lstrip('.')
        if file_ext in extensions:
             all_files.append(scan_path)
        else:
             logger.warning(f"File '{scan_path.name}' bị bỏ qua do không khớp extension: {file_ext}")
             return []
        
    files_to_process: List[Path] = []
    
    for file_path in all_files:
        abs_file_path = file_path.resolve()

        # BỎ QUA KIỂM TRA CHÍNH SCRIPT: 
        # Chúng ta đã xóa: `if abs_file_path.samefile(script_file_path.resolve()): continue`

        # Bỏ qua file trong submodule
        is_in_submodule = any(abs_file_path.is_relative_to(p) for p in submodule_paths)
        if is_in_submodule:
            continue

        # Bỏ qua file khớp ignore_spec
        if is_path_matched(file_path, ignore_spec, scan_root):
            continue

        files_to_process.append(file_path)

    files_to_process.sort(key=lambda p: p.as_posix())
    return files_to_process