from collections.abc import Callable

from markupsafe import Markup

from rs_collector.web.views.layout import page, template

_CONTENT = template("""
<section class="card">
  <h2>{{ heading }}</h2>
  <p>{{ detail }}</p>
  <p><a href="{{ url('/') }}">Back</a></p>
</section>
""")


def render(url: Callable[[str], str], heading: str, detail: str) -> str:
    return page(heading, Markup(_CONTENT.render(url=url, heading=heading, detail=detail)), url)
