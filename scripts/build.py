#!/usr/bin/env python3
"""Build the static site: src/ -> dist/.

src/index.html is a template holding every page as a <!-- view:ROUTE --> ... <!-- /view:ROUTE --> block.
For each page in src/pages.json this writes dist/<path>/index.html containing only that page's
view (so every URL has its own content, <title>, description, canonical URL and structured data),
copies the other files in src/ and generates sitemap.xml. Python 3 standard library only.

Brand pages: every brand in src/brands.json gets its own page /thuong-hieu/<slug>/ (local-SEO landing
page with its own title, description, H1, photos, FAQ and structured data); brand chips link to it.

Brand logos and product photos are optional and picked up automatically:
  - src/assets/img/brands/<slug>.svg|png|webp|jpg replaces the text chip <li data-brand="<slug>">.
  - src/products.json lists photos in src/assets/img/products/<category>/ shown in <div data-gallery="<category>">.

    python3 scripts/build.py
"""
import datetime
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
GENERATED = {"index.html", "pages.json", "products.json", "brands.json", "sitemap.xml"}  # not copied as-is
BRANDS_DIR = SRC / "assets" / "img" / "brands"
PRODUCTS_DIR = SRC / "assets" / "img" / "products"
LOGO_EXTS = (".svg", ".webp", ".png", ".jpg", ".jpeg")
PHOTO_EXTS = (".webp", ".jpg", ".jpeg", ".png", ".avif")
MAX_PHOTO_KB = 400

ORG = {
    "name": "Vuong Gia Phu Solutions Company Limited",
    "email": "vuong@vuonggiaphu.com",
    "telephone": "+84963345099",
    "taxID": "3801317389",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "951 Tôn Đức Thắng, Khu phố 1",
        "addressLocality": "Phường Đồng Xoài",
        "addressRegion": "Thành phố Đồng Nai",
        "addressCountry": "VN",
    },
    "hasMap": "https://maps.app.goo.gl/VMHAGvCfEx3ixXCLA",
}


def fail(msg):
    sys.exit("build failed: " + msg)


def text_attr(fragment):
    """HTML text from the template -> safe attribute value."""
    return html.escape(html.unescape(fragment), quote=True)


def find_logos():
    logos = {}
    if BRANDS_DIR.is_dir():
        for f in sorted(BRANDS_DIR.iterdir()):
            if f.suffix.lower() in LOGO_EXTS:
                logos.setdefault(f.stem.lower(), f.name)
    return logos


def apply_logos(template, logos, brand_slugs):
    def swap(m):
        slug, name = m.group(1), m.group(2)
        inner = name
        cls = ""
        if slug in logos:
            cls = ' class="has-logo"'
            inner = ('<img src="/assets/img/brands/%s" alt="%s" loading="lazy" decoding="async">'
                     % (logos[slug], text_attr(name)))
        if slug in brand_slugs:
            inner = '<a href="/thuong-hieu/%s/" title="%s">%s</a>' % (slug, text_attr(name), inner)
        return '<li data-brand="%s"%s>%s</li>' % (slug, cls, inner)

    out = re.sub(r'<li data-brand="([a-z0-9-]+)">([^<]+)</li>', swap, template)
    used = set(re.findall(r'data-brand="([a-z0-9-]+)"', template))
    for slug in sorted(set(logos) - used):
        print("warning: logo %s has no matching data-brand=\"%s\" in src/index.html" % (logos[slug], slug))
    return out


def load_products():
    path = SRC / "products.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    products = {k: v for k, v in data.items() if not k.startswith("_")}
    for category, items in products.items():
        for item in items:
            if not item.get("file") or not item.get("vi"):
                fail('src/products.json: every photo in "%s" needs "file" and "vi"' % category)
            photo = PRODUCTS_DIR / category / item["file"]
            if not photo.is_file():
                fail("src/products.json: %s not found" % photo.relative_to(ROOT))
            if photo.suffix.lower() not in PHOTO_EXTS:
                fail("%s: use one of %s" % (photo.relative_to(ROOT), ", ".join(PHOTO_EXTS)))
            size_kb = photo.stat().st_size // 1024
            if item.get("fit", "contain") not in ("contain", "cover"):
                fail('src/products.json: "fit" must be "contain" or "cover" (%s)' % item["file"])
            if size_kb > MAX_PHOTO_KB:
                print("warning: %s is %d KB – resize to ~800px wide / under 200 KB so pages stay fast"
                      % (photo.relative_to(ROOT), size_kb))
    return products


