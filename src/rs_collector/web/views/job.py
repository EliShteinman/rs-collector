from collections.abc import Callable

from markupsafe import Markup

from rs_collector.jobs.models import JobView
from rs_collector.web.views.layout import page, template
from rs_collector.web.views.time_text import stamp

_CONTENT = template("""
<section class="panel" data-job="{{ job.id }}" data-log-url="{{ url('/api/jobs/' + job.id) }}">
  <div class="job-head">
    <h2>{{ job.title }}</h2>
    <span class="tag {{ job.status }}" id="job-status">{{ job.status }}</span>
    <span class="when">started {{ started }}</span>
  </div>
  <pre class="log" id="job-log">{% for line in job.lines %}{{ line }}
{% endfor %}</pre>
  <p class="outcome" id="job-outcome">{{ job.outcome }}</p>
  <p id="job-report">
    {% if job.report_url %}
    <a class="report" href="{{ url(job.report_url) }}">Open the report</a>
    {% endif %}
  </p>
  <p class="back"><a href="{{ url('/') }}">Back to the console</a></p>
</section>
""")


def render(url: Callable[[str], str], job: JobView) -> str:
    content = _CONTENT.render(url=url, job=job, started=stamp(job.started_at))
    return page(job.title, Markup(content), url)
