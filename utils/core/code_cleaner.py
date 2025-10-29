# Path: utils/core/code_cleaner.py
"""
Tiện ích làm sạch mã nguồn Python, loại bỏ docstring và comment.
Sử dụng LibCST để đảm bảo giữ nguyên định dạng.
(Module nội bộ, được import bởi utils/core)
"""

import logging
from typing import Union, Sequence, Optional

# --- Sửa lỗi Import ---
_LIBCST_AVAILABLE = False
try:
    import libcst as cst
    # Chỉ kiểm tra import chính ở đây
    _LIBCST_AVAILABLE = True
except ImportError:
    pass # Để _LIBCST_AVAILABLE là False

# Chỉ import các thành phần con nếu libcst thực sự tồn tại
if _LIBCST_AVAILABLE:
    from libcst import BaseStatement, RemovalSentinel, RemoveFromParent
    # Vẫn thêm type: ignore cho Pylance
    from libcst import AsyncFunctionDef # type: ignore [attr-defined]
    from libcst import VersionCannotParseError, ParserSyntaxError # type: ignore [attr-defined]
else:
    # Định nghĩa các lớp giả nếu libcst không tồn tại
    class CSTNode: pass
    class Comment(CSTNode): pass
    class Module(CSTNode): pass
    class ClassDef(CSTNode): pass
    class FunctionDef(CSTNode): pass
    class AsyncFunctionDef(CSTNode): pass # type: ignore [no-redef]
    BaseStatement = CSTNode # type: ignore [misc]
    RemovalSentinel = object() # type: ignore [misc, assignment]
    RemoveFromParent = object() # type: ignore [misc, assignment]
    class ParserSyntaxError(Exception): pass # type: ignore [no-redef]
    class VersionCannotParseError(Exception): pass # type: ignore [no-redef]

LIBCST_AVAILABLE = _LIBCST_AVAILABLE # Gán vào biến global cuối cùng

__all__ = ["clean_python_code"]


if LIBCST_AVAILABLE:
    class DocstringAndCommentRemover(cst.CSTTransformer):
        """
        Một CST Transformer tùy chỉnh để loại bỏ:
        1. Luôn luôn: Docstrings từ Module, Class, và Function.
        2. Tùy chọn (nếu all_clean=True): Tất cả các comments (trừ shebang).
        """
        def __init__(self, all_clean: bool = False):
            super().__init__()
            self.all_clean = all_clean

        def _find_docstring_index(self, body: Sequence[BaseStatement]) -> int:
            """Tìm index của statement là docstring trong body, nếu có."""
            if not body:
                return -1
            node = body[0]
            if isinstance(node, cst.SimpleStatementLine):
                if len(node.body) == 1 and isinstance(node.body[0], cst.Expr):
                    if isinstance(node.body[0].value, (cst.SimpleString, cst.ConcatenatedString)):
                        return 0
            return -1

        def leave_Comment(
            self, original_node: Comment, updated_node: Comment # type: ignore [valid-type]
        ) -> Union[Comment, RemovalSentinel]: # type: ignore [valid-type]
            """Xóa comment nếu all_clean=True (trừ shebang)."""
            if not self.all_clean or original_node.value.startswith("#!"): # type: ignore [attr-defined]
                return updated_node
            return RemoveFromParent # type: ignore [return-value]

        def _remove_docstring_from_body(
            self, body: Sequence[BaseStatement]
        ) -> Optional[Sequence[BaseStatement]]:
            """Trả về body mới (tuple) nếu docstring được tìm thấy và xóa."""
            docstring_index = self._find_docstring_index(body)
            if docstring_index == 0:
                return body[1:]
            return None

        def leave_Module(
            self, original_node: Module, updated_node: Module # type: ignore [valid-type]
        ) -> Module: # type: ignore [valid-type]
            """Xóa docstring ở cấp độ module."""
            new_body_tuple = self._remove_docstring_from_body(updated_node.body) # type: ignore [attr-defined]
            if new_body_tuple is not None:
                return updated_node.with_changes(body=new_body_tuple) # type: ignore [attr-defined]
            return updated_node

        def leave_ClassDef(
            self, original_node: ClassDef, updated_node: ClassDef # type: ignore [valid-type]
        ) -> ClassDef: # type: ignore [valid-type]
            """Xóa docstring ở cấp độ class."""
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body) # type: ignore [attr-defined]
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple) # type: ignore [attr-defined]
                return updated_node.with_changes(body=new_indented_block) # type: ignore [attr-defined]
            return updated_node

        def leave_FunctionDef(
            self, original_node: FunctionDef, updated_node: FunctionDef # type: ignore [valid-type]
        ) -> FunctionDef: # type: ignore [valid-type]
            """Xóa docstring ở cấp độ hàm (đồng bộ)."""
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body) # type: ignore [attr-defined]
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple) # type: ignore [attr-defined]
                return updated_node.with_changes(body=new_indented_block) # type: ignore [attr-defined]
            return updated_node

        def leave_AsyncFunctionDef(
            self, original_node: AsyncFunctionDef, updated_node: AsyncFunctionDef
        ) -> AsyncFunctionDef:
            """Xóa docstring ở cấp độ hàm (bất đồng bộ)."""
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body) # type: ignore [attr-defined]
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple) # type: ignore [attr-defined]
                return updated_node.with_changes(body=new_indented_block) # type: ignore [attr-defined, unbound-variable]
            return updated_node

def clean_python_code(
    code_content: str,
    logger: logging.Logger,
    all_clean: bool = False
) -> str:
    """
    Loại bỏ docstring và tùy chọn comment khỏi một chuỗi mã nguồn Python.
    Args:
        code_content: Chuỗi chứa mã nguồn Python.
        logger: Logger để ghi log lỗi.
        all_clean: True để xóa cả comments (trừ shebang).
    Returns:
        Chuỗi mã nguồn đã được làm sạch, hoặc chuỗi gốc nếu có lỗi hoặc libcst không cài đặt.
    """
    if not LIBCST_AVAILABLE:
        # Log lỗi CHỈ MỘT LẦN ở đây thay vì lặp lại trong vòng lặp của ndoc_analyzer
        logger.error("❌ LibCST chưa được cài đặt. Không thể làm sạch code.")
        return code_content # Trả về gốc nếu thiếu thư viện

    if not code_content.strip():
        return code_content # Trả về gốc nếu chuỗi rỗng

    try:
        cst_module = cst.parse_module(code_content)
        transformer = DocstringAndCommentRemover(all_clean=all_clean)
        modified_tree = cst_module.visit(transformer)
        new_content = modified_tree.code
        return new_content

    except ParserSyntaxError as e: # Sử dụng tên đã import (hoặc dummy)
        line = getattr(e, 'raw_line', '?')
        col = getattr(e, 'raw_column', '?')
        logger.warning(f"⚠️ Lỗi cú pháp Python (LibCST) tại dòng {line}, cột {col} khi làm sạch code: {e.message}") # type: ignore [attr-defined]
        return code_content # Trả về gốc
    except VersionCannotParseError as e: # Sử dụng tên đã import (hoặc dummy)
        logger.warning(f"⚠️ Lỗi phiên bản grammar (LibCST) khi làm sạch code: {e}")
        return code_content # Trả về gốc
    except Exception as e:
        logger.warning(f"⚠️ Lỗi không xác định khi làm sạch code bằng LibCST: {e}")
        return code_content # Trả về gốc