# Path: modules/stubgen/stubgen_executor.py
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import argparse

from utils.logging_config import log_success
from utils.core import auto_commit_changes, is_git_repository
from .stubgen_internal import (
    load_config_files,
    merge_stubgen_configs,
)


StubResult = Dict[str, Any]


__all__ = ["execute_stubgen_action"]


def execute_stubgen_action(
    logger: logging.Logger,
    files_to_create: List[StubResult],
    files_to_overwrite: List[StubResult],
    force: bool,
    scan_root: Path,
    cli_args: argparse.Namespace,
) -> None:
    total_changes = len(files_to_create) + len(files_to_overwrite)
    if not total_changes:
        log_success(logger, "\n✨ Stub generation complete. All stubs are up-to-date.")
        return

    logger.warning(
        f"\n⚠️ Tổng cộng {total_changes} file .pyi cần được tạo/ghi đè (chi tiết ở trên)."
    )

    proceed_to_write = False
    if force:
        proceed_to_write = True
    else:
        try:
            confirmation = input("\nProceed to generate/overwrite these stubs? (y/n): ")
        except (EOFError, KeyboardInterrupt):
            confirmation = "n"

        if confirmation.lower() == "y":
            proceed_to_write = True
        else:
            logger.warning("Stub generation operation cancelled by user.")
            sys.exit(0)

    if proceed_to_write:
        written_count = 0
        files_written_results: List[StubResult] = []
        result_being_processed: Optional[StubResult] = None

        logger.info("✍️ Writing .pyi stub files...")

        def get_rel_path(path: Path) -> str:
            try:
                return path.relative_to(scan_root).as_posix()
            except ValueError:
                return str(path)

        try:

            for result in files_to_create:

                result_being_processed = result
                stub_path: Path = result["stub_path"]
                content_body: str = result["content"]
                path_str = get_rel_path(stub_path)
                header = f"# Path: {path_str}\n"
                content_to_write = header + content_body
                stub_path.write_text(content_to_write, encoding="utf-8")
                log_success(logger, f"Created stub: {path_str}")
                written_count += 1
                files_written_results.append(result)

            for result in files_to_overwrite:

                result_being_processed = result
                stub_path: Path = result["stub_path"]
                content_body: str = result["content"]
                path_str = get_rel_path(stub_path)
                existing_header: Optional[str] = result.get("existing_header")
                header = f"{existing_header}\n" if existing_header else ""
                content_to_write = header + content_body
                stub_path.write_text(content_to_write, encoding="utf-8")
                log_success(logger, f"Overwrote stub: {path_str}")
                written_count += 1
                files_written_results.append(result)

        except IOError as e:
            file_name = (
                get_rel_path(result_being_processed["stub_path"])
                if result_being_processed
                else "UNKNOWN FILE"
            )
            logger.error(f"❌ Failed to write file {file_name}: {e}")
            return
        except Exception as e:
            file_name = (
                get_rel_path(result_being_processed["stub_path"])
                if result_being_processed
                else "UNKNOWN FILE"
            )
            logger.error(f"❌ Unknown error while writing file {file_name}: {e}")
            return

        if written_count > 0:
            log_success(
                logger,
                f"\n✨ Stub generation complete. Successfully processed {written_count} files.",
            )

        files_written_relative = [
            str(r["stub_path"].relative_to(scan_root)) for r in files_written_results
        ]

        git_commit: bool = getattr(cli_args, "git_commit", False)

        if files_written_relative and is_git_repository(scan_root) and git_commit:
            try:

                file_config_data = load_config_files(scan_root, logger)
                cli_config = {
                    "ignore": getattr(cli_args, "ignore", None),
                }
                merged_config = merge_stubgen_configs(
                    logger, cli_config, file_config_data
                )

                settings_to_hash = {
                    "ignore": sorted(list(merged_config["ignore_list"])),
                    "indicators": sorted(list(merged_config["indicators"])),
                    "module_list_name": merged_config["module_list_name"],
                    "all_list_name": merged_config["all_list_name"],
                }

                auto_commit_changes(
                    logger=logger,
                    scan_root=scan_root,
                    files_written_relative=files_written_relative,
                    settings_to_hash=settings_to_hash,
                    commit_scope="stubs",
                    tool_name="sgen",
                )
            except Exception as e:
                logger.error(f"❌ Lỗi khi chuẩn bị auto-commit: {e}")
                logger.debug("Traceback:", exc_info=True)
        elif files_written_relative:
            logger.info(
                "Bỏ qua auto-commit. (Không có cờ -g/--git-commit hoặc không phải gốc Git)"
            )
