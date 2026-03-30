from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StockTheme:
    name: str
    code: str
    themes: list[str] = field(default_factory=list)
    id: Optional[int] = None
