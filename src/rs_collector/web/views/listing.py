from collections.abc import Callable, Sequence

from markupsafe import Markup

from rs_collector.web.views.layout import page, template

_CONTENT = template("""
<section class="panel">
  <h2>{{ heading }}</h2>
  <ul class="files">
    {% if parent %}
    <li><a href="{{ url(parent) }}">..</a></li>
    {% endif %}
    {% for entry in entries %}
    <li><a href="{{ url(entry.url) }}">{{ entry.name }}</a></li>
    {% endfor %}
  </ul>
  {% if not entries %}
  <p class="empty">This directory is empty.</p>
  {% endif %}
  <p class="back"><a href="{{ url('/') }}">Back to the console</a></p>
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
