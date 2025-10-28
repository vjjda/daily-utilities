# Path: modules/stubgen/stubgen_formatter.py
"""
.pyi Content Formatting logic for the Stub Generator (sgen) module.
(Internal module, imported by stubgen_core.py)
"""

from pathlib import Path
from typing import Set

__all__ = ["format_stub_content"]


def format_stub_content(
    init_path: Path, 
    project_root: Path, 
    all_exported_symbols: Set[str],
    stub_template_str: str 
) -> str:
    """
    Generates the content string for the .pyi file.
    (Hàm này được chuyển từ stubgen_core.py)
    """
    
    if not all_exported_symbols:
        return ""

    sorted_symbols = sorted(list(all_exported_symbols))
    
    symbol_declarations = "\n".join(
        f"{symbol}: Any" for symbol in sorted_symbols
    )
    
    quoted_symbols = [repr(symbol) for symbol in sorted_symbols]
    all_list_body = ",\n".join(
        f"    {symbol_repr}" for symbol_repr in quoted_symbols
    )
    all_list_repr = f"[\n{all_list_body}\n]"
    
    rel_path = init_path.relative_to(project_root).as_posix()
    module_name = init_path.parent.name
    
    return stub_template_str.format(
        rel_path=f"{rel_path}i", 
        module_name=module_name,
        symbol_declarations=symbol_declarations,
        all_list_repr=all_list_repr
    )