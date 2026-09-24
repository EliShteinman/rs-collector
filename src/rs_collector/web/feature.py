from typing import Protocol

from rs_collector.web.router import Router


class WebFeature(Protocol):
    def register(self, router: Router) -> None: ...
