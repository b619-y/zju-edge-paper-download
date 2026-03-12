from __future__ import annotations

from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from scripts.core.models import DownloadPlan, NormalizedInput

from .base import PublisherAdapter


class ScienceDirectAdapter(PublisherAdapter):
    publisher = "sciencedirect"

    def build_plan(self, item: NormalizedInput) -> DownloadPlan:
        article_url = item.article_url or self._article_url_from_doi(item.doi)
        return DownloadPlan(
            publisher="sciencedirect",
            label=item.doi or article_url or item.canonical,
            filename=self.filename_for(item),
            article_url=article_url,
            candidate_urls=self._candidate_urls(article_url),
            login_url=None,
            support_level="exploratory",
            primary_mode="article_then_pdf",
            fallback_mode="edge_cdp",
            notes=["ScienceDirect support is exploratory and may require manual article-page interaction."],
        )

    def _article_url_from_doi(self, doi: str | None) -> str | None:
        if not doi:
            return None
        doi_url = f"https://doi.org/{doi}"
        resolved = self._resolve_sciencedirect_article_url(doi_url)
        return resolved or doi_url

    @staticmethod
    def _resolve_sciencedirect_article_url(doi_url: str) -> str | None:
        request = Request(
            doi_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        try:
            with urlopen(request, timeout=15) as response:
                final_url = response.geturl()
        except (URLError, TimeoutError, ValueError):
            return None

        parsed = urlparse(final_url)
        if parsed.netloc.lower().endswith("linkinghub.elsevier.com") and "/retrieve/pii/" in parsed.path:
            pii = parsed.path.rsplit("/retrieve/pii/", 1)[-1].strip("/")
            if pii:
                return f"https://www.sciencedirect.com/science/article/pii/{pii}?via=ihub"
        if parsed.netloc.lower().endswith("sciencedirect.com") and "/science/article/pii/" in parsed.path:
            return parsed._replace(fragment="").geturl()
        return None

    @staticmethod
    def _candidate_urls(article_url: str | None) -> list[str]:
        if not article_url:
            return []
        parsed = urlparse(article_url)
        if parsed.netloc.endswith("sciencedirect.com") and "/science/article/pii/" in parsed.path:
            base = parsed._replace(query="", fragment="").geturl().rstrip("/")
            return [
                f"{base}/pdfft?isDTMRedir=true&download=true",
                f"{base}/pdf",
            ]
        return []
