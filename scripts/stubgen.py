# Path: scripts/stubgen.py
"""
Entrypoint (cổng vào) cho sgen (Stub Generator).
Script này chịu trách nhiệm:
1. Thiết lập `sys.path` để import `utils` và `modules`.
2. Phân tích đối số dòng lệnh (Argparse).
3. Cấu hình logging.
4. Xử lý các yêu cầu khởi tạo config (`--config-local`, `--config-project`).
5. Xác thực đường dẫn quét (`scan_root`).
6. Gọi `process_stubgen_logic` (từ Core) để lấy danh sách kết quả.
7. Gọi `execute_stubgen_action` (từ Executor) để thực hiện side-effects.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Set, Dict, Any, Final

# Thiết lập `sys.path` để import các module của dự án
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    from utils.cli import handle_project_root_validation, handle_config_init_request
    
    # Import các thành phần của module 'stubgen'
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
        execute_stubgen_action
    )
except ImportError as e:
    print(f"Lỗi: Không thể import project utilities/modules. Đảm bảo PROJECT_ROOT là đúng: {PROJECT_ROOT}. Lỗi: {e}", file=sys.stderr)
    sys.exit(1)

# --- HẰNG SỐ CỤ THỂ CHO ENTRYPOINT ---
THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()
MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "stubgen"
TEMPLATE_FILENAME: Final[str] = "stubgen.toml.template" 

# Cấu hình mặc định để điền vào file template .toml khi khởi tạo
SGEN_DEFAULTS: Final[Dict[str, Any]] = {
    "ignore": DEFAULT_IGNORE,
    "include": DEFAULT_INCLUDE or set(), 
    "dynamic_import_indicators": DYNAMIC_IMPORT_INDICATORS,
    "ast_module_list_name": AST_MODULE_LIST_NAME,
    "ast_all_list_name": AST_ALL_LIST_NAME
}


def main():
    """
    Hàm điều phối chính.
    Phân tích args, setup logging, và gọi logic cốt lõi.
    """

    # 1. Định nghĩa Parser
    parser = argparse.ArgumentParser(
        description="Tự động tạo file .pyi stub cho các module gateway động.",
        epilog="Ví dụ: sgen . -i 'modules/core/**' -f",
        formatter_class=argparse.RawTextHelpFormatter 
    )

    # Group 1: Stub Generation Options
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
        help="Danh sách pattern (giống .gitignore) để bỏ qua (THÊM vào config)."
    )
    
    stubgen_group.add_argument(
        "-i", "--include",
        type=str,
        default=None,
        help="Bộ lọc dương (inclusion filter). Chỉ giữ lại các file khớp (THÊM vào config)."
    )

    # Group 2: Config Flags
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
        force_silent=args.force # Nếu --force, không hỏi
    )
    
    if effective_scan_root is None:
        # Người dùng đã chọn 'Quit' trong handle_project_root_validation
        sys.exit(0)

    # 5. Chạy Core Logic và Executor
    try:
        results = process_stubgen_logic(
            logger=logger,
            scan_root=effective_scan_root,
            cli_args=args, # Core sẽ tự trích xuất 'ignore', 'restrict', 'include'
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