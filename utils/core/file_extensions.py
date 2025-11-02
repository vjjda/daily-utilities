# Path: utils/core/file_extensions.py

from pathlib import Path
from typing import Set

__all__ = ["is_extension_matched"]


def is_extension_matched(file_path: Path, extensions_set: Set[str]) -> bool:

    file_name = file_path.name

    if file_name.startswith("."):

        ext_special = file_name.lstrip(".")
        if ext_special in extensions_set:
            return True

    full_ext = "".join(file_path.suffixes).lstrip(".")

    if full_ext in extensions_set:
        return True

    last_ext = file_path.suffix.lstrip(".")

    if last_ext in extensions_set:
        return True

    if not full_ext and not last_ext and "" in extensions_set:
        return True

    return False
