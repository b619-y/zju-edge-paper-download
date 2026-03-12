from __future__ import annotations

from scripts.core.models import DownloadPlan, NormalizedInput

from .base import PublisherAdapter


class NatureAdapter(PublisherAdapter):
    publisher = "nature"

    def build_plan(self, item: NormalizedInput) -> DownloadPlan:
        article_url = item.article_url or self._article_url_from_doi(item.doi)
        candidate_urls = self._candidate_urls(item, article_url)
        return DownloadPlan(
            publisher="nature",
            label=item.doi or article_url or item.canonical,
            filename=self.filename_for(item),
            article_url=article_url,
            candidate_urls=candidate_urls,
            login_url=None,
            support_level="first_class",
            primary_mode="article_then_pdf",
            notes=["Nature support is adapter-backed and may fall back to opening the article page."],
        )

    @staticmethod
    def _article_url_from_doi(doi: str | None) -> str | None:
        if not doi:
            return None
        return f"https://doi.org/{doi}"

    @staticmethod
    def _candidate_urls(item: NormalizedInput, article_url: str | None) -> list[str]:
        if article_url and "nature.com/articles/" in article_url:
            base = article_url.rstrip("/")
            return [
                f"{base}.pdf",
                f"{base}.pdf?download=true",
                f"{base}_reference.pdf",
                f"{base}_reference.pdf?download=true",
            ]
        if item.doi:
            slug = item.doi.split("/", 1)[1]
            return [
                f"https://www.nature.com/articles/{slug}.pdf",
                f"https://www.nature.com/articles/{slug}.pdf?download=true",
                f"https://www.nature.com/articles/{slug}_reference.pdf",
                f"https://www.nature.com/articles/{slug}_reference.pdf?download=true",
            ]
        return []
