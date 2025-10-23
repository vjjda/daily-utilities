# Path: modules/path_checker/path_checker_core.py

import logging
import os  # <-- THÊM IMPORT
from pathlib import Path
from typing import List, Set, Optional, Dict, Any

# --- IMPORT LOGIC & CONFIG TỪ FILE MỚI ---
from .path_checker_config import COMMENT_RULES_BY_EXT
from .path_checker_rules import apply_line_comment_rule, apply_block_comment_rule
# --- NEW: Import scanner mới ---
from .path_checker_scanner import scan_for_files
# --- END NEW ---


# --- 1. Hàm phân tích (Analysis Function) ---
# (Hàm _update_files không thay đổi so với bước trước)
def _update_files(
    files_to_scan: List[Path], 
    project_root: Path, 
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    This function *only* analyzes and *never* writes.
    Returns:
        A list of dictionaries ({'path': ..., 'line': ..., 'new_lines': ..., 'fix_preview': ...})
    """
    
    files_needing_fix: List[Dict[str, Any]] = []
    
    if not files_to_scan:
        logger.warning("No files to process (after exclusions).")
        return files_needing_fix

    for file_path in files_to_scan:
        relative_path = file_path.relative_to(project_root)
        
        file_ext = file_path.suffix
        rule = COMMENT_RULES_BY_EXT.get(file_ext)

        if not rule:
            logger.debug(f"Skipping unsupported file type: {relative_path.as_posix()}")
            continue

        try:
            try:
                original_lines = file_path.read_text(encoding='utf-8').splitlines(True)
                lines = list(original_lines)
            except UnicodeDecodeError:
                logger.warning(f"Skipping file with encoding error: {relative_path.as_posix()}")
                continue
            except IOError as e:
                logger.error(f"Could not read file {relative_path.as_posix()}: {e}")
                continue
            
            if not lines:
                logger.debug(f"Skipping empty file: {relative_path.as_posix()}")
                continue
            
            # --- NEW: Kiểm tra quyền thực thi ---
            try:
                is_executable = os.access(file_path, os.X_OK)
            except Exception:
                is_executable = False # Mặc định là False nếu có lỗi
            # --- END NEW ---
            
            first_line_content = lines[0].strip()
            
            new_lines = []
            correct_comment_str = "" 
            rule_type = rule["type"]
            
            if rule_type == "line":
                prefix = rule["comment_prefix"]
                correct_comment = f"{prefix} Path: {relative_path.as_posix()}\n"
                correct_comment_str = correct_comment 
                # --- MODIFIED: Truyền cờ is_executable ---
                new_lines = apply_line_comment_rule(
                    lines, 
                    correct_comment, 
                    check_prefix=prefix,
                    is_executable=is_executable # <-- Tham số mới
                )
                # --- END MODIFIED ---
            
            elif rule_type == "block":
                prefix = rule["comment_prefix"]
                suffix = rule["comment_suffix"]
                padding = " " if rule.get("padding", False) else ""
                correct_comment = f"{prefix}{padding}Path: {relative_path.as_posix()}{padding}{suffix}\n"
                correct_comment_str = correct_comment 
                new_lines = apply_block_comment_rule(lines, correct_comment, rule)
            
            else:
                logger.warning(f"Skipping file: Unknown rule type '{rule_type}' for {relative_path.as_posix()}")
                continue

            if new_lines != original_lines:
                # --- MODIFIED: Cải thiện logic preview ---
                fix_preview_str = correct_comment_str.strip()
                if first_line_content.startswith("#!") and not is_executable:
                    fix_preview_str = f"(Removed Shebang) -> {fix_preview_str}"
                
                files_needing_fix.append({
                    "path": file_path,
                    "line": first_line_content,
                    "new_lines": new_lines,
                    "fix_preview": fix_preview_str
                })
                # --- END MODIFIED ---
                
        except Exception as e:
            logger.error(f"Error processing file {relative_path.as_posix()}: {e}")
            logger.debug("Traceback:", exc_info=True)
    
    return files_needing_fix

# --- 2. Hàm Điều phối (Orchestrator) ---
# --- (Hàm process_path_updates không thay đổi) ---
def process_path_updates(
    logger: logging.Logger,
    project_root: Path,
    target_dir_str: Optional[str],
    extensions: List[str],
    cli_ignore: Set[str],
    script_file_path: Path,
    check_mode: bool
) -> List[Dict[str, Any]]: 
    """
    Orchestrates the path checking process:
    1. Scans for files.
    2. Analyzes them for compliance.
    Returns:
        A list of dictionaries for files that need processing.
    """
    
    # 1. Quét file (Gọi file scanner.py)
    files_to_process = scan_for_files(
        logger=logger,
        project_root=project_root,
        target_dir_str=target_dir_str,
        extensions=extensions,
        cli_ignore=cli_ignore,
        script_file_path=script_file_path,
        check_mode=check_mode
    )
    
    # 2. Phân tích file (Gọi hàm _update_files)
    return _update_files(files_to_process, project_root, logger)