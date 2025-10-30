# Path: modules/stubgen/stubgen_internal/gateway_processor.py
"""
(Internal Worker)
Processes a single __init__.py gateway file.
Runs AST parsing and formatting.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

# Import các worker nội bộ khác (thông qua facade)
from . import (
    extract_module_list,
    collect_all_exported_symbols,
    format_stub_content
)

__all__ = ["process_single_gateway"]

def process_single_gateway(
    init_file: Path,
    scan_root: Path,
    merged_config: Dict[str, Any],
    stub_template_str: str,
    logger: logging.Logger
) -> Tuple[Optional[str], int]:
    """
    Chạy logic Parse/Format cho một file gateway duy nhất.
    """
    
    try:
        # 1. Parse (AST)
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
            # (Không log warning ở đây, để hàm gọi quyết định)
            return None, 0

        # 2. Format (gọi Formatter)
        stub_content = format_stub_content(
            init_file, 
            scan_root, # Gốc cục bộ
            exported_symbols,
            stub_template_str 
        )
        return stub_content, len(exported_symbols)
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi xử lý file {init_file.name}: {e}")
        return None, 0