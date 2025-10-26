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
    project_root: Path
) -> None:
    """
    Thực hiện kiểm tra an toàn và ghi tất cả file ra đĩa.
    """
    
    # 1. KIỂM TRA AN TOÀN
    if module_path.exists():
        logger.error(f"❌ Dừng lại! Thư mục module sau đã tồn tại. Sẽ không ghi đè:")
        logger.error(f"   -> {module_path.relative_to(project_root).as_posix()}")
        sys.exit(1)
        
    existing_files = [p for p in target_paths.values() if p.exists()]
    if existing_files:
        logger.error(f"❌ Dừng lại! Các file sau đã tồn tại. Sẽ không ghi đè:")
        for p in existing_files:
            logger.error(f"   -> {p.relative_to(project_root).as_posix()}")
        sys.exit(1)

    # 2. GHI FILE (I/O)
    try:
        # Tạo thư mục module trước
        module_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Đã tạo thư mục: {module_path.relative_to(project_root).as_posix()}")
            
        for key, path in target_paths.items():
            content = generated_content[key]
            # Đảm bảo thư mục cha (như /bin, /scripts) tồn tại
            path.parent.mkdir(parents=True, exist_ok=True) 
            path.write_text(content, encoding='utf-8')
            
            relative_path = path.relative_to(project_root).as_posix()
            log_success(logger, f"Đã tạo: {relative_path}")

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