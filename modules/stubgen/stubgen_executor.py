# Path: modules/stubgen/stubgen_executor.py
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import argparse 

from utils.logging_config import log_success
from utils.core import git_add_and_commit, is_git_repository 
# Thêm import
from utils.core.config_helpers import generate_config_hash 
from .stubgen_internal import (
    load_config_files, 
    merge_stubgen_configs, 
)


StubResult = Dict[str, Any]

__all__ = ["execute_stubgen_action", "classify_and_report_stub_changes"]


def _split_header_and_content(file_content: str) -> Tuple[Optional[str], str]:
    if not file_content:
        return None, ""

    lines = file_content.splitlines()
    first_line = lines[0].strip()

    if first_line.startswith("# Path:"):
        header = lines[0]

        body = "\n".join(lines[1:])
        return header, body
    else:

        return None, file_content


def classify_and_report_stub_changes(
    logger: logging.Logger,
    group_name: str,
    group_raw_results: List[StubResult],
    scan_root: Path,
) -> Tuple[List[StubResult], List[StubResult], List[StubResult]]:

    files_to_create: List[StubResult] = []
    files_to_overwrite: List[StubResult] = []
    files_no_change: List[StubResult] = []

    for result in group_raw_results:
        stub_path: Path = result["stub_path"]

        new_content_body: str = result["content"]

        if not stub_path.exists():
            files_to_create.append(result)
        else:
            try:
                existing_full_content = stub_path.read_text(encoding="utf-8")

                existing_header, existing_content_body = _split_header_and_content(
                    existing_full_content
                )

                if existing_content_body.strip() == new_content_body.strip():
                    files_no_change.append(result)
                else:

                    result["existing_header"] = existing_header
                    files_to_overwrite.append(result)
            except Exception as e:
                logger.warning(
                    f"Không thể đọc/so sánh stub {stub_path.name}: {e}. Đánh dấu là OVERWRITE."
                )
                result["existing_header"] = None
                files_to_overwrite.append(result)

    def get_rel_path(path: Path) -> str:
        try:
            return path.relative_to(scan_root).as_posix()
        except ValueError:
            return str(path)

    total_changes = len(files_to_create) + len(files_to_overwrite)
    if not total_changes and not files_no_change:
        return [], [], []

    logger.info(
        f"\n   --- 📄 Nhóm: {group_name} ({len(group_raw_results)} gateway) ---"
    )

    if files_no_change:
        logger.info(f"     ✅ Files up-to-date ({len(files_no_change)}):")
        for r in files_no_change:
            logger.info(
                f"        -> OK: {get_rel_path(r['stub_path'])} ({r['symbols_count']} symbols)"
            )

    if files_to_create:
        logger.info(f"     📝 Files to create ({len(files_to_create)}):")
        for r in files_to_create:
            logger.info(
                f"        -> NEW: {get_rel_path(r['stub_path'])} ({r['symbols_count']} symbols)"
            )

    if files_to_overwrite:
        logger.warning(f"     ⚠️ Files to OVERWRITE ({len(files_to_overwrite)}):")
        for r in files_to_overwrite:
            logger.warning(
                f"        -> OVERWRITE: {get_rel_path(r['stub_path'])} ({r['symbols_count']} symbols)"
            )

    return files_to_create, files_to_overwrite, files_no_change


def execute_stubgen_action(
    logger: logging.Logger,
    files_to_create: List[StubResult],
    files_to_overwrite: List[StubResult],
    force: bool,
    scan_root: Path,
    cli_args: argparse.Namespace, # <-- Đã thêm ở bước trước
) -> None:

    # ... (Logic dry_run, force, proceed_to_write giữ nguyên) ... 
    
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
        # ... (Logic ghi file giữ nguyên) ... 
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

        # --- CẬP NHẬT LOGIC GIT ---
        if files_written_results and is_git_repository(scan_root): 
            try:
                # Tải cấu hình để hash
                file_config_data = load_config_files(scan_root, logger) 
                cli_config = {
                    "ignore": getattr(cli_args, "ignore", None),
                    "include": getattr(cli_args, "include", None),
                }
                merged_config = merge_stubgen_configs(logger, cli_config, file_config_data) 

                # Tạo dict cài đặt ổn định để hash
                settings_to_hash = {
                    "ignore": sorted(list(merged_config["ignore_list"])),
                    "include": sorted(list(merged_config["include_list"])),
                    "indicators": sorted(list(merged_config["indicators"])),
                    "module_list_name": merged_config["module_list_name"],
                    "all_list_name": merged_config["all_list_name"],
                }
                
                config_hash = generate_config_hash(settings_to_hash, logger) 

                relative_paths = [
                    str(r["stub_path"].relative_to(scan_root))
                    for r in files_written_results
                ]

                # --- THAY ĐỔI ĐỊNH DẠNG COMMIT MSG ---
                commit_msg = f"style(stubs): Cập nhật {len(relative_paths)} file .pyi (sgen) [Settings:{config_hash}]"

                git_add_and_commit(
                    logger=logger,
                    scan_root=scan_root,
                    file_paths_relative=relative_paths,
                    commit_message=commit_msg,
                ) 
            except Exception as e:
                logger.error(f"❌ Lỗi khi tạo hash hoặc thực thi git commit: {e}")
                logger.debug("Traceback:", exc_info=True)

        elif files_written_results:
            logger.info(
                "Bỏ qua auto-commit: Thư mục làm việc hiện tại không phải là gốc Git."
            )