#!/usr/bin/env python3
"""Write a verified local PDF result back to one RSS item by GUID/DOI."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import tempfile
from datetime import datetime, timezone
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


def sync_item(rss_path: Path, guid: str, pdf_path: Path, source_url: str | None, note: str | None) -> dict[str, object]:
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
    block = re.sub(
        r'(<content:encoded><!\[CDATA\[)',
        lambda m: m.group(1) + f'<p><strong>本地PDF：</strong><a href="{href}">打开已校验 PDF</a></p>',
        block,
        count=1,
    )
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
    args = parser.parse_args()
    print(sync_item(args.rss.expanduser().resolve(), args.guid, args.pdf.expanduser().resolve(), args.source_url, args.note))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
