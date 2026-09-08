from __future__ import annotations

from abc import ABC, abstractmethod
from urllib.parse import quote

from scripts.core.models import DownloadPlan, NormalizedInput


class PublisherAdapter(ABC):
    publisher: str

    @abstractmethod
    def build_plan(self, item: NormalizedInput) -> DownloadPlan:
        raise NotImplementedError

    @staticmethod
    def filename_for(item: NormalizedInput) -> str:
        label = item.doi or item.article_url or item.canonical
        safe = label.replace("https://", "").replace("http://", "")
        safe = safe.replace("/", "_").replace(":", "_").replace("?", "_")
        return f"{safe}.pdf"

    @staticmethod
    def acs_login_url(doi: str) -> str:
        redirect = quote(f"/doi/{doi}", safe="")
        return (
            "https://pubs.acs.org/action/ssostart"
            "?idp=https%3A%2F%2Fidp.zju.edu.cn%2Fidp%2Fshibboleth"
            f"&redirectUri={redirect}"
            "&federationId=urn%3Amace%3Ashibboleth%3Acarsifed"
        )
