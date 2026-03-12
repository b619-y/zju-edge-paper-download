from pathlib import Path
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


from scripts.adapters import get_adapter
from scripts.core.inputs import normalize_entry


def test_acs_adapter_keeps_fast_path_and_login_retry():
    adapter = get_adapter("acs")
    plan = adapter.build_plan(normalize_entry("10.1021/acs.est.6c01242"))

    assert plan.publisher == "acs"
    assert plan.support_level == "verified"
    assert plan.primary_mode == "direct_pdf"
    assert plan.candidate_urls == [
        "https://pubs.acs.org/doi/pdf/10.1021/acs.est.6c01242?ref=article_openPDF"
    ]
    assert "action/ssostart" in plan.login_url


def test_nature_adapter_builds_pdf_candidate_and_article_fallback():
    adapter = get_adapter("nature")
    plan = adapter.build_plan(normalize_entry("10.1038/ncomms14183"))

    assert plan.publisher == "nature"
    assert plan.support_level == "first_class"
    assert plan.primary_mode == "article_then_pdf"
    assert plan.article_url == "https://doi.org/10.1038/ncomms14183"
    assert "https://www.nature.com/articles/ncomms14183.pdf" in plan.candidate_urls


def test_nature_adapter_includes_reference_pdf_pattern_for_modern_articles():
    adapter = get_adapter("nature")
    plan = adapter.build_plan(normalize_entry("10.1038/s41467-026-70488-y"))

    assert plan.publisher == "nature"
    assert "https://www.nature.com/articles/s41467-026-70488-y_reference.pdf" in plan.candidate_urls


def test_science_adapter_marks_support_as_exploratory():
    adapter = get_adapter("science")
    plan = adapter.build_plan(normalize_entry("10.1126/science.ada1091"))

    assert plan.publisher == "science"
    assert plan.support_level == "exploratory"
    assert plan.article_url == "https://www.science.org/doi/10.1126/science.ada1091"
    assert plan.candidate_urls[0] == "https://www.science.org/doi/pdf/10.1126/science.ada1091"


def test_sciencedirect_adapter_handles_article_url_inputs():
    adapter = get_adapter("sciencedirect")
    plan = adapter.build_plan(
        normalize_entry("https://www.sciencedirect.com/science/article/pii/S1876610217346770")
    )

    assert plan.publisher == "sciencedirect"
    assert plan.support_level == "exploratory"
    assert plan.article_url == "https://www.sciencedirect.com/science/article/pii/S1876610217346770"
    assert "pdfft" in plan.candidate_urls[0]
    assert plan.fallback_mode == "edge_cdp"


def test_sciencedirect_adapter_resolves_doi_to_article_url_when_available(monkeypatch):
    adapter = get_adapter("sciencedirect")
    monkeypatch.setattr(
        adapter,
        "_resolve_sciencedirect_article_url",
        lambda doi_url: "https://www.sciencedirect.com/science/article/pii/S0013935126005669?via=ihub",
    )

    plan = adapter.build_plan(normalize_entry("10.1016/j.envres.2026.124236"))

    assert plan.article_url == "https://www.sciencedirect.com/science/article/pii/S0013935126005669?via=ihub"
    assert plan.candidate_urls == [
        "https://www.sciencedirect.com/science/article/pii/S0013935126005669/pdfft?isDTMRedir=true&download=true",
        "https://www.sciencedirect.com/science/article/pii/S0013935126005669/pdf",
    ]


def test_sciencedirect_adapter_maps_linkinghub_pii_to_sciencedirect_article_url(monkeypatch):
    adapter = get_adapter("sciencedirect")
    monkeypatch.setattr(
        "scripts.adapters.sciencedirect.urlopen",
        lambda request, timeout=15: _FakeResponse("https://linkinghub.elsevier.com/retrieve/pii/S0013935126005669"),
    )

    article_url = adapter._resolve_sciencedirect_article_url("https://doi.org/10.1016/j.envres.2026.124236")

    assert article_url == "https://www.sciencedirect.com/science/article/pii/S0013935126005669?via=ihub"


class _FakeResponse:
    def __init__(self, url: str) -> None:
        self._url = url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self) -> str:
        return self._url
