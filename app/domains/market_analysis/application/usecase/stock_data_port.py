from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class StockData:
    name: str
    code: str
    themes: list[str] = field(default_factory=list)


class StockDataPort(ABC):
    @abstractmethod
    def find_all(self) -> list[StockData]: ...
