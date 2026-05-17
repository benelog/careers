#!/usr/bin/env python3
"""
QA script: compare GitBook source (A) vs MkDocs site (B).

Tiers:
  1. Structural completeness  — all GitBook pages exist in docs/kr/
  2. Asset completeness       — every image referenced in docs/kr/ exists on disk
  3. Broken links on B        — internal <a> + <img src> in deployed HTML
  4. Content metrics          — sampled pages: image count, heading count delta
  5. Image sizing             — sampled pages: img width/height/style A vs B

Usage:
    python3 scripts/qa_compare.py            # runs all tiers, writes qa-report.md
    python3 scripts/qa_compare.py --tier 1   # run only tier 1
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from html.parser import HTMLParser
from pathlib import Path
from typing import NamedTuple
from urllib.parse import quote, urljoin, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_KR = REPO_ROOT / "docs" / "kr"
ASSETS_KR = REPO_ROOT / "docs" / "assets" / "kr"

A_BASE = "https://naver-career.gitbook.io/kr"
B_BASE = "https://benelog.github.io/careers/kr"

SAMPLE_SLUGS = [
    # image-heavy pages
    "service/search/ai-and-data-platform",
    "service/clova",          # index page → /service/clova/
    "service/search/vision",
    # YouTube embed pages
    "service/search/nlp",     # index page → /service/search/nlp/
    "service/media",          # index page → /service/media/
    # gallery page
    "service/band",           # index page → /service/band/
    # plain text control
    "service/search/nlp/text-analysis",
    "service/search/websearch",
    "service/shopping/smartstore",
    "service/whale/browser",
]

# ── helpers ─────────────────────────────────────────────────────────────────

def gh_api(path: str) -> list | dict:
    result = subprocess.run(
        ["gh", "api", path, "--paginate"],
        capture_output=True, text=True, check=True,
    )
    # gh --paginate may produce multiple JSON objects; join arrays
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        # multiple pages: each line is a JSON array
        combined = []
        for line in result.stdout.splitlines():
            if line.strip():
                try:
                    obj = json.loads(line)
                    if isinstance(obj, list):
                        combined.extend(obj)
                    else:
                        combined.append(obj)
                except json.JSONDecodeError:
                    pass
        return combined


def fetch_html(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (QA-bot)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"__ERROR__: {e}"


def head_url(url: str, timeout: int = 10) -> int:
    req = urllib.request.Request(url, method="HEAD",
                                  headers={"User-Agent": "Mozilla/5.0 (QA-bot)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


# ── HTML parsers ─────────────────────────────────────────────────────────────

class ImgInfo(NamedTuple):
    src: str
    width: str
    height: str
    style: str
    alt: str


class PageMetrics(NamedTuple):
    imgs: list[ImgInfo]
    headings: int
    links: list[str]  # href values (internal only)


class _MetricsParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.imgs: list[ImgInfo] = []
        self.headings = 0
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        d = dict(attrs)
        if tag == "img":
            self.imgs.append(ImgInfo(
                src=d.get("src", ""),
                width=d.get("width", ""),
                height=d.get("height", ""),
                style=d.get("style", ""),
                alt=d.get("alt", ""),
            ))
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.headings += 1
        elif tag == "a":
            href = d.get("href", "")
            if href and not href.startswith(("http://", "https://", "mailto:", "#")):
                self.links.append(href)


def parse_page(html: str, base_url: str) -> PageMetrics:
    p = _MetricsParser(base_url)
    p.feed(html)
    return PageMetrics(imgs=p.imgs, headings=p.headings, links=p.links)


# ── slug utilities ────────────────────────────────────────────────────────────

def gitbook_path_to_slug(path: str) -> str:
    """Map a job_desc repo path to a URL slug (no leading/trailing slash)."""
    if path == "README.md":
        return ""
    if path.endswith("/README.md"):
        return path[: -len("/README.md")]
    if path.endswith(".md"):
        return path[: -len(".md")]
    return path


def mkdocs_path_to_slug(rel: Path) -> str:
    """Map a docs/kr relative path to a URL slug."""
    s = str(rel)
    if s == "index.md":
        return ""
    if s.endswith("/index.md"):
        return s[: -len("/index.md")]
    if s.endswith(".md"):
        return s[: -len(".md")]
    return s


def slug_to_a_url(slug: str) -> str:
    return f"{A_BASE}/{slug}" if slug else A_BASE


def slug_to_b_url(slug: str) -> str:
    return f"{B_BASE}/{slug}/" if slug else f"{B_BASE}/"


# ── image references in markdown ─────────────────────────────────────────────

IMG_HTML_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)


def _extract_md_image_urls(text: str) -> list[str]:
    """Extract markdown image URLs, correctly handling balanced parentheses."""
    results = []
    for m in re.finditer(r"!\[[^\]]*\]\(", text):
        start = m.end()
        depth = 1
        pos = start
        while pos < len(text) and depth > 0:
            if text[pos] == "(":
                depth += 1
            elif text[pos] == ")":
                depth -= 1
            pos += 1
        url = text[start : pos - 1].strip()
        # Strip optional title ("…" or '…') at end
        url = re.sub(r'\s+["\'][^"\']*["\']$', "", url).strip()
        results.append(url)
    return results


def extract_asset_refs(md_path: Path) -> list[str]:
    """Return asset filenames (not URLs) referenced in a markdown file."""
    text = md_path.read_text(encoding="utf-8", errors="replace")
    refs = []
    for src in _extract_md_image_urls(text):
        if "assets/" in src:
            refs.append(Path(src).name)
    for m in IMG_HTML_RE.finditer(text):
        src = m.group(1).strip()
        if "assets/" in src:
            refs.append(Path(src).name)
    return refs


# ─────────────────────────────────────────────────────────────────────────────
# Tier 1: Structural completeness
# ─────────────────────────────────────────────────────────────────────────────

def tier1_structural() -> dict:
    print("Tier 1: structural completeness …", flush=True)

    # A: slugs from job_desc repo
    data = gh_api("repos/NaverTechCareers/job_desc/git/trees/HEAD?recursive=1")
    tree = data.get("tree", data) if isinstance(data, dict) else data
    a_paths = [
        item["path"]
        for item in tree
        if isinstance(item, dict)
        and item.get("type") == "blob"
        and item.get("path", "").endswith(".md")
    ]
    # SUMMARY.md is GitBook's auto-generated table of contents, not content
    a_slugs = {gitbook_path_to_slug(p) for p in a_paths if p != "SUMMARY.md"}

    # B: slugs from docs/kr
    b_paths = list(DOCS_KR.rglob("*.md"))
    b_slugs = {mkdocs_path_to_slug(p.relative_to(DOCS_KR)) for p in b_paths}

    missing_in_b = sorted(a_slugs - b_slugs)
    extra_in_b = sorted(b_slugs - a_slugs)

    print(f"  A slugs: {len(a_slugs)}, B slugs: {len(b_slugs)}", flush=True)
    print(f"  Missing in B: {len(missing_in_b)}, Extra in B: {len(extra_in_b)}", flush=True)

    return {
        "a_count": len(a_slugs),
        "b_count": len(b_slugs),
        "missing_in_b": missing_in_b,
        "extra_in_b": extra_in_b,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tier 2: Asset completeness (local)
# ─────────────────────────────────────────────────────────────────────────────

def tier2_assets() -> dict:
    print("Tier 2: asset completeness …", flush=True)

    # Decode URL-encoded filenames for comparison
    from urllib.parse import unquote

    existing = {f.name for f in ASSETS_KR.rglob("*") if f.is_file()}
    existing_decoded = {unquote(n) for n in existing}

    broken: list[dict] = []
    for md_path in sorted(DOCS_KR.rglob("*.md")):
        for ref in extract_asset_refs(md_path):
            decoded = unquote(ref)
            if decoded not in existing_decoded and ref not in existing:
                rel = md_path.relative_to(DOCS_KR)
                broken.append({"file": str(rel), "missing_asset": ref})

    print(f"  Broken asset refs: {len(broken)}", flush=True)
    return {
        "total_assets": len(existing),
        "broken_refs": broken,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tier 3: Broken links / images on B (sampled)
# ─────────────────────────────────────────────────────────────────────────────

def tier3_broken_links(slugs: list[str]) -> dict:
    print(f"Tier 3: broken links/images on B ({len(slugs)} sampled pages) …", flush=True)

    broken_imgs: list[dict] = []
    broken_links: list[dict] = []

    for slug in slugs:
        url = slug_to_b_url(slug)
        html = fetch_html(url)
        if html.startswith("__ERROR__"):
            broken_links.append({"page": url, "href": "(page itself)", "status": 0, "error": html})
            continue

        metrics = parse_page(html, url)

        for img in metrics.imgs:
            src = img.src
            if not src or src.startswith("data:"):
                continue
            abs_src = urljoin(url, src)
            status = head_url(abs_src)
            if status not in (200, 206):
                broken_imgs.append({"page": url, "src": src, "status": status})

        for href in metrics.links:
            abs_href = urljoin(url, href)
            status = head_url(abs_href)
            if status not in (200, 206):
                broken_links.append({"page": url, "href": href, "status": status})

        time.sleep(0.3)

    print(f"  Broken imgs: {len(broken_imgs)}, Broken links: {len(broken_links)}", flush=True)
    return {"broken_imgs": broken_imgs, "broken_links": broken_links}


# ─────────────────────────────────────────────────────────────────────────────
# Tier 4 & 5: Content metrics + image sizing (sampled)
# ─────────────────────────────────────────────────────────────────────────────

def tier4_5_content_and_images(slugs: list[str]) -> dict:
    print(f"Tier 4/5: content metrics + image sizing ({len(slugs)} pages) …", flush=True)

    results = []

    for slug in slugs:
        url_a = slug_to_a_url(slug)
        url_b = slug_to_b_url(slug)
        print(f"  {slug} …", flush=True)

        html_a = fetch_html(url_a)
        time.sleep(0.5)
        html_b = fetch_html(url_b)
        time.sleep(0.5)

        err_a = html_a.startswith("__ERROR__")
        err_b = html_b.startswith("__ERROR__")

        if err_a or err_b:
            results.append({
                "slug": slug,
                "error_a": html_a if err_a else None,
                "error_b": html_b if err_b else None,
            })
            continue

        m_a = parse_page(html_a, url_a)
        m_b = parse_page(html_b, url_b)

        # image sizing comparison: pair by index
        img_pairs = []
        for i, (ia, ib) in enumerate(zip(m_a.imgs, m_b.imgs)):
            img_pairs.append({
                "index": i,
                "a_src": ia.src,
                "a_width": ia.width,
                "a_height": ia.height,
                "a_style": ia.style,
                "b_src": ib.src,
                "b_width": ib.width,
                "b_height": ib.height,
                "b_style": ib.style,
                "sizing_mismatch": (
                    ia.width != ib.width or ia.height != ib.height
                ),
            })

        results.append({
            "slug": slug,
            "url_a": url_a,
            "url_b": url_b,
            "headings_a": m_a.headings,
            "headings_b": m_b.headings,
            "img_count_a": len(m_a.imgs),
            "img_count_b": len(m_b.imgs),
            "img_count_delta": len(m_b.imgs) - len(m_a.imgs),
            "img_pairs": img_pairs,
        })

    return {"pages": results}


# ─────────────────────────────────────────────────────────────────────────────
# Report generation
# ─────────────────────────────────────────────────────────────────────────────

def render_report(t1: dict, t2: dict, t3: dict, t45: dict) -> str:
    lines = [
        "# QA Report: GitBook → MkDocs",
        "",
        f"Source A: {A_BASE}  ",
        f"Site B:   {B_BASE}  ",
        "",
        "---",
        "",
        "## Tier 1 — Structural Completeness",
        "",
        f"| | Count |",
        f"|---|---|",
        f"| GitBook pages (A) | {t1['a_count']} |",
        f"| MkDocs pages (B)  | {t1['b_count']} |",
        f"| Missing in B      | **{len(t1['missing_in_b'])}** |",
        f"| Extra in B        | {len(t1['extra_in_b'])} |",
        "",
    ]

    if t1["missing_in_b"]:
        lines += ["### Pages in A missing from B", ""]
        for slug in t1["missing_in_b"]:
            lines.append(f"- `{slug or '(root)'}` → {slug_to_a_url(slug)}")
        lines.append("")

    if t1["extra_in_b"]:
        lines += ["### Pages in B not in A (added locally)", ""]
        for slug in t1["extra_in_b"]:
            lines.append(f"- `{slug or '(root)'}`")
        lines.append("")

    lines += [
        "---",
        "",
        "## Tier 2 — Asset Completeness",
        "",
        f"| | Count |",
        f"|---|---|",
        f"| Assets in docs/assets/kr/ | {t2['total_assets']} |",
        f"| Broken asset references    | **{len(t2['broken_refs'])}** |",
        "",
    ]

    if t2["broken_refs"]:
        lines += ["### Broken image references (file not on disk)", ""]
        lines.append("| File | Missing asset |")
        lines.append("|------|--------------|")
        for r in t2["broken_refs"][:50]:
            lines.append(f"| `{r['file']}` | `{r['missing_asset']}` |")
        if len(t2["broken_refs"]) > 50:
            lines.append(f"| … | _(+{len(t2['broken_refs'])-50} more)_ |")
        lines.append("")

    lines += [
        "---",
        "",
        "## Tier 3 — Broken Links & Images on Live B (sampled)",
        "",
        f"| | Count |",
        f"|---|---|",
        f"| Broken images | **{len(t3['broken_imgs'])}** |",
        f"| Broken links  | **{len(t3['broken_links'])}** |",
        "",
    ]

    if t3["broken_imgs"]:
        lines += ["### Broken images", ""]
        lines.append("| Page | src | HTTP |")
        lines.append("|------|-----|------|")
        for r in t3["broken_imgs"]:
            lines.append(f"| {r['page']} | `{r['src'][:60]}` | {r['status']} |")
        lines.append("")

    if t3["broken_links"]:
        lines += ["### Broken links", ""]
        lines.append("| Page | href | HTTP |")
        lines.append("|------|------|------|")
        for r in t3["broken_links"]:
            lines.append(f"| {r['page']} | `{r['href'][:60]}` | {r['status']} |")
        lines.append("")

    lines += [
        "---",
        "",
        "## Tier 4 & 5 — Content Metrics & Image Sizing (sampled pages)",
        "",
    ]

    for page in t45["pages"]:
        slug = page["slug"]
        lines.append(f"### `{slug}`")
        lines.append("")
        if "error_a" in page or "error_b" in page:
            if page.get("error_a"):
                lines.append(f"⚠️ A fetch error: `{page['error_a']}`")
            if page.get("error_b"):
                lines.append(f"⚠️ B fetch error: `{page['error_b']}`")
            lines.append("")
            continue

        img_delta = page["img_count_delta"]
        hd_delta = page["headings_b"] - page["headings_a"]
        delta_flag = " ⚠️" if abs(img_delta) > 2 else ""
        hd_flag = " ⚠️" if abs(hd_delta) > 3 else ""

        lines += [
            f"| Metric | A | B | Delta |",
            f"|--------|---|---|-------|",
            f"| Images | {page['img_count_a']} | {page['img_count_b']} | {img_delta:+d}{delta_flag} |",
            f"| Headings | {page['headings_a']} | {page['headings_b']} | {hd_delta:+d}{hd_flag} |",
            "",
        ]

        sizing_issues = [p for p in page.get("img_pairs", []) if p["sizing_mismatch"]]
        if sizing_issues:
            lines += ["**Image sizing mismatches:**", ""]
            lines.append("| # | A width | A height | A style | B width | B height | B style |")
            lines.append("|---|---------|----------|---------|---------|----------|---------|")
            for p in sizing_issues:
                lines.append(
                    f"| {p['index']+1}"
                    f" | `{p['a_width'] or '—'}`"
                    f" | `{p['a_height'] or '—'}`"
                    f" | `{p['a_style'][:30] or '—'}`"
                    f" | `{p['b_width'] or '—'}`"
                    f" | `{p['b_height'] or '—'}`"
                    f" | `{p['b_style'][:30] or '—'}` |"
                )
            lines.append("")
        elif page.get("img_pairs"):
            lines.append("✅ All image width/height attributes match (or both sides have none).")
            lines.append("")
        else:
            lines.append("_(No images on this page, or counts differ too much to pair.)_")
            lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4], default=0,
                        help="Run only this tier (0 = all)")
    parser.add_argument("--out", default=str(REPO_ROOT / "qa-report.md"))
    args = parser.parse_args()

    t1 = tier1_structural() if args.tier in (0, 1) else {"a_count": 0, "b_count": 0, "missing_in_b": [], "extra_in_b": []}
    t2 = tier2_assets() if args.tier in (0, 2) else {"total_assets": 0, "broken_refs": []}
    t3 = tier3_broken_links(SAMPLE_SLUGS) if args.tier in (0, 3) else {"broken_imgs": [], "broken_links": []}
    t45 = tier4_5_content_and_images(SAMPLE_SLUGS) if args.tier in (0, 4) else {"pages": []}

    report = render_report(t1, t2, t3, t45)

    out_path = Path(args.out)
    out_path.write_text(report, encoding="utf-8")
    print(f"\n✅ Report written to {out_path}", flush=True)


if __name__ == "__main__":
    main()
