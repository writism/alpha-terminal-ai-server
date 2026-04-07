from app.domains.market_analysis.application.request.analyze_question_request import AnalyzeQuestionRequest
from app.domains.market_analysis.application.response.analyze_question_response import AnalyzeQuestionResponse
from app.domains.market_analysis.application.usecase.question_analyzer_port import QuestionAnalyzerPort
from app.domains.market_analysis.application.usecase.stock_data_port import StockDataPort
from app.domains.market_analysis.domain.service.market_context_builder_service import MarketContextBuilderService


class AnalyzeQuestionUseCase:
    def __init__(
        self,
        stock_data_port: StockDataPort,
        question_analyzer_port: QuestionAnalyzerPort,
        context_builder: MarketContextBuilderService,
    ):
        self._stock_data_port = stock_data_port
        self._question_analyzer_port = question_analyzer_port
        self._context_builder = context_builder

    async def execute(self, request: AnalyzeQuestionRequest) -> AnalyzeQuestionResponse:
        stocks = self._stock_data_port.find_all()
        context = self._context_builder.build_context(stocks)
        answer = await self._question_analyzer_port.analyze(context, request.question)
        return AnalyzeQuestionResponse(question=request.question, answer=answer)
