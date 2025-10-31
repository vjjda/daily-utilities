# Path: modules/pack_code/pack_code_internal/pack_code_resolver.py
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
    resolve_config_value,
)

from ..pack_code_config import (
    DEFAULT_EXTENSIONS,
    DEFAULT_IGNORE,
    DEFAULT_CLEAN_EXTENSIONS,
    DEFAULT_OUTPUT_DIR,
    
    DEFAULT_FORMAT_EXTENSIONS
)

__all__ = ["resolve_filters", "resolve_output_path"]


def resolve_filters(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    scan_root: Path,
) -> Tuple[Set[str], Optional["pathspec.PathSpec"], Set[Path], Set[str], Set[str]]: 

    
    file_ext_list = file_config.get("extensions")
    default_ext_set = parse_comma_list(DEFAULT_EXTENSIONS)
    tentative_extensions: Set[str]
    if file_ext_list is not None:
        tentative_extensions = set(file_ext_list)
    else:
        tentative_extensions = default_ext_set
    ext_filter_set = resolve_set_modification(
        tentative_extensions, cli_args.get("extensions")
    )
    logger.debug(
        f"Set 'extensions' cuối cùng (để quét): {sorted(list(ext_filter_set))}"
    )

    
    default_ignore_set = parse_comma_list(DEFAULT_IGNORE)
    config_cli_ignore_list = resolve_config_list(
        cli_str_value=cli_args.get("ignore"),
        file_list_value=file_config.get("ignore"),
        default_set_value=default_ignore_set,
    )
    gitignore_patterns: List[str] = []
    if not cli_args.get("no_gitignore", False):
        gitignore_patterns = parse_gitignore(scan_root)
    
    all_ignore_patterns_list: List[str] = config_cli_ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)
    logger.debug(
        f"Tổng cộng {len(all_ignore_patterns_list)} quy tắc ignore đã biên dịch cho gốc {scan_root.name}."
    )

    
    submodule_paths = get_submodule_paths(scan_root, logger)

    
    file_clean_ext_list = file_config.get("clean_extensions")
    default_clean_ext_set = DEFAULT_CLEAN_EXTENSIONS
    tentative_clean_extensions: Set[str]
    if file_clean_ext_list is not None:
        tentative_clean_extensions = set(file_clean_ext_list)
    else:
        tentative_clean_extensions = default_clean_ext_set

    clean_extensions_set = resolve_set_modification(
        tentative_set=tentative_clean_extensions,
        cli_string=cli_args.get("clean_extensions"),
    )
    logger.debug(
        f"Set 'clean_extensions' cuối cùng (để làm sạch): {sorted(list(clean_extensions_set))}"
    )
    
    
    file_format_ext_list = file_config.get("format_extensions")
    default_format_ext_set = DEFAULT_FORMAT_EXTENSIONS
    
    format_extensions_set: Set[str]
    if file_format_ext_list is not None:
        format_extensions_set = set(file_format_ext_list)
        logger.debug("Sử dụng 'format_extensions' từ file config.")
    else:
        format_extensions_set = default_format_ext_set
        logger.debug("Sử dụng 'format_extensions' mặc định.")
        
    logger.debug(
        f"Set 'format_extensions' cuối cùng (để định dạng): {sorted(list(format_extensions_set))}"
    )

    
    return ext_filter_set, ignore_spec, submodule_paths, clean_extensions_set, format_extensions_set


def resolve_output_path(
     logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    reporting_root: Optional[Path],
) -> Optional[Path]:
    if cli_args.get("stdout", False) or cli_args.get("dry_run", False): 
        return None
        
    output_path_from_cli: Optional[Path] = cli_args.get("output")
    if output_path_from_cli: 
        return output_path_from_cli
        
    default_output_dir_str = resolve_config_value(
        cli_value=None, file_value=file_config.get("output_dir"), default_value=DEFAULT_OUTPUT_DIR
    )
    default_output_dir_path = Path(default_output_dir_str)
    
    output_name: str
    if reporting_root:
        if reporting_root.name == "" and reporting_root.parent == reporting_root:
            output_name = "root_context.txt"
        else:
            output_name = f"{reporting_root.name}_context.txt"
    else:
        output_name = "mixed_context.txt"
        
    final_output_path = default_output_dir_path / output_name
    logger.debug(f"Sử dụng đường dẫn output mặc định (chưa expand): {final_output_path.as_posix()}")
    return final_output_path