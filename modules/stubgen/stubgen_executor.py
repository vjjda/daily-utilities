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
    results: List[StubResult],
    force: bool
) -> None:
    """
    Hàm thực thi, nhận kết quả từ core, xử lý tương tác và ghi file.
    """
    
    if not results:
        return

    # --- MODIFIED: Cập nhật logic báo cáo ---
    # 1. Báo cáo kết quả
    files_to_create = [r for r in results if r["status"] == "new"]
    files_to_overwrite = [r for r in results if r["status"] == "overwrite"]
    files_no_change = [r for r in results if r["status"] == "no_change"]

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
    # --- END MODIFIED ---

    # --- MODIFIED: Chỉ hỏi/ghi nếu có file cần thay đổi ---
    if not (files_to_create or files_to_overwrite):
        log_success(logger, "\n✨ Stub generation complete. All stubs are up-to-date.")
        return # Thoát sớm
    
    # 2. Xử lý tương tác (nếu không có cờ --force)
    if not force:
        try:
            confirmation = input("\nProceed to generate/overwrite these stubs? (y/n): ")
        except (EOFError, KeyboardInterrupt):
            confirmation = "n"

        if confirmation.lower() != "y":
            logger.warning("Stub generation operation cancelled by user.")
            sys.exit(0)
    
    # 3. Ghi file
    written_count = 0
    
    logger.info("✍️ Writing .pyi stub files...")
    
    for result in results:
        # --- MODIFIED: Bỏ qua file không thay đổi ---
        if result["status"] == "no_change":
            continue
        
        stub_path: Path = result["stub_path"]
        content: str = result["content"]
        
        try:
            # Ghi file
            stub_path.write_text(content, encoding='utf-8')
            
            # --- MODIFIED: Cập nhật logic 'action' ---
            action = "Overwrote" if result["status"] == "overwrite" else "Created"
            log_success(logger, f"{action} stub: {result['rel_path']}")
            written_count += 1
            
        except IOError as e:
            logger.error(f"❌ Failed to write file {result['rel_path']}: {e}")
        except Exception as e:
            logger.error(f"❌ Unknown error while writing file {result['rel_path']}: {e}")
            
    # --- MODIFIED: Cập nhật thông báo cuối (để xử lý trường hợp không ghi gì) ---
    if written_count > 0:
        log_success(logger, f"\n✨ Stub generation complete. Successfully processed {written_count} files.")
    else:
        # Trường hợp này không nên xảy ra do đã return sớm
        log_success(logger, f"\n✨ Stub generation complete. No files needed writing.")
    # --- END MODIFIED ---