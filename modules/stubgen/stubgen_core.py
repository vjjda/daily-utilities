# Path: modules/stubgen/stubgen_core.py

"""
Core logic for the Stub Generator (sgen) module.
Handles Orchestration and .pyi content generation (Pure Logic).
(AST Parsing logic is in stubgen_parser.py)
"""

import logging
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Final

from .stubgen_parser import (
    extract_module_list,
    collect_all_exported_symbols
)

from .stubgen_loader import find_gateway_files

from utils.core import (
    resolve_config_value, 
    resolve_config_list, 
    parse_comma_list,
    load_text_template 
)

# --- MODIFIED: Cập nhật tên import ---
from .stubgen_config import (
    DEFAULT_IGNORE, 
    DEFAULT_RESTRICT, # <-- MODIFIED
    DYNAMIC_IMPORT_INDICATORS,
    AST_MODULE_LIST_NAME,
    AST_ALL_LIST_NAME
)
# --- END MODIFIED ---

MODULE_DIR = Path(__file__).parent
TEMPLATE_FILENAME = "pyi.py.template"

StubResult = Dict[str, Any]

__all__ = ["process_stubgen_logic"]


def _format_stub_content(
    init_path: Path, 
    project_root: Path, 
    all_exported_symbols: Set[str],
    stub_template_str: str 
) -> str:
    """Generates the content string for the .pyi file."""
    
    if not all_exported_symbols:
        return ""

    sorted_symbols = sorted(list(all_exported_symbols))
    
    symbol_declarations = "\n".join(
        f"{symbol}: Any" for symbol in sorted_symbols
    )
    
    all_list_repr = repr(sorted_symbols)
    
    rel_path = init_path.relative_to(project_root).as_posix()
    module_name = init_path.parent.name
    
    return stub_template_str.format(
        rel_path=f"{rel_path}i", 
        module_name=module_name,
        symbol_declarations=symbol_declarations,
        all_list_repr=all_list_repr
    )

# --- MAIN ORCHESTRATOR ---
def process_stubgen_logic(
    logger: logging.Logger, 
    scan_root: Path,
    cli_config: Dict[str, Optional[str]], 
    file_config: Dict[str, Any],        
    script_file_path: Path
) -> List[StubResult]:
    """
    Orchestrates the stub generation process (No I/O).
    1. Loads template
    2. Merges configs
    3. Loads (finds files)
    4. Parses (analyzes AST)
    5. Formats (generates content)
    """
    
    try:
        template_path = MODULE_DIR / TEMPLATE_FILENAME
        stub_template_str = load_text_template(template_path, logger)
    except Exception as e:
        logger.error(f"❌ Không thể tải PYI template: {e}")
        raise

    # --- 2. Merge Configs ---
    final_ignore_set = resolve_config_list(
        cli_str_value=cli_config.get('ignore'),
        file_list_value=file_config.get('ignore'),
        default_set_value=DEFAULT_IGNORE
    )
    
    cli_restrict_str = cli_config.get('restrict')
    final_restrict_list: List[str]
    if cli_restrict_str is not None:
        final_restrict_list = list(parse_comma_list(cli_restrict_str))
        logger.debug("Sử dụng danh sách 'restrict' từ CLI.")
    elif file_config.get('restrict') is not None:
        final_restrict_list = file_config['restrict']
        logger.debug("Sử dụng danh sách 'restrict' từ file config.")
    else:
        # --- MODIFIED: Sử dụng tên mới ---
        final_restrict_list = DEFAULT_RESTRICT 
        logger.debug("Sử dụng danh sách 'restrict' (DEFAULT_RESTRICT) mặc định.")
        # --- END MODIFIED ---

    final_indicators = resolve_config_value(
        cli_value=None, 
        file_value=file_config.get('dynamic_import_indicators'),
        default_value=DYNAMIC_IMPORT_INDICATORS
    )
    final_module_list_name = resolve_config_value(
        cli_value=None,
        file_value=file_config.get('ast_module_list_name'),
        default_value=AST_MODULE_LIST_NAME
    )
    final_all_list_name = resolve_config_value(
        cli_value=None,
        file_value=file_config.get('ast_all_list_name'),
        default_value=AST_ALL_LIST_NAME
    )
    # --- Kết thúc Merge Configs ---

    # 3. Load: Tìm file gateway (I/O)
    gateway_files = find_gateway_files(
        logger=logger, 
        scan_root=scan_root,
        ignore_set=final_ignore_set,
        restrict_list=final_restrict_list,
        dynamic_import_indicators=final_indicators,
        script_file_path=script_file_path
    )
    
    if not gateway_files:
        return []
        
    results: List[StubResult] = []
    logger.info(f"✅ Found {len(gateway_files)} dynamic gateways to process.")

    for init_file in gateway_files:
        
        # 4. Parse (AST)
        submodule_stems = extract_module_list(
            init_file, 
            ast_module_list_name=final_module_list_name
        )
        exported_symbols = collect_all_exported_symbols(
            init_file, 
            submodule_stems, 
            ast_all_list_name=final_all_list_name
        )
        
        if not exported_symbols:
            logger.warning(f"Skipping {init_file.name}: No exported symbols found.")
            continue

        # 5. Format
        stub_content = _format_stub_content(
            init_file, 
            scan_root, 
            exported_symbols,
            stub_template_str 
        )

        stub_path = init_file.with_suffix(".pyi")
        
        # 6. Collate Pure Result
        results.append({
            "init_path": init_file,
            "stub_path": stub_path,
            "content": stub_content,
            "symbols_count": len(exported_symbols),
            "rel_path": stub_path.relative_to(scan_root).as_posix()
        })
        
    return results