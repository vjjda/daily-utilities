# Path: utils/core/git.py
import logging
import configparser
from pathlib import Path
from typing import Set, Optional, List, TYPE_CHECKING, Tuple, Iterable

from .process import run_command
from ..logging_config import log_success


__all__ = [
    "is_git_repository",
    "find_git_root",
    "get_submodule_paths",
    "parse_gitignore",
    "git_add_and_commit",
    "find_file_upwards",
]


def find_file_upwards(
    filename: str, start_path: Path, logger: logging.Logger, max_levels: int = 10
) -> Optional[Path]:
    current_path = start_path.resolve()
    for _ in range(max_levels):
        file_to_find = current_path / filename
        if file_to_find.is_file():
            logger.debug(f"Đã tìm thấy '{filename}' tại: {current_path.as_posix()}")
            return file_to_find

        if current_path == current_path.parent:
            break
        current_path = current_path.parent

    logger.debug(
        f"Không tìm thấy '{filename}' trong {max_levels} cấp thư mục cha từ {start_path.as_posix()}."
    )
    return None


def is_git_repository(root: Path) -> bool:
    return (root / ".git").is_dir()


def find_git_root(start_path: Path, max_levels: int = 5) -> Optional[Path]:
    current_path = start_path.resolve()
    for _ in range(max_levels):
        if is_git_repository(current_path):
            return current_path

        if current_path == current_path.parent:
            break
        current_path = current_path.parent

    return None


def get_submodule_paths(
    root: Path, logger: Optional[logging.Logger] = None
) -> Set[Path]:
    submodule_paths = set()
    gitmodules_path = root / ".gitmodules"
    if gitmodules_path.exists():
        try:
            config = configparser.ConfigParser()

            config.read(gitmodules_path, encoding="utf-8")
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
    patterns: List[str] = []
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return patterns

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        lines.append(".git/")

        valid_lines = [
            line.strip()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]
        return valid_lines

    except Exception as e:

        logger = logging.getLogger(__name__)
        logger.warning(f"Không thể đọc file .gitignore: {e}")
        return patterns


def git_add_and_commit(
    logger: logging.Logger,
    scan_root: Path,
    file_paths_relative: List[str],
    commit_message: str,
) -> bool:

    if not file_paths_relative:
        logger.debug("Không có file nào được chỉ định, bỏ qua commit.")
        return True

    if not is_git_repository(scan_root):
        logger.warning(
            f"⚠️ Bỏ qua commit: {scan_root} không phải là thư mục gốc của kho Git."
        )
        return False

    try:
        logger.info(f"Đang thực hiện 'git add' cho {len(file_paths_relative)} file...")

        add_command: List[str] = ["git", "add"] + file_paths_relative
        add_success, add_out = run_command(
            add_command, logger, "Staging các file", cwd=scan_root
        )
        if not add_success:
            logger.error("❌ Lỗi khi chạy 'git add'.")
            return False

        logger.info(f"Đang thực hiện 'git commit' với message: \"{commit_message}\"")
        commit_command: List[str] = ["git", "commit", "-m", commit_message]
        commit_success, commit_out = run_command(
            commit_command, logger, "Commit các file", cwd=scan_root
        )

        if commit_success:
            log_success(logger, f"Đã commit thành công: {commit_message}")
            return True
        elif (
            "nothing to commit" in commit_out
            or "no changes added to commit" in commit_out
        ):

            logger.info("Không có thay đổi nào để commit.")
            return True
        else:
            logger.error("❌ Lỗi khi chạy 'git commit'.")
            return False

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn khi thực thi Git: {e}")
        return False