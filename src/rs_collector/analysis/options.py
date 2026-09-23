from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

_SLUG_SEPARATOR = "__"
_DEFAULT_SLUG = "default"
_BDB_SLUG_TEMPLATE = "bdb-{bdb_id}"
_MASKED_SLUG = "masked"


class AnalysisDepth(StrEnum):
    QUICK = "quick"
    DEFAULT = "default"
    FULL = "full"
    MAX = "max"

    @property
    def flags(self) -> tuple[str, ...]:
        return _DEPTH_FLAGS[self]


_DEPTH_FLAGS: dict[AnalysisDepth, tuple[str, ...]] = {
    AnalysisDepth.QUICK: ("--skiplogs",),
    AnalysisDepth.DEFAULT: (),
    AnalysisDepth.FULL: ("--force-full",),
    AnalysisDepth.MAX: ("--force-full", "--count-pattern-occurrences"),
}


class AnalysisOptions(BaseModel):
    model_config = ConfigDict(frozen=True)

    bdb_id: int | None = Field(default=None, gt=0)
    depth: AnalysisDepth = Field(default=AnalysisDepth.DEFAULT)
    mask: bool = Field(default=False)
    verbose: bool = Field(default=False)

    @property
    def flags(self) -> tuple[str, ...]:
        return (*self._bdb_flags(), *self.depth.flags, *self._mask_flags(), *self._verbose_flags())

    def slug(self) -> str:
        candidates = (self._bdb_slug(), self._depth_slug(), self._mask_slug())
        parts = tuple(part for part in candidates if part)
        return _SLUG_SEPARATOR.join(parts) if parts else _DEFAULT_SLUG

    def _bdb_flags(self) -> tuple[str, ...]:
        return () if self.bdb_id is None else ("--bdb", str(self.bdb_id))

    def _mask_flags(self) -> tuple[str, ...]:
        return ("--mask",) if self.mask else ()

    def _verbose_flags(self) -> tuple[str, ...]:
        return ("--verbose",) if self.verbose else ()

    def _bdb_slug(self) -> str:
        return "" if self.bdb_id is None else _BDB_SLUG_TEMPLATE.format(bdb_id=self.bdb_id)

    def _depth_slug(self) -> str:
        return "" if self.depth is AnalysisDepth.DEFAULT else self.depth.value

    def _mask_slug(self) -> str:
        return _MASKED_SLUG if self.mask else ""
