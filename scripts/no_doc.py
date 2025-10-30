# Path: scripts/no_doc.py

"""
Entrypoint (cổng vào) cho ndoc (No Doc).
...
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Final, Dict, Any, List, Set # <-- THÊM List

# Thiết lập sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging
    # THÊM IMPORT MỚI
    from utils.cli import handle_config_init_request, resolve_scan_tasks, ScanTask
    # BỎ IMPORT handle_project_root_validation
    
    from utils.core import parse_comma_list

    from modules.no_doc import (
        process_no_doc_logic,
        execute_ndoc_action,
        DEFAULT_START_PATH, DEFAULT_EXTENSIONS, DEFAULT_IGNORE,
        CONFIG_FILENAME, PROJECT_CONFIG_FILENAME, CONFIG_SECTION_NAME
    )
except ImportError as e:
    print(f"Lỗi: Không thể import project utilities/modules: {e}", file=sys.stderr) # [cite: 982]
    sys.exit(1)

# --- HẰNG SỐ CỤ THỂ CHO ENTRYPOINT ---
THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()
MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "no_doc"
TEMPLATE_FILENAME: Final[str] = "no_doc.toml.template"

# Cấu hình mặc định để điền vào file template config
NDOC_DEFAULTS: Final[Dict[str, Any]] = {
    # SỬA: Sử dụng DEFAULT_EXTENSIONS (Set) cho template
    "extensions": sorted(list(DEFAULT_EXTENSIONS)),
    "ignore": sorted(list(DEFAULT_IGNORE))
}


def main():
    """ Hàm điều phối chính (phiên bản Argparse) """
    
    parser = argparse.ArgumentParser(
        description="Công cụ quét và xóa docstring (và tùy chọn comment) khỏi file mã nguồn.", # [cite: 984]
        epilog="Mặc định: Chạy ở chế độ sửa lỗi. Dùng -d để chạy thử.", # [cite: 984, 985]
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    pack_group = parser.add_argument_group("Tùy chọn Xử lý Docstring")
    pack_group.add_argument(
        "start_path_arg", 
        type=str, 
        nargs='*',  # <-- THAY ĐỔI: Chấp nhận 0 hoặc nhiều
        default=[], # <-- THAY ĐỔI: Mặc định là list rỗng
        help=f'Các đường dẫn (file hoặc thư mục) để quét. Mặc định: "{DEFAULT_START_PATH}".'
    )
    # ... (Các argument khác không đổi: -a, -d, -e, -I, -f) ...
    pack_group.add_argument(
        "-a", "--all-clean", action="store_true",
        help="Loại bỏ cả docstring và tất cả comments (#) khỏi file (ngoại trừ shebang)." # [cite: 986]
    )
    pack_group.add_argument(
        "-d", "--dry-run", action="store_true",
        help="Chỉ chạy ở chế độ kiểm tra (dry-run) và báo cáo các file cần sửa, không thực hiện ghi file." # [cite: 986]
    )
    pack_group.add_argument(
        "-e", "--extensions", type=str, default=None,
        help="Danh sách các đuôi file cần quét (phân cách bởi dấu phẩy). Hỗ trợ + (thêm) và ~ (bớt)." # [cite: 986]
    )
    pack_group.add_argument(
        "-I", "--ignore", type=str, default=None,
        help="Danh sách pattern (giống .gitignore) để bỏ qua khi quét (THÊM vào config)." # [cite: 987]
    )
    pack_group.add_argument(
        "-f", "--force", action="store_true",
        help="Ghi đè file mà không hỏi xác nhận (chỉ áp dụng ở chế độ fix)." # [cite: 987]
    )
    
    config_group = parser.add_argument_group("Khởi tạo Cấu hình (chạy riêng)")
    config_group.add_argument(
         "-c", "--config-project", action="store_true",
        help=f"Khởi tạo/cập nhật section [{CONFIG_SECTION_NAME}] trong {PROJECT_CONFIG_FILENAME}." # [cite: 988]
    )
    config_group.add_argument(
        "-C", "--config-local", action="store_true",
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} (scope 'local')." # [cite: 988]
    )
    args = parser.parse_args()

    # 2. Setup Logging (Không đổi)
    logger = setup_logging(script_name="Ndoc") # [cite: 989]
    logger.debug("Ndoc script started.")

    # 3. Xử lý Config Init (Không đổi)
    try:
        config_action_taken = handle_config_init_request(
            logger=logger, config_project=args.config_project, config_local=args.config_local,
            module_dir=MODULE_DIR, template_filename=TEMPLATE_FILENAME,
            config_filename=CONFIG_FILENAME, project_config_filename=PROJECT_CONFIG_FILENAME,
            config_section_name=CONFIG_SECTION_NAME, base_defaults=NDOC_DEFAULTS
        ) # [cite: 989]
        if config_action_taken: sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}") # [cite: 990]
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    # 4. Xử lý Path và Validation (THAY ĐỔI)
    # Sử dụng util mới để xử lý danh sách đầu vào
    scan_tasks: List[ScanTask]
    git_warnings: Set[str]
    scan_tasks, git_warnings = resolve_scan_tasks(
        logger=logger,
        raw_paths=args.start_path_arg,  # Đây là List[str] từ nargs='*'
        default_path_str=DEFAULT_START_PATH,
        force_silent=args.force
    )

    if not scan_tasks:
        logger.warning("Không tìm thấy đường dẫn hợp lệ nào để quét. Đã dừng.")
        sys.exit(0)

    # 5. Chạy Core Logic và Executor
    try:
        # Truyền danh sách tác vụ vào Core
        files_to_fix = process_no_doc_logic(
            logger=logger,
            scan_tasks=scan_tasks, # <-- THAY ĐỔI
            cli_args=args, # Vẫn truyền args cho các cờ khác
            script_file_path=THIS_SCRIPT_PATH
        )
        
        # Kết hợp tất cả các cảnh báo Git (nếu có)
        combined_git_warning = " ".join(sorted(list(git_warnings)))
        
        execute_ndoc_action(
            logger=logger, 
            files_to_fix=files_to_fix, 
            dry_run=args.dry_run, 
            force=args.force,
            # Sử dụng gốc của tác vụ ĐẦU TIÊN làm gốc báo cáo (chỉ để hiển thị)
            scan_root=scan_tasks[0].scan_root, 
            git_warning_str=combined_git_warning # <-- THAY ĐỔI
        ) # [cite: 992]
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}") # [cite: 992]
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try: 
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Đã dừng xóa Docstring.") # [cite: 992]
        sys.exit(1)