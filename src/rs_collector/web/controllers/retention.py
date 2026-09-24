from collections.abc import Mapping
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from rs_collector.exceptions.web import BadRequestError
from rs_collector.retention.pin import PinService
from rs_collector.web.http import Request, Response
from rs_collector.web.router import Router

_HOME = "/"
_POST = "POST"


class PinContext(Protocol):
    def pins(self) -> PinService: ...


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
    def __init__(self, context: PinContext) -> None:
        self._context = context

    def register(self, router: Router) -> None:
        router.add(_POST, "/keep", self.keep)
        router.add(_POST, "/release", self.release)

    def keep(self, request: Request, _: Mapping[str, str]) -> Response:
        self._context.pins().pin(KeepRequest.parse(request.form).name)
        return Response.redirect(request.url(_HOME))

    def release(self, request: Request, _: Mapping[str, str]) -> Response:
        self._context.pins().unpin(KeepRequest.parse(request.form).name)
        return Response.redirect(request.url(_HOME))
