# Path: modules/path_checker/path_checker_executor.py

"""
Execution and Reporting logic for the Path Checker module.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Import logger helpers
from utils.logging_config import log_success

# --- MODIFIED: Thêm tham số git_warning_str ---
def handle_results(
    logger: logging.Logger,
    files_to_fix: List[Dict[str, Any]],
    check_mode: bool,
    fix_command_str: str,
    scan_root: Path,
    git_warning_str: str # <-- New parameter
) -> None:
# --- END MODIFIED ---
    """
    Handles the list of files needing fixes.
    """
    
    processed_count = len(files_to_fix)

    if processed_count > 0:
        
        # 1. In báo cáo (luôn luôn)
        logger.warning(f"⚠️ {processed_count} files do not conform to the path convention:")
        # ... (print file list) ...
        
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
            
            # --- MODIFIED: In Git warning trước lệnh fix ---
            if git_warning_str:
                logger.warning(f"\n{git_warning_str}")
            # --- END MODIFIED ---

            logger.warning("-> To fix these files, run:")
            logger.warning(f"\n{fix_command_str}\n")
            sys.exit(1)
        else:
            # --- Chế độ "--fix" ---

            # --- MODIFIED: In Git warning trước khi hỏi xác nhận ---
            if git_warning_str:
                logger.warning(f"\n{git_warning_str}")
            # --- END MODIFIED ---
            
            try:
                confirmation = input("\nProceed to fix these files? (y/n): ")
            except EOFError:
                confirmation = 'n'
            
            if confirmation.lower() == 'y':
                # ... (logic ghi file) ...
                written_count = 0
                for info in files_to_fix:
                    file_path: Path = info["path"]
                    new_lines: List[str] = info["new_lines"]
                    try:
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
        # --- MODIFIED: Vẫn in Git warning nếu không có gì để sửa ---
        if git_warning_str:
            logger.warning(f"\n{git_warning_str}")
        # --- END MODIFIED ---

        log_success(logger, "All files already conform to the convention. No changes needed.")