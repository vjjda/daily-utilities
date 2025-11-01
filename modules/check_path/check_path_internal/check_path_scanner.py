# Path: modules/check_path/check_path_internal/check_path_scanner.py
import logging
from pathlib import Path
import sys
from typing import List, Set, Optional, TYPE_CHECKING, Iterable, Tuple, Dict
import os # <-- Thêm import os

if not "PROJECT_ROOT" in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

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
    compile_spec_from_patterns,
)

__all__ = ["scan_files"]


def scan_files(
    logger: logging.Logger,
    start_path: Path,
    ignore_spec: Optional["pathspec.PathSpec"],
    extensions: List[str], # Đây là list từ config
    scan_root: Path,
    script_file_path: Path,
) -> Tuple[List[Path], Dict[str, bool]]:
    """
    Quét file dựa trên logic (ĐÃ SỬA) glob-trước-lọc-sau.
    """
    scan_status = {"gitignore_found": False, "gitmodules_found": False}
    scan_path = start_path.resolve()

    if not scan_path.exists():
        logger.warning(f"Thư mục quét không tồn tại: {scan_path.as_posix()}")
        return [], scan_status

    submodule_paths = get_submodule_paths(scan_root, logger)
    if submodule_paths:
        scan_status["gitmodules_found"] = True

    gitignore_patterns: List[str] = parse_gitignore(scan_root)
    if gitignore_patterns:
        scan_status["gitignore_found"] = True
    
    # Bỏ qua ignore_spec được truyền vào (vì nó sai) và tự build lại
    all_ignore_patterns_list: List[str]
    if ignore_spec:
         # Thử lấy lại pattern từ spec (nếu có thể) hoặc dùng list rỗng
         try:
             all_ignore_patterns_list = [p.pattern for p in ignore_spec.patterns] + gitignore_patterns
         except Exception:
             all_ignore_patterns_list = gitignore_patterns
    else:
        all_ignore_patterns_list = gitignore_patterns

    final_ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)


    all_files: List[Path] = []
    extensions_set = set(extensions) # Chuyển thành Set để tra cứu O(1)

    if scan_path.is_dir():
        # --- START FIX ---
        # 1. Glob tất cả các file trước
        logger.debug(f"Scanner (fixed): Chạy rglob('*') trên {scan_path.name}")
        all_files_raw = [p for p in scan_path.rglob("*") if p.is_file()]

        # 2. Lọc file dựa trên extensions_set
        for f in all_files_raw:
            file_ext = "".join(f.suffixes).lstrip(".")
            if file_ext in extensions_set:
                all_files.append(f)
        # --- END FIX ---
    elif scan_path.is_file():
        # Logic cho file đơn lẻ
        file_ext = "".join(scan_path.suffixes).lstrip(".")
        if file_ext in extensions_set:
            all_files.append(scan_path)
        else:
            logger.warning(
                f"File '{scan_path.name}' bị bỏ qua do không khớp extension: {file_ext}"
            )
            return [], scan_status

    files_to_process: List[Path] = []

    for file_path in all_files:
        abs_file_path = file_path.resolve()

        if abs_file_path.samefile(script_file_path.resolve()):
            continue

        is_in_submodule = any(abs_file_path.is_relative_to(p) for p in submodule_paths)
        if is_in_submodule:
            continue
            
        # Sử dụng os.path.relpath để xử lý symlink an toàn
        try:
            relative_path_str = os.path.relpath(file_path.as_posix(), scan_root.resolve().as_posix())
        except ValueError:
            relative_path_str = file_path.as_posix()

        if is_path_matched(file_path, final_ignore_spec, scan_root):
            continue

        files_to_process.append(file_path)

    files_to_process.sort(key=lambda p: p.as_posix())
    return files_to_process, scan_status