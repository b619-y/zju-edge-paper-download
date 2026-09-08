from __future__ import annotations

import shutil
import time
from pathlib import Path


def file_signature(path: Path) -> tuple[int, int]:
    st = path.stat()
    return (st.st_mtime_ns, st.st_size)


def is_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(5) == b"%PDF-"
    except Exception:
        return False


def scan_pdfs(directory: Path) -> dict[Path, tuple[int, int]]:
    result: dict[Path, tuple[int, int]] = {}
    for path in directory.glob("*.pdf"):
        if path.is_file():
            result[path] = file_signature(path)
    return result


def wait_for_pdf(
    directory: Path,
    before: dict[Path, tuple[int, int]],
    start_ts: float,
    timeout_sec: int,
) -> Path | None:
    deadline = time.time() + timeout_sec
    stable_hits: dict[Path, tuple[int, int]] = {}
    while time.time() < deadline:
        now = scan_pdfs(directory)
        candidates: list[Path] = []
        for path, sig in now.items():
            previous = before.get(path)
            if previous != sig and path.stat().st_mtime >= start_ts - 1:
                candidates.append(path)
        candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        for candidate in candidates:
            if not is_pdf(candidate):
                continue
            sig = now[candidate]
            previous_sig = stable_hits.get(candidate)
            if previous_sig == sig:
                return candidate
            stable_hits[candidate] = sig
        time.sleep(1)
    return None


def move_to_target(downloaded: Path, target: Path) -> None:
    if downloaded.resolve() == target.resolve():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    shutil.move(str(downloaded), str(target))
