from collections.abc import Callable, Sequence

from markupsafe import Markup

from rs_collector.analysis.models import StoredAnalysis
from rs_collector.analysis.options import AnalysisDepth
from rs_collector.inventory.models import Cluster
from rs_collector.jobs.models import JobView
from rs_collector.packages.models import StoredPackage
from rs_collector.web.views.layout import page, template

_TIMESTAMP = "%Y-%m-%d %H:%M"
_BYTES_PER_MIB = 1_048_576

_CONTENT = template("""
<section class="card">
  <h2>Collect a new support package</h2>
  {% if clusters %}
  <form method="post" action="{{ url('/collect') }}">
    <label for="cluster">Cluster</label>
    <select id="cluster" name="cluster">
      {% for cluster in clusters %}
      <option value="{{ cluster.name }}">{{ cluster.name }} — {{ cluster.environment }}</option>
      {% endfor %}
    </select>
    <button type="submit">Collect</button>
  </form>
  {% else %}
  <p class="empty">No cluster is configured. Add one to clusters.yml.</p>
  {% endif %}
</section>

<section class="card">
  <h2>Analyze a stored package</h2>
  {% if packages %}
  <form method="post" action="{{ url('/analyze') }}">
    <label for="package">Package</label>
    <select id="package" name="package">
      {% for package in packages %}
      <option value="{{ package.name }}">
        {{ package.metadata.cluster_fqdn }}
        — {{ package.metadata.collected_at.strftime(timestamp) }}
        ({{ "%.1f"|format(package.metadata.size_bytes / mib) }} MiB)
      </option>
      {% endfor %}
    </select>
    <label for="depth">Depth</label>
    <select id="depth" name="depth">
      {% for depth in depths %}
      <option value="{{ depth }}"{{ ' selected' if depth == 'default' }}>
        {{ depth }}
      </option>
      {% endfor %}
    </select>
    <label for="bdb">Database (empty for every database)</label>
    <input id="bdb" name="bdb" inputmode="numeric" pattern="[0-9]*" placeholder="all">
    <label class="checkbox">
      <input type="checkbox" name="mask" value="yes"> Mask sensitive values
    </label>
    <button type="submit">Analyze</button>
  </form>
  {% else %}
  <p class="empty">No package is stored yet. Collect one first.</p>
  {% endif %}
</section>

<section class="card">
  <h2>Jobs</h2>
  {% if jobs %}
  <ul class="rows">
    {% for job in jobs %}
    <li>
      <a href="{{ url('/jobs/' + job.id) }}">{{ job.title }}</a>
      <span class="status {{ job.status }}">{{ job.status }}</span>
      <span class="when">{{ job.started_at.strftime(timestamp) }}</span>
    </li>
    {% endfor %}
  </ul>
  {% else %}
  <p class="empty">Nothing has run yet.</p>
  {% endif %}
</section>

<section class="card">
  <h2>Analyses</h2>
  {% if analyses %}
  <ul class="rows">
    {% for analysis in analyses %}
    <li>
      <a href="{{ url('/analyses/' + analysis.name + '/') }}">{{ analysis.name }}</a>
      <span class="status {{ analysis.metadata.status }}">{{ analysis.metadata.status }}</span>
      <span class="when">{{ analysis.metadata.analyzed_at.strftime(timestamp) }}</span>
    </li>
    {% endfor %}
  </ul>
  {% else %}
  <p class="empty">No analysis is stored yet.</p>
  {% endif %}
</section>
""")


def render(
    url: Callable[[str], str],
    clusters: Sequence[Cluster],
    packages: Sequence[StoredPackage],
    analyses: Sequence[StoredAnalysis],
    jobs: Sequence[JobView],
) -> str:
    content = _CONTENT.render(
        url=url,
        clusters=clusters,
        packages=packages,
        analyses=analyses,
        jobs=jobs,
        depths=[depth.value for depth in AnalysisDepth],
        timestamp=_TIMESTAMP,
        mib=_BYTES_PER_MIB,
    )
    return page("Collect and analyze", Markup(content), url)
