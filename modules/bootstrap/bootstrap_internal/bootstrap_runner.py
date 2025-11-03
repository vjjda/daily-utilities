# Path: modules/bootstrap/bootstrap_internal/bootstrap_runner.py
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple

from utils.logging_config import log_success


from .builders import process_bootstrap_logic
from .bootstrap_loader import load_spec_file

from ..bootstrap_executor import execute_bootstrap_action
from ..bootstrap_config import (
    DEFAULT_BIN_DIR_NAME,
    DEFAULT_SCRIPTS_DIR_NAME,
    DEFAULT_MODULES_DIR_NAME,
    DEFAULT_DOCS_DIR_NAME,
)

__all__ = ["run_bootstrap_logic"]


def run_bootstrap_logic(
    logger: logging.Logger, cli_args: argparse.Namespace, project_root: Path
) -> None:

    spec_file_path_str = getattr(cli_args, "spec_file_path_str", None)

    if not spec_file_path_str:
        raise ValueError(
            "Lỗi logic: run_bootstrap_logic được gọi mà không có spec_file_path_str."
        )

    spec_file_path = Path(spec_file_path_str).resolve()
    if not spec_file_path.is_file() or not spec_file_path.name.endswith(".spec.toml"):
        logger.error(
            f"❌ Lỗi: Đường dẫn cung cấp không phải là file *.spec.toml hợp lệ."
        )
        logger.error(f"   Đã nhận: {spec_file_path.as_posix()}")
        sys.exit(1)

    logger.info(f"🚀 Bắt đầu bootstrap:")
    try:
        spec_rel_path = spec_file_path.relative_to(project_root).as_posix()
    except ValueError:
        spec_rel_path = spec_file_path.as_posix()
    logger.info(f"   File Spec: {spec_rel_path}")

    config_spec = load_spec_file(logger, spec_file_path)

    layout_config = config_spec.get("layout", {})
    if not layout_config:
        logger.error(
            f"❌ Lỗi: File spec '{spec_file_path.name}' thiếu section [layout] bắt buộc."
        )
        logger.error(
            f"   Gợi ý: Chạy `btool -s {spec_file_path.as_posix()}` để tạo lại file spec với cấu trúc đúng."
        )
        sys.exit(1)

    logger.debug(f"Đã tải cấu hình [layout] từ file spec: {layout_config}")

    bin_dir_name = layout_config.get("bin_dir", DEFAULT_BIN_DIR_NAME)
    scripts_dir_name = layout_config.get("scripts_dir", DEFAULT_SCRIPTS_DIR_NAME)
    modules_dir_name = layout_config.get("modules_dir", DEFAULT_MODULES_DIR_NAME)
    docs_dir_name = layout_config.get("docs_dir", DEFAULT_DOCS_DIR_NAME)

    configured_paths = {
        "BIN_DIR": project_root / bin_dir_name,
        "SCRIPTS_DIR": project_root / scripts_dir_name,
        "MODULES_DIR": project_root / modules_dir_name,
        "DOCS_DIR": project_root / docs_dir_name,
    }
    logger.debug(f"Đã giải quyết các đường dẫn cấu hình: {configured_paths}")

    (generated_content, target_paths, module_path) = process_bootstrap_logic(
        logger=logger,
        config=config_spec,
        configured_paths=configured_paths,
        cli_args=cli_args,
        project_root=project_root,
    )

    logger.info(
        f"   Thư mục Module: {module_path.relative_to(project_root).as_posix()}"
    )

    execute_bootstrap_action(
        logger=logger,
        generated_content=generated_content,
        target_paths=target_paths,
        module_path=module_path,
        project_root=project_root,
        force=cli_args.force,
    )

    log_success(
        logger, "\n✨ Bootstrap hoàn tất! Cấu trúc file cho tool mới đã sẵn sàng."
    )
