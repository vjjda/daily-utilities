# Path: utils/cli/config_init/__init__.py
from pathlib import Path
from importlib import import_module
from typing import List


current_dir = Path(__file__).parent


modules_to_export: List[str] = [
    "config_defaults_resolver",
    "config_content_generator",
    "config_writer_local",
    "config_writer_project",
]

__all__: List[str] = []

for module_name in modules_to_export:
    try:
        module = import_module(f".{module_name}", package=__name__)

        if hasattr(module, "__all__"):
            public_symbols = getattr(module, "__all__")
            for name in public_symbols:
                obj = getattr(module, name)
                globals()[name] = obj
            __all__.extend(public_symbols)
        else:
            print(
                f"Cảnh báo: Module '{module_name}' trong utils/cli/config_init thiếu __all__."
            )

    except ImportError as e:
        print(
            f"Cảnh báo: Không thể import từ {module_name} trong utils/cli/config_init: {e}"
        )


del Path, import_module, List, current_dir, modules_to_export
if "module_name" in locals():
    del module_name
if "module" in locals():
    del module
if "public_symbols" in locals():
    del public_symbols
if "name" in locals():
    del name
if "obj" in locals():
    del obj