from collections.abc import Callable, Sequence

from markupsafe import Markup

from rs_collector.web.views.layout import page, template

_CONTENT = template("""
<section class="card">
  <h2>{{ heading }}</h2>
  <ul class="rows">
    {% if parent %}
    <li><a href="{{ url(parent) }}">..</a></li>
    {% endif %}
    {% for entry in entries %}
    <li><a href="{{ url(entry.url) }}">{{ entry.name }}</a></li>
    {% endfor %}
  </ul>
  <p><a href="{{ url('/') }}">Back</a></p>
</section>
""")


class Entry:
    def __init__(self, name: str, url: str) -> None:
        self.name = name
        self.url = url


def render(
    url: Callable[[str], str], heading: str, entries: Sequence[Entry], parent: str | None
) -> str:
    content = _CONTENT.render(url=url, heading=heading, entries=entries, parent=parent)
    return page(heading, Markup(content), url)
