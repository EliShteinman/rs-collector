from jinja2 import Environment

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
<header>
  <a class="brand" href="{{ url('/') }}">rsc</a>
  <span class="subtitle">RedisScope collector</span>
</header>
<main>
{{ content }}
</main>
<script src="{{ url('/static/app.js') }}"></script>
</body>
</html>
"""


def template(markup: str) -> Environment.template_class:
    return _ENVIRONMENT.from_string(markup)


_LAYOUT = template(_PAGE)


def page(title: str, content: str, url: object) -> str:
    return _LAYOUT.render(title=title, content=content, url=url)
