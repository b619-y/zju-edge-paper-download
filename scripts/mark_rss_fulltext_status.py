#!/usr/bin/env python3
"""Correct an RSS item when the publisher exposes only an abstract/auxiliary PDF."""
from __future__ import annotations

import argparse
import os
import re
import tempfile
from pathlib import Path


def mark_unavailable(rss: Path, guid: str, message: str) -> None:
    text = rss.read_text(encoding="utf-8")
    matches = list(re.finditer(r"<item(?:\s[^>]*)?>.*?</item>", text, re.S))
    target = next((m for m in matches if re.search(r"<guid(?:\s[^>]*)?>(.*?)</guid>", m.group(0), re.S) and re.search(r"<guid(?:\s[^>]*)?>(.*?)</guid>", m.group(0), re.S).group(1).strip() == guid), None)
    if target is None:
        raise ValueError(f"RSS item not found: {guid}")
    block = target.group(0)
    block = re.sub(r'<p><strong>全文状态：</strong>.*?</p>', f'<p><strong>全文状态：</strong>{message}</p>', block, count=1, flags=re.S)
    block = re.sub(r'<p><strong>本地全文：</strong>.*?</p>', '', block, count=1, flags=re.S)
    block = re.sub(r'<content:encoded><!\[CDATA\[.*?\]\]></content:encoded>', lambda _: '<content:encoded><![CDATA[<h2>Multi-modal learning with incomplete data</h2><p><strong>当前可用资产：</strong>Nature 官方页面摘要与元数据；当前没有可确认的正文全文 PDF。</p><p><strong>说明：</strong>' + message + '</p><p><a href="https://www.nature.com/articles/s41467-026-77212-w">打开 Nature 官方文章页</a></p><p><a href="file:///Users/b/Desktop/%E6%99%BA%E8%83%BD%E4%BD%93/RSS-%E5%B9%BF%E5%9F%9F%E8%AE%A2%E9%98%85/%E6%95%B0%E6%8D%AE%E5%A4%84%E7%90%86/Multi-modal%20learning%20with%20incomplete%20data.html">打开本地已保存页面</a></p><p><a href="file:///Users/b/Downloads/repro-s41467-026-77212-w_reference.pdf">打开 reference PDF（非正文）</a></p>]]></content:encoded>', block, count=1, flags=re.S)
    updated = text[:target.start()] + block + text[target.end():]
    fd, temp_name = tempfile.mkstemp(prefix=rss.name + ".", dir=rss.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, rss)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rss", type=Path, required=True)
    parser.add_argument("--guid", required=True)
    parser.add_argument("--message", required=True)
    args = parser.parse_args()
    mark_unavailable(args.rss.expanduser().resolve(), args.guid, args.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
