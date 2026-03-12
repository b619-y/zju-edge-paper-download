from __future__ import annotations

from scripts.core.models import DownloadPlan, NormalizedInput

from .base import PublisherAdapter


class ACSAdapter(PublisherAdapter):
    publisher = "acs"

    def build_plan(self, item: NormalizedInput) -> DownloadPlan:
        if not item.doi:
            raise ValueError("ACS downloads require a DOI")
        doi = item.doi
        return DownloadPlan(
            publisher="acs",
            label=doi,
            filename=self.filename_for(item),
            article_url=f"https://pubs.acs.org/doi/{doi}",
            candidate_urls=[f"https://pubs.acs.org/doi/pdf/{doi}?ref=article_openPDF"],
            login_url=self.acs_login_url(doi),
            support_level="verified",
            primary_mode="direct_pdf",
            notes=["Preserves the existing ACS fast path and ZJU SSO retry."],
        )
