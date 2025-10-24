# Path: modules/tree/__init__.py

"""
Module Gateway (Facade) for the Tree (ctree) module.
(Logic updated to match utils/core/__init__.py)
"""

from pathlib import Path
from importlib import import_module
from typing import List

# --- Dynamic Re-export ---
current_dir = Path(__file__).parent

# Define the explicit order of internal modules to load
modules_to_export: List[str] = [
    "tree_config",
    "tree_core",
    "tree_executor"
]

# (This list is for Mypy/linters, but the main logic is globals())
__all__: List[str] = []

for module_name in modules_to_export:
    try:
        # 1. Import the module object (e.g., .tree_config)
        module = import_module(f".{module_name}", package=__name__)
        
        # 2. Check if __all__ is defined and add its contents
        if hasattr(module, '__all__'):
            public_symbols = getattr(module, '__all__')
            for name in public_symbols:
                # Get the actual function/class/constant
                obj = getattr(module, name)
                # Add it to the namespace of this __init__.py
                globals()[name] = obj
            
            # Add to __all__ for linters
            __all__.extend(public_symbols)
        
    except ImportError as e:
        # Handle cases where a submodule might fail to import
        print(f"Warning: Could not import symbols from {module_name}: {e}")

# Clean up temporary variables
del Path, import_module, List, current_dir, modules_to_export, module_name
# Check if loop ran at all before deleting
if 'module' in locals():
    del module
if 'public_symbols' in locals():
    del public_symbols
if 'name' in locals():
    del name
if 'obj' in locals():
    del obj