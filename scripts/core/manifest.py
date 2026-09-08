from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .downloads import is_pdf


def pdf_record(path: Path, *, source_urls: list[str] | None = None) -> dict[str, object]:
    path = path.resolve()
    if not path.is_file() or not is_pdf(path) or path.stat().st_size <= 5:
        raise ValueError(f"not a valid PDF: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "status": "verified",
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "source_urls": source_urls or [],
    }


def update_manifest(directory: Path, record: dict[str, object]) -> Path:
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / "download-manifest.json"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    records = data.setdefault("downloads", {})
    if not isinstance(records, dict):
        records = {}
        data["downloads"] = records
    records[Path(str(record["path"])).name] = record
    fd, temp_name = tempfile.mkstemp(prefix=".download-manifest-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, manifest_path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return manifest_path
