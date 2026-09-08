from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


Publisher = Literal["acs", "nature", "science", "sciencedirect"]
InputKind = Literal["doi", "url"]
SupportLevel = Literal["verified", "first_class", "exploratory"]
PrimaryMode = Literal["direct_pdf", "article_then_pdf"]
FallbackMode = Literal["edge_cdp"]


@dataclass(frozen=True)
class NormalizedInput:
    raw: str
    canonical: str
    publisher: Publisher
    kind: InputKind
    doi: str | None = None
    article_url: str | None = None


@dataclass(frozen=True)
class DownloadPlan:
    publisher: Publisher
    label: str
    filename: str
    article_url: str | None
    candidate_urls: list[str]
    login_url: str | None
    support_level: SupportLevel
    primary_mode: PrimaryMode
    fallback_mode: FallbackMode | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DownloadResult:
    success: bool
    target_path: Path | None
    failure_reason: str | None
    attempts: list[str]
    opened_article_fallback: bool
