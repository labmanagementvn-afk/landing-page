# Ảnh sản phẩm mẫu

1. Đặt ảnh vào thư mục con theo danh mục:
   `thiet-bi-ve-sinh/`, `bon-nuoc-may-nuoc-nong/`, `thiet-bi-dien/`, `den-trang-tri/`, `nha-thong-minh/`.
2. Khai báo ảnh trong `src/products.json` (tên file, thương hiệu, chú thích tiếng Việt và tiếng Anh), ví dụ:

   ```json
   "thiet-bi-ve-sinh": [
     { "file": "inax-bon-cau-mot-khoi.webp", "brand": "INAX", "vi": "Bồn cầu một khối", "en": "One-piece toilet" }
   ]
   ```

- Ảnh nên là `.webp` hoặc `.jpg`, rộng khoảng 800px, dưới 200 KB, nền trắng (ảnh vuông hiển thị đẹp nhất).
- Đặt tên file không dấu, có thương hiệu và loại sản phẩm (tốt cho SEO), ví dụ `toto-sen-tam-nhiet-do.webp`.
- Chỉ dùng ảnh do hãng/nhà phân phối cung cấp cho đại lý, hoặc ảnh tự chụp sản phẩm thật. Không ghi giá trong ảnh.
- Build sẽ báo lỗi nếu khai báo file không tồn tại, và cảnh báo nếu ảnh quá nặng.
