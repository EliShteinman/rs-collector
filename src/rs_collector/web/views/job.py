from collections.abc import Callable

from markupsafe import Markup

from rs_collector.jobs.models import JobView
from rs_collector.web.views.layout import page, template

_CONTENT = template("""
<section class="card" data-job="{{ job.id }}" data-log-url="{{ url('/api/jobs/' + job.id) }}">
  <h2>{{ job.title }}</h2>
  <p>
    <span class="status" id="job-status">{{ job.status }}</span>
    <span class="when">started {{ job.started_at.strftime('%Y-%m-%d %H:%M:%S') }}</span>
  </p>
  <pre id="job-log">{% for line in job.lines %}{{ line }}
{% endfor %}</pre>
  <p id="job-outcome" class="outcome">{{ job.outcome }}</p>
  <p id="job-report">
    {% if job.report_url %}
    <a class="button" href="{{ url(job.report_url) }}">Open the report</a>
    {% endif %}
  </p>
  <p><a href="{{ url('/') }}">Back</a></p>
</section>
""")


def render(url: Callable[[str], str], job: JobView) -> str:
    return page(job.title, Markup(_CONTENT.render(url=url, job=job)), url)
