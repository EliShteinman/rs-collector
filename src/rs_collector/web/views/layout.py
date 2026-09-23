from collections.abc import Callable

from jinja2 import Environment, Template
from markupsafe import Markup

_ENVIRONMENT = Environment(autoescape=True, trim_blocks=True, lstrip_blocks=True)

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} — rsc</title>
<link rel="stylesheet" href="{{ url('/static/app.css') }}">
</head>
<body>
<header class="masthead">
  <a class="mark" href="{{ url('/') }}">rsc</a>
  <span class="host">{{ host }}</span>
  <span class="spacer"></span>
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
    host: str = "",
    state: str = "",
    state_kind: str = "",
) -> str:
    return _LAYOUT.render(
        title=title, content=content, url=url, host=host, state=state, state_kind=state_kind
    )
