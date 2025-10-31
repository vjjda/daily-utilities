# Path: modules/bootstrap/bootstrap_executor.py
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

from utils.logging_config import log_success

__all__ = ["execute_bootstrap_action"]


def execute_bootstrap_action(
    logger: logging.Logger,
    generated_content: Dict[str, str],
    target_paths: Dict[str, Path],
    module_path: Path,
    project_root: Path,
    force: bool,
) -> None:

    module_existed_before = module_path.exists()
    if module_existed_before and not force:
        logger.error(f"❌ Dừng lại! Thư mục module sau đã tồn tại:")
        logger.error(f"   -> {module_path.relative_to(project_root).as_posix()}")
        logger.error("   (Sử dụng -f hoặc --force để ghi đè)")
        sys.exit(1)
    elif module_existed_before and force:
        logger.warning(f"⚠️ Thư mục module đã tồn tại. Sẽ ghi đè (do --force)...")

    existing_files = [p for p in target_paths.values() if p.exists()]
    if existing_files and not force:
        logger.error(f"❌ Dừng lại! Các file sau đã tồn tại:")
        for p in existing_files:
            logger.error(f"   -> {p.relative_to(project_root).as_posix()}")
        logger.error("   (Sử dụng -f hoặc --force để ghi đè)")
        sys.exit(1)
    elif existing_files and force:
        logger.warning(
            f"⚠️ Phát hiện {len(existing_files)} file đã tồn tại. Sẽ ghi đè (do --force)..."
        )

    try:

        module_path.mkdir(parents=True, exist_ok=True)
        if not module_existed_before:
            logger.info(
                f"Đã tạo thư mục: {module_path.relative_to(project_root).as_posix()}"
            )

        for key, path in target_paths.items():
            content = generated_content[key]

            path.parent.mkdir(parents=True, exist_ok=True)

            is_existing_before_write = path.exists()

            path.write_text(content, encoding="utf-8")

            relative_path = path.relative_to(project_root).as_posix()

            if is_existing_before_write and force:
                log_success(logger, f"Đã ghi đè: {relative_path}")
            elif not is_existing_before_write:
                log_success(logger, f"Đã tạo: {relative_path}")

            if key == "bin":
                os.chmod(path, 0o755)
                logger.info(f"   -> Đã cấp quyền thực thi (chmod +x)")

    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi ghi file: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Lỗi không xác định khi ghi file: {e}")
        logger.debug("Traceback:", exc_info=True)
        raise
