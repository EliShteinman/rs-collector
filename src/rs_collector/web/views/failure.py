from collections.abc import Callable

from markupsafe import Markup

from rs_collector.web.navigation import Navigation
from rs_collector.web.views.layout import page, template

_CONTENT = template("""
<section class="panel">
  <h2>{{ heading }}</h2>
  <p>{{ detail }}</p>
  <p class="back"><a href="{{ url('/') }}">Back to the console</a></p>
</section>
""")


def render(
    url: Callable[[str], str], heading: str, detail: str, navigation: Navigation | None = None
) -> str:
    content = _CONTENT.render(url=url, heading=heading, detail=detail)
    return page(heading, Markup(content), url, navigation)
