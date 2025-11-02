# Path: utils/core/git.py
import logging
import configparser
from pathlib import Path
from typing import Set, Optional, List, TYPE_CHECKING, Tuple, Iterable, Dict, Any

from .process import run_command
from ..logging_config import log_success

from .config_helpers import generate_config_hash


__all__ = [
    "is_git_repository",
    "find_git_root",
    "get_submodule_paths",
    "parse_gitignore",
    "git_add_and_commit",
    "find_file_upwards",
    "auto_commit_changes",
    "find_commit_by_hash",
    "get_diffed_files",
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


def find_commit_by_hash(
    logger: logging.Logger, scan_root: Path, settings_hash: str
) -> Optional[str]:
    if not is_git_repository(scan_root):
        logger.debug("Không phải kho Git, bỏ qua tìm kiếm hash commit.")
        return None

    grep_str = f"[Settings:{settings_hash}]"

    command = [
        "git",
        "log",
        "--fixed-strings",
        "--grep",
        grep_str,
        "-n",
        "1",
        "--pretty=format:%H",
    ]

    success, output = run_command(
        command,
        logger,
        description=f"Tìm commit với hash {settings_hash}",
        cwd=scan_root,
    )

    if success and output.strip():
        commit_sha = output.strip()
        logger.debug(f"Tìm thấy commit: {commit_sha} khớp với hash: {settings_hash}")
        return commit_sha

    logger.debug(f"Không tìm thấy commit nào khớp với hash: {settings_hash}")
    return None


def get_diffed_files(
    logger: logging.Logger, scan_root: Path, start_sha: str
) -> List[Path]:
    if not is_git_repository(scan_root):
        logger.warning("Không phải kho Git, không thể lấy diff.")
        return []

    command = ["git", "diff", "--name-only", start_sha]

    success, output = run_command(
        command,
        logger,
        description=f"Lấy diff từ {start_sha[:7]}...WORKING_TREE",
        cwd=scan_root,
    )

    if success and output.strip():
        relative_paths = [p.strip() for p in output.splitlines() if p.strip()]

        absolute_paths = [scan_root / p for p in relative_paths]
        logger.debug(f"Tìm thấy {len(absolute_paths)} file đã thay đổi.")
        return absolute_paths

    logger.debug("Không tìm thấy file nào thay đổi hoặc lệnh diff thất bại.")
    return []


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

    return False


def auto_commit_changes(
    logger: logging.Logger,
    scan_root: Path,
    files_written_relative: List[str],
    settings_to_hash: Dict[str, Any],
    commit_scope: str,
    tool_name: str,
) -> None:
    if not files_written_relative or not is_git_repository(scan_root):
        if files_written_relative:
            logger.info(
                "Bỏ qua auto-commit: Thư mục làm việc hiện tại không phải là gốc Git."
            )
        return

    try:

        config_hash = generate_config_hash(settings_to_hash, logger)

        file_count = len(files_written_relative)
        commit_msg = f"style({commit_scope}): Cập nhật {file_count} file ({tool_name}) [Settings:{config_hash}]"

        git_add_and_commit(
            logger=logger,
            scan_root=scan_root,
            file_paths_relative=files_written_relative,
            commit_message=commit_msg,
        )
    except Exception as e:
        logger.error(f"❌ Lỗi khi tạo hash hoặc thực thi git commit: {e}")
        logger.debug("Traceback:", exc_info=True)
