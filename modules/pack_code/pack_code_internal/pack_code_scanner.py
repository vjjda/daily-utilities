# Path: modules/pack_code/pack_code_internal/pack_code_scanner.py
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
    ignore_spec: Optional["pathspec.PathSpec"],
    ext_filter_set: Set[str],
    submodule_paths: Set[Path],
    scan_root: Path,
) -> List[Path]:
    files_to_pack: List[Path] = []
    all_files: List[Path] = []

    if start_path.is_file():

        all_files = [start_path]
        logger.debug(f"Bắt đầu quét từ file: {start_path.as_posix()}")
    elif start_path.is_dir():

        all_files = list(start_path.rglob("*"))
        logger.debug(f"Bắt đầu quét từ thư mục: {start_path.as_posix()}")
    else:

        logger.error(f"Đường dẫn bắt đầu không hợp lệ: {start_path}")
        return []

    logger.debug(f"Số lượng file/thư mục thô tìm thấy: {len(all_files)}")
    logger.debug(f"Bộ lọc extension: {ext_filter_set}")
    logger.debug(f"Scan root cho quy tắc ignore: {scan_root.as_posix()}")

    processed_count = 0
    ignored_count = 0
    ext_mismatch_count = 0
    submodule_skip_count = 0

    for file_path in all_files:
        processed_count += 1
        if file_path.is_dir():
            continue

        abs_file_path = file_path.resolve()

        if any(abs_file_path.is_relative_to(p.resolve()) for p in submodule_paths):
            logger.debug(
                f"Bỏ qua (submodule): {file_path.relative_to(scan_root).as_posix()}"
            )
            submodule_skip_count += 1
            continue

        if is_path_matched(file_path, ignore_spec, scan_root):
            logger.debug(
                f"Bỏ qua (bị ignore): {file_path.relative_to(scan_root).as_posix()}"
            )
            ignored_count += 1
            continue

        file_ext = file_path.suffix.lstrip(".")
        if file_ext not in ext_filter_set:

            if start_path.is_file() and abs_file_path.samefile(start_path.resolve()):
                logger.warning(
                    f"File chỉ định {start_path.name} bị bỏ qua do không khớp extension."
                )
                return []
            logger.debug(
                f"Bỏ qua (không khớp extension): {file_path.relative_to(scan_root).as_posix()}"
            )
            ext_mismatch_count += 1
            continue

        files_to_pack.append(file_path)

    logger.debug(f"Quét hoàn tất: Đã xử lý {processed_count} mục.")
    logger.debug(f" -> Bỏ qua (quy tắc ignore): {ignored_count}")
    logger.debug(f" -> Bỏ qua (submodule): {submodule_skip_count}")
    logger.debug(f" -> Bỏ qua (extension): {ext_mismatch_count}")
    logger.debug(f" -> File hợp lệ: {len(files_to_pack)}")

    files_to_pack.sort(key=lambda p: p.as_posix())
    return files_to_pack