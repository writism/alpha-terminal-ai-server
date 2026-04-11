from abc import ABC, abstractmethod
from app.domains.user_profile.domain.entity.user_profile import UserProfile


class UserProfileRepositoryPort(ABC):
    @abstractmethod
    def get_by_account_id(self, account_id: int) -> UserProfile | None: ...
