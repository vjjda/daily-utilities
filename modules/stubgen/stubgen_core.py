# Path: modules/stubgen/stubgen_core.py
"""
Core logic for the Stub Generator (sgen) module.
Handles Orchestration (Pure Logic).
"""

import logging
import ast
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pathspec

# SỬA: Import từ facade nội bộ '.stubgen_internal'
from .stubgen_internal import (
    extract_module_list,
    collect_all_exported_symbols,
    find_gateway_files, 
    load_config_files,
    merge_stubgen_configs,
    format_stub_content
)

# Import các thành phần còn lại
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

# ... (Toàn bộ phần còn lại của file _process_single_gateway,
# _process_stubgen_task_file, _process_stubgen_task_dir,
# và process_stubgen_logic không thay đổi) ...

def _process_single_gateway(
    init_file: Path,
    scan_root: Path,
    merged_config: Dict[str, Any],
    stub_template_str: str,
    logger: logging.Logger
) -> Tuple[Optional[str], int]:
    """
    (HELPER 1)
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


def _process_stubgen_task_file(
    file_path: Path,
    cli_args: argparse.Namespace,
    stub_template_str: str,
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path
) -> Tuple[List[StubResult], List[StubResult]]:
    """
    (HELPER 2)
    Xử lý logic sgen cho một file __init__.py riêng lẻ.
    """
    logger.info(f"--- 📄 Đang xử lý file: {file_path.relative_to(reporting_root).as_posix()} ---")
    
    resolved_file = file_path.resolve()
    if resolved_file in processed_files:
        logger.info("   -> Bỏ qua (đã xử lý).")
        logger.info("")
        return [], []
        
    if file_path.name != "__init__.py":
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}': 'sgen' chỉ xử lý file '__init__.py'.")
        logger.info("")
        return [], []

    # 2. Hợp nhất Config (Default + CLI)
    file_config_data = {} 
    cli_config = {
        "ignore": getattr(cli_args, 'ignore', None),
        "include": getattr(cli_args, 'include', None)
    }
    merged_config = merge_stubgen_configs(logger, cli_config, file_config_data)
    scan_dir = file_path.parent
    
    logger.info(f"  [Cấu hình áp dụng]")
    logger.info(f"    - Ignore (từ config/CLI): {merged_config['ignore_list']}")
    logger.info(f"    - Include (từ config/CLI): {merged_config['include_list']}")
    logger.info(f"    - (Bỏ qua .gitignore và config file)")

    # 3. Phân tích & Định dạng
    stub_content, symbols_count = _process_single_gateway(
        init_file=file_path,
        scan_root=scan_dir,
        merged_config=merged_config,
        stub_template_str=stub_template_str,
        logger=logger
    )
    
    processed_files.add(resolved_file)
    file_raw_results: List[StubResult] = []
    
    if stub_content:
        stub_path = file_path.with_suffix(".pyi")
        file_raw_results.append({
            "init_path": file_path,
            "stub_path": stub_path,
            "content": stub_content,
            "symbols_count": symbols_count,
            "rel_path": stub_path.relative_to(reporting_root).as_posix()
        })
    else:
        logger.warning(f"  -> 🤷 Không tìm thấy symbols nào trong: {file_path.name}")

    # 4. Phân loại và Báo cáo
    create, overwrite, _ = classify_and_report_stub_changes(
        logger, file_path.name, file_raw_results, reporting_root
    )
    logger.info("")
    
    return create, overwrite


def _process_stubgen_task_dir(
    scan_dir: Path,
    cli_args: argparse.Namespace,
    stub_template_str: str,
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path,
    script_file_path: Path
) -> Tuple[List[StubResult], List[StubResult]]:
    """
    (HELPER 3)
    Xử lý logic sgen cho một thư mục đầu vào.
    """
    logger.info(f"--- 📁 Quét thư mục: {scan_dir.name} ---")
    
    # 1. Tải/Merge Config (cục bộ)
    file_config = load_config_files(scan_dir, logger)
    cli_config = {
        "ignore": getattr(cli_args, 'ignore', None),
        "include": getattr(cli_args, 'include', None)
    }
    merged_config = merge_stubgen_configs(logger, cli_config, file_config)

    # 2. Biên dịch Specs
    final_include_spec: Optional['pathspec.PathSpec'] = compile_spec_from_patterns(
        merged_config["include_list"], 
        scan_dir
    )
    
    # 3. Load: Tìm file gateway
    gateway_files, scan_status = find_gateway_files(
        logger=logger, 
        scan_root=scan_dir,
        ignore_list=merged_config["ignore_list"], 
        include_spec=final_include_spec,
        dynamic_import_indicators=merged_config["indicators"],
        script_file_path=script_file_path
    )
    
    # 4. In báo cáo cấu hình
    logger.info(f"  [Cấu hình áp dụng]")
    logger.info(f"    - Ignore (từ config/CLI): {merged_config['ignore_list']}")
    logger.info(f"    - Include (từ config/CLI): {merged_config['include_list']}")
    logger.info(f"    - Tải .gitignore cục bộ: {'Có' if scan_status['gitignore_found'] else 'Không'}")
    logger.info(f"    - Tải .gitmodules cục bộ: {'Có' if scan_status['gitmodules_found'] else 'Không'}")
    
    if not gateway_files:
        logger.info(f"  -> 🤷 Không tìm thấy file '__init__.py' (gateway động) nào khớp tiêu chí.")
        logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
        logger.info("")
        return [], []
    
    logger.info(f"  -> ⚡ Tìm thấy {len(gateway_files)} gateway, đang phân tích...")
    
    # 5. Phân tích & Định dạng
    dir_raw_results: List[StubResult] = []
    for init_file in gateway_files:
        resolved_file = init_file.resolve()
        if resolved_file in processed_files:
            continue

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
    
    # 6. Phân loại và Báo cáo
    create, overwrite, _ = classify_and_report_stub_changes(
        logger, scan_dir.name, dir_raw_results, reporting_root
    )
        
    logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
    logger.info("")
    
    return create, overwrite


def process_stubgen_logic(
    logger: logging.Logger, 
    cli_args: argparse.Namespace,
    script_file_path: Path,
    files_to_process: List[Path],
    dirs_to_scan: List[Path]
) -> Tuple[List[StubResult], List[StubResult]]:
    """
    Điều phối toàn bộ quá trình tạo stub (Logic thuần túy, không I/O ghi).
    Xử lý các file và thư mục đầu vào theo logic cục bộ.
    
    Returns:
        Tuple[List[StubResult], List[StubResult]]:
            - all_files_to_create
            - all_files_to_overwrite
    """
    
    # 1. Load Template (một lần)
    try:
        template_path = MODULE_DIR / TEMPLATE_FILENAME
        stub_template_str = load_text_template(template_path, logger)
    except Exception as e:
        logger.error(f"❌ Không thể tải PYI template: {e}")
        raise

    total_files_to_create: List[StubResult] = []
    total_files_to_overwrite: List[StubResult] = []
    processed_files: Set[Path] = set()
    reporting_root = Path.cwd()

    # 2. XỬ LÝ CÁC FILE RIÊNG LẺ
    if files_to_process:
        for file_path in files_to_process:
            create, overwrite = _process_stubgen_task_file(
                file_path=file_path,
                cli_args=cli_args,
                stub_template_str=stub_template_str,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root
            )
            total_files_to_create.extend(create)
            total_files_to_overwrite.extend(overwrite)

    # 3. XỬ LÝ CÁC THƯ MỤC
    if dirs_to_scan:
        logger.info(f"Đang xử lý {len(dirs_to_scan)} thư mục...")
        for scan_dir in dirs_to_scan:
            create, overwrite = _process_stubgen_task_dir(
                scan_dir=scan_dir,
                cli_args=cli_args,
                stub_template_str=stub_template_str,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root,
                script_file_path=script_file_path
            )
            total_files_to_create.extend(create)
            total_files_to_overwrite.extend(overwrite)

    return total_files_to_create, total_files_to_overwrite