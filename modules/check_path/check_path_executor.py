# Path: modules/check_path/check_path_executor.py

"""
Execution and Reporting logic for the Path Checker (cpath) module.
(Side-effects: Báo cáo, Xác nhận người dùng, Ghi file)
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from utils.logging_config import log_success

__all__ = ["execute_check_path_action"]


def execute_check_path_action(
    logger: logging.Logger,
    files_to_fix: List[Dict[str, Any]],
    check_mode: bool,
    fix_command_str: str,
    scan_root: Path,
    git_warning_str: str,
) -> None:
    """
    Xử lý danh sách các file cần sửa, thực hiện side-effects.

    Args:
        logger: Logger.
        files_to_fix: Danh sách kết quả từ Analyzer.
        check_mode: True nếu ở chế độ 'check' (dry-run).
        fix_command_str: Chuỗi lệnh để chạy lại ở chế độ 'fix'.
        scan_root: Gốc quét (để tính đường dẫn tương đối).
        git_warning_str: Cảnh báo Git (nếu có) từ entrypoint.
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
            
            logger.warning(f"   -> {rel_path}")
            logger.warning(f"      (Dòng 1 hiện tại: {first_line})")
            logger.warning(f"      (Đề xuất:     {fix_preview})")

        # 2. Xử lý theo chế độ
        if check_mode:
            # --- Chế độ "check" (dry-run) ---
            if git_warning_str:
                logger.warning(f"\n{git_warning_str}")

            logger.warning("-> Để sửa các file này, hãy chạy:")
            logger.warning(f"\n{fix_command_str}\n")
            sys.exit(1) # Thoát với mã lỗi
        else:
            # --- Chế độ "fix" (mặc định) ---
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