# Path: modules/no_doc/__init__.py
"""
Cổng giao tiếp (Facade) cho module 'no_doc'.
(Tạo tự động bởi bootstrap_tool.py)

Export các thành phần public từ các file con.
"""

from pathlib import Path
from importlib import import_module
from typing import List

# --- Tự động Tái xuất (Dynamic Re-export) ---
from typing import List

# --- Tự động Tái xuất (Dynamic Re-export) ---
current_dir = Path(__file__).parent

# Thay thế khối try/except bằng logic Fallback trực tiếp:
# Fallback: Tự động tìm các file .py
modules_to_export: List[str] = [
    f.stem
    for f in current_dir.iterdir()
    if f.is_file() and f.suffix == '.py' and f.name != '__init__.py'
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
        print(f"Cảnh báo: Không thể import từ {submodule_stem} trong module {__name__}: {e}") #

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

# Thêm định nghĩa logger chung cho module (tùy chọn)
# import logging
# Logger = logging.getLogger(__name__)