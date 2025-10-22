#!/usr/bin/env python3
# Path: modules/path_checker/path_checker_core.py

import logging
from pathlib import Path
from typing import List, Set, Optional

# Import shared utilities
from utils.core import is_path_matched

# --- IMPORT LOGIC & CONFIG TỪ FILE MỚI ---
from .path_checker_config import COMMENT_RULES_BY_EXT
from .path_checker_rules import apply_line_comment_rule
# ----------------------------------------

# --- MODULE-SPECIFIC CONSTANTS ---
DEFAULT_IGNORE = {
    ".venv", "venv", "__pycache__", ".git", 
    "node_modules", "dist", "build", "out"
}

# --- 1. Hàm điều phối I/O (I/O Orchestrator) ---
# (Phần này "ít thay đổi")
def _update_files(
    files_to_scan: List[Path], 
    project_root: Path, 
    logger: logging.Logger,
    check_mode: bool
) -> List[Path]:
    """
    Internal function to process files. Reads, calls rule logic,
    and writes files if needed.
    """
    
    files_needing_fix: List[Path] = []
    
    if not files_to_scan:
        logger.warning("No files to process (after exclusions).")
        return files_needing_fix

    for file_path in files_to_scan:
        relative_path = file_path.relative_to(project_root)
        
        # 1. Tra cứu quy tắc
        file_ext = file_path.suffix
        rule = COMMENT_RULES_BY_EXT.get(file_ext)

        if not rule:
            logger.debug(f"Skipping unsupported file type: {relative_path.as_posix()}")
            continue

        try:
            # 2. Đọc file
            try:
                original_lines = file_path.read_text(encoding='utf-8').splitlines(True)
                lines = list(original_lines) # Make a mutable copy
            except UnicodeDecodeError:
                logger.warning(f"Skipping file with encoding error: {relative_path.as_posix()}")
                continue
            except IOError as e:
                logger.error(f"Could not read file {relative_path.as_posix()}: {e}")
                continue
            
            if not lines:
                logger.debug(f"Skipping empty file: {relative_path.as_posix()}")
                continue

            # 3. Gọi hàm logic (Rule) tương ứng
            new_lines = []
            
            if rule["type"] == "line":
                prefix = rule["comment_prefix"]
                correct_comment = f"{prefix} Path: {relative_path.as_posix()}\n"
                
                # Gọi logic từ file rules.py
                new_lines = apply_line_comment_rule(
                    lines, 
                    correct_comment, 
                    check_prefix=prefix
                )
            
            # (Chúng ta sẽ thêm 'elif rule["type"] == "block":' ở đây sau)
            
            else:
                logger.warning(f"Skipping file: Unknown rule type '{rule['type']}' for {relative_path.as_posix()}")
                continue

            # 4. Ghi file (nếu cần)
            if new_lines != original_lines:
                files_needing_fix.append(file_path)
                
                if not check_mode:
                    logger.info(f"Fixing header for: {relative_path.as_posix()}")
                    with file_path.open('w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                
        except Exception as e:
            logger.error(f"Error processing file {relative_path.as_posix()}: {e}")
            logger.debug("Traceback:", exc_info=True)
    
    return files_needing_fix

# --- 2. Hàm Quét file (File Scanner) ---
# (Phần này "ít thay đổi" - Đây là Public API của module)
def process_path_updates(
    logger: logging.Logger,
    project_root: Path,
    target_dir_str: Optional[str],
    extensions: List[str],
    cli_ignore: Set[str],
    script_file_path: Path,
    check_mode: bool
) -> List[Path]:
    """
    Scans and updates path comments for files in the project.
    Returns:
        A list of files that needed processing.
    """
    
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