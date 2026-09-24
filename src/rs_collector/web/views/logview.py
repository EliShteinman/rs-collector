from collections.abc import Callable

from markupsafe import Markup

from rs_collector.web.files.log_lines import LogContent
from rs_collector.web.navigation import Navigation
from rs_collector.web.views.layout import page, template
from rs_collector.web.views.log_html import as_html
from rs_collector.web.views.size_text import size

_CONTENT = template("""
<section class="panel logview" data-log-view>
  <div class="job-head">
    <h2>{{ name }}</h2>
    <span class="when">{{ content.total_lines }} lines, {{ size(byte_count) }}</span>
  </div>

  <div class="logbar">
    <input type="search" id="log-filter" placeholder="Filter lines" autocomplete="off">
    <span class="levels">
      {% for level in content.levels() %}
      <label class="inline">
        <input type="checkbox" class="level-toggle" value="{{ level }}" checked> {{ level }}
      </label>
      {% endfor %}
    </span>
    <span class="spacer"></span>
    <label class="inline"><input type="checkbox" id="log-wrap"> wrap</label>
    <a class="note" href="{{ url(raw_url) }}">download</a>
  </div>

  {% if not content.is_complete %}
  <p class="note">
    Showing the last {{ content.lines|length }} lines. Download the file for the whole log.
  </p>
  {% endif %}

  <div class="loglines" id="log-lines">
    {% for line in content.lines %}
    <div class="logline {{ line.level }}" data-level="{{ line.level }}">
      <span class="ln">{{ line.number }}</span><span class="lt">{{ html(line.text) }}</span>
    </div>
    {% endfor %}
  </div>
  <p class="note" id="log-count"></p>

  <p class="back"><a href="{{ url(parent_url) }}">Back to the directory</a></p>
</section>
""")


def render(
    url: Callable[[str], str],
    name: str,
    content: LogContent,
    byte_count: int,
    raw_url: str,
    parent_url: str,
    navigation: Navigation | None = None,
) -> str:
    markup = _CONTENT.render(
        url=url,
        name=name,
        content=content,
        byte_count=byte_count,
        raw_url=raw_url,
        parent_url=parent_url,
        size=size,
        html=as_html,
    )
    return page(name, Markup(markup), url, navigation, wide=True)
