# Path: scripts/no_doc.py

"""
Entrypoint (cổng vào) cho ndoc (No Doc).
Script này chịu trách nhiệm:
1. Thiết lập `sys.path` để import `utils` và `modules`[cite: 918].
2. Phân tích đối số dòng lệnh (Argparse).
3. Cấu hình logging[cite: 919].
4. Xử lý yêu cầu khởi tạo config (--config-local, --config-project)[cite: 929].
5. Gọi logic cốt lõi (`process_no_doc_logic`)[cite: 933].
6. Gọi logic thực thi (`execute_ndoc_action`) dựa trên kết quả[cite: 933].
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Final, Dict, Any

# Thiết lập sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# --- Import Module và Tiện ích ---
try:
    from utils.logging_config import setup_logging
    from utils.cli import handle_project_root_validation, handle_config_init_request
    from utils.core import parse_comma_list 
    
    from modules.no_doc import (
        process_no_doc_logic,
        execute_ndoc_action,
        
        # Hằng số config
        DEFAULT_START_PATH, DEFAULT_EXTENSIONS, DEFAULT_IGNORE,
        CONFIG_FILENAME, PROJECT_CONFIG_FILENAME, CONFIG_SECTION_NAME
    )
except ImportError as e:
    print(f"Lỗi: Không thể import project utilities/modules: {e}", file=sys.stderr)
    sys.exit(1)

# --- HẰNG SỐ CỤ THỂ CHO ENTRYPOINT ---
THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()
MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "no_doc"
TEMPLATE_FILENAME: Final[str] = "no_doc.toml.template" 

# Cấu hình mặc định để điền vào file template config
NDOC_DEFAULTS: Final[Dict[str, Any]] = {
    "extensions": sorted(list(DEFAULT_EXTENSIONS)), # [py]
    "ignore": sorted(list(DEFAULT_IGNORE)) 
}


def main():
    """ Hàm điều phối chính (phiên bản Argparse) """
    
    # 1. Định nghĩa Parser
    parser = argparse.ArgumentParser(
        description="Công cụ quét và xóa docstring (và tùy chọn comment) khỏi file mã nguồn Python.",
        epilog="Mặc định: Chạy ở chế độ sửa lỗi. Dùng -d để chạy thử.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Nhóm Tùy chọn Xử lý Docstring
    pack_group = parser.add_argument_group("Tùy chọn Xử lý Docstring")
    pack_group.add_argument(
        "start_path_arg",
        type=str,
        nargs='?',
        default=DEFAULT_START_PATH,
        help='Đường dẫn (file hoặc thư mục) để bắt đầu quét. Mặc định: ".".'
    )
    pack_group.add_argument(
        "-a", "--all-clean",
        action="store_true",
        help="Loại bỏ cả docstring và tất cả comments (#) khỏi file (ngoại trừ shebang)."
    )
    pack_group.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="Chỉ chạy ở chế độ kiểm tra (dry-run) và báo cáo các file cần sửa, không thực hiện ghi file."
    )
    pack_group.add_argument(
        "-e", "--extensions",
        type=str,
        default=None,
        help="Danh sách các đuôi file cần quét (phân cách bởi dấu phẩy). Hỗ trợ + (thêm) và ~ (bớt)."
    )
    pack_group.add_argument(
        "-I", "--ignore",
        type=str,
        default=None,
        help="Danh sách pattern (giống .gitignore) để bỏ qua khi quét (THÊM vào config)."
    )
    pack_group.add_argument(
        "-f", "--force",
        action="store_true",
        help="Ghi đè file mà không hỏi xác nhận (chỉ áp dụng ở chế độ fix)."
    )
    
    # Nhóm Khởi tạo Config
    config_group = parser.add_argument_group("Khởi tạo Cấu hình (chạy riêng)")
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
    logger = setup_logging(script_name="Ndoc")
    logger.debug("Ndoc script started.")

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
            base_defaults=NDOC_DEFAULTS
        )
        if config_action_taken:
            sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    # 4. Xử lý Path và Validation
    start_path_str = args.start_path_arg 
    start_path = Path(start_path_str).expanduser().resolve()
    
    if not start_path.exists():
        logger.error(f"❌ Lỗi: Đường dẫn mục tiêu không tồn tại: {start_path}")
        sys.exit(1)

    # Tìm gốc Git để làm gốc quét
    effective_scan_root: Optional[Path]
    # Lấy thư mục cha nếu là file, nếu không thì lấy chính thư mục đó làm gốc tìm kiếm
    root_to_search = start_path.parent if start_path.is_file() else start_path 

    effective_scan_root, git_warning_str = handle_project_root_validation(
        logger=logger, 
        scan_root=root_to_search, 
        force_silent=args.force # Nếu --force, không hỏi
    )
    
    if effective_scan_root is None:
        sys.exit(0)

    # Gán đường dẫn đã resolve vào args (cho Core sử dụng)
    setattr(args, 'start_path_path', start_path)
    
    # 5. Chạy Core Logic và Executor
    try:
        # Core sẽ tự load config, merge, scan, và analyze
        files_to_fix = process_no_doc_logic(
            logger=logger, 
            project_root=effective_scan_root,
            cli_args=args, # Truyền thẳng namespace vào core
            script_file_path=THIS_SCRIPT_PATH
        )
        
        # Executor thực hiện side-effect (báo cáo, ghi file)
        execute_ndoc_action(
            logger=logger, 
            files_to_fix=files_to_fix, 
            dry_run=args.dry_run, # Mặc định là False (chế độ Fix)
            force=args.force,
            scan_root=effective_scan_root,
            git_warning_str=git_warning_str
        )

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Đã dừng xóa Docstring.")
        sys.exit(1)