# Path: modules/check_path/check_path_core.py

import logging
import os
from pathlib import Path
from typing import List, Set, Optional, Dict, Any

# --- MODIFIED: Import hàm merge và default mới ---
from utils.core import (
    resolve_config_value, 
    resolve_config_list, # <-- Hàm này giờ trả về List
    parse_comma_list,
    resolve_set_modification # <-- THÊM HÀM MỚI
)
from .check_path_config import (
    COMMENT_RULES_BY_EXT, 
    DEFAULT_EXTENSIONS, # <-- Import Set mới
    DEFAULT_IGNORE
)
# --- END MODIFIED ---

from .check_path_rules import apply_line_comment_rule, apply_block_comment_rule
from .check_path_scanner import scan_for_files

__all__ = ["process_check_path_logic"]


def _update_files(
    files_to_scan: List[Path], 
    project_root: Path, 
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    
    # (Nội dung hàm _update_files giữ nguyên)
    files_needing_fix: List[Dict[str, Any]] = []
    if not files_to_scan:
        logger.warning("Không có file nào để xử lý (sau khi loại trừ).")
        return files_needing_fix

    for file_path in files_to_scan:
        relative_path = file_path.relative_to(project_root)
        file_ext = "".join(file_path.suffixes) # Xử lý đuôi kép như .py.template
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
            
            if not lines: continue
            
            try: is_executable = os.access(file_path, os.X_OK)
            except Exception: is_executable = False
            
            first_line_content = lines[0].strip()
            new_lines = []
            correct_comment_str = "" 
            rule_type = rule["type"]
            
            if rule_type == "line":
                prefix = rule["comment_prefix"]
                correct_comment = f"{prefix} Path: {relative_path.as_posix()}\n"
                correct_comment_str = correct_comment 
                new_lines = apply_line_comment_rule(lines, correct_comment, prefix, is_executable)
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


def process_check_path_logic(
    logger: logging.Logger,
    project_root: Path,
    target_dir_str: Optional[str],
    cli_extensions: Optional[str],    
    cli_ignore: Optional[str],        
    file_config_data: Dict[str, Any], 
    script_file_path: Path,
    check_mode: bool
) -> List[Dict[str, Any]]: 
    """
    Điều phối quá trình kiểm tra đường dẫn:
    1. Hợp nhất cấu hình (Logic)
    2. Quét file.
    3. Phân tích chúng.
    """
    
    # --- 1. Hợp nhất Cấu hình ---
    
    # --- MODIFIED: Sử dụng resolve_set_modification cho extensions ---
    # (Logic 'extensions' giữ nguyên, vì nó dùng resolve_set_modification)
    file_extensions_value = file_config_data.get('extensions')
    
    file_ext_list: Optional[List[str]]
    if isinstance(file_extensions_value, str):
        file_ext_list = list(parse_comma_list(file_extensions_value))
    else:
        file_ext_list = file_extensions_value # Giữ nguyên (List hoặc None)
        
    tentative_extensions: Set[str]
    if file_ext_list is not None:
         tentative_extensions = set(file_ext_list)
         logger.debug("Sử dụng danh sách 'extensions' từ file config làm cơ sở.")
    else:
         tentative_extensions = DEFAULT_EXTENSIONS
         logger.debug("Sử dụng danh sách 'extensions' mặc định làm cơ sở.")
    
    final_extensions_set = resolve_set_modification(
        tentative_set=tentative_extensions,
        cli_string=cli_extensions
    )
    
    if cli_extensions:
        logger.debug(f"Đã áp dụng logic CLI: '{cli_extensions}'. Set 'extensions' cuối cùng: {sorted(list(final_extensions_set))}")
    else:
        logger.debug(f"Set 'extensions' cuối cùng (không có CLI): {sorted(list(final_extensions_set))}")

    final_extensions_list = sorted(list(final_extensions_set))
    # --- END MODIFIED ---

    # --- MODIFIED: Cập nhật logic 'ignore' để nhận List ---
    final_ignore_list = resolve_config_list(
        cli_str_value=cli_ignore,
        file_list_value=file_config_data.get('ignore'), # <-- Đây là List[str] hoặc None
        default_set_value=DEFAULT_IGNORE
    )
    logger.debug(f"Danh sách 'ignore' cuối cùng (đã merge, giữ trật tự): {final_ignore_list}")
    # --- END MODIFIED ---
    
    # 2. Quét file
    files_to_process = scan_for_files(
        logger=logger,
        project_root=project_root,
        target_dir_str=target_dir_str,
        extensions=final_extensions_list, # <-- Truyền List đã xử lý
        ignore_list=final_ignore_list,     # <-- MODIFIED: Đổi tên
        script_file_path=script_file_path,
        check_mode=check_mode
    )
    
    # 3. Phân tích file
    return _update_files(files_to_process, project_root, logger)