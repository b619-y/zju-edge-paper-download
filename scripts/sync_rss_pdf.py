#!/usr/bin/env python3
"""Write a verified local PDF result back to one RSS item by GUID/DOI."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape


def verify_pdf(path: Path) -> tuple[int, str]:
    if not path.is_file():
        raise ValueError(f"PDF does not exist: {path}")
    with path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ValueError(f"not a PDF: {path}")
        handle.seek(0)
        digest = hashlib.sha256()
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    size = path.stat().st_size
    if size <= 5:
        raise ValueError(f"PDF is empty or truncated: {path}")
    return size, digest.hexdigest()


class _ArticleExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.depth = 0
        self.capture_depth: int | None = None
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.capture_depth is None and tag == "article" and dict(attrs).get("lang") == "en":
            self.capture_depth = self.depth
        if self.capture_depth is not None:
            self.parts.append(self.get_starttag_text() or f"<{tag}>")
        self.depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.capture_depth is not None:
            self.parts.append(self.get_starttag_text() or f"<{tag}/>" )

    def handle_endtag(self, tag: str) -> None:
        self.depth -= 1
        if self.capture_depth is not None:
            self.parts.append(f"</{tag}>")
            if tag == "article" and self.depth == self.capture_depth:
                self.capture_depth = None

    def handle_data(self, data: str) -> None:
        if self.capture_depth is not None and self.capture_depth >= 0:
            self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if self.capture_depth is not None and self.capture_depth >= 0:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self.capture_depth is not None and self.capture_depth >= 0:
            self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        if self.capture_depth is not None and self.capture_depth >= 0:
            self.parts.append(f"<!--{data}-->")


def extract_article_html(path: Path) -> str:
    parser = _ArticleExtractor()
    parser.feed(path.read_text(encoding="utf-8"))
    body = "".join(parser.parts).strip()
    if len(body) < 1000:
        raise ValueError(f"main article body not found or too short: {path}")
    return body


def sync_item(rss_path: Path, guid: str, pdf_path: Path, source_url: str | None, note: str | None, html_path: Path | None) -> dict[str, object]:
    size, sha256 = verify_pdf(pdf_path.resolve())
    text = rss_path.read_text(encoding="utf-8")
    item_matches = list(re.finditer(r"<item(?:\s[^>]*)?>.*?</item>", text, re.S))
    target = None
    for match in item_matches:
        guid_match = re.search(r"<guid(?:\s[^>]*)?>(.*?)</guid>", match.group(0), re.S)
        if guid_match and guid_match.group(1).strip() == guid:
            target = match
            break
    if target is None:
        raise ValueError(f"RSS item not found for GUID: {guid}")

    timestamp = datetime.now(timezone.utc).isoformat()
    href = "file://" + quote(str(pdf_path.resolve()))
    source = escape(source_url or "")
    article_html = extract_article_html(html_path) if html_path else None
    note_html = f'<p><strong>资产说明：</strong>{escape(note)}</p>\n' if note else ''
    additions = (
        f'<p><strong>PDF状态：</strong>已下载并校验（{size:,} bytes，SHA-256：{sha256}）。</p>'
        f'<p><strong>本地PDF：</strong><a href="{href}">打开已校验 PDF</a></p>'
        f'<p><strong>下载时间：</strong>{escape(timestamp)} · <strong>来源：</strong>{source}</p>\n'
        + note_html
    )
    block = target.group(0)
    block = re.sub(r'<p><strong>PDF状态：</strong>.*?</p>\s*', '', block, flags=re.S)
    block = re.sub(r'<p><strong>本地PDF：</strong>.*?</p>\s*', '', block, flags=re.S)
    block = re.sub(r'<p><strong>下载时间：</strong>.*?</p>\s*', '', block, flags=re.S)
    block = re.sub(
        r'(<description><!\[CDATA\[)',
        lambda m: m.group(1) + additions,
        block,
        count=1,
    )
    if article_html is not None:
        block = re.sub(r'<content:encoded><!\[CDATA\[.*?\]\]></content:encoded>', lambda _: '<content:encoded><![CDATA[' + article_html + f'<p><strong>本地PDF：</strong><a href="{href}">打开已校验 PDF</a></p>]]></content:encoded>', block, count=1, flags=re.S)
    else:
        block = re.sub(r'(<content:encoded><!\[CDATA\[)', lambda m: m.group(1) + f'<p><strong>本地PDF：</strong><a href="{href}">打开已校验 PDF</a></p>', block, count=1)
    updated = text[:target.start()] + block + text[target.end():]

    fd, temp_name = tempfile.mkstemp(prefix=rss_path.name + ".", dir=rss_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, rss_path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return {"status": "synced", "guid": guid, "pdf_path": str(pdf_path.resolve()), "bytes": size, "sha256": sha256, "downloaded_at": timestamp}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rss", type=Path, required=True)
    parser.add_argument("--guid", required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--source-url")
    parser.add_argument("--note", help="Optional qualification, e.g. reference PDF is not the main article")
    parser.add_argument("--fulltext-html", type=Path, help="Embed the main article element from a saved HTML page")
    args = parser.parse_args()
    print(sync_item(args.rss.expanduser().resolve(), args.guid, args.pdf.expanduser().resolve(), args.source_url, args.note, args.fulltext_html.expanduser().resolve() if args.fulltext_html else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
