from pydantic import BaseModel


class NormalizeDisclosureRequest(BaseModel):
    rcept_no: str    # 공시 번호
    report_nm: str   # 공시 제목 (DART 원문 필드명)
    content: str     # 본문
    rcept_dt: str    # 공시일시 (DART 원문: "20240314" 또는 "20240314120000")
    stock_code: str  # 종목 코드
