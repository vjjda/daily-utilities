# Path: utils/core/__init__.py

"""
Utility Core (Facade Pattern)
...
"""

import logging
from pathlib import Path
from importlib import import_module
from typing import List, Tuple, Union, Set, Optional, Dict, Any # <-- Thêm Dict, Any

Logger = logging.Logger

# --- Tự động Tái xuất (Dynamic Re-export) ---
current_dir = Path(__file__).parent

# --- MODIFIED: Thêm 'config_io' ---
modules_to_export = [
    f.stem
    for f in current_dir.iterdir()
    if f.is_file() and f.suffix == '.py' and f.name != '__init__.py'
]
# --- END MODIFIED ---

# --- MODIFIED: Tạo __all__ để gateway biết cần export gì ---
__all__: List[str] = [] # Khởi tạo __all__ rỗng

for module_name in modules_to_export:
    try:
        module = import_module(f".{module_name}", package=__name__)

        if hasattr(module, '__all__'):
            module_exports = getattr(module, '__all__')
            for name in module_exports:
                obj = getattr(module, name)
                globals()[name] = obj
            __all__.extend(module_exports) # Thêm vào __all__ của utils.core
        else:
             # Fallback nếu module con không có __all__ (không nên xảy ra)
             print(f"Warning: Module '{module_name}' in utils/core is missing __all__ definition.")

    except ImportError as e:
         print(f"Warning: Could not import from utils/core/{module_name}: {e}")
# --- END MODIFIED ---

# Clean up temporary variables không cần thiết nữa vì đã có __all__
# del current_dir, modules_to_export, module_name, module, module_exports, name, obj