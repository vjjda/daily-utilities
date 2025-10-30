# Path: modules/pack_code/pack_code_internal/pack_code_scanner.py

"""
Logic quét file cho module Pack Code.
(Module nội bộ, được import bởi pack_code_core)
"""

import logging
from pathlib import Path
from typing import List, Set, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pathspec

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

    Args:
        logger: Logger.
        start_path: Đường dẫn bắt đầu quét (có thể là file hoặc thư mục).
        ignore_spec: PathSpec đã biên dịch cho các quy tắc ignore.
        ext_filter_set: Set các đuôi file (đã lột ".") được phép.
        submodule_paths: Set các đường dẫn tuyệt đối đến các submodule.
        scan_root: Thư mục gốc (dùng để tính relpath cho ignore).

    Returns:
        Danh sách các đối tượng Path đã được lọc và sắp xếp.
    """
    files_to_pack: List[Path] = []
    all_files: List[Path] = [] # List các file thô trước khi lọc

    if start_path.is_file():
        # Nếu start_path là file, chỉ xử lý file đó
        all_files = [start_path]
        logger.debug(f"Bắt đầu quét từ file: {start_path.as_posix()}") #
    elif start_path.is_dir():
        # Nếu là thư mục, quét đệ quy
        all_files = list(start_path.rglob("*"))
        logger.debug(f"Bắt đầu quét từ thư mục: {start_path.as_posix()}") #
    else:
        # Trường hợp không tồn tại đã được xử lý ở resolver
        logger.error(f"Đường dẫn bắt đầu không hợp lệ: {start_path}") #
        return []

    logger.debug(f"Số lượng file/thư mục thô tìm thấy: {len(all_files)}") #
    logger.debug(f"Bộ lọc extension: {ext_filter_set}") #
    logger.debug(f"Scan root cho quy tắc ignore: {scan_root.as_posix()}") #

    processed_count = 0
    ignored_count = 0
    ext_mismatch_count = 0
    submodule_skip_count = 0

    for file_path in all_files:
        processed_count += 1
        if file_path.is_dir():
            continue # Chỉ xử lý file

        abs_file_path = file_path.resolve()

        # 1. Bỏ qua file trong submodule
        if any(abs_file_path.is_relative_to(p.resolve()) for p in submodule_paths):
            logger.debug(f"Bỏ qua (submodule): {file_path.relative_to(scan_root).as_posix()}") #
            submodule_skip_count += 1
            continue

        # 2. Bỏ qua file bị ignore (Config + .gitignore)
        if is_path_matched(file_path, ignore_spec, scan_root):
            logger.debug(f"Bỏ qua (bị ignore): {file_path.relative_to(scan_root).as_posix()}") #
            ignored_count += 1
            continue

        # 3. Lọc theo đuôi file
        file_ext = file_path.suffix.lstrip('.')
        if file_ext not in ext_filter_set:
            # Nếu start_path là file và chính file đó bị lọc -> cảnh báo và trả về rỗng
            if start_path.is_file() and abs_file_path.samefile(start_path.resolve()):
                logger.warning(f"File chỉ định {start_path.name} bị bỏ qua do không khớp extension.") #
                return []
            logger.debug(f"Bỏ qua (không khớp extension): {file_path.relative_to(scan_root).as_posix()}") #
            ext_mismatch_count +=1
            continue

        files_to_pack.append(file_path)

    logger.debug(f"Quét hoàn tất: Đã xử lý {processed_count} mục.") #
    logger.debug(f" -> Bỏ qua (quy tắc ignore): {ignored_count}")
    logger.debug(f" -> Bỏ qua (submodule): {submodule_skip_count}")
    logger.debug(f" -> Bỏ qua (extension): {ext_mismatch_count}")
    logger.debug(f" -> File hợp lệ: {len(files_to_pack)}")

    # Sắp xếp file theo thứ tự alphabet để đảm bảo output ổn định
    files_to_pack.sort(key=lambda p: p.as_posix())
    return files_to_pack