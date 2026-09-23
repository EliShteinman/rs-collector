from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from rs_collector.analysis.models import StoredAnalysis
from rs_collector.analysis.outputs import AnalysisOutputs
from rs_collector.dblogs.models import DatabaseLogs
from rs_collector.dblogs.service import DatabaseLogService
from rs_collector.exceptions.dblogs import NoLogsForDatabaseError
from rs_collector.exceptions.web import BadRequestError
from rs_collector.web.context import WebContext
from rs_collector.web.http import Request, Response
from rs_collector.web.views import databases as view

_ANALYSES_PATH = "/analyses/"
_OUTPUT_DIR = "rsc_database_logs"


class DatabaseLogsRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    analysis: str = Field(min_length=1)
    database: str = Field(min_length=1)

    @classmethod
    def parse(cls, form: Mapping[str, str]) -> DatabaseLogsRequest:
        try:
            return cls.model_validate(
                {"analysis": form.get("analysis", ""), "database": form.get("database", "")}
            )
        except ValidationError as error:
            raise BadRequestError(f"Name a database to collect: {error}") from error


class DatabasesController:
    def __init__(self, container: WebContext) -> None:
        self._container = container

    def show(self, request: Request, parameters: Mapping[str, str]) -> Response:
        analysis = self._container.analyses().get(parameters["name"])
        service = self._service(analysis)
        if service is None:
            raise NoLogsForDatabaseError(
                f"{analysis.name} holds no extracted support package to read logs from"
            )
        return Response.html(view.render(request.url, analysis.name, service.databases(), asked=""))

    def collect(self, request: Request, _: Mapping[str, str]) -> Response:
        asked = DatabaseLogsRequest.parse(request.form)
        analysis = self._container.analyses().get(asked.analysis)
        service = self._service(analysis)
        if service is None:
            raise NoLogsForDatabaseError(
                f"{analysis.name} holds no extracted support package to read logs from"
            )
        logs = service.collect(asked.database)
        return Response.html(
            view.render_result(
                request.url,
                analysis.name,
                logs,
                links=self._links(analysis, logs),
                directory=self._directory_url(analysis, logs),
                file_links={
                    str(file.path): self._url(analysis, file.path) for file in logs.package_files
                },
            )
        )

    def _service(self, analysis: StoredAnalysis) -> DatabaseLogService | None:
        package = AnalysisOutputs(analysis).raw_logs()
        if package is None:
            return None
        return DatabaseLogService(package, analysis.directory / _OUTPUT_DIR)

    def _links(self, analysis: StoredAnalysis, logs: DatabaseLogs) -> dict[str, str]:
        return {log.title: self._url(analysis, log.path) for log in logs.merged}

    def _directory_url(self, analysis: StoredAnalysis, logs: DatabaseLogs) -> str:
        return self._url(analysis, logs.merged[0].path.parent) + "/"

    def _url(self, analysis: StoredAnalysis, target: Path) -> str:
        inside = str(target).removeprefix(str(analysis.directory)).lstrip("/")
        return f"{_ANALYSES_PATH}{analysis.name}/{inside}"
