# Path: modules/bootstrap/bootstrap_executor.py
"""
Execution/Action logic for the Bootstrap module.
(Ghi file, chmod, kiểm tra an toàn)
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

from utils.logging_config import log_success

__all__ = ["execute_bootstrap_action"]

def execute_bootstrap_action(
    logger: logging.Logger,
    generated_content: Dict[str, str],
    target_paths: Dict[str, Path],
    module_path: Path,
    project_root: Path,
    force: bool # <-- NEW PARAMETER
) -> None:
    """
    Thực hiện kiểm tra an toàn và ghi tất cả file ra đĩa.
    """
    
    # 1. KIỂM TRA AN TOÀN
    # --- MODIFIED: Check force flag ---
    if module_path.exists():
        if not force:
            logger.error(f"❌ Dừng lại! Thư mục module sau đã tồn tại. Sẽ không ghi đè:")
            logger.error(f"   -> {module_path.relative_to(project_root).as_posix()}")
            logger.error("   (Sử dụng -f hoặc --force để ghi đè)")
            sys.exit(1)
        else:
            logger.warning(f"⚠️  Thư mục module đã tồn tại. Ghi đè (do --force)...")
        
    existing_files = [p for p in target_paths.values() if p.exists()]
    if existing_files:
        if not force:
            logger.error(f"❌ Dừng lại! Các file sau đã tồn tại. Sẽ không ghi đè:")
            for p in existing_files:
                logger.error(f"   -> {p.relative_to(project_root).as_posix()}")
            logger.error("   (Sử dụng -f hoặc --force để ghi đè)")
            sys.exit(1)
        else:
            logger.warning(f"⚠️  Phát hiện {len(existing_files)} file đã tồn tại. Ghi đè (do --force)...")
    # --- END MODIFIED ---

    # 2. GHI FILE (I/O)
    try:
        # Kiểm tra trước khi tạo thư mục
        module_existed_before = module_path.exists()
        
        # Tạo thư mục module
        module_path.mkdir(parents=True, exist_ok=True)
        
        if not module_existed_before:
            logger.info(f"Đã tạo thư mục: {module_path.relative_to(project_root).as_posix()}")
            
        for key, path in target_paths.items():
            content = generated_content[key]
            # Đảm bảo thư mục cha (như /bin, /scripts) tồn tại
            path.parent.mkdir(parents=True, exist_ok=True) 
            
            is_existing = path.exists() # Check before writing
            
            path.write_text(content, encoding='utf-8')
            
            relative_path = path.relative_to(project_root).as_posix()
            
            # --- MODIFIED: Log khác nhau cho tạo mới/ghi đè ---
            if is_existing and force:
                log_success(logger, f"Đã ghi đè: {relative_path}")
            elif not is_existing:
                log_success(logger, f"Đã tạo: {relative_path}")
            # (Trường hợp file tồn tại nhưng không có --force đã bị chặn ở trên)
            # --- END MODIFIED ---

            # Cấp quyền thực thi cho wrapper /bin/
            if key == "bin":
                os.chmod(path, 0o755) 
                logger.info(f"   -> Đã cấp quyền executable (chmod +x)")
            
    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi ghi file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Lỗi không xác định khi ghi file: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)