# Path: utils/cli/stepwise_resolver.py
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from utils.core.git import find_commit_by_hash, get_diffed_files
from utils.core.config_helpers import generate_config_hash
from utils.core.file_extensions import is_extension_matched
from .path_resolver import resolve_input_paths

__all__ = ["resolve_stepwise_paths"]


def resolve_stepwise_paths(
    logger: logging.Logger,
    stepwise_flag: bool,
    reporting_root: Path,
    settings_to_hash: Dict[str, Any],
    relevant_extensions: Set[str],
    raw_paths: List[str],
    default_path_str: str,
) -> List[Path]:

    last_run_sha: Optional[str] = None
    if stepwise_flag:
        config_hash = generate_config_hash(settings_to_hash, logger)
        logger.info(f"Chế độ Stepwise (-w): Tìm kiếm cài đặt hash: {config_hash}")
        last_run_sha = find_commit_by_hash(logger, reporting_root, config_hash)

    if stepwise_flag and last_run_sha:
        logger.info(f"Tìm thấy commit khớp: {last_run_sha[:7]}. Lấy diff file...")
        diffed_files = get_diffed_files(logger, reporting_root, last_run_sha)

        validated_paths = [
            f
            for f in diffed_files
            if f.is_file() and is_extension_matched(f, relevant_extensions)
        ]

        if not validated_paths:
            logger.info(
                "✅ Không có file nào (khớp extension) thay đổi kể từ lần chạy cuối."
            )
            return []

        logger.info(f"Sẽ chỉ quét {len(validated_paths)} file đã thay đổi.")
        return validated_paths
    else:
        if stepwise_flag:
            logger.warning(
                "Không tìm thấy commit nào khớp. Sẽ thực hiện quét toàn bộ..."
            )

        return resolve_input_paths(
            logger=logger,
            raw_paths=raw_paths,
            default_path_str=default_path_str,
        )