def gallery_html(category, items):
    if not items:
        return ""
    figures = []
    for item in items:
        brand = item.get("brand", "").strip()
        vi, en = item["vi"].strip(), (item.get("en") or item["vi"]).strip()
        alt_vi = "%s – %s" % (brand, vi) if brand else vi
        alt_en = "%s – %s" % (brand, en) if brand else en
        fit = " fit-cover" if item.get("fit") == "cover" else ""
        figures.append(
            '<figure class="product"><div class="product-img%s"><img src="/assets/img/products/%s/%s" alt="%s" '
            'data-en-alt="%s" loading="lazy" decoding="async"></div><figcaption>%s<span data-en="%s">%s</span>'
            '</figcaption></figure>' % (
                fit, category, html.escape(item["file"], quote=True), html.escape(alt_vi, quote=True),
                html.escape(alt_en, quote=True), "<strong>%s</strong>" % html.escape(brand) if brand else "",
                html.escape(en, quote=True), html.escape(vi)))
    return ('<div class="gallery"><h3 data-i18n="prod.gallery">Sản phẩm mẫu</h3><div class="gallery-grid">%s</div>'
            '<p class="gallery-note" data-i18n="prod.gallery.note">Hình ảnh sản phẩm từ website chính thức của các hãng.</p></div>'
            % "".join(figures))


def apply_galleries(template, products):
    slots = set(re.findall(r'<div data-gallery="([a-z0-9-]+)"></div>', template))
    for category in products:
        if category not in slots:
            fail('src/products.json: unknown category "%s" (known: %s)' % (category, ", ".join(sorted(slots))))
    return re.sub(r'<div data-gallery="([a-z0-9-]+)"></div>',
                  lambda m: gallery_html(m.group(1), products.get(m.group(1), [])), template)


CATEGORY_NAMES = {
    "thiet-bi-ve-sinh": ("thiết bị vệ sinh", "sanitary ware"),
    "bon-nuoc-may-nuoc-nong": ("bồn nước & nước nóng", "water tanks & water heating"),
    "thiet-bi-dien": ("thiết bị điện", "electrical"),
    "den-trang-tri": ("đèn trang trí", "decorative lighting"),
    "nha-thong-minh": ("nhà thông minh", "smart home"),
}


def bi(tag, vi, en, attrs=""):
    """Element with Vietnamese text and its English translation (switched by main.js via data-en)."""
    return '<%s%s data-en="%s">%s</%s>' % (tag, attrs, html.escape(en, quote=True), html.escape(vi), tag)


def load_brands():
    path = SRC / "brands.json"
    if not path.exists():
        return []
    brands = json.loads(path.read_text(encoding="utf-8"))["brands"]
    for b in brands:
        for key in ("slug", "name", "category", "kind", "title", "h1", "description", "intro", "products"):
            if key not in b:
                fail('src/brands.json: brand "%s" is missing "%s"' % (b.get("slug", "?"), key))
        if b["category"] not in CATEGORY_NAMES:
            fail('src/brands.json: unknown category "%s" for %s' % (b["category"], b["slug"]))
    return brands


def brand_page(b):
    return {"route": "brand-" + b["slug"], "path": "/thuong-hieu/%s/" % b["slug"], "nav": "thiet-bi",
            "parent": "thiet-bi", "brand": b["name"], "name": {"vi": b["name"], "en": b["name"]},
            "title": b["title"], "description": b["description"]}


