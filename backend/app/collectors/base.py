from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.jobs.candidate import JobCandidate


@dataclass
class CollectionResult:
    source: str
    requested_count: int = 0
    candidates: list[JobCandidate] = field(default_factory=list)
    error: str | None = None

    @property
    def new_count(self) -> int:
        return len(self.candidates)


class Collector(ABC):
    source: str

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=30.0)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def collect(self) -> CollectionResult:
        try:
            candidates = self.fetch_candidates()
            return CollectionResult(source=self.source, requested_count=len(candidates), candidates=candidates)
        except (httpx.HTTPError, ValueError, KeyError) as error:
            return CollectionResult(source=self.source, error=str(error))

    @abstractmethod
    def fetch_candidates(self) -> list[JobCandidate]:
        raise NotImplementedError

    @staticmethod
    def first_value(payload: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if payload.get(key) not in (None, ""):
                return payload[key]
        return None
