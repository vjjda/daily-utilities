# Path: modules/path_checker/path_checker_executor.py

"""
Logic thực thi và báo cáo cho module Path Checker.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from utils.logging_config import log_success

__all__ = ["handle_results"]


def handle_results(
    logger: logging.Logger,
    files_to_fix: List[Dict[str, Any]],
    check_mode: bool,
    fix_command_str: str,
    scan_root: Path,
    git_warning_str: str,
) -> None:
    """
    Xử lý danh sách các file cần sửa.
    """

    processed_count = len(files_to_fix)

    if processed_count > 0:

        # 1. In báo cáo
        logger.warning(
            f"⚠️ {processed_count} file không tuân thủ quy ước đường dẫn:"
        )

        for info in files_to_fix:
            file_path = info["path"]
            first_line = info["line"]
            fix_preview = info["fix_preview"]

            try:
                rel_path = file_path.relative_to(scan_root).as_posix()
            except ValueError:
                rel_path = str(file_path)
            
            # --- MODIFIED: Đã xóa dòng lặp ---
            logger.warning(f"   -> {rel_path}")
            # --- END MODIFIED ---
            
            logger.warning(f"      (Dòng 1 hiện tại: {first_line})")
            logger.warning(f"      (Đề xuất:     {fix_preview})")

        # 2. Xử lý theo chế độ
        if check_mode:
            # --- Chế độ "check" (mặc định) ---

            if git_warning_str:
                logger.warning(f"\n{git_warning_str}")

            logger.warning("-> Để sửa các file này, hãy chạy:")
            logger.warning(f"\n{fix_command_str}\n")
            sys.exit(1)
        else:
            # --- Chế độ "--fix" ---

            if git_warning_str:
                logger.warning(f"\n{git_warning_str}")

            try:
                confirmation = input("\nTiếp tục sửa các file này? (y/n): ")
            except EOFError:
                confirmation = "n"

            if confirmation.lower() == "y":
                written_count = 0
                for info in files_to_fix:
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
                            e
                        )

                log_success(logger, f"Hoàn tất! Đã sửa {written_count} file.")

            else:
                logger.warning("Hoạt động sửa file bị hủy bởi người dùng.")
                sys.exit(0)

    else:
        # 0 file cần sửa
        if git_warning_str:
            logger.warning(f"\n{git_warning_str}")

        log_success(
            logger,
            "Tất cả file đã tuân thủ quy ước. Không cần thay đổi.",
        )