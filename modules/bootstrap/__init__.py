# Path: modules/bootstrap/__init__.py
"""
Cổng giao tiếp (Facade) cho hệ thống con Bootstrap.

Tự động export tất cả các thành phần public (`__all__`)
từ các submodule bên trong theo thứ tự định nghĩa.
"""

from pathlib import Path
from importlib import import_module
from typing import List

# --- Tự động Tái xuất (Dynamic Re-export) ---
current_dir = Path(__file__).parent

# Định nghĩa thứ tự load các module nội bộ
# Thứ tự này quan trọng vì các module sau có thể phụ thuộc vào module trước
modules_to_export: List[str] = [
    "bootstrap_config",
    "bootstrap_loader",   # Chứa logic tải template, config
    "bootstrap_utils",    # Chứa các hàm helper nhỏ, dùng chung
    "bootstrap_builder",  # Cổng vào cho các builder (argparse, typer, config)
    "bootstrap_core",     # Chứa logic điền template chính
    "bootstrap_executor"  # Chứa logic ghi file, kiểm tra an toàn
]

__all__: List[str] = []

for module_name in modules_to_export:
    try:
        module = import_module(f".{module_name}", package=__name__)

        if hasattr(module, '__all__'):
            public_symbols = getattr(module, '__all__')
            for name in public_symbols:
                obj = getattr(module, name)
                globals()[name] = obj # Thêm vào namespace của bootstrap
            __all__.extend(public_symbols) # Thêm vào __all__ của bootstrap

    except ImportError as e:
        print(f"Cảnh báo: Không thể import từ {module_name}: {e}") #

# Dọn dẹp
del Path, import_module, List, current_dir, modules_to_export, module_name
if 'module' in locals():
    del module
if 'public_symbols' in locals():
    del public_symbols
if 'name' in locals():
    del name
if 'obj' in locals():
    del obj