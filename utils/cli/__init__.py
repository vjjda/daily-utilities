# Path: utils/cli/__init__.py

"""
Module Gateway (Facade) cho các tiện ích CLI (Typer/UI).
"""

from pathlib import Path
from importlib import import_module
from typing import List

# --- Dynamic Re-export ---
current_dir = Path(__file__).parent

# (Hiện tại chỉ có 'ui_helpers', sau này có thể thêm 'formatters', v.v.)
modules_to_export: List[str] = [
    "ui_helpers"
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

# Clean up
del Path, import_module, List, current_dir, modules_to_export
if 'module_name' in locals(): del module_name
if 'module' in locals(): del module
if 'public_symbols' in locals(): del public_symbols
if 'name' in locals(): del name
if 'obj' in locals(): del obj