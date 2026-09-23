from collections.abc import Callable, Mapping, Sequence

from markupsafe import Markup
from pydantic import BaseModel, ConfigDict, Field

from rs_collector.analysis.models import StoredAnalysis
from rs_collector.analysis.options import AnalysisDepth
from rs_collector.inventory.models import Cluster
from rs_collector.jobs.models import JobView
from rs_collector.packages.models import StoredPackage
from rs_collector.status.models import SystemStatus
from rs_collector.status.schedule_text import spoken
from rs_collector.web.views.layout import page, template
from rs_collector.web.views.size_text import size
from rs_collector.web.views.time_text import ago, stamp

_TIGHT_DISK = 0.9


class AnalysisLinks(BaseModel):
    model_config = ConfigDict(frozen=True)

    files: str
    report: str = Field(default="")
    raw_logs: str = Field(default="")


_CONTENT = template("""
<section class="state">
  <div class="fact">
    <h3>Web interface</h3>
    {% if status.server.is_running %}
    <p>Running in the background</p>
    <p class="note">Process <span class="num">{{ status.server.pid }}</span></p>
    {% else %}
    <p>Started by hand</p>
    <p class="note">Run <span class="num">rsc start</span> to keep it up on its own</p>
    {% endif %}
  </div>
  <div class="fact">
    <h3>After a reboot</h3>
    {% if status.schedule.starts_after_reboot %}
    <p>Comes back by itself</p>
    <p class="note">Scheduled in the crontab of this user</p>
    {% else %}
    <p>Stays down</p>
    <p class="note">Run <span class="num">rsc start</span> to schedule it</p>
    {% endif %}
  </div>
  <div class="fact">
    <h3>Cleanup</h3>
    <p>{{ cleanup_schedule }}</p>
    {% if status.schedule.cleanup_last_run %}
    <p class="note">
      Last ran {{ cleanup_ago }}, removed {{ status.schedule.removed_last_run }} item(s).
      Keeps {{ status.schedule.keeps_days }} days.
    </p>
    {% else %}
    <p class="note">Has not run yet. Keeps {{ status.schedule.keeps_days }} days.</p>
    {% endif %}
  </div>
  <div class="fact">
    <h3>Disk</h3>
    <p class="num">{{ size(status.storage.free_bytes) }} free</p>
    <p class="note path" title="{{ data_root }}">
      of {{ size(status.storage.total_bytes) }} on {{ data_root }}
    </p>
    <div class="meter{{ ' tight' if status.storage.used_share > tight }}">
      <span style="width: {{ (status.storage.used_share * 100)|round|int }}%"></span>
    </div>
  </div>
</section>

<section class="panels">
  <div class="panel">
    <h2>Collect a support package</h2>
    {% if clusters %}
    <form class="stack" method="post" action="{{ url('/collect') }}">
      <div class="field">
        <label for="cluster">Cluster</label>
        <select id="cluster" name="cluster">
          {% for cluster in clusters %}
          <option value="{{ cluster.name }}">
            {{ cluster.name }}{% if cluster.environment %} — {{ cluster.environment }}{% endif %}
          </option>
          {% endfor %}
        </select>
      </div>
      <button type="submit">Collect now</button>
    </form>
    {% else %}
    <p class="empty">No cluster is configured yet. Add one to clusters.yml and reload.</p>
    {% endif %}
  </div>

  <div class="panel">
    <h2>Analyze a package</h2>
    {% if packages %}
    <form class="stack" method="post" action="{{ url('/analyze') }}">
      <div class="field">
        <label for="package">Package</label>
        <select id="package" name="package">
          {% for package in packages %}
          <option value="{{ package.name }}">
            {{ package.metadata.cluster_fqdn }} — {{ stamp(package.metadata.collected_at) }}
          </option>
          {% endfor %}
        </select>
      </div>
      <div class="field">
        <label for="depth">How deep</label>
        <select id="depth" name="depth">
          {% for depth in depths %}
          <option value="{{ depth.value }}"{{ ' selected' if depth.value == 'default' }}>
            {{ depth_labels[depth] }}
          </option>
          {% endfor %}
        </select>
      </div>
      <div class="field">
        <label for="bdb">One database only (leave empty for all)</label>
        <input id="bdb" name="bdb" type="text" inputmode="numeric" placeholder="all databases">
      </div>
      <label class="inline">
        <input type="checkbox" name="mask" value="yes"> Hide sensitive values in the report
      </label>
      <button type="submit">Analyze now</button>
    </form>
    {% else %}
    <p class="empty">Nothing to analyze yet. Collect a package first.</p>
    {% endif %}
  </div>
</section>

<section class="panel">
  <h2>Packages <span class="count">{{ packages|length }},
    {{ size(status.storage.packages_bytes) }}</span></h2>
  {% if packages %}
  <table>
    <thead>
      <tr>
        <th>Cluster</th>
        <th>Collected</th>
        <th class="num">Size</th>
        <th></th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {% for package in packages %}
      <tr>
        <td>
          {{ package.metadata.cluster_fqdn }}
          <div class="name">{{ package.name }}</div>
        </td>
        <td>
          {{ stamp(package.metadata.collected_at) }}
          <div class="note">{{ ago(package.metadata.collected_at) }}</div>
        </td>
        <td class="num">{{ size(package.metadata.size_bytes) }}</td>
        <td>{% if package.metadata.pinned %}<span class="tag kept">kept</span>{% endif %}</td>
        <td class="actions">
          <form method="post" action="{{ url('/analyze') }}">
            <input type="hidden" name="package" value="{{ package.name }}">
            <input type="hidden" name="depth" value="default">
            <button class="quiet" type="submit">Analyze</button>
          </form>
          {{ keep_button(package.name, package.metadata.pinned) }}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="empty">Collected packages will be listed here.</p>
  {% endif %}
</section>

<section class="panel">
  <h2>Analyses <span class="count">{{ analyses|length }}</span></h2>
  {% if analyses %}
  <table>
    <thead>
      <tr>
        <th>Analysis</th>
        <th>Result</th>
        <th>Finished</th>
        <th></th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {% for analysis in analyses %}
      <tr>
        <td>
          {{ analysis.metadata.cluster_fqdn }}
          <div class="name">{{ analysis.name }}</div>
        </td>
        <td>
          <span class="tag {{ analysis.metadata.status }}">{{ analysis.metadata.status }}</span>
        </td>
        <td>
          {{ stamp(analysis.metadata.analyzed_at) }}
          <div class="note">{{ ago(analysis.metadata.analyzed_at) }}</div>
        </td>
        <td>{% if analysis.metadata.pinned %}<span class="tag kept">kept</span>{% endif %}</td>
        <td class="actions">
          {% if links[analysis.name].report %}
          <a class="report" href="{{ url(links[analysis.name].report) }}">Report</a>
          {% endif %}
          {% if links[analysis.name].raw_logs %}
          <a href="{{ url(links[analysis.name].raw_logs) }}">Raw logs</a>
          {% endif %}
          <a href="{{ url(links[analysis.name].files) }}">All files</a>
          {{ keep_button(analysis.name, analysis.metadata.pinned) }}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="empty">Finished analyses and their reports will be listed here.</p>
  {% endif %}
</section>

<section class="panel">
  <h2>Recent runs</h2>
  {% if jobs %}
  <table>
    <thead>
      <tr>
        <th>What ran</th>
        <th>Result</th>
        <th>Started</th>
      </tr>
    </thead>
    <tbody>
      {% for job in jobs %}
      <tr>
        <td><a href="{{ url('/jobs/' + job.id) }}">{{ job.title }}</a></td>
        <td><span class="tag {{ job.status }}">{{ job.status }}</span></td>
        <td>{{ stamp(job.started_at) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="empty">Collections and analyses you start will appear here while they run.</p>
  {% endif %}
</section>
""")

