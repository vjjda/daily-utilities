# Path: modules/no_doc/no_doc_analyzer.py
"""
Logic loại bỏ Docstring và Comment sử dụng LibCST (Concrete Syntax Tree)
để đảm bảo giữ nguyên 100% định dạng mã nguồn.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, Sequence

try:
    import libcst as cst
    # Import các lớp cụ thể để type hint rõ ràng hơn
    from libcst import BaseStatement, RemovalSentinel, RemoveFromParent
    LIBCST_AVAILABLE = True
except ImportError:
    LIBCST_AVAILABLE = False
    # Không cần fallback class nữa, vì hàm analyze_ sẽ raise ImportError


__all__ = ["analyze_file_for_docstrings"]


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
            self, original_node: cst.Comment, updated_node: cst.Comment
        ) -> Union[cst.Comment, RemoveFromParent]:
            """Xóa comment nếu all_clean=True (trừ shebang)."""
            if not self.all_clean or original_node.value.startswith("#!"):
                return updated_node
            return RemoveFromParent()

        def _remove_docstring_from_body(
            self, body: Sequence[BaseStatement]
        ) -> Optional[Sequence[BaseStatement]]:
            """Trả về body mới (tuple) nếu docstring được tìm thấy và xóa."""
            docstring_index = self._find_docstring_index(body)
            if docstring_index == 0:
                return body[1:]
            return None

        def leave_Module(
            self, original_node: cst.Module, updated_node: cst.Module
        ) -> cst.Module:
            """Xóa docstring ở cấp độ module."""
            new_body_tuple = self._remove_docstring_from_body(updated_node.body)
            if new_body_tuple is not None:
                return updated_node.with_changes(body=new_body_tuple)
            return updated_node

        def leave_ClassDef(
            self, original_node: cst.ClassDef, updated_node: cst.ClassDef
        ) -> cst.ClassDef:
            """Xóa docstring ở cấp độ class."""
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body)
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple)
                return updated_node.with_changes(body=new_indented_block)
            return updated_node

        def leave_FunctionDef(
            self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
        ) -> cst.FunctionDef:
            """Xóa docstring ở cấp độ hàm (đồng bộ)."""
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body)
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple)
                return updated_node.with_changes(body=new_indented_block)
            return updated_node

        def leave_AsyncFunctionDef(
            self, original_node: cst.AsyncFunctionDef, updated_node: cst.AsyncFunctionDef
        ) -> cst.AsyncFunctionDef:
            """Xóa docstring ở cấp độ hàm (bất đồng bộ)."""
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body)
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple)
                return updated_node.with_changes(body=new_indented_block)
            return updated_node

# --- Hàm Phân tích Chính ---
def analyze_file_for_docstrings(
    file_path: Path,
    logger: logging.Logger,
    all_clean: bool
) -> Optional[Dict[str, Any]]:
    """
    Phân tích file Python, loại bỏ docstring, và tùy chọn comments.
    Sử dụng LibCST để đảm bảo an toàn về định dạng.
    """

    if not LIBCST_AVAILABLE:
        logger.error("❌ Lỗi: Tính năng này yêu cầu thư viện 'libcst'.")
        logger.error("   Vui lòng cài đặt: pip install libcst")
        raise ImportError("Không tìm thấy LibCST. Vui lòng cài đặt: pip install libcst")

    try:
        original_content = file_path.read_text(encoding='utf-8')
        # Thêm config parse để LibCST hiểu Python version (quan trọng!)
        parser_config = cst.PartialParserConfig(python_version="3.11") # Hoặc version bạn dùng
        cst_module = cst.parse_module(original_content, config=parser_config)

    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi đọc/encoding: {e}")
        return None
    except cst.ParserSyntaxError as e:
        line = getattr(e, 'raw_line', '?')
        col = getattr(e, 'raw_column', '?')
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi cú pháp (LibCST) tại dòng {line}, cột {col}: {e.message}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi parse không xác định: {e}")
        return None

    try:
        transformer = DocstringAndCommentRemover(all_clean=all_clean)
        modified_tree = cst_module.visit(transformer)
        new_content = modified_tree.code

        if new_content != original_content:
            return {
                "path": file_path,
                "original_content": original_content,
                "new_content": new_content,
            }
        return None
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi biến đổi CST file '{file_path.name}': {e}")
        # Log thêm traceback để debug
        logger.debug("Traceback:", exc_info=True)
        return None