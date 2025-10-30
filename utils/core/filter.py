# Path: utils/core/filter.py
from pathlib import Path
from typing import List, TYPE_CHECKING, Optional, Iterable
import logging


try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

__all__ = ["is_path_matched", "compile_spec_from_patterns"]


logger = logging.getLogger(__name__)


def compile_spec_from_patterns(
    patterns_iterable: Iterable[str], scan_root: Path
) -> Optional["pathspec.PathSpec"]:
    if pathspec is None:
        logger.warning(
            "Thư viện 'pathspec' không được cài đặt. Việc lọc file sẽ bị hạn chế."
        )
        return None

    patterns = list(patterns_iterable)
    if not patterns:
        return None

    processed_patterns: List[str] = []
    for pattern in patterns:

        if not pattern:
            continue

        if "/" not in pattern and (scan_root / pattern).is_dir():

            processed_patterns.append(f"{pattern}/")
        else:
            processed_patterns.append(pattern)

    if not processed_patterns:
        return None

    try:

        spec = pathspec.PathSpec.from_lines("gitwildmatch", processed_patterns)
        return spec
    except Exception as e:
        logger.error(f"Lỗi khi biên dịch các pattern pathspec: {e}")
        logger.debug(f"Patterns gây lỗi: {processed_patterns}")
        return None


def is_path_matched(
    path: Path, spec: Optional["pathspec.PathSpec"], start_dir: Path
) -> bool:
    if spec is None:
        return False

    try:

        relative_path: Path
        try:
            relative_path = path.resolve().relative_to(start_dir.resolve())
        except ValueError:

            relative_path_str = path.resolve().as_posix()
        else:
            relative_path_str = relative_path.as_posix()

        if path.is_dir() and not relative_path_str.endswith("/"):

            if relative_path_str != ".":
                relative_path_str += "/"

        if relative_path_str == "." or relative_path_str == "./":
            return False

        return spec.match_file(relative_path_str)
    except Exception as e:
        logger.debug(f"Lỗi khi khớp đường dẫn '{path}' với spec: {e}")
        return False