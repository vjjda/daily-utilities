# Path: scripts/stubgen.py

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Set, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    from utils.cli import handle_project_root_validation, handle_config_init_request
    
    # --- MODULE IMPORTS (SGen) ---
    from modules.stubgen import (
        DEFAULT_IGNORE, 
        DEFAULT_RESTRICT, 
        DYNAMIC_IMPORT_INDICATORS,
        AST_MODULE_LIST_NAME,
        AST_ALL_LIST_NAME,
        PROJECT_CONFIG_FILENAME,
        CONFIG_FILENAME,
        CONFIG_SECTION_NAME,
        
        load_config_files,
        process_stubgen_logic,
        execute_stubgen_action
    )
    # --- END MODULE IMPORTS ---
except ImportError as e:
    print(f"Lỗi: Không thể import project utilities/modules. Đảm bảo PROJECT_ROOT là đúng: {PROJECT_ROOT}. Lỗi: {e}", file=sys.stderr)
    sys.exit(1)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()
MODULE_DIR = PROJECT_ROOT / "modules" / "stubgen"
TEMPLATE_FILENAME = "stubgen.toml.template" 
SGEN_DEFAULTS: Dict[str, Any] = {
    "ignore": DEFAULT_IGNORE,
    "restrict": DEFAULT_RESTRICT,
    "dynamic_import_indicators": DYNAMIC_IMPORT_INDICATORS,
    "ast_module_list_name": AST_MODULE_LIST_NAME,
    "ast_all_list_name": AST_ALL_LIST_NAME
}


def main():
    """
    Hàm điều phối chính. Phân tích args, setup logging, và gọi logic cốt lõi.
    """

    # 1. Định nghĩa Parser
    parser = argparse.ArgumentParser(
        description="Tự động tạo file .pyi stub cho các module gateway động.",
        epilog="Ví dụ: sgen . -f -R modules/auth,utils/core",
        formatter_class=argparse.RawTextHelpFormatter 
    )

    # --- MODIFIED: Tách thành 2 Argument Groups ---

    # Group 2: Stub Generation Options
    stubgen_group = parser.add_argument_group("Stub Generation Options")
    stubgen_group.add_argument(
        "target_dir",
        nargs='?',
        default=".",
        help="Đường dẫn thư mục để bắt đầu quét (base directory). Mặc định là thư mục hiện tại (.)."
    )
    
    stubgen_group.add_argument(
        "-f", "--force",
        action="store_true",
        help="Ghi đè file .pyi nếu đã tồn tại (không hỏi xác nhận)."
    )
    stubgen_group.add_argument(
        "-I", "--ignore",
        type=str,
        default=None,
        help="Danh sách pattern (fnmatch) ngăn cách bởi dấu phẩy để bỏ qua (THÊM vào config)."
    )
    stubgen_group.add_argument(
        "-R", "--restrict",
        type=str,
        default=None,
        help="Danh sách thư mục con (so với target_dir) ngăn cách bởi dấu phẩy để giới hạn quét (GHI ĐÈ config)."
    )

        # Group 1: Config Flags
    config_group = parser.add_argument_group("Config Initialization (Chạy riêng lẻ)")
    config_group.add_argument(
        "-c", "--config-project",
        action="store_true",
        help=f"Khởi tạo/cập nhật section [{CONFIG_SECTION_NAME}] trong {PROJECT_CONFIG_FILENAME}."
    )
    config_group.add_argument(
        "-C", "--config-local",
        action="store_true",
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} (scope 'local')."
    )
    # --- END MODIFIED ---
    
    args = parser.parse_args()
    
    # 2. Setup Logging
    logger = setup_logging(script_name="SGen")
    logger.debug("SGen script started.")

    # 3. Xử lý Config Init
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
            base_defaults=SGEN_DEFAULTS
        )
        if config_action_taken:
            sys.exit(0) 
            
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
    
    # 4. Xử lý Path và Validation
    scan_root = Path(args.target_dir).expanduser().resolve()

    if not scan_root.exists() or not scan_root.is_dir():
        logger.error(f"❌ Lỗi: Thư mục mục tiêu không tồn tại hoặc không phải là thư mục: {scan_root.as_posix()}")
        sys.exit(1)

    effective_scan_root: Optional[Path]
    effective_scan_root, _ = handle_project_root_validation(
        logger=logger,
        scan_root=scan_root,
        force_silent=args.force 
    )
    
    if effective_scan_root is None:
        sys.exit(0)

    # 5. Load Configs và Chạy Core Logic
    file_config = load_config_files(effective_scan_root, logger)
    
    cli_config: Dict[str, Optional[str]] = {
        "ignore": args.ignore,
        "restrict": args.restrict
    }
    
    try:
        results = process_stubgen_logic(
            logger=logger,
            scan_root=effective_scan_root,
            cli_config=cli_config,
            file_config=file_config,
            script_file_path=THIS_SCRIPT_PATH
        )
        
        if results:
            execute_stubgen_action(
                logger=logger,
                results=results,
                force=args.force,
                scan_root=effective_scan_root
            )
        else:
            log_success(logger, "Không tìm thấy dynamic module gateways nào để xử lý.")
       
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