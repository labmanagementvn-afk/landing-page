# Vuong Gia Phu Solutions – Landing page

Website giới thiệu **Vuong Gia Phu Solutions Company Limited** – HTML/CSS/JS thuần, không framework, không backend,
không thu thập thông tin khách hàng.

| Trang | Đường dẫn |
| --- | --- |
| Trang chủ | `/` |
| Giải pháp Công nghệ | `/cong-nghe/` |
| Giải pháp Nội thất | `/noi-that/` |
| Thiết bị & Thương hiệu | `/thiet-bi/` |
| Chính sách bảo mật | `/chinh-sach-bao-mat/` |
| Trang riêng từng thương hiệu (15 trang) | `/thuong-hieu/inax/`, `/thuong-hieu/toto/`, … |
| Liên hệ (có trên mọi trang) | `#lien-he` |

**Chuẩn SEO:** mỗi trang là một file HTML riêng với tiêu đề, mô tả, URL chuẩn (canonical), hreflang VI/EN,
breadcrumb và dữ liệu có cấu trúc (schema.org LocalBusiness, BreadcrumbList) riêng; có `sitemap.xml` tự sinh.
Trong trình duyệt, chuyển trang vẫn tức thì như single page app (không tải lại cả trang).
Link cũ dạng `/#noi-that` tự chuyển sang `/noi-that/`.

Trang có hai ngôn ngữ **Tiếng Việt (mặc định)** và **English**, chuyển bằng nút `VI | EN` trên thanh menu.
Lựa chọn được ghi nhớ trên trình duyệt; thêm `?lang=en` vào link để chia sẻ bản tiếng Anh, ví dụ `https://vuonggiaphu.com/thiet-bi/?lang=en`.

## Cấu trúc

```
src/                    ← mã nguồn – chỉ sửa ở đây
  index.html            ← khuôn mẫu chứa nội dung của tất cả các trang (mỗi trang là một khối <!-- view:… -->)
  pages.json            ← tiêu đề, mô tả SEO và đường dẫn của từng trang (VI + EN)
  products.json         ← danh sách ảnh sản phẩm mẫu của trang Thiết bị & Thương hiệu
  assets/css/styles.css
  assets/js/main.js     ← chuyển trang, chuyển ngôn ngữ, menu mobile
  assets/js/i18n-en.js  ← toàn bộ bản dịch tiếng Anh
  assets/img/           ← logo, favicon, ảnh chia sẻ mạng xã hội; brands/ (logo hãng), products/ (ảnh sản phẩm)
  404.html, robots.txt, site.webmanifest
scripts/build.py        ← tạo thư mục dist/ (mỗi trang một file HTML + sitemap.xml); chỉ cần Python 3
dist/                   ← kết quả build, được deploy (không commit)
brand/                  ← file logo gốc
firebase.json           ← cấu hình Firebase Hosting
.github/workflows/deploy.yml ← tự build + deploy lên GitHub Pages; build thử cho mỗi pull request
```

## Xem thử trên máy

```bash
python3 scripts/build.py
python3 -m http.server 8080 -d dist
# mở http://localhost:8080
```

## Deploy

### Cách 1 – GitHub Pages (miễn phí, khuyên dùng)

1. Merge code vào nhánh `main`.
2. Trên GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
   Mỗi lần push lên `main`, workflow `Deploy to GitHub Pages` sẽ tự build và đăng trang.
3. Gắn tên miền: **Settings → Pages → Custom domain** → nhập `vuonggiaphu.com` → Save,
   sau đó tick **Enforce HTTPS** khi chứng chỉ đã sẵn sàng.
4. Tại nơi quản lý DNS của tên miền, thêm các bản ghi:

   | Loại | Tên | Giá trị |
   | --- | --- | --- |
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | CNAME | `www` | `labmanagementvn-afk.github.io` |

   Lưu ý: không xóa các bản ghi **MX** đang dùng cho email `vuong@vuonggiaphu.com`.

### Cách 2 – Firebase Hosting (miễn phí, gói Spark)

```bash
npm install -g firebase-tools
firebase login
firebase use --add          # chọn project Firebase của bạn
firebase deploy --only hosting   # tự chạy scripts/build.py trước khi deploy
```

Gắn tên miền trong **Firebase Console → Hosting → Add custom domain** và làm theo hướng dẫn DNS.

### Cách 3 – Cloudflare Pages / Netlify

Kết nối repo, lệnh build: `python3 scripts/build.py`, thư mục xuất bản (output directory): `dist`.

### Sau khi deploy (SEO)

- Bật **Enforce HTTPS** (GitHub → Settings → Pages) – Google ưu tiên trang HTTPS.
- Đăng ký trang với **Google Search Console** (xác minh tên miền), gửi `https://vuonggiaphu.com/sitemap.xml`.
- Tạo/cập nhật **Google Business Profile** với cùng tên, địa chỉ, số điện thoại như trên website.
  Đây là yếu tố quan trọng nhất để xuất hiện khi khách tìm "… Đồng Xoài" hoặc "… gần đây"; chọn đúng danh mục
  (vd. cửa hàng thiết bị vệ sinh, cửa hàng thiết bị điện), thêm ảnh cửa hàng, giờ mở cửa và link website.
