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

# --- Type Hint cho Result ---
StubResult = Dict[str, Any]

__all__ = ["execute_stubgen_action"]

def execute_stubgen_action(
    logger: logging.Logger, 
    results: List[StubResult], # <-- Nhận danh sách "pure" từ core
    force: bool
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
    
    if not force:
        try:
            confirmation = input("\nProceed to generate/overwrite these stubs? (y/n): ")
        except (EOFError, KeyboardInterrupt):
            confirmation = "n"

        if confirmation.lower() != "y":
            logger.warning("Stub generation operation cancelled by user.")
            sys.exit(0)
    
    # 3. Ghi file (I/O Write)
    written_count = 0
    
    logger.info("✍️ Writing .pyi stub files...")
    
    # --- MODIFIED: Tách riêng 2 vòng lặp để log "action" chính xác ---
    try:
        # Vòng 1: Tạo file mới
        for result in files_to_create:
            stub_path: Path = result["stub_path"]
            content: str = result["content"]
            stub_path.write_text(content, encoding='utf-8')
            log_success(logger, f"Created stub: {result['rel_path']}")
            written_count += 1
            
        # Vòng 2: Ghi đè file
        for result in files_to_overwrite:
            stub_path: Path = result["stub_path"]
            content: str = result["content"]
            stub_path.write_text(content, encoding='utf-8')
            log_success(logger, f"Overwrote stub: {result['rel_path']}")
            written_count += 1
            
    except IOError as e:
        logger.error(f"❌ Failed to write file {result['rel_path']}: {e}") # type: ignore
    except Exception as e:
        logger.error(f"❌ Unknown error while writing file {result['rel_path']}: {e}") # type: ignore
    # --- END MODIFIED ---
            
    if written_count > 0:
        log_success(logger, f"\n✨ Stub generation complete. Successfully processed {written_count} files.")
    else:
        log_success(logger, f"\n✨ Stub generation complete. No files needed writing.")