# Path: modules/pack_code/pack_code_executor.py

"""
Execution/Action logic for pack_code.
(Ghi file, chạy lệnh, in ra console, v.v...)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- NEW: __all__ definition ---
__all__ = ["execute_pack_code_action"]
# --- END NEW ---

def execute_pack_code_action(logger: logging.Logger, result: Dict[str, Any]) -> None:
    """
    Hàm thực thi, nhận kết quả từ _core và thực hiện side-effect.
    """
    logger.info(f"Executor running with result:")
    
    # (TODO: Thêm logic thực thi ở đây)
    # (Đây là ví dụ in kết quả)
    if result.get('status') == 'ok':
        data = result.get('data', {}) # (Escaped braces)
        for key, value in data.items():
            # --- MODIFIED: Escaped f-string braces ---
            logger.info(f"   -> {key}: {value}")
            # --- END MODIFIED ---
    else:
        logger.error("Core logic failed, executor aborted.")
    
    pass