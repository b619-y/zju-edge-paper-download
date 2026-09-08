from pathlib import Path
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


from scripts.core.models import DownloadPlan
from scripts.core.runner import execute_plan


def test_runner_retries_login_after_first_failed_download(tmp_path):
    calls = []
    saved = tmp_path / "downloaded.pdf"
    saved.write_bytes(b"%PDF-1.4\n")

    plan = DownloadPlan(
        publisher="acs",
        label="10.1021/acs.est.6c01242",
        filename="10.1021_acs.est.6c01242.pdf",
        article_url="https://pubs.acs.org/doi/10.1021/acs.est.6c01242",
        candidate_urls=["https://pubs.acs.org/doi/pdf/10.1021/acs.est.6c01242?ref=article_openPDF"],
        login_url="https://pubs.acs.org/action/ssostart?idp=test",
        support_level="verified",
        primary_mode="direct_pdf",
    )

    waits = iter([None, saved])

    result = execute_plan(
        plan,
        open_url=lambda url: calls.append(url),
        wait_for_pdf=lambda: next(waits),
        move_to_target=lambda src, target: target.write_bytes(src.read_bytes()),
        validate_pdf=lambda path: True,
        target_dir=tmp_path / "final",
    )

    assert result.success is True
    assert calls == [
        "https://pubs.acs.org/doi/pdf/10.1021/acs.est.6c01242?ref=article_openPDF",
        "https://pubs.acs.org/action/ssostart?idp=test",
        "https://pubs.acs.org/doi/pdf/10.1021/acs.est.6c01242?ref=article_openPDF",
    ]


def test_runner_opens_article_fallback_when_pdf_never_downloads(tmp_path):
    calls = []
    plan = DownloadPlan(
        publisher="science",
        label="10.1126/science.ada1091",
        filename="10.1126_science.ada1091.pdf",
        article_url="https://www.science.org/doi/10.1126/science.ada1091",
        candidate_urls=["https://www.science.org/doi/pdf/10.1126/science.ada1091"],
        login_url=None,
        support_level="exploratory",
        primary_mode="article_then_pdf",
    )

    result = execute_plan(
        plan,
        open_url=lambda url: calls.append(url),
        wait_for_pdf=lambda: None,
        move_to_target=lambda src, target: None,
        validate_pdf=lambda path: True,
        target_dir=tmp_path / "final",
    )

    assert result.success is False
    assert result.failure_reason == "download_not_detected"
    assert calls == [
        "https://www.science.org/doi/pdf/10.1126/science.ada1091",
        "https://www.science.org/doi/10.1126/science.ada1091",
    ]


def test_runner_uses_browser_fallback_for_sciencedirect(tmp_path):
    calls = []
    plan = DownloadPlan(
        publisher="sciencedirect",
        label="https://www.sciencedirect.com/science/article/pii/S1876610217346770",
        filename="www.sciencedirect.com_science_article_pii_S1876610217346770.pdf",
        article_url="https://www.sciencedirect.com/science/article/pii/S1876610217346770",
        candidate_urls=[
            "https://www.sciencedirect.com/science/article/pii/S1876610217346770/pdfft?isDTMRedir=true&download=true"
        ],
        login_url=None,
        support_level="exploratory",
        primary_mode="article_then_pdf",
        fallback_mode="edge_cdp",
    )

    target_dir = tmp_path / "final"
    fallback_target = target_dir / plan.filename

    result = execute_plan(
        plan,
        open_url=lambda url: calls.append(url),
        wait_for_pdf=lambda: None,
        move_to_target=lambda src, target: None,
        validate_pdf=lambda path: True,
        target_dir=target_dir,
        browser_fallback=lambda current_plan, target: target.write_bytes(b"%PDF-1.4\n"),
    )

    assert result.success is True
    assert result.target_path == fallback_target
    assert calls == [
        "https://www.sciencedirect.com/science/article/pii/S1876610217346770/pdfft?isDTMRedir=true&download=true",
        "https://www.sciencedirect.com/science/article/pii/S1876610217346770",
    ]
