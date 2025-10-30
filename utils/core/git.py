# Path: utils/core/git.py
"""
Các tiện ích liên quan đến Git và hệ thống file.
(Module nội bộ, được import bởi utils/core)
"""

import logging
import configparser
from pathlib import Path
from typing import Set, Optional, List, TYPE_CHECKING, Tuple, Iterable

from .process import run_command
from ..logging_config import log_success

# ... (try/except pathspec) ...

__all__ = [
    "is_git_repository", "find_git_root", "get_submodule_paths", "parse_gitignore",
    "git_add_and_commit",
    "find_file_upwards" # <-- THÊM MỚI
]

def find_file_upwards(
    filename: str, 
    start_path: Path, 
    logger: logging.Logger,
    max_levels: int = 10
) -> Optional[Path]:
    """
    (HÀM MỚI)
    Tìm một file cụ thể bằng cách đi ngược lên cây thư mục.
    """
    current_path = start_path.resolve()
    for _ in range(max_levels):
        file_to_find = current_path / filename
        if file_to_find.is_file():
            logger.debug(f"Đã tìm thấy '{filename}' tại: {current_path.as_posix()}")
            return file_to_find

        if current_path == current_path.parent:
            break
        current_path = current_path.parent

    logger.debug(f"Không tìm thấy '{filename}' trong {max_levels} cấp thư mục cha từ {start_path.as_posix()}.")
    return None

def is_git_repository(root: Path) -> bool:
    """Kiểm tra xem đường dẫn `root` có phải là gốc của một kho Git không."""
    return (root / ".git").is_dir()

def find_git_root(start_path: Path, max_levels: int = 5) -> Optional[Path]:
    """
    Tìm thư mục gốc `.git` gần nhất bằng cách đi ngược lên cây thư mục.
    """
    current_path = start_path.resolve()
    for _ in range(max_levels):
        if is_git_repository(current_path):
            return current_path

        # Dừng nếu đã lên đến thư mục gốc của hệ thống file
        if current_path == current_path.parent:
            break
        current_path = current_path.parent

    return None

def get_submodule_paths(root: Path, logger: Optional[logging.Logger] = None) -> Set[Path]:
    """
    Lấy danh sách đường dẫn tuyệt đối đến các thư mục submodule dựa trên file `.gitmodules`.

    Args:
        root: Đường dẫn gốc của kho Git.
        logger: Logger tùy chọn để ghi cảnh báo nếu không parse được file.

    Returns:
        Một Set chứa các đối tượng Path tuyệt đối đến thư mục submodule.
    """
    submodule_paths = set()
    gitmodules_path = root / ".gitmodules"
    if gitmodules_path.exists():
        try:
            config = configparser.ConfigParser()
            # Đọc file với encoding utf-8 để tránh lỗi
            config.read(gitmodules_path, encoding='utf-8')
            for section in config.sections():
                if config.has_option(section, "path"):
                    path_str = config.get(section, "path")
                    submodule_paths.add((root / path_str).resolve())
        except configparser.Error as e:
            warning_msg = f"Không thể phân tích file .gitmodules: {e}"
            if logger:
                logger.warning(f"⚠️ {warning_msg}")
            else:
                print(f"Cảnh báo: {warning_msg}")
    return submodule_paths

def parse_gitignore(root: Path) -> List[str]:
    """
    Đọc file `.gitignore` tại thư mục `root` và trả về danh sách
    các quy tắc (patterns), giữ nguyên thứ tự gốc.

    Bao gồm cả quy tắc ẩn `.git` mà Git luôn áp dụng.
    Loại bỏ các dòng trống và comment (#).

    Args:
        root: Đường dẫn đến thư mục chứa file `.gitignore`.

    Returns:
        List các chuỗi pattern từ `.gitignore`. Trả về list rỗng nếu
        file không tồn tại hoặc có lỗi đọc.
    """
    patterns: List[str] = []
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return patterns # Không có file .gitignore

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Thêm các quy tắc mặc định mà Git luôn áp dụng (vào cuối)
        lines.append(".git/") # Thêm dấu / để chắc chắn là thư mục

        valid_lines = [
            line.strip() for line in lines
            if line.strip() and not line.strip().startswith('#')
        ]
        return valid_lines

    except Exception as e:
        # Ghi log thay vì print để nhất quán
        logger = logging.getLogger(__name__) # Lấy logger tạm
        logger.warning(f"Không thể đọc file .gitignore: {e}") #
        return patterns

def git_add_and_commit(
    logger: logging.Logger,
    scan_root: Path,
    file_paths_relative: List[str],
    commit_message: str
) -> bool:
    """
    Thực hiện 'git add' và 'git commit' cho các file được chỉ định.

    Args:
        logger: Logger để ghi log.
        scan_root: Thư mục gốc (cwd) để chạy lệnh Git (phải là gốc repo).
        file_paths_relative: Danh sách các đường dẫn file (tương đối so với `scan_root`).
        commit_message: Message cho commit.

    Returns:
        True nếu thành công (add và commit, hoặc không có gì để commit),
        False nếu thất bại (không phải repo, lỗi add, lỗi commit).
    """

    if not file_paths_relative:
        logger.debug("Không có file nào được chỉ định, bỏ qua commit.")
        return True

    if not is_git_repository(scan_root):
        logger.warning(f"⚠️ Bỏ qua commit: {scan_root} không phải là thư mục gốc của kho Git.")
        return False

    try:
        logger.info(f"Đang thực hiện 'git add' cho {len(file_paths_relative)} file...")

        # 1. Git Add
        add_command: List[str] = ["git", "add"] + file_paths_relative
        add_success, add_out = run_command(
            add_command, logger, "Staging các file", cwd=scan_root #
        )
        if not add_success:
            logger.error("❌ Lỗi khi chạy 'git add'.") #
            return False

        # 2. Git Commit
        logger.info(f"Đang thực hiện 'git commit' với message: \"{commit_message}\"") #
        commit_command: List[str] = ["git", "commit", "-m", commit_message]
        commit_success, commit_out = run_command(
            commit_command, logger, "Commit các file", cwd=scan_root #
        )

        if commit_success:
            log_success(logger, f"Đã commit thành công: {commit_message}") #
            return True
        elif "nothing to commit" in commit_out or "no changes added to commit" in commit_out:
            # Trường hợp file đã được add nhưng không có thay đổi thực sự
            logger.info("Không có thay đổi nào để commit.") #
            return True # Vẫn coi là thành công
        else:
            logger.error("❌ Lỗi khi chạy 'git commit'.") #
            return False

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn khi thực thi Git: {e}") #
        return False