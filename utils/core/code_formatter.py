# Path: utils/core/code_formatter.py
"""
Tiện ích điều phối (Orchestrator) việc định dạng mã nguồn.
Sử dụng một Registry để gọi "chiến lược" định dạng (formatter)
phù hợp cho từng ngôn ngữ.
"""

import logging
from pathlib import Path
from typing import Protocol, runtime_checkable, Dict, Final, Optional

# --- 1. Định nghĩa Giao diện "Add-on" (Interface) ---

@runtime_checkable
class CodeFormatter(Protocol):
    """
    Một giao diện (Protocol) định nghĩa "hình dạng" của một hàm
    định dạng code "add-on".
    
    Nó BẮT BUỘC phải nhận 'file_path: Optional[Path]'.
    """
    def __call__(
        self, 
        code_content: str, 
        logger: logging.Logger,
        file_path: Optional[Path] = None
    ) -> str:
        ...

# --- 2. Registry (Sổ đăng ký) ---
FORMATTER_REGISTRY: Final[Dict[str, CodeFormatter]] = {}

def register_formatter(language_id: str, formatter_func: CodeFormatter) -> None:
    """
    Hàm public để các "add-on" tự đăng ký vào Registry.
    """
    lang_id_lower = language_id.lower()
    if lang_id_lower in FORMATTER_REGISTRY:
        logger = logging.getLogger("CodeFormatterRegistry")
        logger.warning(f"⚠️ Đang ghi đè formatter đã đăng ký cho ngôn ngữ: {lang_id_lower}")
    FORMATTER_REGISTRY[lang_id_lower] = formatter_func

# --- 3. Hàm Điều phối Công khai (Public Orchestrator) ---

__all__ = ["format_code", "register_formatter"]

def format_code(
    code_content: str,
    language: str,
    logger: logging.Logger,
    file_path: Optional[Path] = None
) -> str:
    """
    Định dạng một khối mã nguồn bằng cách sử dụng formatter (add-on)
    phù hợp với ngôn ngữ được chỉ định.
    
    Args:
        code_content: Chuỗi mã nguồn cần định dạng.
        language: Mã định danh ngôn ngữ (ví dụ: "python", "js").
        logger: Logger để ghi log.
        file_path: (Tùy chọn) Đường dẫn đến file. Nếu được cung cấp,
                   formatter có thể sử dụng nó để tìm file cấu hình
                   (ví dụ: pyproject.toml).

    Returns:
        Chuỗi mã nguồn đã được định dạng, hoặc chuỗi gốc nếu không
        tìm thấy formatter hoặc có lỗi xảy ra.
    """
    # Tìm formatter trong registry
    formatter = FORMATTER_REGISTRY.get(language.lower())
    
    if not formatter:
        logger.debug(f"Không tìm thấy code formatter nào được đăng ký cho ngôn ngữ '{language}'. Trả về nội dung gốc.")
        return code_content
        
    try:
        # Gọi "chiến lược" (add-on) tương ứng, truyền file_path
        return formatter(code_content, logger, file_path)
    except Exception as e:
        logger.error(f"❌ Lỗi xảy ra trong quá trình định dạng code cho '{language}': {e}")
        logger.debug("Traceback:", exc_info=True)
        return code_content # An toàn: trả về gốc nếu có lỗi

# --- 4. Tự động khám phá và đăng ký "Add-ons" ---
try:
    from . import formatters
    
    # Đăng ký Python
    register_formatter("python", formatters.formatter_python.format_python_black)
    
    # (Tương lai: Đăng ký JS, v.v.)
    # register_formatter("javascript", formatters.formatter_js.format_js_prettier)
    # register_formatter("js", formatters.formatter_js.format_js_prettier)

except ImportError as e:
    _registry_logger = logging.getLogger("CodeFormatterRegistry")
    _registry_logger.error(f"❌ Lỗi nghiêm trọng: Không thể import thư mục 'formatters': {e}")