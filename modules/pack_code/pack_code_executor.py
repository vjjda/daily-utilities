# Path: modules/pack_code/pack_code_executor.py

"""
Execution/Action logic for pack_code.
(Ghi file, chạy lệnh, in ra console, v.v...)
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
    Hàm thực thi, nhận kết quả từ _core và thực hiện side-effect.
"""
    
    status = result.get('status')
    if status == 'empty':
        logger.info("Không có file nào để xử lý. Đã dừng.")
        return
    elif status != 'ok':
        logger.error("Core logic failed, executor aborted.")
        return

    # Trích xuất kết quả
    dry_run: bool = result.get('dry_run', False)
    stdout: bool = result.get('stdout', False)
    final_content: str = result.get('final_content', '')
    # --- MODIFIED: Đổi tên biến để xử lý ---
    output_path_raw: Optional[Path] = result.get('output_path') #
    # --- END MODIFIED ---
    scan_root: Path = result.get('scan_root', Path.cwd())
    copy_to_clipboard: bool = result.get('copy_to_clipboard', False)

    # --- 1. Chế độ Dry Run ---
    if dry_run:
        logger.info("⚡ [Dry Run] Các file sẽ được đóng gói:")
        
        if not result.get('no_tree', False):
            print("\n" + result.get('tree_string', '')) # [cite: 266, 269]
        else:
            file_list_rel: List[Path] = result.get('file_list_relative', [])
            for rel_path in file_list_rel:
                logger.info(f"   -> {rel_path.as_posix()}")
        
        logger.info(f"\nTổng cộng: {len(result.get('file_list_relative', []))} file.")
        if output_path_raw:
             # --- MODIFIED: Hiển thị đường dẫn đã expand cho dry run ---
             logger.info(f"Output dự kiến: {output_path_raw.expanduser().resolve().as_posix()}")
             # --- END MODIFIED ---
        return

    # --- 2. Chế độ Stdout ---
    if stdout:
        logger.debug("Đang in kết quả ra STDOUT...")
        print(final_content)
        logger.debug("In ra STDOUT hoàn tất.")
        return

    # --- 3. Chế độ Ghi File (Mặc định) ---
    if output_path_raw:
        # --- NEW: Expand (~) và resolve đường dẫn TRƯỚC KHI dùng ---
        output_path = output_path_raw.expanduser().resolve()
        # --- END NEW ---

        tree_str = result.get('tree_string', '')
        no_tree = result.get('no_tree', False)
        
        if not no_tree and tree_str:
            print("\n" + tree_str)
            print("\n" + ("=" * 80) + "\n")

        try:
            logger.info(f"Đang ghi vào file: {output_path.as_posix()}")
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            output_path.write_text(final_content, encoding='utf-8')
            logger.info("✅ Ghi file hoàn tất.")

            # --- NEW: Xử lý --copy ---
            if copy_to_clipboard:
                logger.info("Đang sao chép file vào clipboard hệ thống...")
                copy_success = copy_file_to_clipboard(logger, output_path)
                if copy_success:
                    log_success(logger, "Đã sao chép file vào clipboard.")
                else:
                    # Lỗi đã được log bên trong hàm utility
                    logger.warning("⚠️ Không thể sao chép file vào clipboard.")
            # --- END NEW ---
            
        except IOError as e:
            logger.error(f"❌ Lỗi I/O khi ghi file: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Lỗi không mong muốn khi ghi file: {e}")
            sys.exit(1)
    else:
        logger.error("❌ Lỗi logic: Không ở chế độ stdout/dry_run nhưng không có đường dẫn output.")
        sys.exit(1)