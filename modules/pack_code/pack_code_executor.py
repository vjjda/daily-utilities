# Path: modules/pack_code/pack_code_executor.py

"""
Execution/Action logic for pack_code.
(Ghi file, chạy lệnh, in ra console, v.v...)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

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
    output_path: Optional[Path] = result.get('output_path')
    scan_root: Path = result.get('scan_root', Path.cwd())

    # --- 1. Chế độ Dry Run ---
    if dry_run:
        logger.info("⚡ [Dry Run] Các file sẽ được đóng gói:")
        
        # Nếu cây đã được tạo, nó nằm trong final_content
        if not result.get('no_tree', False):
            print("\n" + final_content) # In cây (và chỉ cây)
        else:
            # Nếu không có cây, chỉ in danh sách
            file_list_rel: List[Path] = result.get('file_list_relative', [])
            for rel_path in file_list_rel:
                logger.info(f"   -> {rel_path.as_posix()}")
        
        logger.info(f"\nTổng cộng: {len(result.get('file_list_relative', []))} file.")
        if output_path:
             logger.info(f"Output dự kiến: {output_path.relative_to(scan_root).as_posix()}")
        return

    # --- 2. Chế độ Stdout ---
    if stdout:
        logger.debug("Đang in kết quả ra STDOUT...")
        print(final_content)
        logger.debug("In ra STDOUT hoàn tất.")
        return

    # --- 3. Chế độ Ghi File (Mặc định) ---
    if output_path:
        try:
            logger.info(f"Đang ghi vào file: {output_path.relative_to(scan_root).as_posix()}")
            # Đảm bảo thư mục (ví dụ: tmp/) tồn tại
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            output_path.write_text(final_content, encoding='utf-8')
            logger.info("✅ Ghi file hoàn tất.")
            
        except IOError as e:
            logger.error(f"❌ Lỗi I/O khi ghi file: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Lỗi không mong muốn khi ghi file: {e}")
            sys.exit(1)
    else:
        # Trường hợp này không nên xảy ra nếu logic core đúng
        logger.error("❌ Lỗi logic: Không ở chế độ stdout/dry_run nhưng không có đường dẫn output.")
        sys.exit(1)
