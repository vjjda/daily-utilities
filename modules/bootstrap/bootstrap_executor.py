# Path: modules/bootstrap/bootstrap_executor.py
"""
Logic thực thi/hành động cho module Bootstrap.
(Side-effects: Ghi file, chmod, kiểm tra an toàn)
"""

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
    force: bool
) -> None:
    """
    Thực hiện kiểm tra an toàn và ghi tất cả các file đã tạo ra đĩa.

    Args:
        logger: Logger.
        generated_content: Dict chứa nội dung các file.
        target_paths: Dict chứa đường dẫn đích tuyệt đối cho các file.
        module_path: Đường dẫn đến thư mục module mới.
        project_root: Đường dẫn gốc của dự án (để tính đường dẫn tương đối).
        force: True nếu cờ --force được sử dụng (ghi đè file).

    Raises:
        SystemExit: Nếu kiểm tra an toàn thất bại (file/thư mục tồn tại và force=False).
        IOError, Exception: Nếu có lỗi khi ghi file hoặc chmod.
    """

    # 1. KIỂM TRA AN TOÀN (tránh ghi đè nếu không có --force)
    # Kiểm tra thư mục module
    module_existed_before = module_path.exists()
    if module_existed_before and not force:
        logger.error(f"❌ Dừng lại! Thư mục module sau đã tồn tại:") #
        logger.error(f"   -> {module_path.relative_to(project_root).as_posix()}") #
        logger.error("   (Sử dụng -f hoặc --force để ghi đè)") #
        sys.exit(1)
    elif module_existed_before and force:
        logger.warning(f"⚠️ Thư mục module đã tồn tại. Sẽ ghi đè (do --force)...") #

    # Kiểm tra các file đích
    existing_files = [p for p in target_paths.values() if p.exists()]
    if existing_files and not force:
        logger.error(f"❌ Dừng lại! Các file sau đã tồn tại:") #
        for p in existing_files:
            logger.error(f"   -> {p.relative_to(project_root).as_posix()}") #
        logger.error("   (Sử dụng -f hoặc --force để ghi đè)") #
        sys.exit(1)
    elif existing_files and force:
        logger.warning(f"⚠️ Phát hiện {len(existing_files)} file đã tồn tại. Sẽ ghi đè (do --force)...") #

    # 2. GHI FILE (I/O)
    try:
        # Tạo thư mục module (và các thư mục cha nếu cần)
        module_path.mkdir(parents=True, exist_ok=True)
        if not module_existed_before:
             logger.info(f"Đã tạo thư mục: {module_path.relative_to(project_root).as_posix()}") #

        # Ghi từng file
        for key, path in target_paths.items():
            content = generated_content[key]
            # Đảm bảo thư mục cha của file (ví dụ: bin/, scripts/) tồn tại
            path.parent.mkdir(parents=True, exist_ok=True)

            is_existing_before_write = path.exists() # Kiểm tra trước khi ghi

            # Ghi nội dung file
            path.write_text(content, encoding='utf-8')

            relative_path = path.relative_to(project_root).as_posix()

            # Log thông báo phù hợp
            if is_existing_before_write and force:
                log_success(logger, f"Đã ghi đè: {relative_path}") #
            elif not is_existing_before_write:
                log_success(logger, f"Đã tạo: {relative_path}") #
            # (Trường hợp file tồn tại nhưng không có --force đã bị chặn ở trên)

            # Cấp quyền thực thi cho wrapper trong bin/
            if key == "bin":
                os.chmod(path, 0o755)
                logger.info(f"   -> Đã cấp quyền thực thi (chmod +x)") #

    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi ghi file: {e}") #
        raise # Ném lại lỗi
    except Exception as e:
        logger.error(f"❌ Lỗi không xác định khi ghi file: {e}") #
        logger.debug("Traceback:", exc_info=True)
        raise # Ném lại lỗi