# Path: modules/check_path/check_path_core.py

import logging
import os
from pathlib import Path
from typing import List, Set, Optional, Dict, Any

from .check_path_config import COMMENT_RULES_BY_EXT
from .check_path_rules import apply_line_comment_rule, apply_block_comment_rule
from .check_path_scanner import scan_for_files

__all__ = ["process_check_path_logic"]


# --- 1. Hàm phân tích (Analysis Function) ---
# (Hàm _update_files không thay đổi)
def _update_files(
    files_to_scan: List[Path], 
    project_root: Path, 
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    
    files_needing_fix: List[Dict[str, Any]] = []
    
    if not files_to_scan:
        logger.warning("Không có file nào để xử lý (sau khi loại trừ).")
        return files_needing_fix

    # (Nội dung hàm _update_files giữ nguyên)
    # ...
    for file_path in files_to_scan:
        relative_path = file_path.relative_to(project_root)
        
        file_ext = file_path.suffix
        rule = COMMENT_RULES_BY_EXT.get(file_ext)

        if not rule:
            logger.debug(f"Bỏ qua kiểu file không hỗ trợ: {relative_path.as_posix()}")
            continue

        try:
            try:
                original_lines = file_path.read_text(encoding='utf-8').splitlines(True)
                lines = list(original_lines)
            except UnicodeDecodeError:
                logger.warning(f"Bỏ qua file lỗi encoding: {relative_path.as_posix()}")
                continue
            except IOError as e:
                logger.error(f"Không thể đọc file {relative_path.as_posix()}: {e}")
                continue
            
            if not lines:
                logger.debug(f"Bỏ qua file rỗng: {relative_path.as_posix()}")
                continue
            
            try:
                is_executable = os.access(file_path, os.X_OK)
            except Exception:
                is_executable = False
            
            first_line_content = lines[0].strip()
            
            new_lines = []
            correct_comment_str = "" 
            rule_type = rule["type"]
            
            if rule_type == "line":
                prefix = rule["comment_prefix"]
                correct_comment = f"{prefix} Path: {relative_path.as_posix()}\n"
                correct_comment_str = correct_comment 
                new_lines = apply_line_comment_rule(
                    lines, 
                    correct_comment, 
                    check_prefix=prefix,
                    is_executable=is_executable
                )
            
            elif rule_type == "block":
                prefix = rule["comment_prefix"]
                suffix = rule["comment_suffix"]
                padding = " " if rule.get("padding", False) else ""
                correct_comment = f"{prefix}{padding}Path: {relative_path.as_posix()}{padding}{suffix}\n"
                correct_comment_str = correct_comment 
                new_lines = apply_block_comment_rule(lines, correct_comment, rule)
            
            else:
                logger.warning(f"Bỏ qua file: Kiểu quy tắc không rõ '{rule_type}' cho {relative_path.as_posix()}")
                continue

            if new_lines != original_lines:
                fix_preview_str = correct_comment_str.strip()
                if first_line_content.startswith("#!") and not is_executable:
                    fix_preview_str = f"(Đã xóa Shebang) -> {fix_preview_str}"
                
                files_needing_fix.append({
                    "path": file_path,
                    "line": first_line_content,
                    "new_lines": new_lines,
                    "fix_preview": fix_preview_str
                })
                
        except Exception as e:
            logger.error(f"Lỗi xử lý file {relative_path.as_posix()}: {e}")
            logger.debug("Traceback:", exc_info=True)
    
    return files_needing_fix


# --- 2. Hàm Điều phối (Orchestrator) ---
def process_check_path_logic(
    logger: logging.Logger,
    project_root: Path,
    target_dir_str: Optional[str],
    extensions: List[str],
    # --- MODIFIED: Thay đổi tên tham số ---
    ignore_set: Set[str], # (Thay vì 'cli_ignore')
    # --- END MODIFIED ---
    script_file_path: Path,
    check_mode: bool
) -> List[Dict[str, Any]]: 
    """
    Điều phối quá trình kiểm tra đường dẫn:
    1. Quét file.
    2. Phân tích chúng.
    """
    
    # 1. Quét file (Gọi file scanner.py)
    files_to_process = scan_for_files(
        logger=logger,
        project_root=project_root,
        target_dir_str=target_dir_str,
        extensions=extensions,
        # --- MODIFIED: Thay đổi tên keyword argument ---
        ignore_set=ignore_set, # (Thay vì 'cli_ignore')
        # --- END MODIFIED ---
        script_file_path=script_file_path,
        check_mode=check_mode
    )
    
    # 2. Phân tích file (Gọi hàm _update_files)
    return _update_files(files_to_process, project_root, logger)