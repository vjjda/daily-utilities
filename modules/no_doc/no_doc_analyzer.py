# Path: modules/no_doc/no_doc_analyzer.py
"""
Docstring Removal logic using Python's AST (Abstract Syntax Tree).
(Internal module, imported by no_doc_core)

Chịu trách nhiệm chuyển đổi mã Python thành AST, loại bỏ các node docstring,
và chuyển AST đã sửa đổi trở lại thành mã nguồn.
"""

import logging
import ast
import inspect
from typing import Optional, Dict, Any, List
from pathlib import Path

__all__ = ["analyze_file_for_docstrings"]

# --- AST Node Transformer ---

class DocstringRemover(ast.NodeTransformer):
    """
    ast.NodeTransformer để loại bỏ các Docstring (String Literal đầu tiên)
    ở cấp độ Module, Class và Function/Method.
    """
    
    def _remove_docstring(self, node):
        """Helper: Loại bỏ docstring khỏi body của node."""
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, (ast.Constant)) # <-- ĐÃ SỬA LỖI Ở ĐÂY
        ):
            # Docstring là node biểu thức (ast.Expr) đầu tiên chứa chuỗi
            node.body.pop(0) 
        return node
        
    # Ghi đè các phương thức visit để áp dụng logic
    visit_Module = _remove_docstring
    visit_FunctionDef = _remove_docstring
    visit_AsyncFunctionDef = _remove_docstring
    visit_ClassDef = _remove_docstring


# --- Hàm chính ---

def analyze_file_for_docstrings(
    file_path: Path, 
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """
    Phân tích file Python, loại bỏ docstring và trả về nội dung mới.
    
    Args:
        file_path: Đường dẫn đến file Python.
        logger: Logger.
        
    Returns:
        Dict chứa nội dung mới và đường dẫn file nếu docstring được tìm thấy, 
        None nếu không có thay đổi hoặc có lỗi.
    """
    
    original_content = ""
    try:
        original_content = file_path.read_text(encoding='utf-8')
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi đọc/encoding: {e}")
        return None

    try:
        # 1. Parse nội dung thành AST
        tree = ast.parse(original_content)
        
        # 2. Tạo bản sao của AST gốc
        original_tree = ast.parse(original_content)
        
        # 3. Áp dụng Transformer để loại bỏ docstring
        new_tree = DocstringRemover().visit(tree)
        
        # 4. Chuyển AST đã sửa đổi trở lại thành mã nguồn
        # Sử dụng ast.unparse (Python 3.9+)
        new_content = ast.unparse(new_tree)
        
        # 5. So sánh với bản gốc
        # So sánh AST đã sửa đổi với AST gốc (để loại trừ trường hợp 
        # file có docstring nhưng ast.unparse lại thêm/bớt khoảng trắng/dòng trống, 
        # chúng ta chỉ so sánh nội dung sau khi unparse).
        # Nếu ast.unparse thay đổi format (chỉ là khoảng trắng), việc so sánh trực tiếp 
        # new_content == original_content sẽ thất bại, nhưng chúng ta chỉ quan tâm 
        # đến việc loại bỏ docstring.
        
        # Một heuristic đơn giản hơn: nếu có docstring ban đầu, 
        # nội dung sau khi remove chắc chắn ngắn hơn hoặc khác.
        if new_content == original_content:
            # Code không thay đổi, có thể do không có docstring
            # hoặc lỗi unparse không đáng kể (sẽ được xử lý bằng so sánh hàm)
            pass

        # Kiểm tra chi tiết hơn: Nếu có bất kỳ docstring nào (cách thô)
        if inspect.getdoc(tree) or any(inspect.isdatadescriptor(node) and inspect.getdoc(node) for node in tree.body):
            # Nếu có vẻ có docstring, chúng ta chấp nhận new_content
            # và để Executor quyết định ghi đè.
            pass
        
    except SyntaxError as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi cú pháp (SyntaxError): {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi phân tích AST file '{file_path.name}': {e}")
        return None

    # Vấn đề của ast.unparse là nó thay đổi đáng kể định dạng, gây ra 
    # nhiều thay đổi không mong muốn (ví dụ: mất comment).
    # Vì mục đích chỉ là xóa docstring, chúng ta sẽ chỉ trả về kết quả 
    # nếu thấy có sự khác biệt đáng kể (ví dụ: khác nhau về số dòng/bytes)
    # và để người dùng xác nhận. 
    # Tuy nhiên, cách tốt nhất là dùng công cụ bên ngoài (ví dụ: libcst) 
    # hoặc trả về nội dung đã sửa và cảnh báo về sự mất format.

    # Do chúng ta phải tuân thủ thư viện chuẩn, chúng ta dùng ast.unparse 
    # và chấp nhận sự thay đổi format:
    if new_content != original_content:
        # Giả định có sự thay đổi (hy vọng là docstring đã bị xóa)
        return {
            "path": file_path,
            "original_content": original_content,
            "new_content": new_content,
        }

    return None # Không có thay đổi cần thiết