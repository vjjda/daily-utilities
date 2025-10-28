#!/usr/bin/env python3
# Path: scripts/bootstrap_tool.py

"""
Script nội bộ để bootstrap (khởi tạo) một tool utility mới.
Sử dụng cấu trúc module `bootstrap` đã được refactor theo SRP.
"""

import sys
import argparse
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Final

# Thiết lập sys.path để import các module của dự án
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success

    # Import các thành phần SRP từ module 'bootstrap'
    from modules.bootstrap import (
        # Hằng số cấu hình
        DEFAULT_BIN_DIR_NAME,
        DEFAULT_SCRIPTS_DIR_NAME,
        DEFAULT_MODULES_DIR_NAME,
        DEFAULT_DOCS_DIR_NAME,
        # Các hàm chức năng
        load_bootstrap_config, # Loader
        load_spec_file,        # Loader
        process_bootstrap_logic, # Core
        execute_bootstrap_action # Executor
    )
except ImportError as e:
    print(f"Lỗi: Không thể import utils hoặc gateway bootstrap: {e}", file=sys.stderr) #
    sys.exit(1)

def main():
    """Hàm chính chạy script bootstrap."""

    logger = setup_logging(script_name="Bootstrap", console_level_str="INFO")
    logger.debug("Script bootstrap bắt đầu.") #

    # --- Phân tích đối số dòng lệnh ---
    parser = argparse.ArgumentParser(description="Bootstrap (khởi tạo) một tool utility mới từ file *.spec.toml.") #
    parser.add_argument(
        "spec_file_path_str",
        type=str,
        help="Đường dẫn đầy đủ đến file *.spec.toml (ví dụ: docs/drafts/new_tool.spec.toml)." #
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Ghi đè (overwrite) các file và thư mục đã tồn tại nếu có." #
    )
    args = parser.parse_args()

    try:
        # --- 1. LOAD (Đọc Config và Spec) ---

        # 1.1. Tải cấu hình đường dẫn dự án từ .project.toml
        toml_config = load_bootstrap_config(logger, PROJECT_ROOT)

        bin_dir_name = toml_config.get("bin_dir", DEFAULT_BIN_DIR_NAME)
        scripts_dir_name = toml_config.get("scripts_dir", DEFAULT_SCRIPTS_DIR_NAME)
        modules_dir_name = toml_config.get("modules_dir", DEFAULT_MODULES_DIR_NAME)
        docs_dir_name = toml_config.get("docs_dir", DEFAULT_DOCS_DIR_NAME)

        # Xây dựng các đường dẫn tuyệt đối
        configured_paths = {
            "BIN_DIR": PROJECT_ROOT / bin_dir_name,
            "SCRIPTS_DIR": PROJECT_ROOT / scripts_dir_name,
            "MODULES_DIR": PROJECT_ROOT / modules_dir_name,
            "DOCS_DIR": PROJECT_ROOT / docs_dir_name
        }
        logger.debug(f"Đã tải các đường dẫn cấu hình: {configured_paths}") #

        # 1.2. Tải file spec từ đối số CLI
        spec_file_path = Path(args.spec_file_path_str).resolve()
        if not spec_file_path.is_file() or not spec_file_path.name.endswith(".spec.toml"):
            logger.error(f"❌ Lỗi: Đường dẫn cung cấp không phải là file *.spec.toml hợp lệ.") #
            logger.error(f"   Đã nhận: {spec_file_path.as_posix()}") #
            sys.exit(1)

        logger.info(f"🚀 Bắt đầu bootstrap:") #
        try:
            # Hiển thị đường dẫn tương đối nếu có thể
            spec_rel_path = spec_file_path.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            spec_rel_path = spec_file_path.as_posix()
        logger.info(f"   File Spec: {spec_rel_path}") #

        config_spec = load_spec_file(logger, spec_file_path)

        # --- 2. CORE (Xử lý logic, tạo nội dung) ---
        (
            generated_content, # Dict[str, str]
            target_paths,      # Dict[str, Path]
            module_path        # Path
        ) = process_bootstrap_logic(
            logger=logger,
            config=config_spec,
            configured_paths=configured_paths
        )

        logger.info(f"   Thư mục Module: {module_path.relative_to(PROJECT_ROOT).as_posix()}") #

        # --- 3. EXECUTOR (Ghi file, kiểm tra an toàn) ---
        execute_bootstrap_action(
            logger=logger,
            generated_content=generated_content,
            target_paths=target_paths,
            module_path=module_path,
            project_root=PROJECT_ROOT,
            force=args.force # Truyền cờ force
        )

        log_success(logger, "\n✨ Bootstrap hoàn tất! Cấu trúc file cho tool mới đã sẵn sàng.") #

    except SystemExit: # Bắt lỗi SystemExit từ các module con
        # Lỗi đã được log, chỉ cần thoát
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn trong quá trình bootstrap: {e}") #
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()