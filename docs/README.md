# Tài liệu Công cụ Dòng lệnh

Thư mục này chứa tài liệu chi tiết cho các công cụ dòng lệnh (command-line tools) của dự án `daily-utilities`.

## Danh sách các công cụ

| Tên Lệnh | Mô tả | Tài liệu |
| :--- | :--- | :--- |
| `btool` | **B**ootstrap **Tool**: Tự động tạo cấu trúc file cho một công cụ mới từ file đặc tả. | [`btool.md`](./tools/btool.md) |
| `cdiag` | **C**lipboard **Diag**ram: Xử lý code đồ thị (Graphviz/Mermaid) từ clipboard và render ra ảnh. | [`cdiag.md`](./tools/cdiag.md) |
| `cpath` | **C**heck **Path**: Kiểm tra và sửa các comment đường dẫn (`# Path: ...`) ở đầu file. | [`cpath.md`](./tools/cpath.md) |
| `ctree` | **C**ustom **Tree**: Hiển thị cây thư mục với các tùy chọn lọc nâng cao. | [`tree.md`](./tools/tree.md) |
| `forc` | **For**mat **C**ode: Định dạng (format) các file mã nguồn, hỗ trợ chế độ gia tăng. | [`forc.md`](./tools/forc.md) |
| `ndoc` | **N**o **Doc**string: Loại bỏ docstring và comment khỏi các file mã nguồn. | [`ndoc.md`](./tools/ndoc.md) |
| `pcode` | **P**ack **Code**: Đóng gói nhiều file mã nguồn thành một file context duy nhất cho LLM. | [`pcode.md`](./tools/pcode.md) |
| `sgen` | **S**tub **Gen**erator: Tự động tạo file stub `.pyi` từ các file `__init__.py`. | [`sgen.md`](./tools/sgen.md) |
| `zrap` | **Z**sh W**rap**per: Gói một script Python thành một file thực thi Zsh tự quản lý venv. | [`zrap.md`](./tools/zrap.md) |