# Path: modules/check_path/check_path_executor.py
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from utils.logging_config import log_success

__all__ = ["execute_check_path_action", "print_dry_run_report_for_group"]

FileResult = Dict[str, Any]


def print_dry_run_report_for_group(
    logger: logging.Logger,
    group_name: str,
    files_in_group: List[FileResult],
    scan_root: Path,
) -> None:
    logger.warning(
        f"\n   --- 📄 Nhóm: {group_name} ({len(files_in_group)} file cần sửa) ---"
    )
    for info in files_in_group:
        file_path: Path = info["path"]
        first_line = info["line"]
        fix_preview = info["fix_preview"]

        try:
            rel_path = file_path.relative_to(scan_root).as_posix()
        except ValueError:
            rel_path = str(file_path)

        logger.warning(f"   -> {rel_path}")
        logger.warning(f"      (Dòng 1 hiện tại: {first_line})")
        logger.warning(f"      (Đề xuất:     {fix_preview})")


def execute_check_path_action(
    logger: logging.Logger,
    all_files_to_fix: List[FileResult],
    dry_run: bool,
    force: bool,
    scan_root: Path,
) -> None:

    total_files_to_fix = len(all_files_to_fix)

    if total_files_to_fix == 0:
        log_success(logger, "Tất cả file đã tuân thủ. Không cần thay đổi.")
        return

    logger.warning(
        f"\n⚠️ Tổng cộng {total_files_to_fix} file không tuân thủ quy ước (chi tiết ở trên)."
    )

    if dry_run:
        logger.warning(f"-> Chạy lại mà không có cờ -d để sửa (hoặc -f để tự động).")
        sys.exit(1)
    else:
        proceed_to_write = force
        if not force:
            try:
                confirmation = input("\nTiếp tục sửa các file này? (y/n): ")
            except (EOFError, KeyboardInterrupt):
                confirmation = "n"

            if confirmation.lower() == "y":
                proceed_to_write = True
            else:
                logger.warning("Hoạt động sửa file bị hủy bởi người dùng.")
                sys.exit(0)

        if proceed_to_write:
            written_count = 0
            for info in all_files_to_fix:
                target_path: Path = info["path"]
                new_lines: List[str] = info["new_lines"]
                try:
                    with target_path.open("w", encoding="utf-8") as f:
                        f.writelines(new_lines)
                    rel_path_str = target_path.relative_to(scan_root).as_posix()
                    logger.info(f"Đã sửa: {rel_path_str}")
                    written_count += 1
                except IOError as e:
                    logger.error(
                        "❌ Lỗi khi ghi file %s: %s",
                        target_path.relative_to(scan_root).as_posix(),
                        e,
                    )
                except ValueError:

                    logger.info(f"Đã sửa (absolute path): {target_path.as_posix()}")
                    written_count += 1

            log_success(logger, f"Hoàn tất! Đã sửa {written_count} file.")