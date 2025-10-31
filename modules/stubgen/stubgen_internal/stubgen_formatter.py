# Path: modules/stubgen/stubgen_internal/stubgen_formatter.py
from pathlib import Path
from typing import Set

__all__ = ["format_stub_content"]


def format_stub_content(
    init_path: Path,
    project_root: Path,
    all_exported_symbols: Set[str],
    stub_template_str: str,
) -> str:

    if not all_exported_symbols:

        return stub_template_str.format(
            module_name=init_path.parent.name,
            symbol_declarations="# (No symbols found)",
            all_list_repr="[]",
        )

    sorted_symbols = sorted(list(all_exported_symbols))

    symbol_declarations = "\n".join(f"{symbol}: Any" for symbol in sorted_symbols)

    quoted_symbols = [f'"{symbol}"' for symbol in sorted_symbols]

    all_list_body: str
    all_list_repr: str

    if not quoted_symbols:

        all_list_repr = "[]"
    else:

        all_list_body = ",\n".join(
            f"    {symbol_repr}" for symbol_repr in quoted_symbols
        )

        all_list_body += ","

        all_list_repr = f"[\n{all_list_body}\n]"

    module_name = init_path.parent.name

    return stub_template_str.format(
        module_name=module_name,
        symbol_declarations=symbol_declarations,
        all_list_repr=all_list_repr,
    )