def brand_view(b, brands, products, logos):
    name, slug = b["name"], b["slug"]
    kind_vi, kind_en = b["kind"]["vi"], b["kind"]["en"]
    route = "brand-" + slug
    logo = ""
    if slug in logos:
        logo = ('<div class="brand-hero-logo"><img src="/assets/img/brands/%s" alt="Logo %s" width="220" height="72" '
                'decoding="async"></div>' % (logos[slug], html.escape(name, quote=True)))
    photos = [p for p in products.get(b["category"], []) if p.get("brand", "").strip().lower() == name.lower()]
    gallery = gallery_html(b["category"], photos)
    siblings = [o for o in brands if o["category"] == b["category"] and o["slug"] != slug]
    cat_vi, cat_en = CATEGORY_NAMES[b["category"]]
    related = "".join('<li><a href="/thuong-hieu/%s/">%s</a></li>' % (o["slug"], html.escape(o["name"])) for o in siblings)
    faq = [
        ("Mua %s %s ở đâu tại Đồng Xoài?" % (kind_vi, name), "Where can I buy %s %s in Dong Xoai?" % (name, kind_en),
         "Bạn có thể liên hệ Vương Gia Phú tại 951 Tôn Đức Thắng, Khu phố 1, phường Đồng Xoài, Đồng Nai "
         "(khu vực Đồng Xoài, Bình Phước cũ), hoặc gọi/nhắn Zalo 0963.345.099 để được tư vấn %s %s." % (kind_vi, name),
         "Contact Vuong Gia Phu at 951 Ton Duc Thang Street, Quarter 1, Dong Xoai Ward, Dong Nai (Dong Xoai, formerly "
         "Binh Phuoc province), or call/message us on Zalo at +84 963 345 099 for advice on %s %s." % (name, kind_en)),
        ("Vương Gia Phú có lắp đặt %s %s tận nơi không?" % (kind_vi, name), "Do you install %s %s on site?" % (name, kind_en),
         "Có. Đội kỹ thuật của chúng tôi giao hàng và lắp đặt tại Đồng Xoài và các khu vực trong tỉnh Đồng Nai; "
         "với công trình ở xa, vui lòng liên hệ để được tư vấn.",
         "Yes. Our technicians deliver and install in Dong Xoai and across Dong Nai province; for projects further "
         "away, please contact us."),
        ("Giá %s %s bao nhiêu?" % (kind_vi, name), "How much do %s %s cost?" % (name, kind_en),
         "Website không niêm yết giá. Giá phụ thuộc mẫu mã và quy mô công trình – vui lòng gọi hoặc nhắn Zalo "
         "0963.345.099 để được tư vấn chọn sản phẩm phù hợp.",
         "We do not list prices on the website. Prices depend on the model and the size of the project – call or "
         "message us on Zalo at +84 963 345 099 for advice on the right product."),
    ]
    why = [
        ("Tư vấn chọn mẫu %s phù hợp không gian, nhu cầu và ngân sách." % name,
         "Advice on %s models that fit your space, needs and budget." % name),
        ("Giao hàng và lắp đặt tận nơi tại Đồng Xoài và các khu vực trong tỉnh Đồng Nai.",
         "Delivery and on-site installation in Dong Xoai and across Dong Nai province."),
        ("Hỗ trợ bảo hành theo chính sách của %s và hỗ trợ kỹ thuật sau lắp đặt." % name,
         "Warranty support under %s's policy and technical support after installation." % name),
    ]
    parts = [
        '\n    <!-- view:%s -->\n' % route,
        '    <section class="view" data-view="%s" aria-labelledby="%s-title" hidden>\n' % (route, route),
        '      <div class="page-hero page-hero-products">\n        <div class="container brand-hero">\n          <div>\n',
        '            <nav class="breadcrumb" aria-label="Breadcrumb" data-i18n-attr="aria-label:crumb.aria">'
        '<a href="/" data-i18n="nav.home">Trang chủ</a><span aria-hidden="true">›</span>'
        '<a href="/thiet-bi/" data-i18n="nav.products">Thiết bị &amp; Thương hiệu</a><span aria-hidden="true">›</span>'
        '<span aria-current="page">%s</span></nav>\n' % html.escape(name),
        '            ' + bi("h1", b["h1"]["vi"], b["h1"]["en"], ' id="%s-title"' % route) + '\n',
        '            ' + bi("p", b["description"]["vi"], b["description"]["en"], ' class="lead"') + '\n',
        '            <div class="hero-actions"><a class="btn btn-primary" href="tel:+84963345099"><svg class="icon"><use href="#i-phone"/></svg> '
        + bi("span", "Gọi 0963.345.099", "Call +84 963 345 099") + '</a>'
        '<a class="btn btn-outline" href="https://zalo.me/0963345099" target="_blank" rel="noopener"><svg class="icon"><use href="#i-chat"/></svg> '
        + bi("span", "Nhắn Zalo", "Message on Zalo") + '</a></div>\n',
        '          </div>\n          %s\n        </div>\n      </div>\n' % logo,
        '      <div class="section">\n        <div class="container narrow-wide">\n',
        '          ' + bi("h2", "Về thương hiệu %s" % name, "About %s" % name) + '\n',
        "".join('          ' + bi("p", vi, en) + '\n' for vi, en in zip(b["intro"]["vi"], b["intro"]["en"])),
        '          ' + bi("h2", "Sản phẩm %s Vương Gia Phú cung cấp" % name, "%s products we supply" % name) + '\n',
        '          <ul class="checklist checklist-cols">%s</ul>\n' % "".join(
            bi("li", vi, en) for vi, en in zip(b["products"]["vi"], b["products"]["en"])),
        ('          %s\n' % gallery) if gallery else '',
        '          ' + bi("h2", "Vì sao chọn mua %s %s tại Vương Gia Phú" % (kind_vi, name),
                        "Why buy %s %s from Vuong Gia Phu" % (name, kind_en)) + '\n',
        '          <ul class="checklist">%s</ul>\n' % "".join(bi("li", vi, en) for vi, en in why),
        '          ' + bi("h2", "Câu hỏi thường gặp về %s" % name, "%s FAQ" % name) + '\n',
        '          <div class="faq">%s</div>\n' % "".join(
            '<details>%s%s</details>' % (bi("summary", qv, qe), bi("p", av, ae)) for qv, qe, av, ae in faq),
        ('          ' + bi("h2", "Thương hiệu %s khác" % cat_vi, "Other %s brands" % cat_en) + '\n'
         '          <ul class="brands brand-links">%s</ul>\n' % related) if related else '',
        '          <p class="section-link"><a class="btn btn-outline" href="/thiet-bi/#%s">' % b["category"]
        + bi("span", "Xem tất cả thiết bị & thương hiệu", "See all products & brands")
        + ' <svg class="icon"><use href="#i-arrow"/></svg></a></p>\n',
        '          <p class="disclaimer" data-i18n="prod.disclaimer">Tên thương hiệu được nêu nhằm giới thiệu các dòng sản phẩm '
        'Vương Gia Phú tư vấn, cung cấp và lắp đặt; các nhãn hiệu thuộc quyền sở hữu của chủ sở hữu tương ứng. '
        'Website không bán hàng hay nhận đặt hàng trực tuyến.</p>\n',
        '        </div>\n      </div>\n    </section>\n    <!-- /view:%s -->\n' % route,
    ]
    return "".join(parts)


