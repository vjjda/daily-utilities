#!/usr/bin/env python3
# Path: modules/path_checker/path_checker_core.py
# Path: modules/path_checker/path_checker_core.py

import logging
from pathlib import Path
from typing import List, Set, Optional

# Import shared utilities from the central core
from utils.core import is_path_matched

# --- MODULE-SPECIFIC CONSTANTS ---
DEFAULT_IGNORE = {
    ".venv", "venv", "__pycache__", ".git", 
    "node_modules", "dist", "build", "out"
}

# This is the internal function that does the file writing
def _update_files(
    files_to_scan: List[Path], 
    project_root: Path, 
    logger: logging.Logger
) -> int:
    """Internal function to process and rewrite files with correct path comments."""
    
    processed_count = 0
    if not files_to_scan:
        logger.warning("No files to process (after exclusions).")
        return 0

    for file_path in files_to_scan:
        relative_path = file_path.relative_to(project_root)
        try:
            comment_prefix = None
            
            # --- FIX 1: SỬA LOGIC COMMENT VÀ .MD ---
            # Group all '#' comment types together, including '.md'
            # --- FIX: Logic mới để xử lý các loại comment khác nhau ---
            if file_path.suffix in {'.py', '.zsh', '.sh'}:
                comment_prefix_for_check = '#'
                correct_path_comment = f"# Path: {relative_path.as_posix()}\n"
            elif file_path.suffix in {'.js', '.ts', '.css', '.scss'}:
                comment_prefix_for_check = '//'
                correct_path_comment = f"// Path: {relative_path.as_posix()}\n"
            elif file_path.suffix == '.md':
                # Xử lý đặc biệt cho Markdown
                comment_prefix_for_check = '<!--'
                correct_path_comment = f"<!--Path: {relative_path.as_posix()}-->\n"
            else:
                # Skip files with extensions we don't know how to comment
                logger.debug(f"Skipping unsupported file type: {relative_path.as_posix()}")
                continue 

            # --- FIX 3: Read the file content *before* checking lines ---
            try:
                # Read text and split into lines, keeping newline characters
                original_lines = file_path.read_text(encoding='utf-8').splitlines(True)
                lines = list(original_lines) # Make a mutable copy
            except UnicodeDecodeError:
                logger.warning(f"Skipping file with encoding error: {relative_path.as_posix()}")
                continue
            except IOError as e:
                logger.error(f"Could not read file {relative_path.as_posix()}: {e}")
                continue
            
            # Handle empty files
            if not lines:
                lines.append(correct_path_comment)
                logger.info(f"Fixing header for: {relative_path.as_posix()} (empty file)")
                with file_path.open('w', encoding='utf-8') as f:
                    f.writelines(lines)
                processed_count += 1
                continue # Go to next file

            # --- FIX 4: Corrected logic (Variables are now defined) ---
            line1_is_shebang = lines[0].startswith('#!')
            line1_is_path = lines[0].startswith(f"{comment_prefix} Path:")
            line2_is_path = False
            if len(lines) > 1 and lines[1].startswith(f"{comment_prefix} Path:"):
                line2_is_path = True

            # Logic to insert or correct the path comment
            if line1_is_shebang:
                if line2_is_path:
                    if lines[1] != correct_path_comment:
                        lines[1] = correct_path_comment # Fix existing
                else:
                    lines.insert(1, correct_path_comment) # Insert
            elif line1_is_path:
                # Check for swapped shebang/path
                if len(lines) > 1 and lines[1].startswith('#!'):
                    lines[0], lines[1] = lines[1], lines[0] # Swap them
                    if lines[1] != correct_path_comment: # Fix path (now on line 2)
                        lines[1] = correct_path_comment
                else: # Path on line 1, no shebang
                    if lines[0] != correct_path_comment:
                        lines[0] = correct_path_comment # Fix existing
            else: # No shebang, no path
                lines.insert(0, correct_path_comment) # Insert at top

            # Write changes if needed
            if lines != original_lines:
                logger.info(f"Fixing header for: {relative_path.as_posix()}")
                with file_path.open('w', encoding='utf-8') as f:
                    f.writelines(lines)
                processed_count += 1
                
        except Exception as e:
            logger.error(f"Error processing file {relative_path.as_posix()}: {e}")
            logger.debug("Traceback:", exc_info=True)
    
    return processed_count

# This is the main public function called by the script
def process_path_updates(
    logger: logging.Logger,
    project_root: Path,
    target_dir_str: Optional[str],
    extensions: List[str],
    cli_ignore: Set[str],
    script_file_path: Path
) -> int:
    """
    Scans and updates path comments for files in the project.
    Returns:
        The number of files processed.
    """
    
    # Import shared utilities here, inside the function
    from utils.core import get_submodule_paths, parse_gitignore, is_path_matched

    use_gitignore = target_dir_str is None
    scan_path = project_root / (target_dir_str or ".")
    
    logger.debug(f"Project root identified as: {project_root}")
    logger.debug(f"Scan path set to: {scan_path}")

    submodule_paths = get_submodule_paths(project_root, logger)
    
    # Merge ignore sources
    gitignore_patterns = set()
    if use_gitignore:
        gitignore_patterns = parse_gitignore(project_root)
        logger.info("Default mode: Respecting .gitignore rules.")
    else:
        logger.info(f"Specific path mode: Not using .gitignore for '{target_dir_str}'.")

    # Combine all ignore patterns
    final_ignore_patterns = DEFAULT_IGNORE.union(gitignore_patterns).union(cli_ignore)
    
    logger.info(f"Scanning for *.{', *.'.join(extensions)} in: {scan_path.relative_to(project_root)}")
    if final_ignore_patterns:
        logger.debug(f"Ignoring patterns: {', '.join(sorted(list(final_ignore_patterns)))}")

    all_files = []
    for ext in extensions:
        all_files.extend(scan_path.rglob(f"*.{ext}"))
    
    files_to_process = []
    for file_path in all_files:
        # 1. Resolve to absolute path for comparisons
        abs_file_path = file_path.resolve()

        # 2. Skip this script itself
        if abs_file_path.samefile(script_file_path):
            continue
            
        # 3. Skip files in submodules
        is_in_submodule = any(abs_file_path.is_relative_to(p) for p in submodule_paths)
        if is_in_submodule:
            continue
            
        # 4. Skip ignored files
        if is_path_matched(file_path, final_ignore_patterns, project_root):
            continue
            
        files_to_process.append(file_path)
        
    # Run the update logic
    return _update_files(files_to_process, project_root, logger)