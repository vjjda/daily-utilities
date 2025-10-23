# Path: modules/path_checker/path_checker_scanner.py

"""
File Scanning logic for the Path Checker module.

Responsible for finding, globbing, and filtering all files
based on extensions, .gitignore, submodules, and other rules
before they are passed to the analysis core.
"""

import logging
from pathlib import Path
from typing import List, Set, Optional

# Import utilities used for scanning
from utils.core import get_submodule_paths, parse_gitignore, is_path_matched
# Import config
from .path_checker_config import DEFAULT_IGNORE

def scan_for_files(
    logger: logging.Logger,
    project_root: Path,
    target_dir_str: Optional[str],
    extensions: List[str],
    cli_ignore: Set[str],
    script_file_path: Path,
    check_mode: bool
) -> List[Path]:
    """
    Scans the project directory, filters files, and returns a clean
    list of files to be processed.
    
    Đây là logic đã được chuyển từ 'process_path_updates' của core.
    """
    
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

    # DEFAULT_IGNORE được import từ config
    final_ignore_patterns = DEFAULT_IGNORE.union(gitignore_patterns).union(cli_ignore)
    
    if check_mode:
        logger.info("Running in [Check Mode] (dry-run).")
    
    logger.info(f"Scanning for *.{', *.'.join(extensions)} in: {scan_path.relative_to(scan_path.parent) if scan_path.parent != scan_path else scan_path.name}")
    if final_ignore_patterns:
        logger.debug(f"Ignoring patterns: {', '.join(sorted(list(final_ignore_patterns)))}")

    all_files = []
    for ext in extensions:
        all_files.extend(scan_path.rglob(f"*.{ext}"))
    
    files_to_process = []
    for file_path in all_files:
        abs_file_path = file_path.resolve()

        # 1. Skip this script itself
        if abs_file_path.samefile(script_file_path):
            continue
        
        # 2. Skip files in submodules
        is_in_submodule = any(abs_file_path.is_relative_to(p) for p in submodule_paths)
        if is_in_submodule:
            continue
            
        # 3. Skip ignored files
        if is_path_matched(file_path, final_ignore_patterns, project_root):
            continue
            
        files_to_process.append(file_path)
        
    return files_to_process