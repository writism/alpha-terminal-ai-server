from dataclasses import dataclass
from datetime import datetime


@dataclass
class NormalizedDisclosure:
    rcept_no: str       # 공시 번호
    title: str          # 공시 제목
    content: str        # 본문
    disclosed_at: datetime  # 공시일시
    stock_code: str     # 종목 코드
