from __future__ import annotations

from .acs import ACSAdapter
from .base import PublisherAdapter
from .nature import NatureAdapter
from .science import ScienceAdapter
from .sciencedirect import ScienceDirectAdapter


REGISTRY: dict[str, PublisherAdapter] = {
    "acs": ACSAdapter(),
    "nature": NatureAdapter(),
    "science": ScienceAdapter(),
    "sciencedirect": ScienceDirectAdapter(),
}


def get_adapter(publisher: str) -> PublisherAdapter:
    try:
        return REGISTRY[publisher]
    except KeyError as exc:
        raise ValueError(f"unsupported publisher: {publisher}") from exc
