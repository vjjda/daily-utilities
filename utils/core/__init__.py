# Path: utils/core/__init__.py
"""
Cổng giao tiếp (Facade) cho các tiện ích cốt lõi (utils/core).

Sử dụng Dynamic Re-export để tự động đưa tất cả các thành phần public (`__all__`)
từ các module con (.py files) trong thư mục này vào namespace `utils.core`.
"""

import logging
from pathlib import Path
from importlib import import_module
from typing import List, Tuple, Union, Set, Optional, Dict, Any

Logger = logging.Logger # Type hint alias

# --- Tự động Tái xuất (Dynamic Re-export) ---
current_dir = Path(__file__).parent

# Lấy danh sách tên file (không có .py) trong thư mục hiện tại
modules_to_export = [
    f.stem
    for f in current_dir.iterdir()
    if f.is_file() and f.suffix == '.py' and f.name != '__init__.py'
]

__all__: List[str] = [] # Khởi tạo __all__ rỗng

for module_name in modules_to_export:
    try:
        # Import module con (ví dụ: .git, .parsing)
        module = import_module(f".{module_name}", package=__name__)

        # Nếu module con có định nghĩa __all__
        if hasattr(module, '__all__'):
            module_exports = getattr(module, '__all__')
            # Lặp qua các tên trong __all__ của module con
            for name in module_exports:
                obj = getattr(module, name) # Lấy đối tượng (hàm, class, hằng số)
                globals()[name] = obj       # Thêm vào namespace của utils.core
            __all__.extend(module_exports) # Thêm vào __all__ của utils.core
        else:
             # Cảnh báo nếu module con thiếu __all__
             print(f"Cảnh báo: Module '{module_name}' trong utils/core thiếu định nghĩa __all__.") #

    except ImportError as e:
        print(f"Cảnh báo: Không thể import từ utils/core/{module_name}: {e}") #