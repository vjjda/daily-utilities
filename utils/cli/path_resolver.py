# Path: utils/cli/path_resolver.py
import logging
from pathlib import Path
from typing import List, Set, Optional

__all__ = ["resolve_input_paths"]


def resolve_input_paths(
    logger: logging.Logger, raw_paths: List[str], default_path_str: str
) -> List[Path]:
    validated_paths: List[Path] = []

    paths_to_process = raw_paths if raw_paths else [default_path_str]

    for path_str in paths_to_process:
        try:
            start_path = Path(path_str).expanduser().resolve()
        except Exception as e:
            logger.error(f"❌ Lỗi khi xử lý đường dẫn '{path_str}': {e}")
            continue

        if not start_path.exists():
            logger.error(f"❌ Lỗi: Đường dẫn không tồn tại: {start_path}")
            continue

        validated_paths.append(start_path)

    return validated_paths