- Trong Search Console, dùng **Kiểm tra URL → Yêu cầu lập chỉ mục** cho trang chủ, `/thiet-bi/` và các trang `/thuong-hieu/…`.

## Chỉnh sửa nội dung thường gặp

- **Văn bản, dịch vụ, thương hiệu, chính sách bảo mật:** sửa trong `src/index.html`
  (mỗi trang là một khối `<!-- view:… -->`, ví dụ trang Thiết bị & Thương hiệu là `view:thiet-bi`).
- **Trang thương hiệu (SEO địa phương):** mỗi hãng trong `src/brands.json` có một trang riêng `/thuong-hieu/<mã-hãng>/`
  với tiêu đề, H1, mô tả dạng "Thiết bị vệ sinh INAX tại Đồng Xoài", giới thiệu, sản phẩm, ảnh, câu hỏi thường gặp.
  Sửa nội dung VI/EN trong `src/brands.json`; thêm hãng mới = thêm một mục (và logo, ảnh nếu có).
- **Tiêu đề và mô tả hiển thị trên Google:** sửa trong `src/pages.json` (nên giữ tiêu đề dưới ~65 ký tự, mô tả ~150–160 ký tự).
- **Thêm trang mới:** thêm một khối `<!-- view:ten-trang -->…<!-- /view:ten-trang -->` vào `src/index.html`
  (thẻ `<section class="view" data-view="ten-trang" … hidden>`, đúng một thẻ `<h1>`), thêm trang vào `src/pages.json`
  và thêm liên kết vào menu. `scripts/build.py` sẽ báo lỗi nếu thiếu khối hoặc sai số lượng `<h1>`.
- **Song ngữ VI/EN:** tiếng Việt viết trực tiếp trong `src/index.html`, tiếng Anh nằm trong `src/assets/js/i18n-en.js`
  (tiêu đề/mô tả SEO tiếng Anh nằm trong `src/pages.json`).
  - Đoạn văn ngắn: thẻ HTML có `data-i18n="khoa"` → sửa tiếng Việt trong `index.html`, sửa tiếng Anh ở dòng `'khoa': '...'` trong `i18n-en.js`.
  - Thuộc tính (aria-label, title): `data-i18n-attr="aria-label:khoa"`.
  - Thêm đoạn mới: thêm `data-i18n="khoa-moi"` vào thẻ và thêm `'khoa-moi': '...'` vào `i18n-en.js`. Thiếu bản dịch thì trang tự hiển thị tiếng Việt.
  - Chính sách bảo mật là văn bản dài nên có hai bản riêng trong `index.html`: khối `data-lang="vi"` và khối `data-lang="en"` – nhớ sửa cả hai.
- **Ngày cập nhật chính sách bảo mật:** tìm `Cập nhật lần cuối` trong `index.html` và `pp.updated` trong `i18n-en.js`.
- **Màu thương hiệu:** biến CSS ở đầu `src/assets/css/styles.css`.
- **Tên miền khác `vuonggiaphu.com`:** sửa `site` trong `src/pages.json` và dòng `Sitemap:` trong `src/robots.txt`.
- **Logo thương hiệu:** lấy từ website chính thức của từng hãng, nằm trong `src/assets/img/brands/` với tên đúng mã hãng
  (vd. `inax.webp`, `toto.svg` – danh sách trong `src/assets/img/brands/README.md`). Khi build, tên hãng dạng chữ tự được thay
  bằng logo; hãng chưa có file logo (hiện là Senko) vẫn hiển thị tên dạng chữ.
- **Ảnh sản phẩm mẫu:** ảnh thật lấy từ website chính thức của các hãng, nằm trong `src/assets/img/products/<danh-muc>/`
  và được khai báo trong `src/products.json` (hướng dẫn trong `src/assets/img/products/README.md`; `"fit": "cover"` cho ảnh
  chụp trong không gian thật, mặc định hiển thị trọn sản phẩm).
- **Bản quyền hình ảnh:** logo và ảnh sản phẩm là nhãn hiệu/tác phẩm của các hãng, được dùng để giới thiệu sản phẩm mà công ty
  cung cấp; nên xin xác nhận của hãng hoặc nhà phân phối, và gỡ ngay nếu hãng yêu cầu. Không ghi giá, không giỏ hàng.
  Nếu là đại lý/nhà phân phối ủy quyền của hãng nào, có thể ghi rõ – chỉ khi có giấy ủy quyền.
- **Không thu thập thông tin khách hàng:** website không có biểu mẫu nhập liệu, giỏ hàng hay đặt hàng trực tuyến –
  khách liên hệ qua điện thoại, Zalo, email. Nếu sau này thêm form, giỏ hàng hoặc đặt hàng/thanh toán trực tuyến,
  cần cập nhật Chính sách bảo mật và kiểm tra nghĩa vụ thông báo theo Luật Thương mại điện tử 2025 / Nghị định 248/2026/NĐ-CP.
