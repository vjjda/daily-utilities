# Path: modules/check_path/__init__.py

"""
Module Gateway (Facade) for the Path Checker (cpath) module.

Tự động export tất cả các thành phần public (`__all__`) 
từ các submodule bên trong.
"""

from pathlib import Path
from importlib import import_module
from typing import List

# --- Dynamic Re-export ---
current_dir = Path(__file__).parent

# Định nghĩa thứ tự load các module nội bộ
modules_to_export: List[str] = [
    "check_path_config",
    "check_path_loader",
    "check_path_merger",
    "check_path_analyzer",
    "check_path_core",
    "check_path_executor",
    "check_path_rules",
    "check_path_scanner"
]

__all__: List[str] = []

for module_name in modules_to_export:
    try:
        module = import_module(f".{module_name}", package=__name__)
        
        if hasattr(module, '__all__'):
            public_symbols = getattr(module, '__all__')
            for name in public_symbols:
                obj = getattr(module, name)
                globals()[name] = obj
            __all__.extend(public_symbols)
    except ImportError as e:
        print(f"Warning: Could not import symbols from {module_name}: {e}")

# Cleanup
del Path, import_module, List, current_dir, modules_to_export, module_name
if 'module' in locals(): del module
if 'public_symbols' in locals(): del public_symbols
if 'name' in locals(): del name
if 'obj' in locals(): del obj