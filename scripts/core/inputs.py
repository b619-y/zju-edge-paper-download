from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from .models import NormalizedInput, Publisher


DOI_PREFIX_TO_PUBLISHER: tuple[tuple[str, Publisher], ...] = (
    ("10.1021/", "acs"),
    ("10.1038/", "nature"),
    ("10.1126/", "science"),
    ("10.1016/", "sciencedirect"),
)


def is_doi(value: str) -> bool:
    return value.startswith("10.") and "/" in value


def detect_publisher(raw: str) -> Publisher:
    value = raw.strip()
    if not value:
        raise ValueError("empty input")

    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        host = parsed.netloc.lower()
        if host.endswith("doi.org"):
            return detect_publisher(parsed.path.strip("/"))
        if host.endswith("pubs.acs.org"):
            return "acs"
        if host.endswith("nature.com"):
            return "nature"
        if host.endswith("science.org") or host.endswith("sciencemag.org"):
            return "science"
        if host.endswith("sciencedirect.com"):
            return "sciencedirect"
        raise ValueError(f"unsupported publisher URL: {raw}")

    for prefix, publisher in DOI_PREFIX_TO_PUBLISHER:
        if value.startswith(prefix):
            return publisher

    raise ValueError(f"unsupported DOI or URL: {raw}")


def normalize_entry(raw: str, forced_publisher: Publisher | None = None) -> NormalizedInput:
    value = raw.strip()
    if not value:
        raise ValueError("empty input")

    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        if parsed.netloc.lower().endswith("doi.org"):
            doi = parsed.path.strip("/")
            publisher = forced_publisher or detect_publisher(doi)
            return NormalizedInput(
                raw=raw,
                canonical=doi,
                publisher=publisher,
                kind="doi",
                doi=doi,
            )

        publisher = forced_publisher or detect_publisher(value)
        cleaned = parsed._replace(query="", fragment="").geturl()
        doi = _extract_doi_from_url(parsed, publisher)
        return NormalizedInput(
            raw=raw,
            canonical=cleaned,
            publisher=publisher,
            kind="url",
            doi=doi,
            article_url=cleaned,
        )

    publisher = forced_publisher or detect_publisher(value)
    return NormalizedInput(
        raw=raw,
        canonical=value,
        publisher=publisher,
        kind="doi",
        doi=value,
    )


def load_inputs(
    values: list[str] | tuple[str, ...],
    from_file: Path | None,
    forced_publisher: Publisher | None = None,
) -> list[NormalizedInput]:
    items = list(values)
    if from_file:
        for raw in from_file.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if line:
                items.append(line)

    if not items:
        raise SystemExit("no DOI or publisher URL provided")

    normalized: list[NormalizedInput] = []
    seen: set[str] = set()
    for item in items:
        entry = normalize_entry(item, forced_publisher=forced_publisher)
        if entry.canonical in seen:
            continue
        seen.add(entry.canonical)
        normalized.append(entry)
    return normalized


def _extract_doi_from_url(parsed, publisher: Publisher) -> str | None:
    path = parsed.path.strip("/")
    if publisher == "acs" and path.startswith("doi/"):
        return path[len("doi/") :]
    if publisher == "science" and path.startswith("doi/"):
        return path[len("doi/") :]
    return None
