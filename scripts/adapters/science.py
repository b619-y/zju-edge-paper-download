from __future__ import annotations

from scripts.core.models import DownloadPlan, NormalizedInput

from .base import PublisherAdapter


class ScienceAdapter(PublisherAdapter):
    publisher = "science"

    def build_plan(self, item: NormalizedInput) -> DownloadPlan:
        article_url = item.article_url or self._article_url_from_doi(item.doi)
        candidate_urls = []
        if item.doi:
            candidate_urls = [
                f"https://www.science.org/doi/pdf/{item.doi}",
                f"https://www.science.org/doi/pdf/{item.doi}?download=true",
            ]

        return DownloadPlan(
            publisher="science",
            label=item.doi or article_url or item.canonical,
            filename=self.filename_for(item),
            article_url=article_url,
            candidate_urls=candidate_urls,
            login_url=None,
            support_level="exploratory",
            primary_mode="article_then_pdf",
            notes=["Science adapter is exploratory; it reports article fallback when direct PDF heuristics fail."],
        )

    @staticmethod
    def _article_url_from_doi(doi: str | None) -> str | None:
        if not doi:
            return None
        return f"https://www.science.org/doi/{doi}"
