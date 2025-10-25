# Path: modules/stubgen/stubgen_core.py

"""
Core logic for the Stub Generator (sgen) module.
Handles AST parsing and .pyi content generation (Pure Logic).
"""

import logging
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Final

# Import Configs
from .stubgen_config import (
    AST_MODULE_LIST_NAME, 
    AST_ALL_LIST_NAME
)

# Import Loader
from .stubgen_loader import find_gateway_files

# --- Type Hint cho Result ---
StubResult = Dict[str, Any]

__all__ = ["process_stubgen_logic"]


# --- AST UTILITIES (Refactored from pyi_generator.py) ---

def _get_ast_tree(path: Path) -> Optional[ast.Module]:
    """Reads a file and returns its AST."""
    try:
        content = path.read_bytes()
        return ast.parse(content.decode('utf-8'))
    except (UnicodeDecodeError, FileNotFoundError, SyntaxError, OSError): 
        return None

def _extract_module_list(init_path: Path) -> List[str]:
    """Extracts the list of submodules from an __init__.py file using AST, with heuristic fallback."""
    tree = _get_ast_tree(init_path)
    
    module_names: List[str] = []

    if tree:
        for node in ast.walk(tree):
            # Tìm kiếm: modules_to_export = [...]
            if (isinstance(node, ast.Assign) and 
                len(node.targets) == 1 and 
                isinstance(node.targets[0], ast.Name) and 
                node.targets[0].id == AST_MODULE_LIST_NAME and
                isinstance(node.value, ast.List)):
                
                # Trích xuất từ AST (Dùng cho module/clip_diag, module/zsh_wrapper, ...)
                for element in node.value.elts:
                    if isinstance(element, ast.Constant) and isinstance(element.value, str):
                        module_names.append(element.value)
                return module_names # Trả về ngay nếu thành công

    # --- HEURISTIC FALLBACK ---
    # Nếu không tìm thấy biến modules_to_export rõ ràng, hãy thử quét thư mục.
    # Logic này bao gồm utils/core/__init__.py và các trường hợp tương tự.
    parent_dir = init_path.parent
    module_names = [
        f.stem for f in parent_dir.iterdir() 
        if f.is_file() and f.suffix == '.py' and f.name != '__init__.py'
    ]
    # Logic này an toàn vì các file này sau đó sẽ được kiểm tra __all__
    # --- END HEURISTIC ---

    return module_names

def _extract_direct_symbols(tree: ast.Module) -> Set[str]:
    """
    Extracts symbols defined by simple assignment directly in the __init__.py file
    and which are not considered private (starts with uppercase/PascalCase).
    (Heuristic for constants/types like Logger).
    """
    direct_symbols: Set[str] = set()
    for node in tree.body:
        # Dừng lại khi gặp các khối logic phức tạp (vòng lặp for)
        # để tránh phân tích logic dynamic re-export.
        if isinstance(node, (ast.For, ast.While, ast.If)):
            break
            
        # Capture simple assignments: Logger = logging.Logger
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbol_name = target.id
                    # Heuristic: Thêm vào nếu nó là Logger HOẶC bắt đầu bằng chữ hoa
                    if symbol_name[0].isupper() or symbol_name == 'Logger':
                        direct_symbols.add(symbol_name)
    
    return direct_symbols

def _extract_all_symbols(module_path: Path) -> Set[str]:
    """Extracts symbols from the __all__ list of a submodule."""
    tree = _get_ast_tree(module_path)
    if not tree:
        return set()

    for node in ast.walk(tree):
        # Tìm kiếm: __all__ = [...]
        if (isinstance(node, ast.Assign) and 
            len(node.targets) == 1 and 
            isinstance(node.targets[0], ast.Name) and 
            node.targets[0].id == AST_ALL_LIST_NAME and
            isinstance(node.value, ast.List)):
            
            symbols: Set[str] = set()
            for element in node.value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    symbols.add(element.value)
            return symbols
    return set()

def _generate_stub_content(init_path: Path, project_root: Path, submodule_stems: List[str]) -> Tuple[str, Set[str]]:
    """Generates the content for the .pyi file."""
    
    # 1. Collect all exported symbols from all submodules
    all_exported_symbols: Set[str] = set()
    for stem in submodule_stems:
        submodule_path = init_path.parent / f"{stem}.py"
        if submodule_path.is_file():
            symbols = _extract_all_symbols(submodule_path)
            all_exported_symbols.update(symbols)
            
    # 2. Collect symbols defined directly in __init__.py (Logger, etc.) <--- BỔ SUNG MỚI
    init_tree = _get_ast_tree(init_path)
    if init_tree:
        direct_symbols = _extract_direct_symbols(init_tree)
        all_exported_symbols.update(direct_symbols) # <-- Thêm vào danh sách tổng
    # --- KẾT THÚC BỔ SUNG MỚI ---
    if not all_exported_symbols:
        return "", set()

    # 2. Build the .pyi content
    stub_lines: List[str] = []
    
    # Header
    rel_path = init_path.relative_to(project_root).as_posix()
    stub_lines.append(f"# Path: {rel_path}i (Auto-generated by sgen)")
    stub_lines.append(f"\"\"\"Statically declared API for {init_path.parent.name}\"\"\"")
    stub_lines.append("")
    stub_lines.append("from typing import Any, List, Optional, Set, Dict, Union")
    stub_lines.append("from pathlib import Path")
    stub_lines.append("")

    # Declarations (sorted alphabetically)
    for symbol in sorted(list(all_exported_symbols)):
        # Khai báo tất cả symbol là Any (phương pháp an toàn nhất)
        stub_lines.append(f"{symbol}: Any")

    # __all__ declaration
    stub_lines.append("")
    stub_lines.append("# Static declaration of exported symbols (for Pylance)")
    # Sử dụng repr để đảm bảo chuỗi list là hợp lệ
    stub_lines.append(f"__all__: List[str] = {sorted(list(all_exported_symbols))!r}")

    return "\n".join(stub_lines), all_exported_symbols

# --- MAIN ORCHESTRATOR ---
def process_stubgen_logic(
    logger: logging.Logger, 
    scan_root: Path,
    cli_ignore: Set[str],
    cli_restrict: Set[str],
    script_file_path: Path
) -> List[StubResult]:
    """
    Orchestrates the stub generation process: 
    1. Loads (finds files).
    2. Processes (analyzes AST, generates content).
    """
    
    # 1. Load: Tìm file gateway (sử dụng stubgen_loader.py)
    gateway_files = find_gateway_files(
        logger=logger, 
        scan_root=scan_root,
        cli_ignore=cli_ignore,
        cli_restrict=cli_restrict,
        script_file_path=script_file_path
    )
    
    if not gateway_files:
        return []
        
    results: List[StubResult] = []
    logger.info(f"✅ Found {len(gateway_files)} dynamic gateways to process.")

    for init_file in gateway_files:
        
        # 2. Extract submodule stems
        submodule_stems = _extract_module_list(init_file)

        # 3. Generate stub content
        stub_content, exported_symbols = _generate_stub_content(init_file, scan_root, submodule_stems)
        
        if not exported_symbols:
            logger.warning(f"Skipping {init_file.name}: No exported symbols found.")
            continue

        stub_path = init_file.with_suffix(".pyi")
        
        # 4. Collate Result
        results.append({
            "init_path": init_file,
            "stub_path": stub_path,
            "content": stub_content,
            "exists": stub_path.exists(),
            "symbols_count": len(exported_symbols),
            "rel_path": stub_path.relative_to(scan_root).as_posix()
        })
        
    return results