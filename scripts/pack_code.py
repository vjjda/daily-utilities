# Path: scripts/pack_code.py
"""
Entrypoint (cổng vào) cho pcode (Pack Code).
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Final
import os # SỬA: Thêm 'os' để tìm tổ tiên chung

# --- Thiết lập sys.path ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    # SỬA: Import 'resolve_input_paths'
    from utils.cli import handle_config_init_request, resolve_input_paths
    from utils.core import parse_comma_list
    from modules.pack_code.pack_code_config import (
        DEFAULT_START_PATH,
        DEFAULT_EXTENSIONS,
        DEFAULT_IGNORE,
        DEFAULT_CLEAN_EXTENSIONS,
        DEFAULT_OUTPUT_DIR,
        PROJECT_CONFIG_FILENAME,
        CONFIG_FILENAME,
        CONFIG_SECTION_NAME,
    )
    from modules.pack_code import (
        process_pack_code_logic,
        execute_pack_code_action,
    )
except ImportError as e:
    print(f"Lỗi: Không thể import các tiện ích/module dự án: {e}", file=sys.stderr)
    sys.exit(1)

MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "pack_code"
TEMPLATE_FILENAME: Final[str] = "pack_code.toml.template"
PCODE_DEFAULTS: Final[Dict[str, Any]] = {
    "output_dir": DEFAULT_OUTPUT_DIR,
    "extensions": list(parse_comma_list(DEFAULT_EXTENSIONS)),
    "ignore": list(parse_comma_list(DEFAULT_IGNORE)),
    "clean_extensions": sorted(list(DEFAULT_CLEAN_EXTENSIONS)),
}


def main():

    parser = argparse.ArgumentParser(
        description="Đóng gói nội dung của nhiều file/thư mục thành một file văn bản duy nhất.",
        epilog="Ví dụ: pcode ./src -e 'py,md' -o context.txt",
    )

    pack_group = parser.add_argument_group("Tùy chọn Đóng gói")
    pack_group.add_argument(
        # SỬA: Đổi tên và dùng nargs='*'
        "start_paths_arg",
        type=str,
        nargs="*",
        default=[],
        help='Các đường dẫn (file hoặc thư mục) để quét. Mặc định: ".".',
    )
    # ... (các cờ -o, -a, -e, -x, -I, -N, -d, --stdout, --no-header, --no-tree, --copy không đổi) ...
    pack_group.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="File output để ghi. Mặc định: '[output_dir]/<start_name>_context.txt' (từ config).",
    )
    pack_group.add_argument(
        "-a",
        "--all-clean",
        action="store_true",
        help="Làm sạch (xóa docstring/comment) nội dung của các file có đuôi trong 'clean_extensions' trước khi đóng gói.",
    )
    pack_group.add_argument(
        "-e",
        "--extensions",
        type=str,
        default=None,
        help="Chỉ bao gồm các đuôi file này (vd: 'py,md'). Hỗ trợ +/-/~.",
    )
    pack_group.add_argument(
        "-x",
        "--clean-extensions",
        type=str,
        default=None,
        help="Chỉ định/sửa đổi danh sách đuôi file cần làm sạch KHI -a được bật (vd: 'py,js'). Hỗ trợ +/-/~.",
    )
    pack_group.add_argument(
        "-I",
        "--ignore",
        type=str,
        default=None,
        help="Các pattern (giống .gitignore) để bỏ qua (THÊM vào config).",
    )
    pack_group.add_argument(
        "-N",
        "--no-gitignore",
        action="store_true",
        help="Không tôn trọng các file .gitignore.",
    )
    pack_group.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Chỉ in danh sách file sẽ được đóng gói (không đọc/in nội dung).",
    )
    pack_group.add_argument(
        "--stdout",
        action="store_true",
        help="In kết quả ra stdout (console) thay vì ghi file.",
    )
    pack_group.add_argument(
        "--no-header",
        action="store_true",
        help="Không in header phân tách ('===== path/to/file.py =====').",
    )
    pack_group.add_argument(
        "--no-tree",
        action="store_true",
        help="Không in cây thư mục của các file được chọn ở đầu output.",
    )
    pack_group.add_argument(
        "--copy",
        action="store_true",
        dest="copy_to_clipboard", # SỬA: Đảm bảo dest khớp
        help="Sao chép file output (không phải nội dung) vào clipboard hệ thống.",
    )

    config_group = parser.add_argument_group("Khởi tạo Cấu hình (chạy riêng)")
    # ... (không đổi) ...
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
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} cục bộ.",
    )

    args = parser.parse_args()

    logger = setup_logging(script_name="pcode")
    logger.debug("Script pcode bắt đầu.")

    # ... (Config init không đổi) ...
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
            base_defaults=PCODE_DEFAULTS,
        )
        if config_action_taken:
            sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    # --- SỬA: Logic xử lý đa đầu vào ---
    
    # 1. Resolve tất cả đường dẫn
    validated_paths: List[Path] = resolve_input_paths(
        logger=logger,
        raw_paths=args.start_paths_arg, # Lấy từ nargs='*'
        default_path_str=DEFAULT_START_PATH
    )
    if not validated_paths:
        logger.warning("Không tìm thấy đường dẫn hợp lệ nào để quét. Đã dừng.")
        sys.exit(0)

    # 2. Tìm Tổ tiên Chung Gần nhất (Lowest Common Ancestor)
    reporting_root: Optional[Path]
    try:
        # Chuyển đổi thành chuỗi tuyệt đối để os.path.commonpath xử lý
        abs_path_strings = [str(p.resolve()) for p in validated_paths]
        common_path_str = os.path.commonpath(abs_path_strings)
        reporting_root = Path(common_path_str)
        
        # Nếu tổ tiên chung là một file (ví dụ: pcode file.py file.py), dùng thư mục cha
        if reporting_root.is_file():
            reporting_root = reporting_root.parent
            
    except ValueError:
        # Xảy ra lỗi (ví dụ: C:\ và D:\ trên Windows),
        # fallback về None -> sẽ dùng đường dẫn tuyệt đối
        reporting_root = None

    if reporting_root:
        logger.debug(f"Gốc báo cáo (Reporting Root) được xác định: {reporting_root}")
    else:
        logger.debug("Không tìm thấy gốc báo cáo chung. Sẽ sử dụng đường dẫn tuyệt đối.")

    # 3. Phân loại file/thư mục
    files_to_process: List[Path] = [p for p in validated_paths if p.is_file()]
    dirs_to_scan: List[Path] = [p for p in validated_paths if p.is_dir()]

    # 4. Chuẩn bị CLI args
    output_path_obj = Path(args.output).expanduser() if args.output else None
    
    cli_args_dict = {
        # (Đã loại bỏ 'start_path')
        "output": output_path_obj,
        "stdout": args.stdout,
        "extensions": args.extensions,
        "ignore": args.ignore,
        "no_gitignore": args.no_gitignore,
        "dry_run": args.dry_run,
        "no_header": args.no_header,
        "no_tree": args.no_tree,
        "copy_to_clipboard": args.copy_to_clipboard,
        "all_clean": args.all_clean,
        "clean_extensions": args.clean_extensions,
    }

    try:
        # 5. Gọi Core với logic mới
        result = process_pack_code_logic(
            logger=logger,
            cli_args=cli_args_dict,
            files_to_process=files_to_process,
            dirs_to_scan=dirs_to_scan,
            reporting_root=reporting_root,
            script_file_path=PROJECT_ROOT / "scripts" / "pack_code.py" # (Cần cho scanner)
        )
        if result:
            execute_pack_code_action(logger=logger, result=result)
        if (
            not (args.dry_run or args.stdout)
            and result
            and result.get("status") == "ok"
        ):
            log_success(logger, "Hoạt động hoàn tất thành công.")
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
    # --- Kết thúc SỬA ---

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Hoạt động bị dừng bởi người dùng.")
        sys.exit(1)