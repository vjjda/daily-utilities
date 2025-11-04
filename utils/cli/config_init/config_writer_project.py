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

from ..ui_helpers import prompt_config_overwrite

__all__ = ["write_project_config_section"]


def write_project_config_section(
    logger: logging.Logger,
    config_file_path: Path,
    config_section_name: str,
    new_section_content_string: str,
    root_key: Optional[str] = None,
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

        target_table: TOMLDocument | Table = main_doc
        display_section_name = config_section_name

        if root_key:
            if root_key not in main_doc:
                logger.info(
                    f"Tạo section [{root_key}] mới trong '{config_file_path.name}'."
                )
                main_doc.add(tomlkit.nl())
                root_table = tomlkit.table()
                main_doc.add(root_key, root_table)
            else:
                root_table = main_doc[root_key]  # type: ignore

            if not isinstance(root_table, (Table, dict)):
                logger.error(
                    f"❌ Lỗi: Mục '[{root_key}]' trong '{config_file_path.name}' "
                    "không phải là một bảng (table)."
                )
                return None

            target_table = root_table
            display_section_name = f"{root_key}.{config_section_name}"

        section_existed = config_section_name in target_table
        if section_existed:
            should_write = prompt_config_overwrite(
                logger,
                config_file_path,
                f"Section [{display_section_name}]",
            )

        if should_write is None:
            return None

        if should_write:
            if not section_existed:
                logger.debug(f"Section [{display_section_name}] mới. Thêm vào file.")
            else:
                logger.debug(
                    f"Section [{display_section_name}] đã tồn tại. Đang ghi đè (Overwrite)..."
                )

            target_table[config_section_name] = new_section_table

            if root_key and isinstance(target_table, (Table, dict)):
                logger.debug(f"Đang sắp xếp lại các khóa bên trong [{root_key}]...")

                current_tables = {
                    k: v
                    for k, v in target_table.items()
                    if isinstance(v, (Table, dict))
                }
                other_items = {
                    k: v
                    for k, v in target_table.items()
                    if not isinstance(v, (Table, dict))
                }

                target_table.clear()

                for k, v in other_items.items():
                    target_table[k] = v

                sorted_keys = sorted(current_tables.keys())
                for key in sorted_keys:
                    target_table[key] = current_tables[key]

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
