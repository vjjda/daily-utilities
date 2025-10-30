# Path: modules/stubgen/stubgen_executor.py
"""
Execution/Action logic for the Stub Generator (sgen) module.
(Side-effects: Báo cáo, Xác nhận người dùng, Ghi file, Git commit)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logging_config import log_success
# SỬA: Import thêm 'is_git_repository'
from utils.core import git_add_and_commit, is_git_repository

# Type Hint cho Result Object
StubResult = Dict[str, Any]

__all__ = ["execute_stubgen_action"]


def execute_stubgen_action(
    logger: logging.Logger, 
    results: List[StubResult],
    force: bool,
    scan_root: Path # Sẽ là Path.cwd() từ entrypoint
) -> None:
    """
    Hàm thực thi, nhận kết quả từ core, xử lý tương tác và ghi file.
    ...
    Args:
        ...
        scan_root: Thư mục gốc (dùng để tính relpath và chạy git).
    """
    
    if not results:
        return

    # 1. Phân loại file (I/O Đọc)
    files_to_create: List[StubResult] = []
    files_to_overwrite: List[StubResult] = []
    files_no_change: List[StubResult] = []

    logger.debug("Categorizing stub files (Read I/O)...")
    for result in results:
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
            except Exception as e:
                logger.warning(f"Could not read existing stub {stub_path.name}: {e}")
                files_to_overwrite.append(result)

    # 2. Báo cáo cho người dùng
    # (SỬA: In đường dẫn tương đối từ scan_root (CWD) thay vì 'rel_path'
    #  vì 'rel_path' được tính từ gốc quét cục bộ, có thể gây nhầm lẫn)
    
    def get_rel_path_for_reporting(stub_path: Path) -> str:
        try:
            return stub_path.relative_to(scan_root).as_posix()
        except ValueError:
            return str(stub_path) # Fallback nếu nằm ngoài CWD

    if files_no_change:
        logger.info(f"\n✅ Files up-to-date ({len(files_no_change)}):")
        for r in files_no_change:
            path_str = get_rel_path_for_reporting(r['stub_path'])
            logger.info(f"   -> OK: {path_str} ({r['symbols_count']} symbols)")
    
    if files_to_create:
        logger.info(f"\n📝 Files to create ({len(files_to_create)}):")
        for r in files_to_create:
            path_str = get_rel_path_for_reporting(r['stub_path'])
            logger.info(f"   -> NEW: {path_str} ({r['symbols_count']} symbols)")

    if files_to_overwrite:
        logger.warning(f"\n⚠️ Files to OVERWRITE ({len(files_to_overwrite)}):")
        for r in files_to_overwrite:
            path_str = get_rel_path_for_reporting(r['stub_path'])
            logger.warning(f"   -> OVERWRITE: {path_str} ({r['symbols_count']} symbols)")

    if not (files_to_create or files_to_overwrite):
        log_success(logger, "\n✨ Stub generation complete. All stubs are up-to-date.")
        return 
    
    # 3. Hỏi xác nhận
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
    
    # 4. Ghi file (I/O Write)
    if proceed_to_write:
        written_count = 0
        files_written_results: List[StubResult] = []
        result_being_processed: Optional[StubResult] = None # Để debug khi lỗi
        
        logger.info("✍️ Writing .pyi stub files...")
        
        try:
            for result in files_to_create:
                result_being_processed = result
                stub_path: Path = result["stub_path"]
                content: str = result["content"]
                stub_path.write_text(content, encoding='utf-8')
                path_str = get_rel_path_for_reporting(stub_path)
                log_success(logger, f"Created stub: {path_str}")
                written_count += 1
                files_written_results.append(result)
                
            for result in files_to_overwrite:
                result_being_processed = result
                stub_path: Path = result["stub_path"]
                content: str = result["content"]
                stub_path.write_text(content, encoding='utf-8')
                path_str = get_rel_path_for_reporting(stub_path)
                log_success(logger, f"Overwrote stub: {path_str}")
                written_count += 1
                files_written_results.append(result)
                
        except IOError as e:
            file_name = get_rel_path_for_reporting(result_being_processed['stub_path']) if result_being_processed else "UNKNOWN FILE"
            logger.error(f"❌ Failed to write file {file_name}: {e}")
            return 
        except Exception as e:
            file_name = get_rel_path_for_reporting(result_being_processed['stub_path']) if result_being_processed else "UNKNOWN FILE"
            logger.error(f"❌ Unknown error while writing file {file_name}: {e}")
            return 
                
        if written_count > 0:
            log_success(logger, f"\n✨ Stub generation complete. Successfully processed {written_count} files.")
        else:
            log_success(logger, f"\n✨ Stub generation complete. No files needed writing.")

        # 5. Tự động Git Commit (SỬA: Thêm kiểm tra an toàn)
        if files_written_results and is_git_repository(scan_root):
            relative_paths = [
                str(r["stub_path"].relative_to(scan_root)) 
                for r in files_written_results
            ]
            
            commit_msg = f"style(stubs): Cập nhật {len(relative_paths)} file .pyi (tự động bởi sgen)"
            
            git_add_and_commit(
                logger=logger,
                scan_root=scan_root, # Sẽ là CWD
                file_paths_relative=relative_paths,
                commit_message=commit_msg
            )
        elif files_written_results:
            logger.info("Bỏ qua auto-commit: Thư mục làm việc hiện tại không phải là gốc Git.")