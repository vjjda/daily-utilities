# Path: utils/cli/config_init/config_writer_project.py
import logging
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomlkit
    from tomlkit.exceptions import ConvertError, ParseError
    from tomlkit.items import Item, Table
    from tomlkit.toml_document import TOMLDocument
except ImportError:
    tomlkit = None
    ParseError = Exception
    ConvertError = Exception
    Table = Dict[str, Any]
    Item = Any
    TOMLDocument = Dict[str, Any]

from utils.logging_config import log_success
from utils.core.config_helpers import PROJECT_CONFIG_ROOT_KEY
from ..ui_helpers import prompt_config_overwrite

__all__ = ["write_project_config_section"]


def write_project_config_section(
    logger: logging.Logger,
    config_file_path: Path,
    config_section_name: str,
    new_section_content_string: str,
) -> Optional[Path]:

    if tomlkit is None:
        raise ImportError("Thư viện 'tomlkit' không được cài đặt.")

    should_write = True
    try:

        content = (
            config_file_path.read_text(encoding="utf-8")
            if config_file_path.exists()
            else ""
        )
        main_doc: TOMLDocument = tomlkit.parse(content)

        try:
            parsed_template_doc: TOMLDocument = tomlkit.parse(
                new_section_content_string
            )
            if config_section_name not in parsed_template_doc:
                raise ValueError(
                    f"Generated content unexpectedly missing section [{config_section_name}] after parsing."
                )

            new_section_table: Table = parsed_template_doc[config_section_name]  # type: ignore

        except (ParseError, ValueError, Exception) as e:
            logger.error(f"❌ Lỗi khi phân tích nội dung section đã tạo: {e}")
            raise

        if PROJECT_CONFIG_ROOT_KEY not in main_doc:
            logger.info(
                f"Tạo section [{PROJECT_CONFIG_ROOT_KEY}] mới trong '{config_file_path.name}'."
            )
            main_doc.add(tomlkit.nl())
            tool_table = tomlkit.table()
            main_doc.add(PROJECT_CONFIG_ROOT_KEY, tool_table)
        else:
            tool_table = main_doc[PROJECT_CONFIG_ROOT_KEY]  # type: ignore

        if not isinstance(tool_table, (Table, dict)):
            logger.error(
                f"❌ Lỗi: Mục '[{PROJECT_CONFIG_ROOT_KEY}]' trong '{config_file_path.name}' "
                "không phải là một bảng (table)."
            )
            return None

        section_existed = config_section_name in tool_table
        if section_existed:
            should_write = prompt_config_overwrite(
                logger,
                config_file_path,
                f"Section [{PROJECT_CONFIG_ROOT_KEY}.{config_section_name}]",
            )

        if should_write is None:
            return None

        if should_write:
            if not section_existed:
                logger.debug(
                    f"Section [{config_section_name}] mới. Thêm vào [{PROJECT_CONFIG_ROOT_KEY}]."
                )
            else:
                logger.debug(
                    f"Section [{config_section_name}] đã tồn tại. Đang ghi đè (Overwrite)..."
                )

            tool_table[config_section_name] = new_section_table

            logger.debug(
                f"Đang sắp xếp lại các khóa bên trong [{PROJECT_CONFIG_ROOT_KEY}]..."
            )

            current_tables = {
                k: v for k, v in tool_table.items() if isinstance(v, (Table, dict))
            }

            other_items = {
                k: v for k, v in tool_table.items() if not isinstance(v, (Table, dict))
            }

            tool_table.clear()

            for k, v in other_items.items():
                tool_table.add(k, v)

            sorted_keys = sorted(current_tables.keys())
            for key in sorted_keys:
                tool_table.add(key, current_tables[key])

            with config_file_path.open("w", encoding="utf-8") as f:
                tomlkit.dump(main_doc, f)

            log_success(
                logger,
                f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.",
            )

    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi cập nhật file '{config_file_path.name}': {e}")
        raise
    except (ParseError, ConvertError, Exception) as e:
        logger.error(f"❌ Lỗi không mong muốn khi cập nhật TOML (tomlkit): {e}")
        raise e

    return config_file_path
