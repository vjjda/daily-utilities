# Path: modules/stubgen/stubgen_internal/__init__.py
"""
Facade nội bộ cho các thành phần "worker" của stubgen.
Che giấu các chi tiết triển khai (parser, loader, merger, formatter)
khỏi namespace chính của module 'stubgen'.
"""
# ... (Nội dung file không đổi) ...
from pathlib import Path
from importlib import import_module
from typing import List

# --- Tự động Tái xuất (Dynamic Re-export) ---
current_dir = Path(__file__).parent

# Định nghĩa thứ tự load (mặc dù không quan trọng bằng bootstrap)
modules_to_export: List[str] = [
    "stubgen_loader",
    "stubgen_merger",
    "stubgen_parser",
    "stubgen_formatter",
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
        print(f"Cảnh báo: Không thể import từ {submodule_stem} trong module {__name__}: {e}")

# Dọn dẹp
del Path, import_module, List, current_dir, modules_to_export, submodule_stem
if 'module' in locals():
    del module
if 'public_symbols' in locals():
    del public_symbols
if 'name' in locals():
    del name
if 'obj' in locals():
    del obj