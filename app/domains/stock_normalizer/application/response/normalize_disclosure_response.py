from datetime import datetime

from pydantic import BaseModel


class NormalizeDisclosureResponse(BaseModel):
    rcept_no: str
    title: str
    content: str
    disclosed_at: datetime
    stock_code: str
