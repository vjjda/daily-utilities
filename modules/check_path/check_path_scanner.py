# Path: modules/check_path/check_path_scanner.py

"""
File Scanning logic for the Path Checker module.
...
"""

import logging
from pathlib import Path
from typing import List, Set, Optional, TYPE_CHECKING

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
    parse_gitignore, 
    is_path_matched,
    compile_spec_from_patterns
)
# --- END MODIFIED ---

__all__ = ["scan_for_files"]

def scan_for_files(
    logger: logging.Logger,
    project_root: Path,
    target_dir_str: Optional[str],
    extensions: List[str],
    # (Tên tham số này vẫn là ignore_set,
    # nó nhận pattern từ config)
    ignore_set: Set[str], 
    script_file_path: Path,
    check_mode: bool
) -> List[Path]:
    """
    Quét thư mục dự án, lọc file, và trả về danh sách file sạch.
    """
    
    use_gitignore = target_dir_str is None
    scan_path = project_root
    
    logger.debug(f"Scan Root (base for rules) identified as: {project_root}")
    logger.debug(f"Scan Path (rglob start) set to: {scan_path}")

    submodule_paths = get_submodule_paths(project_root, logger)
    
    # --- MODIFIED: Gộp logic ignore ---
    gitignore_patterns: Set[str] = set()
    if use_gitignore:
        # parse_gitignore giờ trả về Set[str]
        gitignore_patterns = parse_gitignore(project_root) 
        if gitignore_patterns:
            logger.info("Chế độ mặc định: Tôn trọng quy tắc .gitignore (qua pathspec).")
        else:
            logger.info("Chế độ mặc định: Không tìm thấy .gitignore hoặc 'pathspec' bị thiếu.")
    else:
        logger.info(f"Chế độ đường dẫn cụ thể: Không dùng .gitignore cho '{target_dir_str}'.")

    # Gộp pattern từ config (ignore_set) và .gitignore
    all_ignore_patterns = ignore_set.union(gitignore_patterns)
    
    # Biên dịch 1 lần
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns)
    # --- END MODIFIED ---
    
    if check_mode:
        logger.info("Đang chạy ở [Chế độ Dry-run] (chạy thử).")
    
    logger.info(f"Đang quét *.{', *.'.join(extensions)} trong: {scan_path.relative_to(scan_path.parent) if scan_path.parent != scan_path else scan_path.name}")
    if all_ignore_patterns:
        logger.debug(f"Bỏ qua (pathspec): {', '.join(sorted(list(all_ignore_patterns)))}")

    all_files = []
    for ext in extensions:
        all_files.extend(scan_path.rglob(f"*.{ext}"))
    
    files_to_process = []
    # (Nội dung lọc file giữ nguyên)
    # ...
    for file_path in all_files:
        abs_file_path = file_path.resolve()

        # 1. Skip this script itself
        if abs_file_path.samefile(script_file_path):
            continue
        
        # 2. Skip files in submodules
        is_in_submodule = any(abs_file_path.is_relative_to(p) for p in submodule_paths)
        if is_in_submodule:
            continue
            
        # --- MODIFIED: Gộp 2 bước lọc thành 1 ---
        # 3. Skip ignored files (Config + .gitignore)
        #    Sử dụng is_path_matched (mới) với ignore_spec
        if is_path_matched(file_path, ignore_spec, project_root):
            continue
        # --- END MODIFIED ---
            
        files_to_process.append(file_path)
        
    return files_to_process