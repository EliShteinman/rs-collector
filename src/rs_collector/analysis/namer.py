from collections.abc import Container

from rs_collector.analysis.options import AnalysisOptions

_SEPARATOR = "__"
_FIRST_REPEAT = 2


class AnalysisNamer:
    def name_for(
        self, package_name: str, options: AnalysisOptions, taken_names: Container[str]
    ) -> str:
        base = f"{package_name}{_SEPARATOR}{options.slug()}"
        if base not in taken_names:
            return base
        return self._next_free(base, taken_names)

    def _next_free(self, base: str, taken_names: Container[str]) -> str:
        repeat = _FIRST_REPEAT
        while f"{base}{_SEPARATOR}{repeat}" in taken_names:
            repeat += 1
        return f"{base}{_SEPARATOR}{repeat}"
