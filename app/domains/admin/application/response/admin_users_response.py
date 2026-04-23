from datetime import datetime
from typing import List

from pydantic import BaseModel


class AdminUserItem(BaseModel):
    id: int
    nickname: str
    email: str
    role: str
    created_at: datetime


class AdminUsersResponse(BaseModel):
    users: List[AdminUserItem]
    total: int
