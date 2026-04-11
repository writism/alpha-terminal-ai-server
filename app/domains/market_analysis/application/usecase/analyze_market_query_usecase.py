from app.domains.market_analysis.application.usecase.langchain_qa_port import LangChainQAPort
from app.domains.market_analysis.application.usecase.market_data_repository_port import MarketDataRepositoryPort
from app.domains.market_analysis.application.usecase.user_profile_repository_port import UserProfileRepositoryPort
from app.domains.market_analysis.domain.entity.analysis_answer import AnalysisAnswer
from app.domains.market_analysis.domain.service.context_builder_service import (
    ContextBuilderService,
    WatchlistContext,
)


class AnalyzeMarketQueryUseCase:
    def __init__(
        self,
        repository: MarketDataRepositoryPort,
        qa: LangChainQAPort,
        user_profile_repository: UserProfileRepositoryPort | None = None,
    ):
        self._repository = repository
        self._qa = qa
        self._user_profile_repository = user_profile_repository
        self._context_builder = ContextBuilderService()

    def execute(self, account_id: int, question: str) -> AnalysisAnswer:
        watchlist = self._repository.get_watchlist(account_id)
        if not watchlist:
            return AnalysisAnswer(
                answer="관심종목이 없습니다. 먼저 관심종목을 등록해주세요.",
                in_scope=False,
            )

        codes = [s.symbol for s in watchlist]
        themes = self._repository.get_stock_themes_by_codes(codes)
        themes_map = {t.code: t.themes for t in themes}

        contexts = [
            WatchlistContext(
                symbol=s.symbol,
                name=s.name,
                themes=themes_map.get(s.symbol, []),
            )
            for s in watchlist
        ]

        user_profile = None
        if self._user_profile_repository:
            user_profile = self._user_profile_repository.get_by_account_id(account_id)

        context = self._context_builder.build(contexts, user_profile=user_profile)
        return self._qa.ask(question, context)
