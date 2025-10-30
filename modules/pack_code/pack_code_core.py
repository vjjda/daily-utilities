# Path: modules/pack_code/pack_code_core.py
"""
Logic cốt lõi cho pack_code (Orchestrator).
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

# SỬA: Import các hàm Task đã đổi tên
from .pack_code_internal import (
    process_pack_code_task_file,
    process_pack_code_task_dir,
    generate_tree_string,
    load_config_files, 
    resolve_output_path,
    assemble_packed_content
)

__all__ = ["process_pack_code_logic"] 

FileResult = Dict[str, Any] # Type alias

def process_pack_code_logic(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    files_to_process: List[Path],
    dirs_to_scan: List[Path],
    reporting_root: Optional[Path], # Gốc báo cáo (Tổ tiên chung)
    script_file_path: Path
) -> Dict[str, Any]:
    """
    Hàm logic chính (Orchestrator) cho pack_code.
    Điều phối việc quét, đọc, làm sạch và đóng gói nội dung.
    """
    logger.info("Đang chạy logic cốt lõi...") 

    try:
        all_file_results: List[FileResult] = []
        processed_files: Set[Path] = set() # Tránh xử lý trùng lặp

        # 1. XỬ LÝ CÁC FILE RIÊNG LẺ
        if files_to_process:
            for file_path in files_to_process:
                # SỬA: Gọi hàm task đã đổi tên
                results = process_pack_code_task_file(
                    file_path=file_path,
                    cli_args=cli_args,
                    logger=logger,
                    processed_files=processed_files,
                    reporting_root=reporting_root,
                    script_file_path=script_file_path
                )
                all_file_results.extend(results)

        # 2. XỬ LÝ CÁC THƯ MỤC
        if dirs_to_scan:
            logger.info(f"Đang xử lý {len(dirs_to_scan)} thư mục...")
            for scan_dir in dirs_to_scan:
                # SỬA: Gọi hàm task đã đổi tên
                results = process_pack_code_task_dir(
                    scan_dir=scan_dir,
                    cli_args=cli_args,
                    logger=logger,
                    processed_files=processed_files,
                    reporting_root=reporting_root,
                    script_file_path=script_file_path
                )
                all_file_results.extend(results)

        # --- 3. GIAI ĐOẠN "BUILD" (SAU KHI THU THẬP) ---
        
        if not all_file_results: 
            logger.warning("Không tìm thấy file nào khớp với tiêu chí.") 
            return {'status': 'empty'} 
            
        logger.info(f"Tổng cộng tìm thấy {len(all_file_results)} file để đóng gói.")

        dry_run: bool = cli_args.get("dry_run", False) 
        no_tree: bool = cli_args.get("no_tree", False) 

        # 4. Tạo cây thư mục (từ kết quả tổng)
        tree_str = "" 
        if not no_tree: 
            logger.debug("Đang tạo cây thư mục...") 
            tree_str = generate_tree_string(all_file_results, reporting_root) 

        # 5. Ghép nối nội dung cuối cùng
        final_content = assemble_packed_content(
            all_file_results=all_file_results,
            tree_str=tree_str,
            no_header=cli_args.get("no_header", False),
            dry_run=dry_run,
        ) 

        # 6. Xác định đường dẫn file output
        config_load_dir = reporting_root if reporting_root else Path.cwd() 
        file_config = load_config_files(config_load_dir, logger) 
        
        final_output_path = resolve_output_path(
            logger, cli_args, file_config, reporting_root
        ) 

        # 7. Trả về Result Object cho Executor
        return { 
            'status': 'ok',
            'final_content': final_content,
            'output_path': final_output_path,
            'stdout': cli_args.get("stdout", False),
            'dry_run': dry_run,
            'copy_to_clipboard': cli_args.get("copy_to_clipboard", False),
            'file_list_relative': [r["rel_path"] for r in all_file_results],
            'scan_root': reporting_root if reporting_root else Path.cwd(), 
            'tree_string': tree_str,
            'no_tree': no_tree
        } 

    except FileNotFoundError as e: 
        logger.error(f"❌ {e}") 
        return {'status': 'error', 'message': str(e)} 
    except Exception as e: 
        logger.error(f"Lỗi không mong muốn trong logic cốt lõi pack_code: {e}") 
        logger.debug("Traceback:", exc_info=True) 
        return {'status': 'error', 'message': f"Lỗi không mong muốn: {e}"} 