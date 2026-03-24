from typing import List

from app.domains.stock.application.response.stock_response import StockResponse
from app.domains.stock.application.usecase.stock_repository_port import StockRepositoryPort

# DART 데이터에 영문명으로 등록된 주요 종목의 한글 검색어 → 영문명 매핑
KOREAN_ALIAS: dict[str, str] = {
    "네이버": "NAVER",
    "카카오": "Kakao",
    "포스코": "POSCO",
    "에스케이": "SK",
    "엘지": "LG",
    "현대차": "현대자동차",
    "다음": "카카오",       # 다음카카오 합병 후 카카오로 통합
    "기아차": "기아",
    "에쓰오일": "S-Oil",
    "에스오일": "S-Oil",
}


class SearchStockUseCase:

    def __init__(self, repository: StockRepositoryPort):
        self._repository = repository

    def execute(self, keyword: str) -> List[StockResponse]:
        # 한글 별칭이 있으면 영문/정식명 키워드로 변환
        search_keyword = KOREAN_ALIAS.get(keyword.strip(), keyword)

        stocks = self._repository.search_by_name(search_keyword)

        # 별칭 검색 결과가 없으면 원본 키워드로 재시도
        if not stocks and search_keyword != keyword:
            stocks = self._repository.search_by_name(keyword)

        return [StockResponse(symbol=s.symbol, name=s.name, market=s.market) for s in stocks]
