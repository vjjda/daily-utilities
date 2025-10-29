# Path: utils/core/code_cleaner.py
"""
Tiện ích điều phối (Orchestrator) việc làm sạch mã nguồn.
Sử dụng một Registry để gọi "chiến lược" làm sạch (cleaner)
phù hợp cho từng ngôn ngữ.

(Module nội bộ, được import bởi utils.core)
"""

import logging
from typing import Protocol, runtime_checkable, Dict, Final

# --- 1. Định nghĩa Giao diện "Add-on" (Interface) ---

@runtime_checkable
class CodeCleaner(Protocol):
    """
    Một giao diện (Protocol) định nghĩa "hình dạng" của một hàm
    làm sạch code "add-on".
    """
    def __call__(self, code_content: str, logger: logging.Logger, all_clean: bool = False) -> str:
        ...

# --- 2. Registry (Sổ đăng ký) ---
# Ánh xạ một mã định danh ngôn ngữ (chuỗi viết thường) tới hàm
# cleaner tương ứng.
CLEANER_REGISTRY: Final[Dict[str, CodeCleaner]] = {}

def register_cleaner(language_id: str, cleaner_func: CodeCleaner) -> None:
    """
    Hàm public để các "add-on" tự đăng ký vào Registry.
    """
    lang_id_lower = language_id.lower()
    if lang_id_lower in CLEANER_REGISTRY:
        logger = logging.getLogger("CodeCleanerRegistry")
        logger.warning(f"⚠️ Đang ghi đè cleaner đã đăng ký cho ngôn ngữ: {lang_id_lower}")
    CLEANER_REGISTRY[lang_id_lower] = cleaner_func

# --- 3. Hàm Điều phối Công khai (Public Orchestrator) ---

__all__ = ["clean_code", "register_cleaner"]

def clean_code(
    code_content: str,
    language: str,
    logger: logging.Logger,
    all_clean: bool = False
) -> str:
    """
    Làm sạch một khối mã nguồn bằng cách sử dụng cleaner (add-on)
    phù hợp với ngôn ngữ được chỉ định.
    
    Args:
        code_content: Chuỗi mã nguồn cần làm sạch.
        language: Mã định danh ngôn ngữ (ví dụ: "python", "js", "shell").
        logger: Logger để ghi log.
        all_clean: True để xóa cả comments (nếu cleaner hỗ trợ).

    Returns:
        Chuỗi mã nguồn đã được làm sạch, hoặc chuỗi gốc nếu không
        tìm thấy cleaner hoặc có lỗi xảy ra.
    """
    # Tìm cleaner trong registry
    cleaner = CLEANER_REGISTRY.get(language.lower())
    
    if not cleaner:
        logger.debug(f"Không tìm thấy code cleaner nào được đăng ký cho ngôn ngữ '{language}'. Trả về nội dung gốc.")
        return code_content
        
    try:
        # Gọi "chiến lược" (add-on) tương ứng
        return cleaner(code_content, logger, all_clean)
    except Exception as e:
        logger.error(f"❌ Lỗi xảy ra trong quá trình làm sạch code cho '{language}': {e}")
        logger.debug("Traceback:", exc_info=True)
        return code_content # An toàn: trả về gốc nếu có lỗi

# --- 4. Tự động khám phá và đăng ký "Add-ons" ---
# Đây là phần "plug-in": chỉ cần import các add-on từ thư mục con
# và gọi register_cleaner() cho chúng.

try:
    from . import cleaners
    
    # Đăng ký Python
    register_cleaner("python", cleaners.cleaner_python.clean_python_code)
    
    # Đăng ký JavaScript (và alias 'js')
    register_cleaner("javascript", cleaners.cleaner_js.clean_javascript_code)
    register_cleaner("js", cleaners.cleaner_js.clean_javascript_code)
    
    # Đăng ký Shell (và các alias)
    register_cleaner("shell", cleaners.cleaner_shell.clean_shell_code)
    register_cleaner("bash", cleaners.cleaner_shell.clean_shell_code)
    register_cleaner("sh", cleaners.cleaner_shell.clean_shell_code)

except ImportError as e:
    # Xử lý lỗi nếu thư mục cleaners bị thiếu
    _registry_logger = logging.getLogger("CodeCleanerRegistry")
    _registry_logger.error(f"❌ Lỗi nghiêm trọng: Không thể import thư mục 'cleaners': {e}")