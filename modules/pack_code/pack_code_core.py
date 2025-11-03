# Path: modules/pack_code/pack_code_core.py
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import sys


from .pack_code_internal import (
    process_pack_code_task_file,
    process_pack_code_task_dir,
    generate_tree_string,
    load_config_files,
    resolve_output_path,
    assemble_packed_content,
)

from .pack_code_executor import execute_pack_code_action
from utils.cli import (
    resolve_input_paths,
    resolve_reporting_root,
)
from .pack_code_config import DEFAULT_START_PATH


__all__ = ["process_pack_code_logic", "run_pack_code"]

FileResult = Dict[str, Any]


def run_pack_code(
    logger: logging.Logger, cli_args: argparse.Namespace, this_script_path: Path
) -> None:

    validated_paths: List[Path] = resolve_input_paths(
        logger=logger,
        raw_paths=cli_args.start_paths_arg,
        default_path_str=DEFAULT_START_PATH,
    )

    if not validated_paths:
        logger.warning("Không tìm thấy đường dẫn hợp lệ nào để quét. Đã dừng.")
        sys.exit(0)

    reporting_root = resolve_reporting_root(logger, validated_paths, cli_root_arg=None)

    try:
        cli_args_dict = vars(cli_args)

        results_from_core = process_pack_code_logic(
            logger=logger,
            cli_args=cli_args_dict,
            validated_paths=validated_paths,
            reporting_root=reporting_root,
            script_file_path=this_script_path,
        )

        execute_pack_code_action(logger=logger, result=results_from_core)

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn trong 'run_pack_code': {e}")
        logger.debug("Traceback:", exc_info=True)
        raise


def process_pack_code_logic(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    validated_paths: List[Path],
    reporting_root: Optional[Path],
    script_file_path: Path,
) -> Dict[str, Any]:
    logger.info("Đang chạy logic cốt lõi...")

    try:
        all_file_results: List[FileResult] = []
        processed_files: Set[Path] = set()

        files_to_process: List[Path] = [p for p in validated_paths if p.is_file()]
        dirs_to_scan: List[Path] = [p for p in validated_paths if p.is_dir()]

        format_flag: bool = cli_args.get("format", False)
        if format_flag:
            logger.info(
                "⚡ Chế độ FORMAT (-f) đã bật: Nội dung file sẽ được định dạng."
            )

        if files_to_process:
            for file_path in files_to_process:
                results = process_pack_code_task_file(
                    file_path=file_path,
                    cli_args=cli_args,
                    logger=logger,
                    processed_files=processed_files,
                    reporting_root=reporting_root,
                    script_file_path=script_file_path,
                )
                all_file_results.extend(results)

        if dirs_to_scan:
            logger.info(f"Đang xử lý {len(dirs_to_scan)} thư mục...")
            for scan_dir in dirs_to_scan:
                results = process_pack_code_task_dir(
                    scan_dir=scan_dir,
                    cli_args=cli_args,
                    logger=logger,
                    processed_files=processed_files,
                    reporting_root=reporting_root,
                    script_file_path=script_file_path,
                )
                all_file_results.extend(results)

        if not all_file_results:
            logger.warning("Không tìm thấy file nào khớp với tiêu chí.")
            return {"status": "empty"}

        logger.info(f"Tổng cộng tìm thấy {len(all_file_results)} file để đóng gói.")

        dry_run: bool = cli_args.get("dry_run", False)
        no_tree: bool = cli_args.get("no_tree", False)

        tree_str = ""
        if not no_tree:
            logger.debug("Đang tạo cây thư mục...")
            tree_str = generate_tree_string(all_file_results, reporting_root)

        final_content = assemble_packed_content(
            all_file_results=all_file_results,
            tree_str=tree_str,
            no_header=cli_args.get("no_header", False),
            dry_run=dry_run,
        )

        config_load_dir = reporting_root if reporting_root else Path.cwd()
        file_config = load_config_files(config_load_dir, logger)

        final_output_path = resolve_output_path(
            logger, cli_args, file_config, reporting_root
        )

        return {
            "status": "ok",
            "final_content": final_content,
            "output_path": final_output_path,
            "stdout": cli_args.get("stdout", False),
            "dry_run": dry_run,
            "copy_to_clipboard": cli_args.get("copy_to_clipboard", False),
            "file_list_relative": [r["rel_path"] for r in all_file_results],
            "scan_root": reporting_root if reporting_root else Path.cwd(),
            "tree_string": tree_str,
            "no_tree": no_tree,
        }

    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"Lỗi không mong muốn trong logic cốt lõi pack_code: {e}")
        logger.debug("Traceback:", exc_info=True)
        return {"status": "error", "message": f"Lỗi không mong muốn: {e}"}
