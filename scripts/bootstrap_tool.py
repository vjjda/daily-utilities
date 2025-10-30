# Path: scripts/bootstrap_tool.py

import sys
import argparse
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Final


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success

    from modules.bootstrap import (
        DEFAULT_BIN_DIR_NAME,
        DEFAULT_SCRIPTS_DIR_NAME,
        DEFAULT_MODULES_DIR_NAME,
        DEFAULT_DOCS_DIR_NAME,
        load_bootstrap_config,
        load_spec_file,
        process_bootstrap_logic,
        execute_bootstrap_action,
    )
except ImportError as e:
    print(f"Lỗi: Không thể import utils hoặc gateway bootstrap: {e}", file=sys.stderr)
    sys.exit(1)


def main():

    logger = setup_logging(script_name="Bootstrap", console_level_str="INFO")
    logger.debug("Script bootstrap bắt đầu.")

    parser = argparse.ArgumentParser(
        description="Bootstrap (khởi tạo) một tool utility mới từ file *.spec.toml."
    )
    parser.add_argument(
        "spec_file_path_str",
        type=str,
        help="Đường dẫn đầy đủ đến file *.spec.toml (ví dụ: docs/drafts/new_tool.spec.toml).",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Ghi đè (overwrite) các file và thư mục đã tồn tại nếu có.",
    )

    parser.add_argument(
        "-i",
        "--interface",
        type=str,
        choices=["typer", "argparse"],
        default=None,
        help="Ghi đè (overwrite) loại interface (typer/argparse) được định nghĩa trong file spec.",
    )

    args = parser.parse_args()

    try:

        toml_config = load_bootstrap_config(logger, PROJECT_ROOT)

        bin_dir_name = toml_config.get("bin_dir", DEFAULT_BIN_DIR_NAME)
        scripts_dir_name = toml_config.get("scripts_dir", DEFAULT_SCRIPTS_DIR_NAME)
        modules_dir_name = toml_config.get("modules_dir", DEFAULT_MODULES_DIR_NAME)
        docs_dir_name = toml_config.get("docs_dir", DEFAULT_DOCS_DIR_NAME)

        configured_paths = {
            "BIN_DIR": PROJECT_ROOT / bin_dir_name,
            "SCRIPTS_DIR": PROJECT_ROOT / scripts_dir_name,
            "MODULES_DIR": PROJECT_ROOT / modules_dir_name,
            "DOCS_DIR": PROJECT_ROOT / docs_dir_name,
        }
        logger.debug(f"Đã tải các đường dẫn cấu hình: {configured_paths}")

        spec_file_path = Path(args.spec_file_path_str).resolve()
        if not spec_file_path.is_file() or not spec_file_path.name.endswith(
            ".spec.toml"
        ):
            logger.error(
                f"❌ Lỗi: Đường dẫn cung cấp không phải là file *.spec.toml hợp lệ."
            )
            logger.error(f"   Đã nhận: {spec_file_path.as_posix()}")
            sys.exit(1)

        logger.info(f"🚀 Bắt đầu bootstrap:")
        try:

            spec_rel_path = spec_file_path.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            spec_rel_path = spec_file_path.as_posix()
        logger.info(f"   File Spec: {spec_rel_path}")

        config_spec = load_spec_file(logger, spec_file_path)

        (generated_content, target_paths, module_path) = process_bootstrap_logic(
            logger=logger,
            config=config_spec,
            configured_paths=configured_paths,
            cli_args=args,
        )

        logger.info(
            f"   Thư mục Module: {module_path.relative_to(PROJECT_ROOT).as_posix()}"
        )

        execute_bootstrap_action(
            logger=logger,
            generated_content=generated_content,
            target_paths=target_paths,
            module_path=module_path,
            project_root=PROJECT_ROOT,
            force=args.force,
        )

        log_success(
            logger, "\n✨ Bootstrap hoàn tất! Cấu trúc file cho tool mới đã sẵn sàng."
        )

    except SystemExit:

        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn trong quá trình bootstrap: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()