from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from rs_collector.exceptions.web import BadRequestError
from rs_collector.web.context import WebContext
from rs_collector.web.http import Request, Response

_HOME = "/"


class KeepRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)

    @classmethod
    def parse(cls, form: Mapping[str, str]) -> KeepRequest:
        try:
            return cls.model_validate({"name": form.get("name", "")})
        except ValidationError as error:
            raise BadRequestError(f"The form is not valid: {error}") from error


class RetentionController:
    def __init__(self, container: WebContext) -> None:
        self._container = container

    def keep(self, request: Request, _: Mapping[str, str]) -> Response:
        self._container.pins().pin(KeepRequest.parse(request.form).name)
        return Response.redirect(request.url(_HOME))

    def release(self, request: Request, _: Mapping[str, str]) -> Response:
        self._container.pins().unpin(KeepRequest.parse(request.form).name)
        return Response.redirect(request.url(_HOME))
