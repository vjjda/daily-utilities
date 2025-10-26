# Path: modules/stubgen/stubgen_executor.py

"""
Execution/Action logic for the Stub Generator (sgen) module.
Handles reporting, user confirmation, and file writing (I/O).
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

import typer

from utils.logging_config import log_success
# --- NEW IMPORTS ---
from utils.core import run_command, is_git_repository
# --- END NEW ---

# --- Type Hint cho Result ---
StubResult = Dict[str, Any]

__all__ = ["execute_stubgen_action"]

# --- NEW HELPER FUNCTION ---
def _handle_git_commit(
    logger: logging.Logger, 
    files_changed: List[StubResult], 
    scan_root: Path
) -> None:
    """Kiểm tra, 'git add' và 'git commit' các file .pyi đã thay đổi."""
    
    if not files_changed:
        logger.debug("Không có file .pyi nào thay đổi, bỏ qua commit.")
        return

    # 1. Kiểm tra xem đây có phải là Git repo không
    if not is_git_repository(scan_root):
        logger.warning("⚠️  Bỏ qua auto-commit: Thư mục quét không phải là gốc của Git repo.")
        return

    # 2. Thu thập đường dẫn file
    file_paths_to_add: List[str] = [str(r["stub_path"].resolve()) for r in files_changed]
    
    try:
        logger.info(f"Đang thực hiện 'git add' cho {len(file_paths_to_add)} file .pyi...")
        
        # 3. Git Add
        add_command: List[str] = ["git", "add"] + file_paths_to_add
        add_success, add_out = run_command(
            add_command, logger, "Staging .pyi files"
        )
        if not add_success:
            logger.error("❌ Lỗi khi 'git add' file .pyi.")
            return

        # 4. Git Commit
        commit_count = len(file_paths_to_add)
        commit_msg = f"style(stubs): Cập nhật {commit_count} file .pyi (tự động bởi sgen)"
        
        commit_command: List[str] = ["git", "commit", "-m", commit_msg]
        commit_success, commit_out = run_command(
            commit_command, logger, "Committing .pyi files"
        )
        
        if commit_success:
            log_success(logger, f"Đã commit thành công: {commit_msg}")
        elif "nothing to commit" in commit_out:
            logger.info("Không có thay đổi .pyi nào để commit.")
        else:
            logger.error("❌ Lỗi khi 'git commit' file .pyi.")

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn khi thực thi Git: {e}")
# --- END NEW HELPER ---


def execute_stubgen_action(
    logger: logging.Logger, 
    results: List[StubResult], # <-- Nhận danh sách "pure" từ core
    force: bool,
    # --- MODIFIED: Nhận scan_root ---
    scan_root: Path
    # --- END MODIFIED ---
) -> None:
    """
    Hàm thực thi, nhận kết quả từ core, xử lý tương tác và ghi file.
    """
    
    if not results:
        return

    # --- NEW: Logic phân loại (I/O Read) ---
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
                # Đọc nội dung file .pyi hiện có
                existing_content = stub_path.read_text(encoding='utf-8')
                if existing_content == new_content:
                    files_no_change.append(result)
                else:
                    files_to_overwrite.append(result)
            except Exception as e:
                # Lỗi khi đọc file, coi như cần overwrite
                logger.warning(f"Could not read existing stub {stub_path.name}: {e}")
                files_to_overwrite.append(result)
    # --- END NEW ---


    # 1. Báo cáo kết quả (Logic giữ nguyên, chỉ đổi tên biến)
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

    # 2. Xử lý tương tác (Logic giữ nguyên)
    if not (files_to_create or files_to_overwrite):
        log_success(logger, "\n✨ Stub generation complete. All stubs are up-to-date.")
        return # Thoát sớm
    
    # --- MODIFIED: Điều chỉnh khối logic xác nhận ---
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
    
    # 3. Ghi file (I/O Write) - Chỉ chạy nếu người dùng đồng ý (hoặc --force)
    if proceed_to_write:
        written_count = 0
        files_changed_for_git: List[StubResult] = []
        
        logger.info("✍️ Writing .pyi stub files...")
        
        try:
            # Vòng 1: Tạo file mới
            for result in files_to_create:
                stub_path: Path = result["stub_path"]
                content: str = result["content"]
                stub_path.write_text(content, encoding='utf-8')
                log_success(logger, f"Created stub: {result['rel_path']}")
                written_count += 1
                files_changed_for_git.append(result) # <-- Thu thập file đã thay đổi
                
            # Vòng 2: Ghi đè file
            for result in files_to_overwrite:
                stub_path: Path = result["stub_path"]
                content: str = result["content"]
                stub_path.write_text(content, encoding='utf-8')
                log_success(logger, f"Overwrote stub: {result['rel_path']}")
                written_count += 1
                files_changed_for_git.append(result) # <-- Thu thập file đã thay đổi
                
        except IOError as e:
            logger.error(f"❌ Failed to write file {result['rel_path']}: {e}") # type: ignore
            return # Dừng lại nếu có lỗi I/O
        except Exception as e:
            logger.error(f"❌ Unknown error while writing file {result['rel_path']}: {e}") # type: ignore
            return # Dừng lại nếu có lỗi
                
        if written_count > 0:
            log_success(logger, f"\n✨ Stub generation complete. Successfully processed {written_count} files.")
        else:
            log_success(logger, f"\n✨ Stub generation complete. No files needed writing.")

        # --- NEW: Gọi auto-commit ---
        # Logic này chỉ được gọi sau khi ghi file thành công
        _handle_git_commit(
            logger=logger, 
            files_changed=files_changed_for_git, 
            scan_root=scan_root
        )