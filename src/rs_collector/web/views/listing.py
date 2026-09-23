from collections.abc import Callable, Sequence
from datetime import datetime

from markupsafe import Markup
from pydantic import BaseModel, ConfigDict, Field

from rs_collector.web.views.layout import page, template
from rs_collector.web.views.size_text import size
from rs_collector.web.views.time_text import stamp

_CONTENT = template("""
<section class="panel">
  <h2>{{ heading }}</h2>
  <table>
    <thead>
      <tr>
        <th>Name</th>
        <th class="num">Size</th>
        <th>Changed</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {% if parent %}
      <tr><td><a href="{{ url(parent) }}">..</a></td><td></td><td></td><td></td></tr>
      {% endif %}
      {% for entry in entries %}
      <tr>
        <td><a class="file" href="{{ url(entry.url) }}">{{ entry.name }}</a></td>
        <td class="num">{{ size(entry.size_bytes) if entry.size_bytes is not none }}</td>
        <td class="note">{{ stamp(entry.changed_at) }}</td>
        <td class="actions">
          {% if entry.raw_url %}
          <a class="note" href="{{ url(entry.raw_url) }}">download</a>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% if not entries %}
  <p class="empty">This directory is empty.</p>
  {% endif %}
  <p class="back"><a href="{{ url('/') }}">Back to the console</a></p>
</section>
""")


class Entry(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    url: str
    changed_at: datetime
    size_bytes: int | None = Field(default=None, ge=0)
    raw_url: str = Field(default="")


def render(
    url: Callable[[str], str], heading: str, entries: Sequence[Entry], parent: str | None
) -> str:
    content = _CONTENT.render(
        url=url, heading=heading, entries=entries, parent=parent, size=size, stamp=stamp
    )
    return page(heading, Markup(content), url)
