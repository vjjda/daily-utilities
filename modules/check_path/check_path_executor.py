# Path: modules/check_path/check_path_executor.py
import logging
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

from utils.logging_config import log_success
from utils.core.git import auto_commit_changes
from modules.check_path.check_path_internal import (
    load_config_files,
    merge_check_path_configs,
)

from utils.cli.ui_helpers import print_grouped_report


__all__ = ["execute_check_path_action"]


FileResult = Dict[str, Any]


def execute_check_path_action(
    logger: logging.Logger,
    all_files_to_fix: List[FileResult],
    cli_args: argparse.Namespace,
    scan_root: Path,
) -> None:

    dry_run: bool = getattr(cli_args, "dry_run", False)
    force: bool = getattr(cli_args, "force", False)

    total_files_to_fix = len(all_files_to_fix)

    if total_files_to_fix == 0:
        return

    logger.warning(f"\n⚠️ Tổng cộng {total_files_to_fix} file không tuân thủ quy ước.")

    def _title_formatter(info: FileResult) -> str:
        file_path: Path = info["path"]
        try:
            rel_path = file_path.relative_to(scan_root).as_posix()
        except ValueError:
            rel_path = str(file_path)
        return rel_path

    def _detail_formatter(info: FileResult) -> List[str]:
        first_line = info["line"]
        fix_preview = info["fix_preview"]
        return [f"(Dòng 1 hiện tại: {first_line})", f"(Đề xuất:     {fix_preview})"]

    if dry_run:
        logger.info("Chế độ Dry-run: Báo cáo các file cần sửa.")
        print_grouped_report(
            logger=logger,
            group_name="Tổng hợp (Dry Run)",
            files_in_group=all_files_to_fix,
            scan_root=scan_root,
            title_formatter=_title_formatter,
            detail_formatter=_detail_formatter,
        )
        logger.warning("\n-> Chạy lại mà không có cờ -d để sửa (hoặc -f để tự động).")
        sys.exit(1)

    proceed_to_write = force
    if not force:

        print_grouped_report(
            logger=logger,
            group_name="Các thay đổi sắp thực hiện",
            files_in_group=all_files_to_fix,
            scan_root=scan_root,
            title_formatter=_title_formatter,
            detail_formatter=_detail_formatter,
        )

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
        files_written_relative: List[str] = []
        for info in all_files_to_fix:
            target_path: Path = info["path"]
            new_lines: List[str] = info["new_lines"]
            try:
                with target_path.open("w", encoding="utf-8") as f:
                    f.writelines(new_lines)
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
            except ValueError:

                files_written_relative.append(target_path.as_posix())
                logger.info(f"Đã sửa (absolute path): {target_path.as_posix()}")
                written_count += 1

        log_success(logger, f"Hoàn tất! Đã sửa {written_count} file.")

        git_commit: bool = getattr(cli_args, "git_commit", False)

        if git_commit and files_written_relative:
            try:

                file_config_data = load_config_files(scan_root, logger)
                merged_file_config = merge_check_path_configs(
                    logger,
                    cli_extensions=getattr(cli_args, "extensions", None),
                    cli_ignore=getattr(cli_args, "ignore", None),
                    file_config_data=file_config_data,
                )

                settings_to_hash = {
                    "extensions": sorted(
                        list(merged_file_config["final_extensions_list"])
                    ),
                    "ignore": sorted(list(merged_file_config["final_ignore_list"])),
                }

                auto_commit_changes(
                    logger=logger,
                    scan_root=scan_root,
                    files_written_relative=files_written_relative,
                    settings_to_hash=settings_to_hash,
                    commit_scope="style(cpath)",
                    tool_name="cpath",
                )

            except Exception as e:
                logger.error(f"❌ Lỗi khi chuẩn bị auto-commit: {e}")
                logger.debug("Traceback:", exc_info=True)
        elif files_written_relative:
            logger.info(
                "Bỏ qua auto-commit. (Không có cờ -g/--git-commit hoặc không phải gốc Git)"
            )
