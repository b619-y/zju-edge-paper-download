import json
from pathlib import Path

from scripts.core.manifest import pdf_record, update_manifest


def test_verified_pdf_record_and_atomic_manifest(tmp_path: Path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.7\nexample")
    record = pdf_record(pdf, source_urls=["https://example.test/paper.pdf"])
    manifest = update_manifest(tmp_path, record)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["downloads"]["paper.pdf"]["status"] == "verified"
    assert data["downloads"]["paper.pdf"]["bytes"] == pdf.stat().st_size
