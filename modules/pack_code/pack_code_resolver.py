# Path: modules/pack_code/pack_code_resolver.py
"""
Logic for resolving paths and filters for pack_code.
(Internal module, imported by pack_code_core)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING, Iterable, Tuple

if TYPE_CHECKING:
    import pathspec

from utils.core import (
    find_git_root,
    parse_gitignore,
    compile_spec_from_patterns,
    resolve_set_modification,
    get_submodule_paths,
    parse_comma_list,
    resolve_config_list,
    resolve_config_value
)

from .pack_code_config import (
    DEFAULT_EXTENSIONS, DEFAULT_IGNORE, DEFAULT_START_PATH,
    DEFAULT_OUTPUT_DIR
)

__all__ = ["resolve_start_and_scan_paths", "resolve_filters", "resolve_output_path"]


def resolve_start_and_scan_paths(
    logger: logging.Logger,
    start_path_from_cli: Optional[Path],
) -> Tuple[Path, Path]:
    """
    Xác định đường dẫn bắt đầu quét (`start_path`) và gốc quét (`scan_root`).
    `scan_root` thường là gốc Git hoặc thư mục cha gần nhất.

    Args:
        logger: Logger.
        start_path_from_cli: Đường dẫn từ CLI (đã resolve, có thể là None).

    Returns:
        Tuple[Path, Path]: (start_path, scan_root) đã được resolve.

    Raises:
        FileNotFoundError: Nếu `start_path` cuối cùng không tồn tại.
    """

    # 1. Xác định Start Path
    start_path: Path
    if start_path_from_cli:
        start_path = start_path_from_cli
        logger.debug(f"Sử dụng start path từ CLI: {start_path.as_posix()}")
    else:
        # Nếu CLI không cung cấp, dùng default (thường là '.')
        start_path = Path(DEFAULT_START_PATH).expanduser().resolve()
        logger.debug(f"Sử dụng start path mặc định: {start_path.as_posix()}")

    # 2. Xác định Scan Root
    scan_root: Path
    if start_path.is_file():
        # Nếu bắt đầu từ file, scan_root là gốc Git của thư mục chứa file,
        # hoặc chính thư mục chứa file nếu không có Git.
        scan_root = find_git_root(start_path.parent) or start_path.parent
    else: # start_path là thư mục (hoặc không tồn tại)
        # Nếu thư mục tồn tại, tìm gốc Git từ nó.
        # Nếu không tồn tại, tìm gốc Git từ thư mục làm việc hiện tại (CWD).
        effective_start_dir = start_path if start_path.exists() else Path.cwd().resolve()
        scan_root = find_git_root(effective_start_dir) or effective_start_dir

    # 3. Validation cuối cùng
    if not start_path.exists():
         logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path.as_posix()}")
         raise FileNotFoundError(f"Start path not found: {start_path.as_posix()}") #

    logger.debug(f"Scan Root (cho quy tắc .gitignore): {scan_root.as_posix()}")
    logger.debug(f"Start Path (nơi bắt đầu quét): {start_path.as_posix()}")

    return start_path, scan_root


def resolve_filters(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    scan_root: Path,
) -> Tuple[Set[str], Optional['pathspec.PathSpec'], Set[Path]]:
    """
    Hợp nhất các cấu hình filter (extensions, ignore, submodules).

    Args:
        logger: Logger.
        cli_args: Dict chứa các đối số CLI đã xử lý (ví dụ: extensions là string).
        file_config: Dict cấu hình [pcode] đã load từ file.
        scan_root: Thư mục gốc quét (để tìm .gitignore và submodule).

    Returns:
        Tuple[Set[str], Optional['pathspec.PathSpec'], Set[Path]]:
            - ext_filter_set: Set các đuôi file được phép.
            - ignore_spec: PathSpec đã biên dịch cho ignore.
            - submodule_paths: Set các đường dẫn tuyệt đối đến submodule.
    """

    # 1. Hợp nhất Extensions (hỗ trợ +/-/~)
    file_ext_list = file_config.get('extensions') # Có thể là List hoặc None
    default_ext_set = parse_comma_list(DEFAULT_EXTENSIONS)

    tentative_extensions: Set[str]
    if file_ext_list is not None:
        tentative_extensions = set(file_ext_list)
        logger.debug("Sử dụng 'extensions' từ file config làm cơ sở.")
    else:
        tentative_extensions = default_ext_set
        logger.debug("Sử dụng 'extensions' mặc định làm cơ sở.")

    ext_filter_set = resolve_set_modification(
        tentative_extensions, cli_args.get("extensions") # cli_args["extensions"] là string
    )
    logger.debug(f"Set 'extensions' cuối cùng: {sorted(list(ext_filter_set))}")

    # 2. Hợp nhất Ignore (File GHI ĐÈ Default) + (CLI NỐI VÀO) + (.gitignore)
    default_ignore_set = parse_comma_list(DEFAULT_IGNORE)

    # Bước 2a: Hợp nhất Config và CLI
    config_cli_ignore_list = resolve_config_list(
        cli_str_value=cli_args.get("ignore"), # cli_args["ignore"] là string
        file_list_value=file_config.get('ignore'), # file_config['ignore'] là List[str]
        default_set_value=default_ignore_set
    )

    # Bước 2b: Thêm .gitignore (nếu không có --no-gitignore)
    gitignore_patterns: List[str] = []
    if not cli_args.get("no_gitignore", False):
        gitignore_patterns = parse_gitignore(scan_root)
        if gitignore_patterns:
             logger.debug(f"Đã tải {len(gitignore_patterns)} quy tắc từ .gitignore")
        else:
             logger.debug("Không tìm thấy .gitignore hoặc không thể đọc.")
    else:
        logger.info("Bỏ qua .gitignore do cờ --no-gitignore.")

    # Bước 2c: Biên dịch thành PathSpec
    all_ignore_patterns_list: List[str] = config_cli_ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)
    logger.debug(f"Tổng cộng {len(all_ignore_patterns_list)} quy tắc ignore đã biên dịch.")

    # 3. Lấy đường dẫn Submodules
    submodule_paths = get_submodule_paths(scan_root, logger)
    if submodule_paths:
        logger.debug(f"Tìm thấy {len(submodule_paths)} submodule(s). Sẽ bỏ qua nội dung của chúng.")

    return ext_filter_set, ignore_spec, submodule_paths


def resolve_output_path(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    start_path: Path,
) -> Optional[Path]:
    """
    Xác định đường dẫn output cuối cùng.
    Trả về None nếu là stdout hoặc dry_run.

    Ưu tiên:
    1. CLI (--output)
    2. Mặc định: `[output_dir]/<start_name>_context.txt`
       - `output_dir` lấy từ File Config hoặc Default (`~/Documents/code.context`).
       - `start_name` lấy từ `start_path`.

    Lưu ý: Hàm này **không** thực hiện `expanduser()` hoặc `resolve()`.
           Đó là trách nhiệm của Executor.

    Args:
        logger: Logger.
        cli_args: Dict các đối số CLI đã xử lý.
        file_config: Dict cấu hình [pcode] đã load từ file.
        start_path: Đường dẫn bắt đầu quét (để lấy tên file mặc định).

    Returns:
        Path object đến file output, hoặc None.
    """
    if cli_args.get("stdout", False) or cli_args.get("dry_run", False):
        return None # Không cần path nếu in ra stdout hoặc dry run

    # 1. Ưu tiên CLI
    output_path_from_cli: Optional[Path] = cli_args.get("output")
    if output_path_from_cli:
        logger.debug(f"Sử dụng đường dẫn output từ CLI: {output_path_from_cli.as_posix()}")
        return output_path_from_cli

    # 2. Xây dựng đường dẫn mặc định
    # 2a. Xác định thư mục output mặc định (File > Default)
    default_output_dir_str = resolve_config_value(
        cli_value=None, # CLI đã được xử lý ở trên
        file_value=file_config.get("output_dir"),
        default_value=DEFAULT_OUTPUT_DIR
    )
    default_output_dir_path = Path(default_output_dir_str) # Chưa expanduser

    # 2b. Tính toán tên file
    start_name = start_path.stem if start_path.is_file() else start_path.name
    final_output_path = default_output_dir_path / f"{start_name}_context.txt"

    logger.debug(f"Sử dụng đường dẫn output mặc định (chưa expand): {final_output_path.as_posix()}")
    return final_output_path