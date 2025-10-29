
"""
Logic loại bỏ Docstring và Comment sử dụng LibCST (Concrete Syntax Tree)
để đảm bảo giữ nguyên 100% định dạng mã nguồn.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union

try:
    import libcst as cst
    LIBCST_AVAILABLE = True
except ImportError:
    LIBCST_AVAILABLE = False


__all__ = ["analyze_file_for_docstrings"]


if LIBCST_AVAILABLE:
    class DocstringAndCommentRemover(cst.CSTTransformer):
        """
        Một CST Transformer tùy chỉnh để loại bỏ:
        1. Luôn luôn: Docstrings từ Module, Class, và Function.
        2. Tùy chọn (nếu all_clean=True): Tất cả các comments (trừ shebang).
        """
        def __init__(self, all_clean: bool = False):
            self.all_clean = all_clean

        def _is_docstring(self, node: cst.BaseStatement) -> bool:
            """Kiểm tra xem một statement có phải là docstring không."""
            if isinstance(node, cst.Expr):
                
                if isinstance(node.value, (cst.SimpleString, cst.ConcatenatedString)):
                    return True
            return False

        

        def leave_Comment(
            self, original_node: cst.Comment, updated_node: cst.Comment
        ) -> Union[cst.Comment, cst.RemoveFromParent]: 
            """
            Được gọi sau khi visit một nút Comment.
            """
            
            if not self.all_clean:
                return updated_node

            
            if original_node.value.startswith("#!"):
                return updated_node

            
            return cst.RemoveFromParent() 

        

        def leave_Module(
            self, original_node: cst.Module, updated_node: cst.Module
        ) -> cst.Module:
            """Xóa docstring ở cấp độ module."""
            if original_node.body and self._is_docstring(original_node.body[0]):
                
                return updated_node.with_changes(body=updated_node.body[1:])
            return updated_node

        def leave_ClassDef(
            self, original_node: cst.ClassDef, updated_node: cst.ClassDef
        ) -> cst.ClassDef:
            """Xóa docstring ở cấp độ class."""
            if original_node.body.body and self._is_docstring(original_node.body.body[0]):
                
                new_body = updated_node.body.with_changes(body=updated_node.body.body[1:])
                return updated_node.with_changes(body=new_body)
            return updated_node

        def leave_FunctionDef(
            self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
        ) -> cst.FunctionDef:
            """Xóa docstring ở cấp độ hàm (đồng bộ)."""
            if original_node.body.body and self._is_docstring(original_node.body.body[0]):
                new_body = updated_node.body.with_changes(body=updated_node.body.body[1:])
                return updated_node.with_changes(body=new_body)
            return updated_node

        def leave_AsyncFunctionDef(
            self, original_node: cst.AsyncFunctionDef, updated_node: cst.AsyncFunctionDef
        ) -> cst.AsyncFunctionDef:
            """Xóa docstring ở cấp độ hàm (bất đồng bộ)."""
            if original_node.body.body and self._is_docstring(original_node.body.body[0]):
                new_body = updated_node.body.with_changes(body=updated_node.body.body[1:])
                return updated_node.with_changes(body=new_body)
            return updated_node










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
        cst_module = cst.parse_module(original_content)
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi đọc/encoding: {e}")
        return None
    except cst.ParserSyntaxError as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi cú pháp (LibCST): {e}")
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
        return None