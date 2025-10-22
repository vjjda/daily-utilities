#!/usr/bin/env python3
# Path: modules/path_checker/path_checker_executor.py

"""
Execution and Reporting logic for the Path Checker module.

Handles all user-facing output, confirmation prompts, and
the final file-writing operations. This keeps the core
logic pure (analysis-only).
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Import logger helpers
from utils.logging_config import log_success

def handle_results(
    logger: logging.Logger,
    files_to_fix: List[Dict[str, Any]],
    check_mode: bool,
    fix_command_str: str,
    scan_root: Path
) -> None:
    """
    Handles the list of files needing fixes.
    - In check_mode, prints a report and the fix command.
    - In fix_mode, prints a report, asks for confirmation,
      and then writes the files.
    """
    
    processed_count = len(files_to_fix)

    if processed_count > 0:
        
        # 1. In báo cáo (luôn luôn)
        logger.warning(f"⚠️ {processed_count} files do not conform to the path convention:")
        for info in files_to_fix:
            file_path = info["path"]
            first_line = info["line"]
            fix_preview = info["fix_preview"]
            
            logger.warning(f"   -> {file_path.relative_to(scan_root).as_posix()}")
            logger.warning(f"      (Current L1: {first_line})")
            logger.warning(f"      (Proposed:   {fix_preview})")

        # 2. Xử lý dựa trên chế độ
        if check_mode:
            # --- Chế độ "check" (mặc định) ---
            logger.warning("\n-> To fix these files, run:")
            logger.warning(f"\n{fix_command_str}\n")
            sys.exit(1) # Thoát với mã lỗi 1 cho CI/CD
        else:
            # --- Chế độ "--fix" ---
            try:
                confirmation = input("\nProceed to fix these files? (y/n): ")
            except EOFError:
                confirmation = 'n'
            
            if confirmation.lower() == 'y':
                logger.debug("User confirmed fix. Proceeding to write files.")
                written_count = 0
                for info in files_to_fix:
                    file_path: Path = info["path"]
                    new_lines: List[str] = info["new_lines"]
                    try:
                        # Đây là nơi duy nhất script ghi file
                        with file_path.open('w', encoding='utf-8') as f:
                            f.writelines(new_lines)
                        logger.info(f"Fixed: {file_path.relative_to(scan_root).as_posix()}")
                        written_count += 1
                    except IOError as e:
                        logger.error(f"❌ Failed to write file {file_path.relative_to(scan_root).as_posix()}: {e}")
                
                log_success(logger, f"Done! Fixed {written_count} files.")
            
            else:
                logger.warning("Fix operation cancelled by user.")
                sys.exit(0)
            
    else:
        # 0 file cần sửa
        log_success(logger, "All files already conform to the convention. No changes needed.")