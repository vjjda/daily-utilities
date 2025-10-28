# Path: modules/check_path/check_path_scanner.py

"""
File Scanning logic for the Path Checker module.
...
"""

import logging
from pathlib import Path
# --- MODIFIED: Thêm Iterable ---
from typing import List, Set, Optional, TYPE_CHECKING, Iterable
# --- END MODIFIED ---

try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec


# Import utilities used for scanning
# --- MODIFIED: Import thêm compile_spec_from_patterns ---
from utils.core import (
    get_submodule_paths,
    parse_gitignore, # Trả về List[str]
    is_path_matched,
    compile_spec_from_patterns # Nhận Iterable[str]
)
# --- END MODIFIED ---

__all__ = ["scan_for_files"]

def scan_for_files(
    logger: logging.Logger,
    project_root: Path,
    target_dir_str: Optional[str],
    extensions: List[str],
    ignore_set: Set[str], # Ignore từ config/CLI (vẫn là Set)
    script_file_path: Path,
    check_mode: bool
) -> List[Path]:
    """
    Quét thư mục dự án, lọc file, và trả về danh sách file sạch.
    """

    use_gitignore = target_dir_str is None
    # --- MODIFIED: Xác định scan_path cẩn thận hơn ---
    # Nếu target_dir_str được cung cấp, đó là nơi bắt đầu quét thực tế
    # Nếu không, quét từ project_root
    scan_path = (project_root / target_dir_str).resolve() if target_dir_str else project_root.resolve()
    # --- END MODIFIED ---

    logger.debug(f"Scan Root (base for rules) identified as: {project_root}")
    logger.debug(f"Scan Path (rglob start) set to: {scan_path}")

    submodule_paths = get_submodule_paths(project_root, logger)

    # --- MODIFIED: Gộp logic ignore ---
    gitignore_patterns: List[str] = [] # <-- List
    if use_gitignore:
        gitignore_patterns = parse_gitignore(project_root) # <-- List
        if gitignore_patterns:
            logger.info("Chế độ mặc định: Tôn trọng quy tắc .gitignore (qua pathspec).")
        else:
            logger.info("Chế độ mặc định: Không tìm thấy .gitignore hoặc 'pathspec' bị thiếu.")
    else:
        logger.info(f"Chế độ đường dẫn cụ thể: Không dùng .gitignore cho '{target_dir_str}'.")

    # --- MODIFIED: Gộp thành List ---
    # Ưu tiên: Config/CLI patterns -> Gitignore patterns
    all_ignore_patterns_list: List[str] = sorted(list(ignore_set)) + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, project_root)
    # --- END MODIFIED ---

    if check_mode:
        logger.info("Đang chạy ở [Chế độ Dry-run] (chạy thử).")

    # --- MODIFIED: Hiển thị tên thư mục quét tương đối ---
    try:
        scan_display_name = scan_path.relative_to(project_root.parent).as_posix()
    except ValueError:
        scan_display_name = scan_path.name
    logger.info(f"Đang quét *.{', *.'.join(extensions)} trong: {scan_display_name}")
    # --- END MODIFIED ---
    if all_ignore_patterns_list: # Check list mới
        logger.debug(f"Bỏ qua (pathspec): {len(all_ignore_patterns_list)} pattern (config/cli + .gitignore)")

    all_files = []
    # --- MODIFIED: Xử lý scan_path không tồn tại ---
    if not scan_path.exists():
         logger.warning(f"Thư mục quét không tồn tại: {scan_path.as_posix()}")
         return []
    # --- END MODIFIED ---
    for ext in extensions:
        all_files.extend(scan_path.rglob(f"*.{ext}"))

    files_to_process = []
    # (Nội dung lọc file giữ nguyên)
    for file_path in all_files:
        abs_file_path = file_path.resolve()

        if abs_file_path.samefile(script_file_path):
            continue

        is_in_submodule = any(abs_file_path.is_relative_to(p) for p in submodule_paths)
        if is_in_submodule:
            continue

        # Sử dụng project_root làm gốc so sánh cho ignore_spec
        if is_path_matched(file_path, ignore_spec, project_root):
            continue

        files_to_process.append(file_path)

    return files_to_process