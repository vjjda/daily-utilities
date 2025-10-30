# Path: modules/stubgen/stubgen_internal/stubgen_parser.py

import logging
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Final

__all__ = ["extract_module_list", "collect_all_exported_symbols"]


def _get_ast_tree(path: Path) -> Optional[ast.Module]:
    try:
        content = path.read_bytes()
        return ast.parse(content.decode("utf-8"))
    except (UnicodeDecodeError, FileNotFoundError, SyntaxError, OSError):
        return None


def extract_module_list(init_path: Path, ast_module_list_name: str) -> List[str]:
    tree = _get_ast_tree(init_path)

    module_names: List[str] = []

    if tree:
        for node in ast.walk(tree):

            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == ast_module_list_name
                and isinstance(node.value, ast.List)
            ):

                for element in node.value.elts:
                    if isinstance(element, ast.Constant) and isinstance(
                        element.value, str
                    ):
                        module_names.append(element.value)
                return module_names

    parent_dir = init_path.parent
    module_names = [
        f.stem
        for f in parent_dir.iterdir()
        if f.is_file() and f.suffix == ".py" and f.name != "__init__.py"
    ]
    return module_names


def _extract_direct_symbols(tree: ast.Module) -> Set[str]:
    direct_symbols: Set[str] = set()
    for node in tree.body:

        if isinstance(node, (ast.For, ast.While, ast.If)):
            break

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbol_name = target.id
                    if symbol_name[0].isupper() or symbol_name == "Logger":
                        direct_symbols.add(symbol_name)

    return direct_symbols


def _extract_all_symbols_from_file(
    module_path: Path, ast_all_list_name: str
) -> Set[str]:
    tree = _get_ast_tree(module_path)
    if not tree:
        return set()

    for node in ast.walk(tree):

        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == ast_all_list_name
            and isinstance(node.value, ast.List)
        ):

            symbols: Set[str] = set()
            for element in node.value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    symbols.add(element.value)
            return symbols
    return set()


def collect_all_exported_symbols(
    init_path: Path, submodule_stems: List[str], ast_all_list_name: str
) -> Set[str]:
    all_exported_symbols: Set[str] = set()

    for stem in submodule_stems:
        submodule_path = init_path.parent / f"{stem}.py"
        if submodule_path.is_file():
            symbols = _extract_all_symbols_from_file(submodule_path, ast_all_list_name)
            all_exported_symbols.update(symbols)

    init_tree = _get_ast_tree(init_path)
    if init_tree:
        direct_symbols = _extract_direct_symbols(init_tree)
        all_exported_symbols.update(direct_symbols)

    return all_exported_symbols