# Path: scripts/stubgen.py
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Set, Dict, Any, Final


try:
    import argcomplete
except ImportError:
    argcomplete = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success

    # SỬA LỖI: Import thêm resolve_reporting_root
    from utils.cli import (
        handle_config_init_request,
        resolve_input_paths,
        resolve_reporting_root, # <-- Thêm
    )

    from modules.stubgen import (
        DEFAULT_IGNORE,
        DEFAULT_INCLUDE,
        DYNAMIC_IMPORT_INDICATORS,
        AST_MODULE_LIST_NAME,
        AST_ALL_LIST_NAME,
        PROJECT_CONFIG_FILENAME,
        CONFIG_FILENAME,
        CONFIG_SECTION_NAME,
        process_stubgen_logic,
        execute_stubgen_action,
    )
except ImportError as e:
    # ... (Giữ nguyên) ...
    pass


THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()
MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "stubgen"
TEMPLATE_FILENAME: Final[str] = "stubgen.toml.template"
SGEN_DEFAULTS: Final[Dict[str, Any]] = {
    "ignore": DEFAULT_IGNORE,
    "include": DEFAULT_INCLUDE or set(),
    "dynamic_import_indicators": DYNAMIC_IMPORT_INDICATORS,
    "ast_module_list_name": AST_MODULE_LIST_NAME,
    "ast_all_list_name": AST_ALL_LIST_NAME,
}


def main():

    parser = argparse.ArgumentParser(
        description="Tự động tạo file .pyi stub cho các module gateway động.",
        epilog="Ví dụ: sgen . -i 'modules/core/**' -f",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    stubgen_group = parser.add_argument_group("Stub Generation Options")
    stubgen_group.add_argument(
        "target_paths",
        type=str,
        nargs="*",
        default=[],
        help="Đường dẫn (file hoặc thư mục) để quét. Mặc định là thư mục hiện tại (.).",
    )
    stubgen_group.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Ghi đè file .pyi nếu đã tồn tại (không hỏi xác nhận).",
    )
    stubgen_group.add_argument(
        "-I",
        "--ignore",
        type=str,
        default=None,
        help="Danh sách pattern (giống .gitignore) để bỏ qua (THÊM vào config).",
    )

    stubgen_group.add_argument(
        "-i",
        "--include",
        type=str,
        default=None,
        help="Bộ lọc dương (inclusion filter). Chỉ giữ lại các file khớp (THÊM vào config).",
    )

    config_group = parser.add_argument_group("Config Initialization (Chạy riêng lẻ)")
    config_group.add_argument(
        "-c",
        "--config-project",
        action="store_true",
        help=f"Khởi tạo/cập nhật section [{CONFIG_SECTION_NAME}] trong {PROJECT_CONFIG_FILENAME}.",
    )
    config_group.add_argument(
        "-C",
        "--config-local",
        action="store_true",
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} (scope 'local').",
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    logger = setup_logging(script_name="SGen")
    logger.debug("SGen script started.")

    try:
        config_action_taken = handle_config_init_request(
            logger=logger,
            config_project=args.config_project,
            config_local=args.config_local,
            module_dir=MODULE_DIR,
            template_filename=TEMPLATE_FILENAME,
            config_filename=CONFIG_FILENAME,
            project_config_filename=PROJECT_CONFIG_FILENAME,
            config_section_name=CONFIG_SECTION_NAME,
            base_defaults=SGEN_DEFAULTS,
        )
        if config_action_taken:
            sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    validated_paths: List[Path] = resolve_input_paths(
        logger=logger, raw_paths=args.target_paths, default_path_str="."
    )

    if not validated_paths:
        logger.warning("Không tìm thấy đường dẫn hợp lệ nào để quét. Đã dừng.")
        sys.exit(0)

    # SỬA LỖI: Xác định reporting_root chính xác
    # (Không có --root arg cho sgen, nên ta truyền None)
    reporting_root = resolve_reporting_root(
        logger, validated_paths, cli_root_arg=None
    ) 

    files_to_process: List[Path] = []
    dirs_to_scan: List[Path] = []
    for path in validated_paths:
        if path.is_file():
            files_to_process.append(path)
        elif path.is_dir():
            dirs_to_scan.append(path)

    try:

        files_to_create, files_to_overwrite = process_stubgen_logic(
            logger=logger,
            cli_args=args,
            script_file_path=THIS_SCRIPT_PATH,
            files_to_process=files_to_process,
            dirs_to_scan=dirs_to_scan,
        )

        # Truyền reporting_root (là gốc Git) vào scan_root
        execute_stubgen_action(
            logger=logger,
            files_to_create=files_to_create,
            files_to_overwrite=files_to_overwrite,
            force=args.force,
            scan_root=reporting_root, # <-- Sửa lỗi
            cli_args=args,
        )

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Hoạt động tạo Stub đã bị dừng bởi người dùng.")
        sys.exit(1)
