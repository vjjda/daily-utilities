# Path: modules/stubgen/stubgen_core.py
"""
Core logic for the Stub Generator (sgen) module.
Handles Orchestration (Pure Logic).
"""

import logging
import ast
import argparse
from pathlib import Path
# SỬA: Import thêm Tuple
from typing import Dict, Any, List, Optional, Set, Tuple

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pathspec

# Import các thành phần của module
from .stubgen_parser import (
    extract_module_list,
    collect_all_exported_symbols
)
from .stubgen_loader import find_gateway_files, load_config_files
from .stubgen_merger import merge_stubgen_configs
from .stubgen_formatter import format_stub_content
# SỬA: Import hàm báo cáo từ executor
from .stubgen_executor import classify_and_report_stub_changes

# Import tiện ích chung
from utils.core import (
    load_text_template,
    compile_spec_from_patterns
)

MODULE_DIR = Path(__file__).parent
TEMPLATE_FILENAME = "pyi.py.template"

StubResult = Dict[str, Any]

__all__ = ["process_stubgen_logic"]


def process_stubgen_logic(
    logger: logging.Logger, 
    cli_args: argparse.Namespace,
    script_file_path: Path,
    files_to_process: List[Path],
    dirs_to_scan: List[Path]
) -> Tuple[List[StubResult], List[StubResult]]: # SỬA: Kiểu trả về
    """
    Điều phối toàn bộ quá trình tạo stub (Logic thuần túy, không I/O ghi).
    Xử lý các file và thư mục đầu vào theo logic cục bộ.
    
    Returns:
        Tuple[List[StubResult], List[StubResult]]:
            - all_files_to_create
            - all_files_to_overwrite
    """
    
    # 1. Load Template
    try:
        template_path = MODULE_DIR / TEMPLATE_FILENAME
        stub_template_str = load_text_template(template_path, logger)
    except Exception as e:
        logger.error(f"❌ Không thể tải PYI template: {e}")
        raise

    # SỬA: Khởi tạo các list tổng
    total_files_to_create: List[StubResult] = []
    total_files_to_overwrite: List[StubResult] = []
    
    processed_files: Set[Path] = set()
    reporting_root = Path.cwd() # Dùng để tính rel_path

    # --- 2. XỬ LÝ CÁC FILE RIÊNG LẺ ---
    if files_to_process:
        logger.info(f"--- 📄 Đang xử lý {len(files_to_process)} file riêng lẻ ---")
        
        file_config_data = {} 
        cli_config = {
            "ignore": getattr(cli_args, 'ignore', None),
            "include": getattr(cli_args, 'include', None)
        }
        merged_config = merge_stubgen_configs(logger, cli_config, file_config_data)

        file_raw_results: List[StubResult] = [] # Thu thập kết quả thô
        for file_path in files_to_process:
            resolved_file = file_path.resolve()
            if resolved_file in processed_files:
                continue
                
            if file_path.name != "__init__.py":
                logger.warning(f"⚠️ Bỏ qua file '{file_path.name}': 'sgen' chỉ xử lý file '__init__.py'.")
                continue
                
            scan_dir = file_path.parent 
            
            logger.info(f"  -> ⚡ Phân tích file: {file_path.relative_to(reporting_root).as_posix()}")
            
            stub_content, symbols_count = _process_single_gateway(
                init_file=file_path,
                scan_root=scan_dir, # Dùng thư mục cha làm gốc
                merged_config=merged_config,
                stub_template_str=stub_template_str,
                logger=logger
            )
            
            if stub_content:
                stub_path = file_path.with_suffix(".pyi")
                file_raw_results.append({
                    "init_path": file_path,
                    "stub_path": stub_path,
                    "content": stub_content,
                    "symbols_count": symbols_count,
                    "rel_path": stub_path.relative_to(reporting_root).as_posix()
                })
            processed_files.add(resolved_file)

        # SỬA: Phân loại và Báo cáo cho nhóm file
        if file_raw_results:
            create, overwrite, _ = classify_and_report_stub_changes(
                logger, "Files Lẻ", file_raw_results, reporting_root
            )
            total_files_to_create.extend(create)
            total_files_to_overwrite.extend(overwrite)
        
        logger.info("") # Dòng trống

    # --- 3. XỬ LÝ CÁC THƯ MỤC ---
    if dirs_to_scan:
        logger.info(f"Đang xử lý {len(dirs_to_scan)} thư mục...")

    for scan_dir in dirs_to_scan:
        logger.info(f"--- 📁 Quét thư mục: {scan_dir.name} ---")
        
        # 3a. Tải/Merge Config
        file_config = load_config_files(scan_dir, logger)
        cli_config = {
            "ignore": getattr(cli_args, 'ignore', None),
            "include": getattr(cli_args, 'include', None)
        }
        merged_config = merge_stubgen_configs(logger, cli_config, file_config)

        # 3b. Biên dịch Specs
        final_include_spec: Optional['pathspec.PathSpec'] = compile_spec_from_patterns(
            merged_config["include_list"], 
            scan_dir
        )
        
        # 3c. Load: Tìm file gateway
        gateway_files, scan_status = find_gateway_files(
            logger=logger, 
            scan_root=scan_dir,
            ignore_list=merged_config["ignore_list"], 
            include_spec=final_include_spec,
            dynamic_import_indicators=merged_config["indicators"],
            script_file_path=script_file_path
        )
        
        # 3d. In báo cáo cấu hình
        logger.info(f"  [Cấu hình áp dụng]")
        logger.info(f"    - Ignore (từ config/CLI): {merged_config['ignore_list']}")
        logger.info(f"    - Include (từ config/CLI): {merged_config['include_list']}")
        logger.info(f"    - Tải .gitignore cục bộ: {'Có' if scan_status['gitignore_found'] else 'Không'}")
        logger.info(f"    - Tải .gitmodules cục bộ: {'Có' if scan_status['gitmodules_found'] else 'Không'}")
        
        if not gateway_files:
            logger.info(f"  -> 🤷 Không tìm thấy file '__init__.py' (gateway động) nào khớp tiêu chí.")
            logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
            logger.info("")
            continue
        
        logger.info(f"  -> ⚡ Tìm thấy {len(gateway_files)} gateway, đang phân tích...")
        
        dir_raw_results: List[StubResult] = [] # Thu thập kết quả thô
        for init_file in gateway_files:
            resolved_file = init_file.resolve()
            if resolved_file in processed_files:
                continue

            # 3e. Phân tích & Định dạng
            stub_content, symbols_count = _process_single_gateway(
                init_file=init_file,
                scan_root=scan_dir, 
                merged_config=merged_config,
                stub_template_str=stub_template_str,
                logger=logger
            )
            
            if stub_content:
                stub_path = init_file.with_suffix(".pyi")
                dir_raw_results.append({
                    "init_path": init_file,
                    "stub_path": stub_path,
                    "content": stub_content,
                    "symbols_count": symbols_count,
                    "rel_path": stub_path.relative_to(reporting_root).as_posix()
                })
            processed_files.add(resolved_file)
        
        # SỬA: Phân loại và Báo cáo cho nhóm thư mục
        if dir_raw_results:
            create, overwrite, _ = classify_and_report_stub_changes(
                logger, scan_dir.name, dir_raw_results, reporting_root
            )
            total_files_to_create.extend(create)
            total_files_to_overwrite.extend(overwrite)
            
        logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
        logger.info("")

    # SỬA: Trả về 2 list tổng
    return total_files_to_create, total_files_to_overwrite


def _process_single_gateway(
    init_file: Path,
    scan_root: Path,
    merged_config: Dict[str, Any],
    stub_template_str: str,
    logger: logging.Logger
) -> Tuple[Optional[str], int]:
    """Hàm helper nội bộ để chạy logic Parse/Format cho một file gateway."""
    
    try:
        # 7. Parse (AST)
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

        # 8. Format (gọi Formatter)
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