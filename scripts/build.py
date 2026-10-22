#!/usr/bin/env python3
"""Build the static site: src/ -> dist/.

src/index.html is a template holding every page as a <!-- view:ROUTE --> ... <!-- /view:ROUTE --> block.
For each page in src/pages.json this writes dist/<path>/index.html containing only that page's
view (so every URL has its own content, <title>, description, canonical URL and structured data),
copies the other files in src/ and generates sitemap.xml. Python 3 standard library only.

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
GENERATED = {"index.html", "pages.json", "sitemap.xml"}  # not copied as-is

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

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SRC, DIST, ignore=lambda d, names: GENERATED if Path(d) == SRC else [])

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
