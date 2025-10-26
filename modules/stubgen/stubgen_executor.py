# Path: modules/stubgen/stubgen_executor.py

"""
Execution/Action logic for the Stub Generator (sgen) module.
Handles reporting, user confirmation, and file writing (I/O).
"""

import logging
import sys
from pathlib import Path
# --- MODIFIED: Thêm Optional ---
from typing import Dict, Any, List, Optional
# --- END MODIFIED ---

import typer

from utils.logging_config import log_success
# --- MODIFIED: Import hàm git mới từ utils ---
from utils.core import git_add_and_commit
# --- END MODIFIED ---

# --- Type Hint cho Result ---
StubResult = Dict[str, Any]

__all__ = ["execute_stubgen_action"]

# --- REMOVED: Hàm _handle_git_commit đã được chuyển sang utils/core/git.py ---


def execute_stubgen_action(
    logger: logging.Logger, 
    results: List[StubResult],
    force: bool,
    scan_root: Path
) -> None:
    """
    Hàm thực thi, nhận kết quả từ core, xử lý tương tác và ghi file.
    """
    
    if not results:
        return

    # --- (Logic phân loại file, báo cáo, và prompt 'y/n' giữ nguyên) ---
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

    if files_no_change:
        logger.info(f"\n✅ Files up-to-date ({len(files_no_change)}):")
        for r in files_no_change:
            logger.info(f"   -> OK: {r['rel_path']} ({r['symbols_count']} symbols)")
    
    if files_to_create:
        logger.info(f"\n📝 Files to create ({len(files_to_create)}):")
        for r in files_to_create:
            logger.info(f"   -> NEW: {r['rel_path']} ({r['symbols_count']} symbols)")

    if files_to_overwrite:
        logger.warning(f"\n⚠️ Files to OVERWRITE ({len(files_to_overwrite)}):")
        for r in files_to_overwrite:
            logger.warning(f"   -> OVERWRITE: {r['rel_path']} ({r['symbols_count']} symbols)")

    if not (files_to_create or files_to_overwrite):
        log_success(logger, "\n✨ Stub generation complete. All stubs are up-to-date.")
        return 
    
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
    
    # 3. Ghi file (I/O Write)
    if proceed_to_write:
        written_count = 0
        # --- MODIFIED: Đổi tên biến để rõ ràng hơn ---
        files_written_results: List[StubResult] = []
        # --- END MODIFIED ---
        
        logger.info("✍️ Writing .pyi stub files...")
        
        # --- NEW: Khởi tạo result để tránh NameError trong except ---
        result: Optional[StubResult] = None 
        # --- END NEW ---
        
        try:
            # Vòng 1: Tạo file mới
            for result in files_to_create:
                stub_path: Path = result["stub_path"]
                content: str = result["content"]
                stub_path.write_text(content, encoding='utf-8')
                log_success(logger, f"Created stub: {result['rel_path']}")
                written_count += 1
                files_written_results.append(result)
                
            # Vòng 2: Ghi đè file
            for result in files_to_overwrite:
                stub_path: Path = result["stub_path"]
                content: str = result["content"]
                stub_path.write_text(content, encoding='utf-8')
                log_success(logger, f"Overwrote stub: {result['rel_path']}")
                written_count += 1
                files_written_results.append(result)
                
        except IOError as e:
            # --- MODIFIED: Xử lý trường hợp 'result' có thể là None ---
            file_name = result['rel_path'] if result else "UNKNOWN FILE"
            logger.error(f"❌ Failed to write file {file_name}: {e}")
            # --- END MODIFIED ---
            return 
        except Exception as e:
            # --- MODIFIED: Xử lý trường hợp 'result' có thể là None ---
            file_name = result['rel_path'] if result else "UNKNOWN FILE"
            logger.error(f"❌ Unknown error while writing file {file_name}: {e}")
            # --- END MODIFIED ---
            return 
                
        if written_count > 0:
            log_success(logger, f"\n✨ Stub generation complete. Successfully processed {written_count} files.")
        else:
            log_success(logger, f"\n✨ Stub generation complete. No files needed writing.")

        # --- MODIFIED: Gọi hàm git_add_and_commit từ utils.core ---
        if files_written_results:
            # 1. Chuẩn bị danh sách đường dẫn tương đối
            relative_paths = [
                str(r["stub_path"].relative_to(scan_root)) 
                for r in files_written_results
            ]
            
            # 2. Tạo commit message
            commit_msg = f"style(stubs): Cập nhật {len(relative_paths)} file .pyi (tự động bởi sgen)"
            
            # 3. Gọi hàm utils
            git_add_and_commit(
                logger=logger,
                scan_root=scan_root,
                file_paths_relative=relative_paths,
                commit_message=commit_msg
            )
        # --- END MODIFIED ---