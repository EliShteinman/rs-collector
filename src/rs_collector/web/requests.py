from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from rs_collector.analysis.options import AnalysisDepth, AnalysisOptions
from rs_collector.exceptions.web import BadRequestError

_AFFIRMATIVE = ("yes", "on", "true")


class CollectRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    cluster: str = Field(min_length=1)

    @classmethod
    def parse(cls, form: Mapping[str, str]) -> CollectRequest:
        return _validated(cls, {"cluster": form.get("cluster", "")})


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    package: str = Field(min_length=1)
    bdb_id: int | None = Field(default=None, gt=0)
    depth: AnalysisDepth = Field(default=AnalysisDepth.DEFAULT)
    mask: bool = Field(default=False)

    @field_validator("bdb_id", mode="before")
    @classmethod
    def _ignore_a_blank_value(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @classmethod
    def parse(cls, form: Mapping[str, str]) -> AnalyzeRequest:
        return _validated(
            cls,
            {
                "package": form.get("package", ""),
                "bdb_id": form.get("bdb", ""),
                "depth": form.get("depth", AnalysisDepth.DEFAULT.value),
                "mask": form.get("mask", "").lower() in _AFFIRMATIVE,
            },
        )

    def options(self) -> AnalysisOptions:
        return AnalysisOptions(bdb_id=self.bdb_id, depth=self.depth, mask=self.mask)


def _validated[T: BaseModel](model: type[T], values: dict[str, object]) -> T:
    try:
        return model.model_validate(values)
    except ValidationError as error:
        raise BadRequestError(f"The form is not valid: {error}") from error
