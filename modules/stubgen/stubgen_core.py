# Path: modules/stubgen/stubgen_core.py

"""
Core logic for the Stub Generator (sgen) module.
Handles Orchestration (Pure Logic).
(Config logic is in stubgen_merger.py)
(Formatting logic is in stubgen_formatter.py)
(AST Parsing logic is in stubgen_parser.py)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

# --- MODIFIED: Import pathspec (cho type checking) ---
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pathspec
# --- END MODIFIED ---

# --- MODIFIED: Import các module SRP mới ---
from .stubgen_parser import (
    extract_module_list,
    collect_all_exported_symbols
)
from .stubgen_loader import find_gateway_files
from .stubgen_merger import merge_stubgen_configs
from .stubgen_formatter import format_stub_content
# --- END MODIFIED ---

# --- MODIFIED: Import utils tối giản ---
from utils.core import (
    load_text_template,
    compile_spec_from_patterns
)
# --- END MODIFIED ---

# (Config imports không cần nữa, đã chuyển sang merger.py)

MODULE_DIR = Path(__file__).parent
TEMPLATE_FILENAME = "pyi.py.template"

StubResult = Dict[str, Any]

__all__ = ["process_stubgen_logic"]


# --- REMOVED: _format_stub_content (đã chuyển sang formatter.py) ---
# --- REMOVED: _merge_stubgen_configs (đã chuyển sang merger.py) ---


# --- MAIN ORCHESTRATOR (Đã refactor) ---
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
    3. Compiles specs
    4. Loads (finds files)
    5. Parses (analyzes AST)
    6. Formats (generates content)
    """
    
    # 1. Load Template
    try:
        template_path = MODULE_DIR / TEMPLATE_FILENAME
        stub_template_str = load_text_template(template_path, logger)
    except Exception as e:
        logger.error(f"❌ Không thể tải PYI template: {e}")
        raise

    # 2. Merge Configs
    merged_config = merge_stubgen_configs(logger, cli_config, file_config)

    # 3. Biên dịch Specs
    final_include_spec: Optional['pathspec.PathSpec'] = compile_spec_from_patterns(
        merged_config["include_list"], 
        scan_root
    )
    
    # 4. Load: Tìm file gateway (I/O)
    gateway_files = find_gateway_files(
        logger=logger, 
        scan_root=scan_root,
        ignore_list=merged_config["ignore_list"], 
        restrict_list=merged_config["restrict_list"],
        include_spec=final_include_spec,
        dynamic_import_indicators=merged_config["indicators"],
        script_file_path=script_file_path
    )
    
    if not gateway_files:
        return []
        
    results: List[StubResult] = []
    logger.info(f"✅ Found {len(gateway_files)} dynamic gateways to process.")

    for init_file in gateway_files:
        
        # 5. Parse (AST)
        submodule_stems = extract_module_list(
            init_file, 
            ast_module_list_name=merged_config["module_list_name"]
        )
        exported_symbols = collect_all_exported_symbols(
            init_file, 
            submodule_stems, 
            ast_all_list_name=merged_config["all_list_name"]
        )
        
        if not exported_symbols:
            logger.warning(f"Skipping {init_file.name}: No exported symbols found.")
            continue

        # 6. Format
        stub_content = format_stub_content(
            init_file, 
            scan_root, 
            exported_symbols,
            stub_template_str 
        )

        stub_path = init_file.with_suffix(".pyi")
        
        # 7. Collate Pure Result
        results.append({
            "init_path": init_file,
            "stub_path": stub_path,
            "content": stub_content,
            "symbols_count": len(exported_symbols),
            "rel_path": stub_path.relative_to(scan_root).as_posix()
        })
        
    # 8. Return
    return results