# Path: modules/pack_code/__init__.py
"""
Module Gateway (Facade) for pack_code.

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
    "pack_code_config",
    "pack_code_loader",
    "pack_code_scanner",
    "pack_code_tree",
    "pack_code_resolver",
    "pack_code_builder",
    "pack_code_core",
    "pack_code_executor"
]

__all__: List[str] = []

for submodule_stem in modules_to_export:
    try:
        module = import_module(f".{submodule_stem}", package=__name__)

        if hasattr(module, '__all__'):
            public_symbols = getattr(module, '__all__')
            for name in public_symbols:
                obj = getattr(module, name)
                globals()[name] = obj
            __all__.extend(public_symbols)

    except ImportError as e:
        print(f"Warning: Could not import symbols from {submodule_stem}: {e}")

# Cleanup
del Path, import_module, List, current_dir, modules_to_export, submodule_stem
if 'module' in locals():
    del module
if 'public_symbols' in locals():
    del public_symbols
if 'name' in locals():
    del name
if 'obj' in locals():
    del obj