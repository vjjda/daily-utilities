# Path: modules/zsh_wrapper/zsh_wrapper_executor.py

"""
Execution/Action logic for zsh_wrapper (zrap).
(Chịu trách nhiệm ghi file, chmod)
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

__all__ = ["execute_zsh_wrapper_action"]

def execute_zsh_wrapper_action(
    logger: logging.Logger, 
    result: Dict[str, Any]
) -> None:
    """
    Hàm thực thi, nhận nội dung wrapper và ghi ra file.
    (Side-effect: Ghi I/O, Chmod)
    
    Args:
        logger: Logger.
        result: Dict kết quả từ core logic.

    Raises:
        IOError: Nếu không thể ghi file.
        Exception: Nếu không thể chmod.
    """
    
    if result.get("status") != "ok":
        logger.error("Dừng thực thi do lỗi từ bước core.")
        return

    output_path: Path = result["output_path"]
    final_content: str = result["final_content"]
    force: bool = result["force"]

    # 1. Kiểm tra an toàn (trừ khi --force)
    if output_path.exists() and not force:
        logger.error(f"❌ Lỗi: File output đã tồn tại: {output_path.name}")
        logger.error(f"   Sử dụng --force (-f) để ghi đè.")
        # Thoát với lỗi để entrypoint biết
        sys.exit(1)
    
    if output_path.exists() and force:
        logger.warning(f"⚠️  File '{output_path.name}' đã tồn tại. Ghi đè (do --force)...")
    
    # 2. Ghi file
    try:
        # Đảm bảo thư mục cha tồn tại
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_path.write_text(final_content, encoding='utf-8')
        
        logger.info(f"✍️  Đã ghi wrapper: {output_path.as_posix()}")

        # 3. Cấp quyền thực thi
        os.chmod(output_path, 0o755)
        logger.info(f"🔑  Đã cấp quyền thực thi (chmod +x) cho: {output_path.name}")
        
    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi ghi file: {e}")
        raise # Ném lỗi lên để core/entrypoint bắt
    except Exception as e:
        logger.error(f"❌ Lỗi không xác định khi ghi file/chmod: {e}")
        raise # Ném lỗi lên