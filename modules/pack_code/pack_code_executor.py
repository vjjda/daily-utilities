# Path: modules/pack_code/pack_code_executor.py

"""
Execution/Action logic for pack_code.
(Side-effects: Ghi file, In ra console, Sao chép vào clipboard)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.core import copy_file_to_clipboard
from utils.logging_config import log_success

__all__ = ["execute_pack_code_action"]


def execute_pack_code_action(logger: logging.Logger, result: Dict[str, Any]) -> None:
    """
    Hàm thực thi, nhận kết quả từ core và thực hiện side-effect.

    Args:
        logger: Logger.
        result: Dict "Result Object" từ `process_pack_code_logic`.
    """

    status = result.get('status')
    if status == 'empty':
        logger.info("Không có file nào để xử lý. Đã dừng.") #
        return
    elif status == 'error':
        # Lỗi đã được log trong core
        logger.error(f"Core logic failed: {result.get('message', 'Unknown error')}")
        sys.exit(1)
    elif status != 'ok':
        logger.error("Core logic failed with unknown status, executor aborted.")
        sys.exit(1)

    # --- Trích xuất kết quả ---
    dry_run: bool = result.get('dry_run', False)
    stdout: bool = result.get('stdout', False)
    final_content: str = result.get('final_content', '')
    output_path_raw: Optional[Path] = result.get('output_path') # Chưa expanduser/resolve
    scan_root: Path = result.get('scan_root', Path.cwd())
    copy_to_clipboard: bool = result.get('copy_to_clipboard', False)
    file_list_relative: List[Path] = result.get('file_list_relative', [])
    tree_string: str = result.get('tree_string', '')
    no_tree: bool = result.get('no_tree', False)

    # --- 1. Chế độ Dry Run ---
    if dry_run:
        logger.info("⚡ [Dry Run] Các file sẽ được đóng gói:")

        if not no_tree and tree_string:
            # In cây nếu có
            print("\n" + tree_string)
        else:
            # Nếu không có cây, in danh sách file
            for rel_path in file_list_relative:
                logger.info(f"   -> {rel_path.as_posix()}")

        logger.info(f"\nTổng cộng: {len(file_list_relative)} file.")
        if output_path_raw:
             # Hiển thị đường dẫn output dự kiến (đã expand)
             logger.info(f"Output dự kiến: {output_path_raw.expanduser().resolve().as_posix()}") #
        return # Kết thúc dry run

    # --- 2. Chế độ Stdout ---
    if stdout:
        logger.debug("Đang in kết quả ra STDOUT...")
        print(final_content) #
        logger.debug("In ra STDOUT hoàn tất.")
        return # Kết thúc stdout

    # --- 3. Chế độ Ghi File (Mặc định) ---
    if output_path_raw:
        # Expand (~) và resolve đường dẫn TRƯỚC KHI dùng
        try:
            output_path = output_path_raw.expanduser().resolve() #
        except Exception as e:
            logger.error(f"❌ Lỗi khi xử lý đường dẫn output: {output_path_raw} -> {e}")
            sys.exit(1)

        # In cây trước khi ghi file (nếu có)
        if not no_tree and tree_string:
            print("\n" + tree_string) #
            print("\n" + ("=" * 80) + "\n") #

        try:
            logger.info(f"Đang ghi vào file: {output_path.as_posix()}")

            # Đảm bảo thư mục cha tồn tại
            output_path.parent.mkdir(parents=True, exist_ok=True) #

            # Ghi nội dung vào file
            output_path.write_text(final_content, encoding='utf-8')
            logger.info("✅ Ghi file hoàn tất.")

            # Sao chép vào clipboard (nếu có cờ --copy)
            if copy_to_clipboard:
                logger.info("Đang sao chép file vào clipboard hệ thống...") #
                copy_success = copy_file_to_clipboard(logger, output_path) #
                if copy_success:
                    log_success(logger, "Đã sao chép file vào clipboard.") #
                else:
                    # Lỗi đã được log bên trong hàm utility
                    logger.warning("⚠️ Không thể sao chép file vào clipboard.") #

        except IOError as e:
            logger.error(f"❌ Lỗi I/O khi ghi file: {e}") #
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Lỗi không mong muốn khi ghi file: {e}") #
            sys.exit(1)
    else:
        # Trường hợp lỗi logic: không dry_run, không stdout nhưng không có output_path
        logger.error("❌ Lỗi logic: Không ở chế độ stdout/dry_run nhưng không có đường dẫn output.") #
        sys.exit(1)