_KEEP_BUTTON = template("""
<form method="post" action="{{ url(action) }}">
  <input type="hidden" name="name" value="{{ name }}">
  <button class="quiet" type="submit">{{ label }}</button>
</form>
""")

_DEPTH_LABELS = {
    AnalysisDepth.QUICK: "quick — skip the logs",
    AnalysisDepth.DEFAULT: "default",
    AnalysisDepth.FULL: "full — analyze everything",
    AnalysisDepth.MAX: "deepest — everything and pattern counts",
}


def render(
    url: Callable[[str], str],
    status: SystemStatus,
    clusters: Sequence[Cluster],
    packages: Sequence[StoredPackage],
    analyses: Sequence[StoredAnalysis],
    links: Mapping[str, AnalysisLinks],
    jobs: Sequence[JobView],
) -> str:
    content = _CONTENT.render(
        url=url,
        status=status,
        clusters=clusters,
        packages=packages,
        analyses=analyses,
        links=links,
        jobs=jobs,
        depths=list(AnalysisDepth),
        depth_labels=_DEPTH_LABELS,
        cleanup_schedule=spoken(status.schedule.cleanup_schedule),
        cleanup_ago=(
            ago(status.schedule.cleanup_last_run) if status.schedule.cleanup_last_run else ""
        ),
        data_root=status.storage.data_root,
        stamp=stamp,
        ago=ago,
        size=size,
        keep_button=_keep_button(url),
        tight=_TIGHT_DISK,
    )
    return page(
        "Collect and analyze",
        Markup(content),
        url,
        host=f"{status.server.host}:{status.server.port}",
        state="Running" if status.server.is_running else "Foreground only",
        state_kind="up" if status.server.is_running else "down",
    )


def _keep_button(url: Callable[[str], str]) -> Callable[[str, bool], Markup]:
    def button(name: str, pinned: bool) -> Markup:
        action = "/release" if pinned else "/keep"
        label = "Let it expire" if pinned else "Keep"
        return Markup(_KEEP_BUTTON.render(url=url, action=action, name=name, label=label))

    return button
