# Path: utils/core/__init__.py
import logging
from pathlib import Path
from importlib import import_module
from typing import List, Tuple, Union, Set, Optional, Dict, Any

Logger = logging.Logger


current_dir = Path(__file__).parent


modules_to_export = [
    f.stem
    for f in current_dir.iterdir()
    if f.is_file() and f.suffix == ".py" and f.name != "__init__.py"
]

__all__: List[str] = []

for module_name in modules_to_export:
    try:

        module = import_module(f".{module_name}", package=__name__)

        if hasattr(module, "__all__"):
            module_exports = getattr(module, "__all__")

            for name in module_exports:
                obj = getattr(module, name)
                globals()[name] = obj
            __all__.extend(module_exports)
        else:

            print(
                f"Cảnh báo: Module '{module_name}' trong utils/core thiếu định nghĩa __all__."
            )

    except ImportError as e:
        print(f"Cảnh báo: Không thể import từ utils/core/{module_name}: {e}")