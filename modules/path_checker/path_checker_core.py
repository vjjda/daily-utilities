#!/usr/bin/env python3
# Path: modules/path_checker/path_checker_core.py

import logging
from pathlib import Path
# --- MODIFIED: Thêm Dict và Any cho type hint ---
from typing import List, Set, Optional, Dict, Any
# --- END MODIFIED ---

# Import shared utilities
from utils.core import is_path_matched

# --- IMPORT LOGIC & CONFIG TỪ FILE MỚI ---
from .path_checker_config import COMMENT_RULES_BY_EXT
from .path_checker_rules import apply_line_comment_rule, apply_block_comment_rule
# ----------------------------------------

# --- MODULE-SPECIFIC CONSTANTS ---
DEFAULT_IGNORE = {
    ".venv", "venv", "__pycache__", ".git", 
    "node_modules", "dist", "build", "out"
}

# --- 1. Hàm điều phối I/O (I/O Orchestrator) ---
def _update_files(
    files_to_scan: List[Path], 
    project_root: Path, 
    logger: logging.Logger,
    check_mode: bool
# --- MODIFIED: Thay đổi kiểu trả về ---
) -> List[Dict[str, Any]]:
# --- END MODIFIED ---
    """
    Internal function to process files. Reads, calls rule logic,
    and writes files if needed.
    Returns:
        A list of dictionaries ({'path': Path, 'line': str}) 
        for files that need (or needed) fixing.
    """
    
    # --- MODIFIED: Thay đổi kiểu của list ---
    files_needing_fix: List[Dict[str, Any]] = []
    # --- END MODIFIED ---
    
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
            
            # --- Biến tạm để lưu dòng đầu tiên ---
            first_line_content = lines[0].strip()
            # ---

            new_lines = []
            rule_type = rule["type"]
            
            if rule_type == "line":
                prefix = rule["comment_prefix"]
                correct_comment = f"{prefix} Path: {relative_path.as_posix()}\n"
                new_lines = apply_line_comment_rule(lines, correct_comment, check_prefix=prefix)
            
            elif rule_type == "block":
                prefix = rule["comment_prefix"]
                suffix = rule["comment_suffix"]
                padding = " " if rule.get("padding", False) else ""
                correct_comment = f"{prefix}{padding}Path: {relative_path.as_posix()}{padding}{suffix}\n"
                new_lines = apply_block_comment_rule(lines, correct_comment, rule)
            
            else:
                logger.warning(f"Skipping file: Unknown rule type '{rule_type}' for {relative_path.as_posix()}")
                continue

            if new_lines != original_lines:
                # --- MODIFIED: Thêm dict vào list (thay vì chỉ path) ---
                files_needing_fix.append({
                    "path": file_path,
                    "line": first_line_content
                })
                # --- END MODIFIED ---
                
                if not check_mode:
                    logger.info(f"Fixing header for: {relative_path.as_posix()}")
                    with file_path.open('w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                
        except Exception as e:
            logger.error(f"Error processing file {relative_path.as_posix()}: {e}")
            logger.debug("Traceback:", exc_info=True)
    
    return files_needing_fix

# --- 2. Hàm Quét file (File Scanner) ---
def process_path_updates(
    logger: logging.Logger,
    project_root: Path,
    target_dir_str: Optional[str],
    extensions: List[str],
    cli_ignore: Set[str],
    script_file_path: Path,
    check_mode: bool
# --- MODIFIED: Thay đổi kiểu trả về ---
) -> List[Dict[str, Any]]:
# --- END MODIFIED ---
    """
    Scans and updates path comments for files in the project.
    Returns:
        A list of dictionaries ({'path': Path, 'line': str}) 
        for files that need processing.
    """
    
    # ... (Nội dung hàm này không thay đổi, chỉ có type hint ở trên) ...
    
    from utils.core import get_submodule_paths, parse_gitignore, is_path_matched

    use_gitignore = target_dir_str is None
    scan_path = project_root
    
    logger.debug(f"Scan Root (base for rules) identified as: {project_root}")
    logger.debug(f"Scan Path (rglob start) set to: {scan_path}")

    submodule_paths = get_submodule_paths(project_root, logger)
    
    gitignore_patterns = set()
    if use_gitignore:
        gitignore_patterns = parse_gitignore(project_root)
        logger.info("Default mode: Respecting .gitignore rules.")
    else:
        logger.info(f"Specific path mode: Not using .gitignore for '{target_dir_str}'.")

    final_ignore_patterns = DEFAULT_IGNORE.union(gitignore_patterns).union(cli_ignore)
    
    if check_mode:
        logger.info("Running in [Check Mode] (dry-run). No files will be modified.")
    
    logger.info(f"Scanning for *.{', *.'.join(extensions)} in: {scan_path.relative_to(scan_path.parent) if scan_path.parent != scan_path else scan_path.name}")
    if final_ignore_patterns:
        logger.debug(f"Ignoring patterns: {', '.join(sorted(list(final_ignore_patterns)))}")

    all_files = []
    for ext in extensions:
        all_files.extend(scan_path.rglob(f"*.{ext}"))
    
    files_to_process = []
    for file_path in all_files:
        abs_file_path = file_path.resolve()
        if abs_file_path.samefile(script_file_path):
            continue
        is_in_submodule = any(abs_file_path.is_relative_to(p) for p in submodule_paths)
        if is_in_submodule:
            continue
        if is_path_matched(file_path, final_ignore_patterns, project_root):
            continue
        files_to_process.append(file_path)
        
    return _update_files(files_to_process, project_root, logger, check_mode)