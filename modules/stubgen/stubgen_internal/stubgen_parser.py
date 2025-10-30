# Path: modules/stubgen/stubgen_internal/stubgen_parser.py
"""
AST (Abstract Syntax Tree) Parsing logic for the Stub Generator (sgen) module.
(Internal module, imported by stubgen_core.py)
"""

import logging
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Final

__all__ = [
    "extract_module_list",
    "collect_all_exported_symbols"
]

def _get_ast_tree(path: Path) -> Optional[ast.Module]:
    """Đọc file Python và trả về cây AST của nó."""
    try:
        content = path.read_bytes()
        return ast.parse(content.decode('utf-8'))
    except (UnicodeDecodeError, FileNotFoundError, SyntaxError, OSError): 
        return None

def extract_module_list(
    init_path: Path,
    ast_module_list_name: str
) -> List[str]:
    """
    Trích xuất danh sách tên submodule (stems) từ file __init__.py.
    Ưu tiên 1: Phân tích AST để tìm biến `ast_module_list_name` (ví dụ: 'modules_to_export').
    Ưu tiên 2 (Fallback): Liệt kê heuristic tất cả các file .py
                       trong cùng thư mục (trừ __init__.py).
    """
    tree = _get_ast_tree(init_path)
    
    module_names: List[str] = []

    if tree:
        for node in ast.walk(tree):
            # Tìm kiếm: ast_module_list_name = [...]
            if (isinstance(node, ast.Assign) and 
                len(node.targets) == 1 and 
                isinstance(node.targets[0], ast.Name) and 
                node.targets[0].id == ast_module_list_name and
                isinstance(node.value, ast.List)):
                
                for element in node.value.elts:
                    if isinstance(element, ast.Constant) and isinstance(element.value, str):
                        module_names.append(element.value)
                return module_names # Trả về ngay nếu thành công

    # --- HEURISTIC FALLBACK ---
    # Nếu không tìm thấy list, dùng heuristic
    parent_dir = init_path.parent
    module_names = [
        f.stem for f in parent_dir.iterdir() 
        if f.is_file() and f.suffix == '.py' and f.name != '__init__.py'
    ]
    return module_names

def _extract_direct_symbols(tree: ast.Module) -> Set[str]:
    """
    Trích xuất (heuristic) các hằng số/types được định nghĩa
    trực tiếp trong __init__.py (ví dụ: Logger, CustomType).
    Chỉ tìm các phép gán ở cấp cao nhất (trước vòng lặp/if đầu tiên)
    và có tên bắt đầu bằng chữ hoa (hoặc là 'Logger').
    """
    direct_symbols: Set[str] = set()
    for node in tree.body:
        # Dừng lại khi gặp logic phức tạp
        if isinstance(node, (ast.For, ast.While, ast.If)):
            break
            
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbol_name = target.id
                    if symbol_name[0].isupper() or symbol_name == 'Logger':
                        direct_symbols.add(symbol_name)
    
    return direct_symbols

def _extract_all_symbols_from_file(
    module_path: Path,
    ast_all_list_name: str
) -> Set[str]:
    """
    Trích xuất danh sách `__all__` từ một file submodule.
    """
    tree = _get_ast_tree(module_path)
    if not tree:
        return set()

    for node in ast.walk(tree):
        # Tìm kiếm: ast_all_list_name = [...]
        if (isinstance(node, ast.Assign) and 
            len(node.targets) == 1 and 
            isinstance(node.targets[0], ast.Name) and 
            node.targets[0].id == ast_all_list_name and
            isinstance(node.value, ast.List)):
            
            symbols: Set[str] = set()
            for element in node.value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    symbols.add(element.value)
            return symbols
    return set()

def collect_all_exported_symbols(
    init_path: Path, 
    submodule_stems: List[str],
    ast_all_list_name: str
) -> Set[str]:
    """
    Tổng hợp tất cả các symbol được export từ các submodule
    và các symbol định nghĩa trực tiếp trong __init__.py.
    """
    all_exported_symbols: Set[str] = set()
    
    # 1. Thu thập từ các file con (submodule)
    for stem in submodule_stems:
        submodule_path = init_path.parent / f"{stem}.py"
        if submodule_path.is_file():
            symbols = _extract_all_symbols_from_file(submodule_path, ast_all_list_name)
            all_exported_symbols.update(symbols)
            
    # 2. Thu thập các symbols định nghĩa trực tiếp trong __init__.py (heuristic)
    init_tree = _get_ast_tree(init_path)
    if init_tree:
        direct_symbols = _extract_direct_symbols(init_tree)
        all_exported_symbols.update(direct_symbols)
        
    return all_exported_symbols