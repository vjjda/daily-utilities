# Path: modules/check_path/check_path_scanner.py

"""
File Scanning logic for the Path Checker (cpath) module.
(Internal module, imported by check_path_core.py)
"""

import logging
from pathlib import Path
from typing import List, Set, Optional, TYPE_CHECKING, Iterable

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

__all__ = ["scan_for_files"]

def scan_for_files(
    logger: logging.Logger,
    project_root: Path,
    target_dir_str: Optional[str],
    extensions: List[str],
    ignore_list: List[str],
    script_file_path: Path,
    check_mode: bool
) -> List[Path]:
    """
    Quét thư mục dự án, lọc file, và trả về danh sách file sạch.

    Args:
        logger: Logger.
        project_root: Gốc dự án (để tính .gitignore và submodule).
        target_dir_str: Thư mục con tùy chọn (nếu được cung cấp qua CLI).
        extensions: Danh sách đuôi file (đã hợp nhất) để quét.
        ignore_list: Danh sách pattern (đã hợp nhất) để bỏ qua.
        script_file_path: Đường dẫn của chính script cpath (để bỏ qua).
        check_mode: True nếu ở chế độ dry-run (ảnh hưởng log).

    Returns:
        List[Path]: Danh sách các file cần phân tích.
    """

    use_gitignore = target_dir_str is None
    
    # Xác định đường dẫn bắt đầu quét (rglob)
    scan_path = (project_root / target_dir_str).resolve() if target_dir_str else project_root.resolve()

    logger.debug(f"Scan Root (base for rules) identified as: {project_root}")
    logger.debug(f"Scan Path (rglob start) set to: {scan_path}")

    submodule_paths = get_submodule_paths(project_root, logger)

    # Tải .gitignore (nếu ở chế độ quét gốc)
    gitignore_patterns: List[str] = []
    if use_gitignore:
        gitignore_patterns = parse_gitignore(project_root)
        if gitignore_patterns:
            logger.info("Chế độ mặc định: Tôn trọng quy tắc .gitignore (qua pathspec).")
        else:
            logger.info("Chế độ mặc định: Không tìm thấy .gitignore hoặc 'pathspec' bị thiếu.")
    else:
        logger.info(f"Chế độ đường dẫn cụ thể: Không dùng .gitignore cho '{target_dir_str}'.")

    # Biên dịch PathSpec: (Config/CLI patterns) + (Gitignore patterns)
    all_ignore_patterns_list: List[str] = ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, project_root)

    if check_mode:
        logger.info("Đang chạy ở [Chế độ Dry-run] (chạy thử).")

    try:
        scan_display_name = scan_path.relative_to(project_root.parent).as_posix()
    except ValueError:
        scan_display_name = scan_path.name
    logger.info(f"Đang quét *.{', *.'.join(extensions)} trong: {scan_display_name}")
    
    if all_ignore_patterns_list:
        logger.debug(f"Bỏ qua (pathspec): {len(all_ignore_patterns_list)} pattern (config/cli + .gitignore)")

    all_files = []
    if not scan_path.exists():
         logger.warning(f"Thư mục quét không tồn tại: {scan_path.as_posix()}")
         return []
         
    for ext in extensions:
        all_files.extend(scan_path.rglob(f"*.{ext}"))

    files_to_process = []
    for file_path in all_files:
        abs_file_path = file_path.resolve()

        # Bỏ qua file trong submodule
        is_in_submodule = any(abs_file_path.is_relative_to(p) for p in submodule_paths)
        if is_in_submodule:
            continue

        # Bỏ qua file khớp ignore_spec
        if is_path_matched(file_path, ignore_spec, project_root):
            continue

        files_to_process.append(file_path)

    return files_to_process