def page_url(site, page):
    return site + page["path"]


def json_for_script(data):
    # Safe inside <script>: no "</script>" can appear in the output
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def structured_data(site, page, by_route=None):
    url = page_url(site, page)
    org_id, site_id = site + "/#organization", site + "/#website"
    graph = [
        dict({"@type": "LocalBusiness", "@id": org_id, "url": site + "/",
              "logo": site + "/assets/img/icon-512.png", "image": site + "/assets/img/og-image.jpg",
              "areaServed": [{"@type": "City", "name": "Đồng Xoài"},
                             {"@type": "AdministrativeArea", "name": "Đồng Nai"}]}, **ORG),
        {"@type": "WebSite", "@id": site_id, "url": site + "/", "name": "Vuong Gia Phu Solutions",
         "inLanguage": ["vi", "en"], "publisher": {"@id": org_id}},
    ]
    webpage = {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": page["title"]["vi"],
               "description": page["description"]["vi"], "inLanguage": "vi",
               "isPartOf": {"@id": site_id}, "about": {"@id": org_id}}
    if page.get("brand"):
        webpage["about"] = [{"@id": org_id}, {"@type": "Brand", "name": page["brand"]}]
    if page["path"] != "/":
        webpage["breadcrumb"] = {"@id": url + "#breadcrumb"}
        trail = [("Trang chủ", site + "/")]
        parent = (by_route or {}).get(page.get("parent"))
        if parent:
            trail.append((parent["name"]["vi"], page_url(site, parent)))
        trail.append((page["name"]["vi"], url))
        graph.append({"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(trail)]})
    graph.append(webpage)
    return {"@context": "https://schema.org", "@graph": graph}


def render(template, site, pages, page):
    route = page["route"]
    out = template

    # Keep only this page's view block
    for other in pages:
        r = other["route"]
        pattern = re.compile(r"\n    <!-- view:%s -->\n.*?    <!-- /view:%s -->\n" % (re.escape(r), re.escape(r)), re.S)
        if len(pattern.findall(out)) != 1:
            fail("expected exactly one view block for '%s' in src/index.html" % r)
        if r != route:
            out = pattern.sub("\n", out)
    out, n = re.subn(r'(<section class="view" data-view="%s"[^>]*?) hidden>' % re.escape(route), r"\1>", out)
    if n != 1:
        fail("view '%s' must start hidden in the template" % route)

    # Highlight this page (or its section, for brand pages) in the navigation
    nav = page.get("nav", route)
    out = out.replace('data-route="%s"' % nav, 'data-route="%s" class="active" aria-current="page"' % nav)

    url = page_url(site, page)
    attr = lambda text: html.escape(text, quote=True)
    client_pages = [dict({k: p[k] for k in ("route", "path", "title", "description")}, nav=p.get("nav", p["route"]))
                    for p in pages]
    by_route = {p["route"]: p for p in pages}
    values = {
        "title": attr(page["title"]["vi"]),
        "description": attr(page["description"]["vi"]),
        "url": attr(url),
        "url_en": attr(url + "?lang=en"),
        "site": attr(site),
        "route": attr(route),
        "jsonld": json_for_script(structured_data(site, page, by_route)),
        "pages_json": json_for_script({"site": site, "pages": client_pages}),
    }
    for key, value in values.items():
        out = out.replace("{{%s}}" % key, value)
    if "{{" in out:
        fail("unknown placeholder left on page '%s': %s" % (route, re.findall(r"\{\{[^}]*\}\}", out)))
    if out.count("<h1") != 1:
        fail("page '%s' must have exactly one <h1>, found %d" % (route, out.count("<h1")))
    return out


def sitemap(site, pages, today):
    rows = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for page in pages:
        url = html.escape(page_url(site, page))
        rows += ["  <url>", "    <loc>%s</loc>" % url, "    <lastmod>%s</lastmod>" % today,
                 '    <xhtml:link rel="alternate" hreflang="vi" href="%s"/>' % url,
                 '    <xhtml:link rel="alternate" hreflang="en" href="%s?lang=en"/>' % url,
                 "  </url>"]
    rows.append("</urlset>")
    return "\n".join(rows) + "\n"


def main():
    config = json.loads((SRC / "pages.json").read_text(encoding="utf-8"))
    site, pages = config["site"].rstrip("/"), config["pages"]
    template = (SRC / "index.html").read_text(encoding="utf-8")
    products, brands, logos = load_products(), load_brands(), find_logos()
    pages = pages + [brand_page(b) for b in brands]
    marker = "\n    <!-- view:chinh-sach-bao-mat -->\n"
    if marker not in template:
        fail("src/index.html: brand pages are inserted before the privacy view, which was not found")
    template = template.replace(marker, "".join(brand_view(b, brands, products, logos) for b in brands) + marker)
    template = apply_galleries(apply_logos(template, logos, {b["slug"] for b in brands}), products)

    if DIST.exists():
        shutil.rmtree(DIST)
    skip = lambda d, names: [n for n in names if n.startswith(".") or n == "README.md" or (Path(d) == SRC and n in GENERATED)]
    shutil.copytree(SRC, DIST, ignore=skip)

    for page in pages:
        if not (page["path"].startswith("/") and page["path"].endswith("/")):
            fail("path must start and end with '/': %s" % page["path"])
        target = DIST / page["path"].lstrip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(template, site, pages, page), encoding="utf-8")
        for lang in ("vi", "en"):
            if len(page["title"][lang]) > 90:
                print("warning: long %s title on %s (%d chars)" % (lang, page["path"], len(page["title"][lang])))
        print("built", page["path"])

    (DIST / "sitemap.xml").write_text(sitemap(site, pages, datetime.date.today().isoformat()), encoding="utf-8")
    print("built /sitemap.xml -> dist/")


if __name__ == "__main__":
    main()
