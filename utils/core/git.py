# Path: utils/core/git.py

"""
Git and Filesystem Utilities
(Internal module, imported by utils/core.py)
"""

import logging
import configparser
from pathlib import Path
# --- MODIFIED: Thêm List và Tuple ---
from typing import Set, Optional, List, TYPE_CHECKING, Tuple
# --- END MODIFIED ---

# --- MODIFIED: Import run_command ---
from .process import run_command
from ..logging_config import log_success # <-- THÊM DÒNG NÀY

# --- MODIFIED: Tách biệt import cho runtime và type-checking ---
try:
    import pathspec
except ImportError:
    print("Warning: 'pathspec' library not found. .gitignore parsing will be basic.")
    print("Please run 'pip install pathspec' for full .gitignore support.")
    pathspec = None

if TYPE_CHECKING:
    import pathspec
# --- END MODIFIED ---

# --- MODIFIED: Thêm parse_gitignore ---
__all__ = [
    "is_git_repository", "find_git_root", "get_submodule_paths", "parse_gitignore",
    "git_add_and_commit"
]
# --- END MODIFIED ---

# ----------------------------------------------------------------------
# FILE SYSTEM & CONFIG UTILITIES
# ----------------------------------------------------------------------

def is_git_repository(root: Path) -> bool:
    """Checks if the given root path is the root of a Git repository."""
    return (root / ".git").is_dir()

def find_git_root(start_path: Path, max_levels: int = 5) -> Optional[Path]:
    """
    Traverses up the directory tree to find the nearest Git repository root.
    (Code moved from utils/core.py)
    """
    current_path = start_path.resolve()
    for _ in range(max_levels):
        if is_git_repository(current_path):
            return current_path
        
        if current_path == current_path.parent:
            break
            
        current_path = current_path.parent
        
    return None

def get_submodule_paths(root: Path, logger: Optional[logging.Logger] = None) -> Set[Path]:
    """
    Gets submodule directory full paths based on the .gitmodules file.
    (Code moved from utils/core.py)
    """
    submodule_paths = set()
    gitmodules_path = root / ".gitmodules"
    if gitmodules_path.exists():
        try:
            config = configparser.ConfigParser()
            config.read(gitmodules_path)
            for section in config.sections():
                if config.has_option(section, "path"):
                    path_str = config.get(section, "path")
                    submodule_paths.add((root / path_str).resolve())
        except configparser.Error as e:
            warning_msg = f"Could not parse .gitmodules file: {e}"
            if logger:
                logger.warning(f"⚠️ {warning_msg}")
            else:
                print(f"Warning: {warning_msg}") 
    return submodule_paths

# --- NEW: Nâng cấp parse_gitignore với pathspec ---
def parse_gitignore(root: Path) -> Set[str]:
    """
    Đọc .gitignore và trả về một Set các chuỗi quy tắc (patterns).
    """
    patterns: Set[str] = set()
    if pathspec is None:
        return patterns # Trả về set rỗng nếu không có thư viện

    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return patterns # Không có file .gitignore

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Thêm các quy tắc mặc định mà Git luôn áp dụng
        lines.append(".git")
        
        # Lọc các dòng rỗng/comment
        valid_lines = {
            line.strip() for line in lines 
            if line.strip() and not line.strip().startswith('#')
        }
        return valid_lines
        
    except Exception as e:
        print(f"Warning: Could not read .gitignore file: {e}")
        return patterns

def git_add_and_commit(
    logger: logging.Logger, 
    scan_root: Path,
    file_paths_relative: List[str], # <-- Nhận danh sách đường dẫn tương đối
    commit_message: str
) -> bool:
    """
    Thực hiện 'git add' và 'git commit' cho các file được chỉ định.
    
    Args:
        logger: Logger để ghi log.
        scan_root: Thư mục gốc (cwd) để chạy lệnh Git.
        file_paths_relative: Danh sách các đường dẫn file (tương đối so với scan_root).
        commit_message: Message cho commit.

    Returns:
        True nếu thành công, False nếu thất bại.
    """
    
    if not file_paths_relative:
        logger.debug("Không có file nào được chỉ định, bỏ qua commit.")
        return True # Coi như thành công vì không có gì làm

    if not is_git_repository(scan_root):
        logger.warning(f"⚠️  Bỏ qua commit: {scan_root} không phải là gốc của Git repo.")
        return False

    try:
        logger.info(f"Đang thực hiện 'git add' cho {len(file_paths_relative)} file...")
        
        # 1. Git Add
        add_command: List[str] = ["git", "add"] + file_paths_relative
        add_success, add_out = run_command(
            add_command, logger, "Staging files", cwd=scan_root
        )
        if not add_success:
            logger.error("❌ Lỗi khi 'git add' file.")
            return False

        # 2. Git Commit
        commit_command: List[str] = ["git", "commit", "-m", commit_message]
        commit_success, commit_out = run_command(
            commit_command, logger, "Committing files", cwd=scan_root
        )
        
        if commit_success:
            log_success(logger, f"Đã commit thành công: {commit_message}")
            return True
        elif "nothing to commit" in commit_out or "no changes added to commit" in commit_out:
            logger.info("Không có thay đổi nào để commit.")
            return True # Vẫn là thành công
        else:
            logger.error("❌ Lỗi khi 'git commit' file.")
            return False

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn khi thực thi Git: {e}")
        return False