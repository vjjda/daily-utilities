# Path: modules/pack_code/pack_code_internal/__init__.py

from pathlib import Path
from importlib import import_module
from typing import List


current_dir = Path(__file__).parent


modules_to_export: List[str] = [
    "pack_code_loader",
    "pack_code_tree",
    "pack_code_resolver",
    "pack_code_builder",
    "pack_code_task_file",
    "pack_code_task_dir",
]

__all__: List[str] = []

for submodule_stem in modules_to_export:
    try:
        module = import_module(f".{submodule_stem}", package=__name__)

        if hasattr(module, "__all__"):
            public_symbols = getattr(module, "__all__")
            for name in public_symbols:
                obj = getattr(module, name)
                globals()[name] = obj
            __all__.extend(public_symbols)

    except ImportError as e:
        print(
            f"Cảnh báo: Không thể import từ {submodule_stem} trong module {__name__}: {e}"
        )


del Path, import_module, List, current_dir, modules_to_export, submodule_stem
if "module" in locals():
    del module
if "public_symbols" in locals():
    del public_symbols
if "name" in locals():
    del name
if "obj" in locals():
    del obj
