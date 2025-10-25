# Path: modules/path_checker/path_checker_scanner.py

"""
File Scanning logic for the Path Checker module.

Responsible for finding, globbing, and filtering all files
based on extensions, .gitignore, submodules, and other rules
before they are passed to the analysis core.
"""

import logging
from pathlib import Path
# --- MODIFIED: Thêm TYPE_CHECKING ---
from typing import List, Set, Optional, TYPE_CHECKING
# --- END MODIFIED ---

# --- MODIFIED: Tách biệt import cho runtime và type-checking ---
try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec
# --- END MODIFIED ---


# Import utilities used for scanning
from utils.core import get_submodule_paths, parse_gitignore, is_path_matched
# Import config (từ gateway)
from .path_checker_config import DEFAULT_IGNORE

__all__ = ["scan_for_files"]

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
    """
    
    use_gitignore = target_dir_str is None
    scan_path = project_root
    
    logger.debug(f"Scan Root (base for rules) identified as: {project_root}")
    logger.debug(f"Scan Path (rglob start) set to: {scan_path}")

    submodule_paths = get_submodule_paths(project_root, logger)
    
    # --- MODIFIED: Tách biệt logic pathspec và fnmatch ---
    gitignore_spec: Optional['pathspec.PathSpec'] = None
    if use_gitignore:
        gitignore_spec = parse_gitignore(project_root)
        if gitignore_spec:
            logger.info("Default mode: Respecting .gitignore rules (via pathspec).")
        else:
            logger.info("Default mode: No .gitignore found or 'pathspec' missing.")
    else:
        logger.info(f"Specific path mode: Not using .gitignore for '{target_dir_str}'.")

    # fnmatch_patterns chỉ chứa các pattern fnmatch (từ config và CLI)
    fnmatch_patterns = DEFAULT_IGNORE.union(cli_ignore)
    # --- END MODIFIED ---
    
    if check_mode:
        logger.info("Running in [Check Mode] (dry-run).")
    
    logger.info(f"Scanning for *.{', *.'.join(extensions)} in: {scan_path.relative_to(scan_path.parent) if scan_path.parent != scan_path else scan_path.name}")
    # --- MODIFIED: Log fnmatch patterns ---
    if fnmatch_patterns:
        logger.debug(f"Ignoring (fnmatch): {', '.join(sorted(list(fnmatch_patterns)))}")
    # --- END MODIFIED ---

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
            
        # --- MODIFIED: Tách biệt logic filter ---
        # 3. Skip ignored files (fnmatch: .tree.ini, CLI)
        if is_path_matched(file_path, fnmatch_patterns, project_root):
            continue
        
        # 4. Skip ignored files (pathspec: .gitignore)
        if gitignore_spec:
            try:
                rel_path = file_path.relative_to(project_root)
                rel_path_str = rel_path.as_posix()

                if file_path.is_dir() and not rel_path_str.endswith('/'):
                    rel_path_str += '/'
                
                if rel_path_str == './': # Bỏ qua thư mục gốc
                    continue
                
                if gitignore_spec.match_file(rel_path_str):
                    continue
            except Exception:
                # Bỏ qua lỗi nếu không thể lấy đường dẫn tương đối
                pass
        # --- END MODIFIED ---
            
        files_to_process.append(file_path)
        
    return files_to_process