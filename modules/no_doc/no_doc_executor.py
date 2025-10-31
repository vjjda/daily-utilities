# Path: modules/no_doc/no_doc_executor.py
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


if not "PROJECT_ROOT" in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from utils.logging_config import log_success


__all__ = ["execute_ndoc_action", "print_dry_run_report_for_group"]

FileResult = Dict[str, Any]


def print_dry_run_report_for_group(
    logger: logging.Logger,
    group_name: str,
    files_in_group: List[FileResult],
    scan_root: Path,
) -> None:
    logger.warning(f"\n   --- Nhóm: {group_name} ({len(files_in_group)} file) ---")
    for info in files_in_group:
        file_path: Path = info["path"]
        try:
            rel_path = file_path.relative_to(scan_root).as_posix()
        except ValueError:
            rel_path = str(file_path)

        logger.warning(f"   -> {rel_path} (Sẽ bị thay đổi định dạng do AST unparse)")


def execute_ndoc_action(
    logger: logging.Logger,
    all_files_to_fix: List[FileResult],
    dry_run: bool,
    force: bool,
    scan_root: Path,
    git_warning_str: str,
) -> None:

    total_files_to_fix = len(all_files_to_fix)

    if total_files_to_fix == 0:

        return

    logger.warning(
        f"\n⚠️ Tổng cộng {total_files_to_fix} file cần được sửa (chi tiết ở trên)."
    )

    if dry_run:
        logger.warning(
            f"-> Để xóa docstring, chạy lại mà không có cờ -d (sử dụng -f/--force để bỏ qua xác nhận)."
        )
        sys.exit(1)
    else:

        proceed_to_write = force
        if not force:
            try:
                confirmation = input(
                    "\nTiếp tục xóa docstring và ghi đè các file này? (y/n): "
                )
            except EOFError:
                confirmation = "n"
            except KeyboardInterrupt:
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
                new_content: str = info["new_content"]

                try:
                    target_path.write_text(new_content, encoding="utf-8")
                    rel_path_str = target_path.relative_to(scan_root).as_posix()
                    logger.info(f"Đã sửa: {rel_path_str}")
                    written_count += 1
                except IOError as e:
                    logger.error(
                        "❌ Lỗi khi ghi file %s: %s",
                        target_path.relative_to(scan_root).as_posix(),
                        e,
                    )

            log_success(
                logger, f"Hoàn tất! Đã xóa docstring khỏi {written_count} file."
            )
