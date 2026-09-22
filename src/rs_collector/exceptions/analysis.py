from rs_collector.exceptions.base import RsCollectorError


class AnalysisError(RsCollectorError):
    pass


class AnalyzerStartError(AnalysisError):
    pass


class AnalysisFailedError(AnalysisError):
    pass


class AnalysisTimeoutError(AnalysisError):
    pass
