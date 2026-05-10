#!/usr/bin/env python3
"""
Import GitBook source repos (job_desc, job_desc_en) into this MkDocs project.

Usage:
    python3 scripts/import_gitbook.py <kr_source> <en_source>

Where <kr_source> is a local clone of NaverTechCareers/job_desc and
<en_source> is a local clone of NaverTechCareers/job_desc_en.

Effects:
    docs/kr/**  - markdown files copied from <kr_source>, README.md renamed to index.md
    docs/en/**  - same, from <en_source>
    docs/assets/kr/**, docs/assets/en/** - images copied from .gitbook/assets/
    mkdocs.yml  - nav block between "# === NAV START ===" / "# === NAV END ===" rewritten

The importer is idempotent: rerunning wipes the destination trees and rebuilds.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
MKDOCS_YML = REPO_ROOT / "mkdocs.yml"

# === Markdown transforms ===

# Alt text may contain backslash-escaped chars like `\[` or `\]` — handle both.
_ALT = r"(?P<alt>(?:[^\]\\]|\\.)*)"

# ![alt](<../../../.gitbook/assets/Name with spaces.png>) — angle-bracketed form
IMG_BRACKETED_RE = re.compile(
    r"!\[" + _ALT + r"\]\(\s*<(?:\.\./)*\.gitbook/assets/(?P<name>[^>]+)>\s*\)"
)
# ![alt](../.gitbook/assets/foo.png) — bare form, no spaces in filename
IMG_BARE_RE = re.compile(
    r"!\[" + _ALT + r"\]\(\s*(?:\.\./)*\.gitbook/assets/(?P<name>[^)\s]+)\s*\)"
)

# {% embed url="https://..." %}
EMBED_RE = re.compile(r"\{%\s*embed\s+url=\"(?P<url>[^\"]+)\"\s*%\}")

# <a href="#anchor" id="anchor"></a>  (GitBook anchor trick — usually empty)
ANCHOR_RE = re.compile(r"<a\s+href=\"#[^\"]*\"\s+id=\"[^\"]*\"\s*>\s*</a>")

# Internal links: keep .md, but rewrite README.md → index.md
README_LINK_RE = re.compile(
    r"(?P<prefix>\]\()(?P<path>[^)#]*?)README\.md(?P<suffix>[#)])"
)


def _encode_asset(name: str) -> str:
    """URL-encode an asset filename so spaces, parens, and Korean chars work."""
    return quote(name, safe="/()")


def transform_markdown(text: str, lang: str) -> str:
    def img_sub(m: re.Match) -> str:
        alt = m.group("alt")
        name = m.group("name").strip()
        return f"![{alt}](/careers/assets/{lang}/{_encode_asset(name)})"

    text = IMG_BRACKETED_RE.sub(img_sub, text)
    text = IMG_BARE_RE.sub(img_sub, text)
    text = EMBED_RE.sub(lambda m: f"[{m.group('url')}]({m.group('url')})", text)
    text = ANCHOR_RE.sub("", text)
    text = README_LINK_RE.sub(
        lambda m: f"{m.group('prefix')}{m.group('path')}index.md{m.group('suffix')}",
        text,
    )
    return text


# === File tree copying ===

def copy_markdown_tree(src_root: Path, dst_root: Path, lang: str) -> None:
    if dst_root.exists():
        shutil.rmtree(dst_root)
    dst_root.mkdir(parents=True)

    for md in src_root.rglob("*.md"):
        rel = md.relative_to(src_root)
        # Skip SUMMARY.md (used only for nav generation)
        if rel.name == "SUMMARY.md":
            continue
        # Skip anything under .gitbook/
        if any(part == ".gitbook" for part in rel.parts):
            continue
        # README.md → index.md
        if rel.name == "README.md":
            rel = rel.with_name("index.md")
        out = dst_root / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        content = md.read_text(encoding="utf-8")
        out.write_text(transform_markdown(content, lang), encoding="utf-8")


def copy_assets(src_root: Path, dst_root: Path) -> None:
    src_assets = src_root / ".gitbook" / "assets"
    if dst_root.exists():
        shutil.rmtree(dst_root)
    if not src_assets.exists():
        return
    shutil.copytree(src_assets, dst_root)


# === SUMMARY.md → nav YAML ===

LINK_RE = re.compile(r"\[(?P<title>[^\]]+)\]\((?P<href>[^)]+)\)")


class NavNode:
    __slots__ = ("title", "href", "children")

    def __init__(self, title: str, href: str | None = None):
        self.title = title
        self.href = href
        self.children: list[NavNode] = []


def parse_summary(summary_path: Path, lang: str) -> list[NavNode]:
    """
    Parse a GitBook SUMMARY.md into a list of nav sections.

    Returns a list of top-level NavNodes. Each ## heading becomes a section node
    whose children are the bullet items under it. Bullets before the first ##
    are grouped under a synthetic "_root" section (caller picks them up).
    """
    text = summary_path.read_text(encoding="utf-8")
    sections: list[NavNode] = []
    current_section = NavNode("_root")
    sections.append(current_section)

    # Stack of (indent_level, node) for the current bullet path
    stack: list[tuple[int, NavNode]] = [(-1, current_section)]

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue

        # Section heading
        if line.startswith("## "):
            # Strip GitBook anchor suffix like '<a href="#x" id="x"></a>'
            heading = ANCHOR_RE.sub("", line[3:]).strip()
            heading = _clean_title(heading)
            current_section = NavNode(heading)
            sections.append(current_section)
            stack = [(-1, current_section)]
            continue

        # Bullet
        m = re.match(r"^(?P<indent>\s*)\*\s+(?P<rest>.*)$", line)
        if not m:
            continue
        indent = len(m.group("indent").replace("\t", "  "))
        rest = m.group("rest")
        link = LINK_RE.search(rest)
        if not link:
            continue
        title = _clean_title(link.group("title"))
        href_raw = link.group("href").strip()

        # External link? Skip.
        if href_raw.startswith(("http://", "https://", "mailto:")):
            continue

        href = _rewrite_href(href_raw, lang)

        node = NavNode(title, href)

        # Find parent based on indent
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not stack:
            stack.append((-1, current_section))
        stack[-1][1].children.append(node)
        stack.append((indent, node))

    return sections


def _clean_title(s: str) -> str:
    """Strip GitBook escape backslashes, control chars, and HTML entities."""
    s = s.replace("\\&", "&").replace("\\_", "_").replace("\\*", "*")
    s = s.replace("&amp;", "&")
    # Drop non-printable control characters (e.g. stray \x08 in source files)
    s = "".join(ch for ch in s if ch >= " " or ch in "\t")
    return s.strip()


def _rewrite_href(href: str, lang: str) -> str:
    """Convert a GitBook-relative href to a docs/<lang>/... mkdocs path."""
    # Drop fragments
    href = href.split("#", 1)[0]
    # README.md → index.md
    if href.endswith("README.md"):
        href = href[: -len("README.md")] + "index.md"
    elif href in ("", "README.md"):
        href = "index.md"
    return f"{lang}/{href}".replace("//", "/")


# === Nav serialization ===

def render_nav(kr_sections: list[NavNode], en_sections: list[NavNode]) -> str:
    """Render a YAML nav: block."""
    lines: list[str] = ["nav:"]
    lines.append("  - Home: index.md")

    def emit(node: NavNode, depth: int) -> None:
        indent = "  " * (depth + 1)
        if node.href and not node.children:
            lines.append(f"{indent}- {_yaml_str(node.title)}: {node.href}")
        else:
            lines.append(f"{indent}- {_yaml_str(node.title)}:")
            if node.href:
                lines.append(f"{indent}  - {node.href}")
            for child in node.children:
                emit(child, depth + 1)

    def emit_lang(label: str, sections: list[NavNode], lang_index: str) -> None:
        lines.append(f"  - {_yaml_str(label)}:")
        lines.append(f"    - {lang_index}")
        # _root section's children go directly under the lang;
        # drop a leading entry that just points back at the same index page.
        root = sections[0]
        for child in root.children:
            if child.href == lang_index and not child.children:
                continue
            emit(child, 1)
        # other sections become labelled subsections
        for sec in sections[1:]:
            if not sec.children and not sec.title.strip():
                continue
            if sec.title == "_root":
                continue
            lines.append(f"    - {_yaml_str(sec.title)}:")
            for child in sec.children:
                emit(child, 2)

    emit_lang("English", en_sections, "en/index.md")
    emit_lang("한국어", kr_sections, "kr/index.md")
    return "\n".join(lines) + "\n"


def _yaml_str(s: str) -> str:
    """Quote a YAML scalar if needed."""
    if not s:
        return '""'
    # Quote if it has special chars or starts with reserved punctuation
    needs_quote = (
        ":" in s
        or s[0] in "!&*-?|>%@`#,[]{}"
        or s.lstrip() != s
        or s.rstrip() != s
    )
    if needs_quote:
        escaped = s.replace('"', '\\"')
        return f'"{escaped}"'
    return s


# === mkdocs.yml splicing ===

NAV_START = "# === NAV START ==="
NAV_END = "# === NAV END ==="


def splice_nav(nav_yaml: str) -> None:
    text = MKDOCS_YML.read_text(encoding="utf-8")
    start_idx = text.find(NAV_START)
    end_idx = text.find(NAV_END)
    if start_idx == -1 or end_idx == -1:
        raise SystemExit(
            f"Could not find nav markers in {MKDOCS_YML}. "
            f"Expected '{NAV_START}' and '{NAV_END}'."
        )
    indented = "\n".join(
        nav_yaml.rstrip().splitlines()
    )
    new = (
        text[: start_idx + len(NAV_START)]
        + "\n"
        + indented
        + "\n"
        + text[end_idx:]
    )
    MKDOCS_YML.write_text(new, encoding="utf-8")


# === Main ===

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("kr_source", type=Path, help="local clone of NaverTechCareers/job_desc")
    p.add_argument("en_source", type=Path, help="local clone of NaverTechCareers/job_desc_en")
    args = p.parse_args(argv)

    for label, root in (("kr", args.kr_source), ("en", args.en_source)):
        if not (root / "SUMMARY.md").exists():
            raise SystemExit(f"{label} source {root} has no SUMMARY.md")

    print(f"[1/4] Copying markdown: {args.kr_source} → docs/kr/")
    copy_markdown_tree(args.kr_source, DOCS / "kr", "kr")
    print(f"[2/4] Copying markdown: {args.en_source} → docs/en/")
    copy_markdown_tree(args.en_source, DOCS / "en", "en")

    print(f"[3/4] Copying assets")
    copy_assets(args.kr_source, DOCS / "assets" / "kr")
    copy_assets(args.en_source, DOCS / "assets" / "en")

    print(f"[4/4] Generating nav from SUMMARY.md files")
    kr_nav = parse_summary(args.kr_source / "SUMMARY.md", "kr")
    en_nav = parse_summary(args.en_source / "SUMMARY.md", "en")
    splice_nav(render_nav(kr_nav, en_nav))

    print("Done. Run `mkdocs build --strict` to verify.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
