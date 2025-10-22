#!/usr/bin/env python3
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

# --- MODIFIED: Cập nhật chữ ký hàm ---
def _update_files(
    files_to_scan: List[Path], 
    project_root: Path, 
    logger: logging.Logger,
    check_mode: bool  # <--- Thêm tham số
) -> List[Path]: # <--- Thay đổi kiểu trả về
    """
    Internal function to process files.
    - If check_mode=False, rewrites files with correct path comments.
    - If check_mode=True, only reports files that need fixing.
    Returns:
        A list of paths that need (or needed) fixing.
    """
    
    # --- MODIFIED: Thay đổi biến đếm ---
    files_needing_fix: List[Path] = []
    # --- END MODIFIED ---
    
    if not files_to_scan:
        logger.warning("No files to process (after exclusions).")
        return files_needing_fix # Trả về list rỗng

    for file_path in files_to_scan:
        relative_path = file_path.relative_to(project_root)
        try:
            
            # --- FIX: Logic mới để xử lý các loại comment khác nhau ---
            if file_path.suffix in {'.py', '.zsh', '.sh'}:
                comment_prefix_for_check = '#'
                correct_path_comment = f"# Path: {relative_path.as_posix()}\n"
            elif file_path.suffix in {'.js', '.ts', '.css', '.scss'}:
                comment_prefix_for_check = '//'
                correct_path_comment = f"// Path: {relative_path.as_posix()}\n"
            # --- FIX: ĐÃ XÓA KHỐI 'elif file_path.suffix == .md' ---
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
            
            # --- FIX: XỬ LÝ FILE RỖNG ---
            # Handle empty files: Log and skip, do not modify.
            if not lines:
                logger.debug(f"Skipping empty file: {relative_path.as_posix()}")
                continue # Go to next file
            # --- END FIX ---

            # --- FIX 4: Corrected logic (Variables are now defined) ---
            line1_is_shebang = lines[0].startswith('#!')

            # --- FIX: SỬ DỤNG 'comment_prefix_for_check' ---
            line1_is_path = lines[0].startswith(f"{comment_prefix_for_check} Path:")
            line2_is_path = False
            if len(lines) > 1 and lines[1].startswith(f"{comment_prefix_for_check} Path:"):
            # --- END FIX ---
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

            # --- MODIFIED: Logic ghi file có điều kiện ---
            if lines != original_lines:
                # Thêm file vào danh sách cần sửa
                files_needing_fix.append(file_path)
                
                # Chỉ ghi file nếu *không* ở check_mode
                if not check_mode:
                    logger.info(f"Fixing header for: {relative_path.as_posix()}")
                    with file_path.open('w', encoding='utf-8') as f:
                        f.writelines(lines)
            # --- END MODIFIED ---
                
        except Exception as e:
            logger.error(f"Error processing file {relative_path.as_posix()}: {e}")
            logger.debug("Traceback:", exc_info=True)
    
    return files_needing_fix # <--- Trả về danh sách
# --- END MODIFIED ---

# This is the main public function called by the script
def process_path_updates(
    logger: logging.Logger,
    project_root: Path, # <--- Đây giờ là CWD (hoặc thư mục chỉ định)
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
    
    # Import shared utilities here, inside the function
    from utils.core import get_submodule_paths, parse_gitignore, is_path_matched

    # --- MODIFIED: Logic xác định đường dẫn quét ---
    # project_root bây giờ là thư mục gốc (base) cho việc quét
    # và là nơi tìm .gitignore, .gitmodules
    
    use_gitignore = target_dir_str is None
    # Đường dẫn để bắt đầu rglob() (quét đệ quy) chính là project_root
    scan_path = project_root
    
    logger.debug(f"Scan Root (base for rules) identified as: {project_root}")
    logger.debug(f"Scan Path (rglob start) set to: {scan_path}")
    # --- END MODIFIED ---

    submodule_paths = get_submodule_paths(project_root, logger)
    
    # Merge ignore sources
    gitignore_patterns = set()
    if use_gitignore:
        # Tìm .gitignore tại thư mục gốc (CWD)
        gitignore_patterns = parse_gitignore(project_root)
        logger.info("Default mode: Respecting .gitignore rules.")
    else:
        logger.info(f"Specific path mode: Not using .gitignore for '{target_dir_str}'.")

    # Combine all ignore patterns
    final_ignore_patterns = DEFAULT_IGNORE.union(gitignore_patterns).union(cli_ignore)
    
    if check_mode:
        logger.info("Running in [Check Mode] (dry-run). No files will be modified.")
    
    logger.info(f"Scanning for *.{', *.'.join(extensions)} in: {scan_path.relative_to(scan_path.parent) if scan_path.parent != scan_path else scan_path.name}")
    if final_ignore_patterns:
        logger.debug(f"Ignoring patterns: {', '.join(sorted(list(final_ignore_patterns)))}")

    all_files = []
    for ext in extensions:
        # Quét từ scan_path
        all_files.extend(scan_path.rglob(f"*.{ext}"))
    
    files_to_process = []
    for file_path in all_files:
        # 1. Resolve to absolute path for comparisons
        abs_file_path = file_path.resolve()

        # 2. Skip this script itself (quan trọng nếu daily-utilities tự quét chính nó)
        if abs_file_path.samefile(script_file_path):
            continue
            
        # 3. Skip files in submodules
        is_in_submodule = any(abs_file_path.is_relative_to(p) for p in submodule_paths)
        if is_in_submodule:
            continue
            
        # 4. Skip ignored files (so sánh tương đối với project_root)
        if is_path_matched(file_path, final_ignore_patterns, project_root):
            continue
            
        files_to_process.append(file_path)
        
    # Run the update logic (dùng project_root làm base cho relative path)
    return _update_files(files_to_process, project_root, logger, check_mode)