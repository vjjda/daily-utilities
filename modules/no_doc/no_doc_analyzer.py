# Path: modules/no_doc/no_doc_analyzer.py

"""
Docstring Removal logic using Python's AST (Abstract Syntax Tree)
để trích xuất vị trí, sau đó xóa bằng cách chỉnh sửa nội dung gốc (string)
để bảo toàn định dạng.

Sử dụng Pygments Lexer để loại bỏ comments an toàn trong chế độ --all-clean.
"""

import logging
import ast
from typing import Optional, Dict, Any, List, cast
from pathlib import Path
import io

# --- Pygments Imports ---
try:
    # 1. Import tường minh các Token Types cần thiết
    from pygments.token import (
        Comment, Token, Text, Name, Literal, Punctuation # Thêm Text, Name, Literal, Punctuation
    )
    from pygments.lexers import PythonLexer
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False
    class Token: # Mock Token class vẫn cần thiết cho Python không có Pygments
        # Mock các thuộc tính được sử dụng trong code
        Text = 1
        Comment = 2
        Name = 3
        Literal = 4
        Punctuation = 5 # Thêm Punctuation mock
        Comment_Hashbang = 6

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
        
        if not isinstance(constant_node.value, str):
            return None
            
        start_line = expr_node.lineno
        end_line = expr_node.end_lineno
        
        return {
            "start_line": start_line,
            "end_line": end_line,
            "col_offset": expr_node.col_offset,
            "end_col_offset": expr_node.end_col_offset,
            "value": constant_node.value,
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

# --- Comment Removal Logic (Pygments) ---

def _remove_comments_from_content(content: str, logger: logging.Logger) -> str:
    """
    Loại bỏ tất cả comments (#) khỏi nội dung bằng Pygments Lexer an toàn.
    """
    if not PYGMENTS_AVAILABLE:
        logger.error("❌ Lỗi: Chế độ --all-clean yêu cầu thư viện 'Pygments'.")
        logger.error("   Vui lòng cài đặt: pip install Pygments")
        return content

    lexer = PythonLexer()
    tokens = list(lexer.get_tokens(content))
    
    new_content_lines: List[str] = []
    
    # Logic để nối lại token, loại bỏ COMMENT, và cố gắng giữ newline
    
    shebang_kept = False
    
    # Biến để theo dõi dòng hiện tại và buffer code
    code_buffer = ""
    
    # 1. Lặp qua các token
    for token_type, value in tokens:
        
        # Bỏ qua token ENCODING và ENDMARKER (xử lý ở bước cuối)
        if token_type is Token.Literal.String.Doc:
            continue
            
        # 2. Xử lý Shebang (Hashbang là token comment đặc biệt)
        if str(token_type).startswith('Comment.Hashbang') and not shebang_kept:
             code_buffer += value
             shebang_kept = True
             continue
             
        # 3. Bỏ qua tất cả các token COMMENT khác
        if str(token_type).startswith('Comment'):
            continue

        # 4. Xử lý Token Text (bao gồm khoảng trắng và newline)
        if token_type is Token.Text:
            if '\n' in value:
                # Nếu có newline, thêm buffer hiện tại vào dòng và reset
                parts = value.split('\n')
                for part in parts[:-1]:
                    code_buffer += part
                    new_content_lines.append(code_buffer)
                    code_buffer = ""
                # Phần còn lại của token (trước newline cuối cùng)
                code_buffer += parts[-1]
            else:
                code_buffer += value
        
        elif token_type is not Token.Name.Builtin and token_type is not Token.Name.Builtin.Pseudo:
            # Nếu là token code, chỉ nối vào buffer
            code_buffer += value

    # Thêm phần còn lại của buffer (nếu có)
    if code_buffer:
        new_content_lines.append(code_buffer)
    
    # 5. Lọc dòng trống thừa
    output_lines: List[str] = []
    for line in new_content_lines:
        # Giữ lại các dòng có nội dung
        if line.strip():
            output_lines.append(line)
        # Giữ lại một dòng trống duy nhất giữa các khối code
        elif not line.strip() and output_lines and output_lines[-1].strip():
             output_lines.append('\n')
            
    # Lọc các dòng trống liên tiếp > 1
    final_output: List[str] = []
    for line in output_lines:
        if not line.strip():
            # Nếu dòng hiện tại là trống và dòng cuối cùng cũng trống -> Bỏ qua
            if final_output and not final_output[-1].strip():
                continue
        final_output.append(line)
        
    return "".join(final_output)

# --- Hàm chính (Orchestrator) ---

def analyze_file_for_docstrings(
    file_path: Path, 
    logger: logging.Logger,
    all_clean: bool
) -> Optional[Dict[str, Any]]:
    """
    Phân tích file Python, loại bỏ docstring, và tùy chọn comments.
    """
    
    # 1. Đọc nội dung gốc
    original_lines: List[str] = []
    try:
        # Đọc file và giữ lại dấu xuống dòng (True)
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
            new_lines = list(original_lines)
            # Sắp xếp theo dòng kết thúc giảm dần (để xóa từ dưới lên)
            docstrings.sort(key=lambda d: d["end_line"], reverse=True)
            
            for doc_info in docstrings:
                start = doc_info["start_line"]
                end = doc_info["end_line"]
                # Chỉ số trong list = line number - 1
                del new_lines[start - 1 : end]
            
            content_after_docstring_removal = "".join(new_lines)
            docstring_removed = True
            
        # 3. Xóa Comments (Nếu all_clean=True)
        content_after_all_cleaning = content_after_docstring_removal
        if all_clean:
            # Sử dụng Pygments Lexer
            content_after_all_cleaning = _remove_comments_from_content(content_after_docstring_removal, logger)

        # 4. So sánh và trả về kết quả
        if docstring_removed or (all_clean and content_after_all_cleaning != original_content):
            
            # Nếu sau khi xóa comment/docstring, nội dung không thay đổi, bỏ qua
            if content_after_all_cleaning == original_content:
                return None
                
            return {
                "path": file_path,
                "original_content": original_content,
                "new_content": content_after_all_cleaning,
            }
        
    except SyntaxError as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi cú pháp (SyntaxError): {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi phân tích AST/xóa dòng file '{file_path.name}': {e}")
        return None

    return None