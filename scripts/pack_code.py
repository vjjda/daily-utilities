# Path: scripts/pack_code.py

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any # <-- MODIFIED: Thêm Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    # --- MODIFIED: Import thêm ---
    from utils.cli import handle_config_init_request
    # --- NEW: Import from utils.core ---
    from utils.core import parse_comma_list
    # --- END NEW ---
    
    from modules.pack_code.pack_code_config import (
        DEFAULT_START_PATH, DEFAULT_EXTENSIONS, DEFAULT_IGNORE,
        DEFAULT_OUTPUT_DIR, # <-- Import DEFAULT_OUTPUT_DIR
        PROJECT_CONFIG_FILENAME, CONFIG_FILENAME, CONFIG_SECTION_NAME
    )
    from modules.pack_code import (
        process_pack_code_logic,
        execute_pack_code_action,
        load_config_files # <-- Import load_config_files
    )
    # --- END MODIFIED ---
except ImportError:
    print(f"Lỗi: Không thể import utils/modules...", file=sys.stderr)
    sys.exit(1)

# --- NEW: Constants for Config Init ---
MODULE_DIR = PROJECT_ROOT / "modules" / "pack_code"
TEMPLATE_FILENAME = "pack_code.toml.template"
PCODE_DEFAULTS: Dict[str, Any] = {
    # --- MODIFIED: Đã xóa "start_path" ---
    # "start_path": DEFAULT_START_PATH,
    # --- END MODIFIED ---
    "output_dir": DEFAULT_OUTPUT_DIR,
    "extensions": parse_comma_list(DEFAULT_EXTENSIONS), # utils.core.parsing
    "ignore": parse_comma_list(DEFAULT_IGNORE),
}
# --- END NEW ---

def main():
    """Hàm điều phối chính."""

    # 1. Định nghĩa Parser (Giữ nguyên)
    parser = argparse.ArgumentParser(
        description="Đóng gói nội dung của nhiều file/thư mục thành một file văn bản duy nhất.",
        epilog="Ví dụ: pcode ./src -e 'py,md' -o context.txt"
    )
    
    # --- MODIFIED: Tách thành 2 group ---
    pack_group = parser.add_argument_group("Packing Options")
    # --- END MODIFIED ---

    # --- Các arguments được tạo tự động ---
    pack_group.add_argument(
        "start_path",
        type=str,
        nargs="?",
        default=None, # <-- MODIFIED: Đặt là None để ưu tiên config
        help='Đường dẫn (file hoặc thư mục) để bắt đầu quét. Mặc định: "." hoặc giá trị trong config.'
    )
    pack_group.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="File output để ghi. Mặc định: 'tmp/<input_name>.txt'"
    )
    pack_group.add_argument(
        "-S", "--stdout",
        action="store_true",
        help='In kết quả ra stdout (console) thay vì ghi file.'
    )
    pack_group.add_argument(
        "-e", "--extensions",
        type=str,
        default=None, # <-- MODIFIED: Đặt là None
        help="Chỉ bao gồm các đuôi file này (vd: 'py,md'). Hỗ trợ +/-."
    )
    pack_group.add_argument(
        "-I", "--ignore",
        type=str,
        default=None, # <-- MODIFIED: Đặt là None
        help='Các pattern (giống .gitignore) để bỏ qua (THÊM vào config).'
    )
    pack_group.add_argument(
        "-N", "--no_gitignore",
        action="store_true",
        help='Không tôn trọng các file .gitignore.'
    )
    pack_group.add_argument(
        "-d", "--dry_run",
        action="store_true",
        help='Chỉ in danh sách file sẽ được đóng gói (không in nội dung).'
    )
    pack_group.add_argument(
        "--no_header",
        action="store_true",
        help="Không in header phân tách ('===== path/to/file.py =====')."
    )
    pack_group.add_argument(
        "--no_tree",
        action="store_true",
        help='Không in cây thư mục của các file được chọn ở đầu output.'
    )
    # --- Hết arguments ---
    
    # --- NEW: Config Group ---
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
    # --- END NEW ---

    args = parser.parse_args()

    # 2. Setup Logging (Giữ nguyên)
    logger = setup_logging(script_name="pcode")
    logger.debug("pcode script started.")

    # --- NEW: Xử lý Config Init ---
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
            base_defaults=PCODE_DEFAULTS
        )
        if config_action_taken:
            sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
    # --- END NEW ---

    # --- Mở rộng Path (nếu có) ---
    
    # --- MODIFIED: Chỉ expand/resolve nếu arg được cung cấp ---
    start_path_path = Path(args.start_path).expanduser().resolve() if args.start_path else None
    output_path = Path(args.output).expanduser() if args.output else None
    # --- END MODIFIED ---

    # --- NEW: Xác định thư mục load config ---
    # (Chúng ta cần làm điều này trước khi gọi core logic)
    # Nếu start_path không được cung cấp, dùng CWD để tìm config
    temp_start_path_for_config = start_path_path if start_path_path else Path.cwd().resolve()
    
    config_load_dir: Path
    if temp_start_path_for_config.is_file():
        config_load_dir = temp_start_path_for_config.parent
    else:
        config_load_dir = temp_start_path_for_config
        
    logger.debug(f"Đang tải config từ: {config_load_dir.as_posix()}")
    file_config = load_config_files(config_load_dir, logger)
    # --- END NEW ---

    # --- MODIFIED: Chuẩn bị args cho core logic ---
    cli_args_dict = {
        "start_path": start_path_path, # Truyền Path obj (hoặc None)
        "output": output_path,         # Truyền Path obj (hoặc None)
        "stdout": args.stdout,
        "extensions": args.extensions,     # Truyền string (hoặc None)
        "ignore": args.ignore,           # Truyền string (hoặc None)
        "no_gitignore": args.no_gitignore,
        "dry_run": args.dry_run,
        "no_header": args.no_header,
        "no_tree": args.no_tree,
    }
    # --- END MODIFIED ---

    # 3. Chạy Core Logic
    try:
        # --- MODIFIED: Thay đổi cách gọi hàm ---
        result = process_pack_code_logic(
            logger=logger,
            cli_args=cli_args_dict,
            file_config=file_config
        )
        # --- END MODIFIED ---

        if result:
            execute_pack_code_action(
                logger=logger,
                result=result
            )

        if not (args.dry_run or args.stdout) and result and result.get('status') == 'ok':
            log_success(logger, "Hoàn thành.")
        # --- END MODIFIED ---

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng.")
        sys.exit(1)