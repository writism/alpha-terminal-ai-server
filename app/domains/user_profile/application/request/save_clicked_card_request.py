from typing import Optional

from pydantic import BaseModel


class SaveClickedCardRequest(BaseModel):
    symbol: str
    name: str
    market: Optional[str] = None
