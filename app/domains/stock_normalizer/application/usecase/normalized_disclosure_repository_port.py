from abc import ABC, abstractmethod

from app.domains.stock_normalizer.domain.entity.normalized_disclosure import NormalizedDisclosure


class NormalizedDisclosureRepositoryPort(ABC):
    @abstractmethod
    async def save(self, disclosure: NormalizedDisclosure) -> NormalizedDisclosure:
        pass
