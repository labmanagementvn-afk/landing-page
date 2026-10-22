#!/usr/bin/env python3
"""Build the static site: src/ -> dist/.

src/index.html is a template holding every page as a <!-- view:ROUTE --> ... <!-- /view:ROUTE --> block.
For each page in src/pages.json this writes dist/<path>/index.html containing only that page's
view (so every URL has its own content, <title>, description, canonical URL and structured data),
copies the other files in src/ and generates sitemap.xml. Python 3 standard library only.

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
GENERATED = {"index.html", "pages.json", "products.json", "sitemap.xml"}  # not copied as-is
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


def apply_logos(template):
    logos = {}
    if BRANDS_DIR.is_dir():
        for f in sorted(BRANDS_DIR.iterdir()):
            if f.suffix.lower() in LOGO_EXTS:
                logos.setdefault(f.stem.lower(), f.name)

    def swap(m):
        slug, name = m.group(1), m.group(2)
        if slug not in logos:
            return m.group(0)
        return ('<li data-brand="%s" class="has-logo"><img src="/assets/img/brands/%s" alt="%s" title="%s" '
                'loading="lazy" decoding="async"></li>' % (slug, logos[slug], text_attr(name), text_attr(name)))

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
        figures.append(
            '<figure class="product"><div class="product-img"><img src="/assets/img/products/%s/%s" alt="%s" '
            'data-en-alt="%s" loading="lazy" decoding="async"></div><figcaption>%s<span data-en="%s">%s</span>'
            '</figcaption></figure>' % (
                category, html.escape(item["file"], quote=True), html.escape(alt_vi, quote=True),
                html.escape(alt_en, quote=True), "<strong>%s</strong>" % html.escape(brand) if brand else "",
                html.escape(en, quote=True), html.escape(vi)))
    return ('<div class="gallery"><h3 data-i18n="prod.gallery">Sản phẩm mẫu</h3><div class="gallery-grid">%s</div></div>'
            % "".join(figures))


def apply_galleries(template, products):
    slots = set(re.findall(r'<div data-gallery="([a-z0-9-]+)"></div>', template))
    for category in products:
        if category not in slots:
            fail('src/products.json: unknown category "%s" (known: %s)' % (category, ", ".join(sorted(slots))))
    return re.sub(r'<div data-gallery="([a-z0-9-]+)"></div>',
                  lambda m: gallery_html(m.group(1), products.get(m.group(1), [])), template)


def page_url(site, page):
    return site + page["path"]


def json_for_script(data):
    # Safe inside <script>: no "</script>" can appear in the output
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def structured_data(site, page):
    url = page_url(site, page)
    org_id, site_id = site + "/#organization", site + "/#website"
    graph = [
        dict({"@type": "LocalBusiness", "@id": org_id, "url": site + "/",
              "logo": site + "/assets/img/icon-512.png", "image": site + "/assets/img/og-image.jpg",
              "areaServed": {"@type": "AdministrativeArea", "name": "Đồng Nai"}}, **ORG),
        {"@type": "WebSite", "@id": site_id, "url": site + "/", "name": "Vuong Gia Phu Solutions",
         "inLanguage": ["vi", "en"], "publisher": {"@id": org_id}},
    ]
    webpage = {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": page["title"]["vi"],
               "description": page["description"]["vi"], "inLanguage": "vi",
               "isPartOf": {"@id": site_id}, "about": {"@id": org_id}}
    if page["path"] != "/":
        webpage["breadcrumb"] = {"@id": url + "#breadcrumb"}
        graph.append({"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": site + "/"},
            {"@type": "ListItem", "position": 2, "name": page["name"]["vi"], "item": url},
        ]})
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

    # Highlight this page in the navigation
    out = out.replace('data-route="%s"' % route, 'data-route="%s" class="active" aria-current="page"' % route)

    url = page_url(site, page)
    attr = lambda text: html.escape(text, quote=True)
    client_pages = [{k: p[k] for k in ("route", "path", "title", "description")} for p in pages]
    values = {
        "title": attr(page["title"]["vi"]),
        "description": attr(page["description"]["vi"]),
        "url": attr(url),
        "url_en": attr(url + "?lang=en"),
        "site": attr(site),
        "route": attr(route),
        "jsonld": json_for_script(structured_data(site, page)),
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
    template = apply_galleries(apply_logos(template), load_products())

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
