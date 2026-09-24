from collections.abc import Callable

from markupsafe import Markup

from rs_collector.web.views.layout import page, template

_HEADING = "A login is needed"
_CONTENT = template("""
<section class="panel">
  <h2>{{ heading }}</h2>
  <p>Sign in with the user and password this server was given.</p>
  <p class="note">
    They come from <span class="num">RSC_WEB_USER</span> and
    <span class="num">RSC_WEB_PASSWORD</span> in <span class="num">rsc.env</span>.
    Ask whoever runs rsc on this machine.
  </p>
</section>
""")


def render(url: Callable[[str], str]) -> str:
    content = _CONTENT.render(heading=_HEADING)
    return page(_HEADING, Markup(content), url)
