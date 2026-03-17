from app.domains.stock_normalizer.application.usecase.normalized_disclosure_repository_port import NormalizedDisclosureRepositoryPort
from app.domains.stock_normalizer.domain.entity.normalized_disclosure import NormalizedDisclosure


class InMemoryNormalizedDisclosureRepository(NormalizedDisclosureRepositoryPort):
    def __init__(self):
        self._storage: dict[str, NormalizedDisclosure] = {}

    async def save(self, disclosure: NormalizedDisclosure) -> NormalizedDisclosure:
        self._storage[disclosure.rcept_no] = disclosure
        return disclosure
