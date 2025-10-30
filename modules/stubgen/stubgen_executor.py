# Path: modules/stubgen/stubgen_executor.py
"""
Execution/Action logic for the Stub Generator (sgen) module.
(Side-effects: Báo cáo, Xác nhận người dùng, Ghi file, Git commit)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.logging_config import log_success
from utils.core import git_add_and_commit, is_git_repository

# Type Hint cho Result Object
StubResult = Dict[str, Any]

# SỬA: Export thêm hàm helper
__all__ = ["execute_stubgen_action", "classify_and_report_stub_changes"]


def classify_and_report_stub_changes(
    logger: logging.Logger, 
    group_name: str,
    group_raw_results: List[StubResult],
    scan_root: Path
) -> Tuple[List[StubResult], List[StubResult], List[StubResult]]:
    """
    (HÀM MỚI)
    Phân loại (I/O đọc) và In báo cáo xen kẽ cho một nhóm kết quả.
    """
    
    files_to_create: List[StubResult] = []
    files_to_overwrite: List[StubResult] = []
    files_no_change: List[StubResult] = []
    
    # 1. Phân loại file (I/O Đọc)
    for result in group_raw_results:
        stub_path: Path = result["stub_path"]
        new_content: str = result["content"]
        if not stub_path.exists():
            files_to_create.append(result)
        else:
            try:
                existing_content = stub_path.read_text(encoding='utf-8')
                if existing_content == new_content:
                    files_no_change.append(result)
                else:
                    files_to_overwrite.append(result)
            except Exception:
                files_to_overwrite.append(result) # Lỗi đọc -> coi như overwrite

    # Helper in đường dẫn tương đối
    def get_rel_path(path: Path) -> str:
        try:
            return path.relative_to(scan_root).as_posix()
        except ValueError:
            return str(path)

    # 2. In báo cáo
    total_changes = len(files_to_create) + len(files_to_overwrite)
    if not total_changes and not files_no_change:
        # Nhóm này không tạo ra kết quả nào (ví dụ: quét thư mục không có gateway)
        return [], [], []

    # SỬA: Thêm emoji 📄
    logger.info(f"\n   --- 📄 Nhóm: {group_name} ({len(group_raw_results)} gateway) ---")
    
    if files_no_change:
        logger.info(f"     ✅ Files up-to-date ({len(files_no_change)}):")
        for r in files_no_change:
            logger.info(f"        -> OK: {get_rel_path(r['stub_path'])} ({r['symbols_count']} symbols)")
    
    if files_to_create:
        logger.info(f"     📝 Files to create ({len(files_to_create)}):")
        for r in files_to_create:
            logger.info(f"        -> NEW: {get_rel_path(r['stub_path'])} ({r['symbols_count']} symbols)")

    if files_to_overwrite:
        logger.warning(f"     ⚠️ Files to OVERWRITE ({len(files_to_overwrite)}):")
        for r in files_to_overwrite:
            logger.warning(f"        -> OVERWRITE: {get_rel_path(r['stub_path'])} ({r['symbols_count']} symbols)")

    return files_to_create, files_to_overwrite, files_no_change


# SỬA: Thay đổi chữ ký hàm
def execute_stubgen_action(
    logger: logging.Logger, 
    files_to_create: List[StubResult],
    files_to_overwrite: List[StubResult],
    force: bool,
    scan_root: Path
) -> None:
    """
    Hàm thực thi, nhận các danh sách đã phân loại, hỏi xác nhận và ghi file.
    """
    
    # 1. Báo cáo tổng kết
    total_changes = len(files_to_create) + len(files_to_overwrite)
    if not total_changes:
        log_success(logger, "\n✨ Stub generation complete. All stubs are up-to-date.")
        return 

    logger.warning(f"\n⚠️ Tổng cộng {total_changes} file .pyi cần được tạo/ghi đè (chi tiết ở trên).")
    
    # 2. Hỏi xác nhận
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
    
    # 3. Ghi file
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
            # Vòng 1: Tạo file mới
            for result in files_to_create:
                result_being_processed = result
                stub_path: Path = result["stub_path"]
                content: str = result["content"]
                stub_path.write_text(content, encoding='utf-8')
                path_str = get_rel_path(stub_path)
                log_success(logger, f"Created stub: {path_str}")
                written_count += 1
                files_written_results.append(result)
                
            # Vòng 2: Ghi đè file
            for result in files_to_overwrite:
                result_being_processed = result
                stub_path: Path = result["stub_path"]
                content: str = result["content"]
                stub_path.write_text(content, encoding='utf-8')
                path_str = get_rel_path(stub_path)
                log_success(logger, f"Overwrote stub: {path_str}")
                written_count += 1
                files_written_results.append(result)
                
        except IOError as e:
            file_name = get_rel_path(result_being_processed['stub_path']) if result_being_processed else "UNKNOWN FILE"
            logger.error(f"❌ Failed to write file {file_name}: {e}")
            return 
        except Exception as e:
            file_name = get_rel_path(result_being_processed['stub_path']) if result_being_processed else "UNKNOWN FILE"
            logger.error(f"❌ Unknown error while writing file {file_name}: {e}")
            return 
                
        if written_count > 0:
            log_success(logger, f"\n✨ Stub generation complete. Successfully processed {written_count} files.")

        # 4. Tự động Git Commit
        if files_written_results and is_git_repository(scan_root):
            relative_paths = [
                str(r["stub_path"].relative_to(scan_root)) 
                for r in files_written_results
            ]
            
            commit_msg = f"style(stubs): Cập nhật {len(relative_paths)} file .pyi (tự động bởi sgen)"
            
            git_add_and_commit(
                logger=logger,
                scan_root=scan_root,
                file_paths_relative=relative_paths,
                commit_message=commit_msg
            )
        elif files_written_results:
            logger.info("Bỏ qua auto-commit: Thư mục làm việc hiện tại không phải là gốc Git.")