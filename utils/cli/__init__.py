# Path: utils/cli/__init__.py
"""
Cổng giao tiếp (Facade) cho các tiện ích giao diện dòng lệnh (CLI).
"""

from pathlib import Path
from importlib import import_module
from typing import List

# --- Tự động Tái xuất (Dynamic Re-export) ---
current_dir = Path(__file__).parent

# Only export necessary functions/classes from the main orchestrator and helpers
# Keep internal modules like _local, _project, _generator internal.
modules_to_export: List[str] = [
    "ui_helpers", # Keep UI helpers exported
    "config_writer" # Export the main orchestrator function handle_config_init_request
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
        else:
             print(f"Cảnh báo: Module '{module_name}' trong utils/cli thiếu định nghĩa __all__.")

    except ImportError as e:
        print(f"Cảnh báo: Không thể import từ {module_name} trong utils/cli: {e}")

# Cleanup
del Path, import_module, List, current_dir, modules_to_export
# ... (rest of cleanup)
if 'module_name' in locals(): del module_name
if 'module' in locals(): del module
if 'public_symbols' in locals(): del public_symbols
if 'name' in locals(): del name
if 'obj' in locals(): del obj