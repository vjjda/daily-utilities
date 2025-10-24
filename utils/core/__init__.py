# Path: utils/core/__init__.py

"""
Utility Core (Facade Pattern)

Đây là cổng giao tiếp chính (Facade). Nó tự động import và
"tái xuất" (re-export) nội dung (được định nghĩa trong __all__)
từ các module phụ trợ trong cùng thư mục 'utils/core/'.

Các script khác (ctree, cpath) vẫn import như cũ:
from utils.core import run_command
"""

import logging
from pathlib import Path
from importlib import import_module 
from typing import List, Tuple, Union, Set, Optional

# Type hint for logger
Logger = logging.Logger

# --- Tự động Tái xuất (Dynamic Re-export) ---
current_dir = Path(__file__).parent

# Lọc ra tất cả các tên module (tên file không phải __init__.py)
modules_to_export = [
    f.stem
    for f in current_dir.iterdir()
    if f.is_file() and f.suffix == '.py' and f.name != '__init__.py'
]

# Thực hiện import * cho từng module
for module_name in modules_to_export:
    # 1. Import module object (relative import)
    module = import_module(f".{module_name}", package=__name__)
    
    # 2. Check for __all__ and explicitly add names to the current module's namespace (globals)
    if hasattr(module, '__all__'):
        for name in module.__all__:
            # Lấy đối tượng (hàm, biến) từ module con
            obj = getattr(module, name)
            # Gán đối tượng đó vào namespace của __init__.py (globals())
            globals()[name] = obj 
            
# ----------------------------------------------------------------------