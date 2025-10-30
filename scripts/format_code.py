# Path: scripts/format_code.py



import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Final, Dict, Any, List, Set


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging
    from utils.cli import handle_config_init_request, resolve_input_paths
    from utils.core import parse_comma_list

    
    from modules.format_code import (
        process_format_code_logic,
        execute_format_code_action,
        DEFAULT_START_PATH, DEFAULT_EXTENSIONS, DEFAULT_IGNORE,
        CONFIG_FILENAME, PROJECT_CONFIG_FILENAME, CONFIG_SECTION_NAME
    )
except ImportError as e:
    print(f"Lỗi: Không thể import project utilities/modules: {e}", file=sys.stderr)
    sys.exit(1)


THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()

MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "format_code"








def main():
    
    parser = argparse.ArgumentParser(
        description="Công cụ quét và định dạng (format) file mã nguồn.",
        epilog="Mặc định: Chạy ở chế độ sửa lỗi tương tác. Dùng -d để chạy thử.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    pack_group = parser.add_argument_group("Tùy chọn Định dạng Code")
    pack_group.add_argument(
        "start_path_arg", 
        type=str, 
        nargs='*',
        default=[],
        help=f'Các đường dẫn (file hoặc thư mục) để quét. Mặc định: "{DEFAULT_START_PATH}".'
    )
    pack_group.add_argument(
        "-d", "--dry-run", action="store_true",
        help="Chỉ chạy ở chế độ kiểm tra (dry-run) và báo cáo các file cần sửa, không thực hiện ghi file."
    )
    pack_group.add_argument(
        "-e", "--extensions", type=str, default=None,
        help="Danh sách các đuôi file cần quét (phân cách bởi dấu phẩy). Hỗ trợ + (thêm) và ~ (bớt)."
    )
    pack_group.add_argument(
        "-I", "--ignore", type=str, default=None,
        help="Danh sách pattern (giống .gitignore) để bỏ qua khi quét (THÊM vào config)."
    )
    pack_group.add_argument(
        "-f", "--force", action="store_true",
        help="Ghi đè file mà không hỏi xác nhận (chỉ áp dụng ở chế độ fix)."
    )
    
    args = parser.parse_args()

    
    
    logger = setup_logging(script_name="FormatCode")
    logger.debug("FormatCode script started.")

    
    

    
    validated_paths: List[Path] = resolve_input_paths(
        logger=logger,
        raw_paths=args.start_path_arg,
        default_path_str=DEFAULT_START_PATH
    )

    if not validated_paths:
        logger.warning("Không tìm thấy đường dẫn hợp lệ nào để quét. Đã dừng.")
        sys.exit(0)

    files_to_process: List[Path] = []
    dirs_to_scan: List[Path] = []
    for path in validated_paths:
        if path.is_file():
            files_to_process.append(path)
        elif path.is_dir():
            dirs_to_scan.append(path)

    
    try:
        
        files_to_fix = process_format_code_logic(
            logger=logger,
            files_to_process=files_to_process,
            dirs_to_scan=dirs_to_scan,
            cli_args=args,
            script_file_path=THIS_SCRIPT_PATH
        )
        
        reporting_root = Path.cwd()
        
        
        execute_format_code_action(
            logger=logger, 
            all_files_to_fix=files_to_fix,
            dry_run=args.dry_run, 
            force=args.force,
            scan_root=reporting_root
        )
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try: 
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Đã dừng định dạng Code.")
        sys.exit(1)