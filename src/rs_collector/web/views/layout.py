from collections.abc import Callable

from jinja2 import Environment, Template
from markupsafe import Markup

from rs_collector.web.navigation import Navigation

_ENVIRONMENT = Environment(autoescape=True, trim_blocks=True, lstrip_blocks=True)

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} — rsc</title>
<link rel="stylesheet" href="{{ url('/static/app.css') }}">
</head>
<body class="{{ 'wide' if wide }}">
<header class="masthead">
  <a class="mark" href="{{ url('/') }}">rsc</a>
  {% if navigation.tools %}
  <nav class="nav">
    {% for tool in navigation.tools %}
    <a href="{{ url(tool.path) }}" class="{{ 'here' if navigation.is_here(tool) }}"
       title="{{ tool.summary }}">{{ tool.name }}</a>
    {% endfor %}
  </nav>
  {% endif %}
  <span class="spacer"></span>
  {% if host %}
  <span class="host">{{ host }}</span>
  {% endif %}
  {% if state %}
  <span class="pill {{ state_kind }}">{{ state }}</span>
  {% endif %}
</header>
<main>
{{ content }}
</main>
<script src="{{ url('/static/app.js') }}"></script>
</body>
</html>
"""


def template(markup: str) -> Template:
    return _ENVIRONMENT.from_string(markup)


_LAYOUT = template(_PAGE)


def page(
    title: str,
    content: Markup,
    url: Callable[[str], str],
    navigation: Navigation | None = None,
    host: str = "",
    state: str = "",
    state_kind: str = "",
    wide: bool = False,
) -> str:
    return _LAYOUT.render(
        title=title,
        content=content,
        url=url,
        navigation=navigation or Navigation(),
        host=host,
        state=state,
        state_kind=state_kind,
        wide=wide,
    )
