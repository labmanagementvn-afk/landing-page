# Vuong Gia Phu Solutions – Landing page

Website giới thiệu **Vuong Gia Phu Solutions Company Limited**, dạng single page app thuần HTML/CSS/JS:
không cần build, không framework, không backend. Toàn bộ trang khoảng 200 KB.

| Tab | Đường dẫn |
| --- | --- |
| Trang chủ | `/#trang-chu` |
| Giải pháp Công nghệ | `/#cong-nghe` |
| Giải pháp Nội thất | `/#noi-that` |
| Chính sách bảo mật | `/#chinh-sach-bao-mat` |
| Liên hệ (có trên mọi tab) | `/#lien-he` |

## Cấu trúc

```
public/                 ← thư mục được deploy
  index.html            ← toàn bộ nội dung các tab
  assets/css/styles.css
  assets/js/main.js     ← router theo hash, menu mobile, form liên hệ (mailto)
  assets/img/           ← logo, favicon, ảnh chia sẻ mạng xã hội
  404.html, robots.txt, sitemap.xml, site.webmanifest
brand/                  ← file logo gốc
firebase.json           ← cấu hình Firebase Hosting
.github/workflows/deploy.yml ← tự deploy lên GitHub Pages
```

## Xem thử trên máy

```bash
python3 -m http.server 8080 -d public
# mở http://localhost:8080
```

## Deploy

### Cách 1 – GitHub Pages (miễn phí, khuyên dùng)

1. Merge code vào nhánh `main`.
2. Trên GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
   Mỗi lần push lên `main`, workflow `Deploy to GitHub Pages` sẽ tự đăng trang.
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
firebase deploy --only hosting
```

Gắn tên miền trong **Firebase Console → Hosting → Add custom domain** và làm theo hướng dẫn DNS.

### Cách 3 – Cloudflare Pages / Netlify

Kết nối repo, để trống lệnh build, chọn thư mục xuất bản (output directory) là `public`.

## Chỉnh sửa nội dung thường gặp

- **Văn bản, dịch vụ, chính sách bảo mật:** sửa trực tiếp trong `public/index.html`
  (mỗi tab là một khối `<section data-view="...">`).
- **Ngày cập nhật chính sách bảo mật:** tìm `Cập nhật lần cuối` trong `index.html`.
- **Màu thương hiệu:** biến CSS ở đầu `public/assets/css/styles.css`.
- **Tên miền khác `vuonggiaphu.com`:** thay trong `index.html` (canonical, og:url, og:image, JSON-LD),
  `robots.txt` và `sitemap.xml`.
- **Form liên hệ:** hiện mở ứng dụng email của khách với nội dung điền sẵn (không cần server).
  Nếu muốn nhận form trực tiếp, có thể dùng dịch vụ miễn phí như Formspree hoặc Google Forms.
