# Path: modules/no_doc/no_doc_executor.py
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
import hashlib # <-- Xóa
import json # <-- Xóa

# Import thêm
if not "PROJECT_ROOT" in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from utils.logging_config import log_success
from utils.core.git import is_git_repository, git_add_and_commit
# Import logic config
from modules.no_doc.no_doc_internal import (
    load_config_files,
    merge_ndoc_configs,
)
# Import util hash mới
from utils.core.config_helpers import generate_config_hash


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
    cli_args: argparse.Namespace,
    scan_root: Path,
    git_warning_str: str,
) -> None:

    # Lấy cờ từ cli_args
    dry_run: bool = getattr(cli_args, "dry_run", False)
    force: bool = getattr(cli_args, "force", False)

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
            except (EOFError, KeyboardInterrupt):
                confirmation = "n"

            if confirmation.lower() == "y": 
                proceed_to_write = True
            else:
                logger.warning("Hoạt động sửa file bị hủy bởi người dùng.") 
                sys.exit(0)

        if proceed_to_write:
            written_count = 0
            files_written_relative: List[str] = []

            for info in all_files_to_fix:
                target_path: Path = info["path"]
                new_content: str = info["new_content"]

                try:
                    target_path.write_text(new_content, encoding="utf-8")
                    rel_path_str = target_path.relative_to(scan_root).as_posix()
                    files_written_relative.append(rel_path_str)
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

            # --- Logic Git và Hash đã được Refactor ---
            if files_written_relative and is_git_repository(scan_root):
                try:
                    # Tải cấu hình để hash
                    file_config_data = load_config_files(scan_root, logger) 
                    merged_file_config = merge_ndoc_configs(
                        logger,
                        cli_extensions=getattr(cli_args, "extensions", None),
                        cli_ignore=getattr(cli_args, "ignore", None),
                        file_config_data=file_config_data,
                    ) 

                    # Tạo dict cài đặt ổn định để hash
                    settings_to_hash = {
                        "all_clean": getattr(cli_args, "all_clean", False),
                        "format": getattr(cli_args, "format", False),
                        # Sắp xếp các list để đảm bảo hash ổn định
                        "extensions": sorted(
                            list(merged_file_config["final_extensions_list"])
                        ), 
                        "ignore": sorted(list(merged_file_config["final_ignore_list"])), 
                        "format_extensions": sorted(
                            list(merged_file_config["final_format_extensions_set"])
                        ), 
                    }

                    # --- SỬ DỤNG UTIL MỚI ---
                    config_hash = generate_config_hash(settings_to_hash, logger)
                    # --- (Xóa logic hash inline) ---

                    commit_msg = f"style(clean): Dọn dẹp {len(files_written_relative)} file (ndoc)\n\nSettings hash: {config_hash}"

                    git_add_and_commit(
                        logger=logger,
                        scan_root=scan_root,
                        file_paths_relative=files_written_relative,
                        commit_message=commit_msg,
                    ) 

                except Exception as e:
                    logger.error(f"❌ Lỗi khi tạo hash hoặc thực thi git commit: {e}")
                    logger.debug("Traceback:", exc_info=True)

            elif files_written_relative:
                logger.info(
                    "Bỏ qua auto-commit: Thư mục làm việc hiện tại không phải là gốc Git."
                )
            # --- Kết thúc logic Git ---