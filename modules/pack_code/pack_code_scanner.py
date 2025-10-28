# Path: modules/pack_code/pack_code_scanner.py

"""
File Scanning logic for the Pack Code module.
"""

import logging
from pathlib import Path
from typing import List, Set, Optional, TYPE_CHECKING

# Import pathspec for type checking
if TYPE_CHECKING:
    import pathspec

# Import utilities from utils.core
from utils.core import is_path_matched, get_submodule_paths

__all__ = ["scan_files"]

def scan_files(
    logger: logging.Logger,
    start_path: Path,
    ignore_spec: Optional['pathspec.PathSpec'],
    ext_filter_set: Set[str],
    submodule_paths: Set[Path],
    scan_root: Path
) -> List[Path]:
    """
    Quét và lọc file dựa trên các bộ lọc đã được biên dịch.
    """
    files_to_pack: List[Path] = []
    
    if start_path.is_file():
        # Rà soát thư mục cha để tìm các file khớp với start_path
        all_files_iter = start_path.parent.rglob("*")
        # Lọc chính xác file được chỉ định
        all_files = [p for p in all_files_iter if p.is_file() and p.resolve().samefile(start_path.resolve())]
        if not all_files:
             logger.warning(f"File chỉ định {start_path.name} không tìm thấy hoặc bị lọc.")
             all_files = [start_path] # Fallback nếu rglob không tìm thấy
    elif start_path.is_dir():
        all_files = list(start_path.rglob("*"))
    else:
        logger.error(f"Đường dẫn bắt đầu không hợp lệ: {start_path}")
        return []

    logger.debug(f"Bắt đầu quét từ: {start_path.as_posix()}")
    logger.debug(f"Số lượng file/thư mục thô tìm thấy: {len(all_files)}")
    logger.debug(f"Bộ lọc extension: {ext_filter_set}")
    logger.debug(f"Scan root cho ignore rules: {scan_root.as_posix()}")

    processed_count = 0
    ignored_count = 0
    ext_mismatch_count = 0
    submodule_skip_count = 0

    for file_path in all_files:
        processed_count += 1
        if file_path.is_dir():
            continue
            
        abs_file_path = file_path.resolve()

        # 0. Nếu start_path là file, chỉ xử lý file đó
        if start_path.is_file() and not abs_file_path.samefile(start_path.resolve()):
            continue

        # 1. Bỏ qua file trong submodule
        if any(abs_file_path.is_relative_to(p.resolve()) for p in submodule_paths):
            logger.debug(f"Skipping (submodule): {file_path.relative_to(scan_root).as_posix()}")
            submodule_skip_count += 1
            continue
            
        # 2. Bỏ qua file bị ignore (Config + .gitignore)
        if is_path_matched(file_path, ignore_spec, scan_root):
            logger.debug(f"Skipping (ignored): {file_path.relative_to(scan_root).as_posix()}")
            ignored_count += 1
            continue
            
        # 3. Lọc theo đuôi file
        file_ext = file_path.suffix.lstrip('.')
        if file_ext not in ext_filter_set:
            # Chỉ cảnh báo nếu file được chỉ định trực tiếp bị bỏ qua
            if start_path.is_file() and abs_file_path.samefile(start_path.resolve()):
                logger.warning(f"File chỉ định {start_path.name} bị bỏ qua do không khớp extension.")
                return [] # Trả về rỗng nếu file duy nhất bị lọc
            logger.debug(f"Skipping (extension mismatch): {file_path.relative_to(scan_root).as_posix()}")
            ext_mismatch_count +=1
            continue
            
        files_to_pack.append(file_path)

    logger.debug(f"Quét hoàn tất: Đã xử lý {processed_count} mục.")
    logger.debug(f" -> Bỏ qua (ignore rule): {ignored_count}")
    logger.debug(f" -> Bỏ qua (submodule): {submodule_skip_count}")
    logger.debug(f" -> Bỏ qua (extension): {ext_mismatch_count}")
    logger.debug(f" -> File hợp lệ: {len(files_to_pack)}")
        
    # Sắp xếp file theo thứ tự alphabet
    files_to_pack.sort(key=lambda p: p.as_posix())
    return files_to_pack