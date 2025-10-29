# Path: modules/no_doc/no_doc_analyzer.py
"""
Docstring Removal logic using Python's AST (Abstract Syntax Tree)
để trích xuất vị trí, sau đó xóa bằng cách chỉnh sửa nội dung gốc (string)
để bảo toàn định dạng.
"""

import logging
import ast
import re # Đảm bảo re được import
from typing import Optional, Dict, Any, List, cast
from pathlib import Path

__all__ = ["analyze_file_for_docstrings"]

# --- AST Helper: Trích xuất vị trí Docstring ---

def _get_docstring_info(node_body: List[ast.stmt]) -> Optional[Dict[str, Any]]:
    """
    Trích xuất docstring và vị trí dòng/cột của nó.
    Trả về None nếu không phải là docstring hợp lệ.
    """
    if (node_body and 
        isinstance(node_body[0], ast.Expr) and 
        isinstance(node_body[0].value, (ast.Constant))
    ):
        expr_node: ast.Expr = node_body[0]
        
        # Thêm khai báo kiểu tường minh cho Type Checker
        constant_node: ast.Constant = cast(ast.Constant, expr_node.value)        
        # Docstring phải là chuỗi
        if not isinstance(constant_node.value, str):
            return None
            
        # Vị trí dòng bắt đầu và dòng kết thúc
        start_line = expr_node.lineno
        end_line = expr_node.end_lineno
        
        return {
            "start_line": start_line,
            "end_line": end_line,
            "col_offset": expr_node.col_offset,
            "end_col_offset": expr_node.end_col_offset,
            "value": constant_node.value, # Pylance giờ đã biết constant_node có 'value'
        }
    return None

def _find_all_docstrings(tree: ast.Module) -> List[Dict[str, Any]]:
    """Duyệt qua AST để tìm tất cả docstring ở các cấp."""
    docstring_list: List[Dict[str, Any]] = []

    for node in ast.walk(tree):
        doc_info = None
        
        # Xử lý các node có thể chứa docstring
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc_info = _get_docstring_info(node.body)
            
        if doc_info:
            docstring_list.append(doc_info)
            
    return docstring_list

# --- Hàm chính ---

def _remove_comments_from_content(content: str) -> str:
    """Loại bỏ tất cả comments (#) khỏi nội dung, ngoại trừ Shebang,
    sử dụng Regex để cố gắng tránh xóa comments bên trong string literals."""
    
    lines = content.splitlines(True) # Giữ dấu xuống dòng
    new_lines: List[str] = []
    
    # 1. Xử lý Shebang (Nếu có, giữ lại)
    shebang_line = ""
    if lines and lines[0].startswith('#!'):
        shebang_line = lines.pop(0)
    
    if shebang_line:
        new_lines.append(shebang_line)

    # Regex an toàn hơn: tìm dấu # không phải là string
    # Pattern: Bắt dấu # (Group 1) theo sau bởi bất cứ thứ gì không phải newline (Group 2).
    # Không sử dụng Pattern phức tạp để tránh string literals 
    # vì không thể phân tích đúng string literals bằng Regex.
    # Thay vào đó, ta sẽ dùng Regex chỉ tìm dấu # đứng sau khoảng trắng/tab
    
    COMMENT_PATTERN = re.compile(r'(\s+)#.*', re.DOTALL)

    for line in lines:
        stripped_line = line.lstrip()
        
        # 2. Bỏ qua các dòng comment hoàn toàn
        if stripped_line.startswith('#'):
            continue
        
        # 3. Loại bỏ comment nội tuyến
        # Dùng COMMENT_PATTERN để tìm khoảng trắng + # + comment
        match = COMMENT_PATTERN.search(line)
        
        if match:
             # Nếu tìm thấy, cắt dòng tại vị trí khoảng trắng (match.group(1))
             # và chỉ giữ lại phần code trước đó.
             line_without_comment = line[:match.start(1)].rstrip()
             
             # Giữ lại dấu xuống dòng
             if line.endswith('\n'):
                line_without_comment += '\n'
             
             # Chỉ thêm nếu dòng không trống sau khi xóa comment
             if line_without_comment.strip():
                 new_lines.append(line_without_comment)
                 
        else:
            # Nếu không tìm thấy comment hoặc dấu # nằm trong string, giữ nguyên dòng (nếu không trống)
            if line.strip():
                new_lines.append(line)

    # Sửa lỗi: Loại bỏ dòng trống thừa do xóa comment
    # Ta chỉ cần một vòng lặp cuối cùng để dọn dẹp các dòng trống
    # (vì các dòng không có comment cũng có thể bị xóa ở bước 3)
    final_lines: List[str] = []
    if shebang_line:
        final_lines.append(shebang_line)
        
    for line in new_lines:
        if line.strip() and line != shebang_line:
             final_lines.append(line)
             
    return "".join(final_lines)

# --- Hàm chính ---

def analyze_file_for_docstrings(
    file_path: Path, 
    logger: logging.Logger,
    all_clean: bool # Thêm cờ all_clean
) -> Optional[Dict[str, Any]]:
    """
    Phân tích file Python, loại bỏ docstring, và tùy chọn comments.
    """
    
    # 1. Đọc nội dung gốc
    original_lines: List[str] = []
    try:
        original_lines = file_path.read_text(encoding='utf-8').splitlines(keepends=True)
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi đọc/encoding: {e}")
        return None
        
    original_content = "".join(original_lines)
    content_after_docstring_removal = original_content
    docstring_removed = False

    try:
        # 2. Xóa Docstrings (Dùng AST)
        tree = ast.parse(original_content)
        docstrings = _find_all_docstrings(tree)
        
        if docstrings:
            # Logic xóa docstring (dựa trên sắp xếp ngược, giống code gốc)
            new_lines = list(original_lines)
            docstrings.sort(key=lambda d: d["end_line"], reverse=True)
            
            for doc_info in docstrings:
                start = doc_info["start_line"]
                end = doc_info["end_line"]
                del new_lines[start - 1 : end] # Xóa dòng từ start đến end
            
            content_after_docstring_removal = "".join(new_lines)
            docstring_removed = True
            
        # 3. Xóa Comments (Nếu all_clean=True)
        content_after_all_cleaning = content_after_docstring_removal
        if all_clean:
            content_after_all_cleaning = _remove_comments_from_content(content_after_docstring_removal)
        
        # 4. So sánh và trả về kết quả
        if docstring_removed or (all_clean and content_after_all_cleaning != original_content):
            
            return {
                "path": file_path,
                "original_content": original_content,
                "new_content": content_after_all_cleaning,
            }
        
    except SyntaxError as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi cú pháp (SyntaxError): {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi phân tích/xóa file '{file_path.name}': {e}")
        return None

    return None