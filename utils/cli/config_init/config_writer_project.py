# Path: utils/cli/config_init/config_writer_project.py
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import sys

try:
    import tomlkit
    from tomlkit.exceptions import ParseError, ConvertError
    # SỬA: Import các kiểu cụ thể
    from tomlkit.items import Table, Item
    from tomlkit.toml_document import TOMLDocument
except ImportError:
    tomlkit = None
    ParseError = Exception
    ConvertError = Exception
    # SỬA: Tạo type stubs
    Table = Dict[str, Any]
    Item = Any
    TOMLDocument = Dict[str, Any]

from ..ui_helpers import prompt_config_overwrite
from utils.logging_config import log_success

__all__ = ["write_project_config_section"]


def write_project_config_section(
    logger: logging.Logger,
    config_file_path: Path,
    config_section_name: str,
    new_section_content_string: str,
) -> Optional[Path]:
    """
    Ghi/cập nhật một section vào file .project.toml, 
    bảo toàn comment và cấu trúc.
    """

    if tomlkit is None:
        raise ImportError("Thư viện 'tomlkit' không được cài đặt.")

    should_write = True
    try:
        # 1. Tải file .project.toml hiện có (nếu có)
        content = (
            config_file_path.read_text(encoding="utf-8")
            if config_file_path.exists()
            else ""
        )
        main_doc: TOMLDocument = tomlkit.parse(content)

        # 2. Phân tích nội dung mới (từ template)
        try:
            parsed_template_doc: TOMLDocument = tomlkit.parse(new_section_content_string)
            if config_section_name not in parsed_template_doc:
                raise ValueError(
                    f"Generated content unexpectedly missing section [{config_section_name}] after parsing."
                )
            # SỬA: Lấy Item (bao gồm Table và trivia)
            new_section_item: Item = parsed_template_doc.item(config_section_name) # type: ignore
            new_section_table: Table = new_section_item.unwrap() # type: ignore
        except (ParseError, ValueError, Exception) as e:
            logger.error(f"❌ Lỗi khi phân tích nội dung section đã tạo: {e}")
            raise

        # 3. Kiểm tra ghi đè
        section_existed = config_section_name in main_doc
        if section_existed:
            should_write = prompt_config_overwrite(
                logger, config_file_path, f"Section [{config_section_name}]"
            )

        if should_write is None:
            return None

        # 4. SỬA LOGIC: Merge thông minh
        if should_write:
            if not section_existed:
                # Nếu section chưa tồn tại, thêm Item mới (giữ comment)
                main_doc.add(tomlkit.comment("--- (Section được tạo/cập nhật bởi bootstrap) ---"))
                main_doc.add(new_section_item) # Thêm Item (Table + trivia)
            else:
                # Nếu section đã tồn tại, merge từng key một
                # SỬA: Lấy Item (Table) CŨ
                existing_section_item: Item = main_doc.item(config_section_name) # type: ignore
                existing_section_table: Table = existing_section_item.unwrap() # type: ignore
                
                # SỬA: Lặp qua các key trong Table MỚI
                for key in new_section_table.keys(): # .keys() là đúng cho Table (dict-like)
                    # Lấy Item MỚI (từ Table MỚI)
                    new_item: Item = new_section_table.item(key) # type: ignore
                    
                    # Gán giá trị (value) vào Table CŨ
                    existing_section_table[key] = new_item.unwrap()
                    
                    # Sao chép comment/trivia
                    if new_item and new_item.trivia.comment:
                        # Lấy Item CŨ (từ Table CŨ)
                        item_in_doc: Item = existing_section_table.item(key) # type: ignore
                        item_in_doc.trivia.comment = new_item.trivia.comment
                        item_in_doc.trivia.indent = new_item.trivia.indent

            # 5. Ghi file
            with config_file_path.open("w", encoding="utf-8") as f:
                tomlkit.dump(main_doc, f)

            log_success(
                logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'."
            )

    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi cập nhật file '{config_file_path.name}': {e}")
        raise
    except (ParseError, ConvertError, Exception) as e:
        logger.error(f"❌ Lỗi không mong muốn khi cập nhật TOML (tomlkit): {e}")
        raise

    return config_file_path