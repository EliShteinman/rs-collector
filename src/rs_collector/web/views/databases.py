from collections.abc import Callable, Sequence

from markupsafe import Markup

from rs_collector.dblogs.models import Database, DatabaseLogs
from rs_collector.web.views.layout import page, template
from rs_collector.web.views.size_text import size
from rs_collector.web.views.time_text import stamp

_CONTENT = template("""
<section class="panel">
  <h2>Logs of one database</h2>
  <p class="note">
    Type the name or the number of a database. Every log of its shards is joined into one file
    per shard, with the rotated and compressed parts unpacked in order.
  </p>
  <form class="stack" method="post" action="{{ url('/database-logs') }}">
    <input type="hidden" name="analysis" value="{{ analysis }}">
    <div class="field">
      <label for="database">Database name or number</label>
      <input id="database" name="database" type="text" value="{{ asked }}"
             placeholder="orders or 1" autocomplete="off">
    </div>
    <button type="submit">Collect its logs</button>
  </form>
</section>

<section class="panel">
  <h2>Databases in this package <span class="count">{{ databases|length }}</span></h2>
  {% if databases %}
  <table>
    <thead>
      <tr><th>Number</th><th>Name</th><th class="num">Shards</th><th>Kind</th><th></th></tr>
    </thead>
    <tbody>
      {% for database in databases %}
      <tr>
        <td class="num">{{ database.uid }}</td>
        <td>{{ database.name or "—" }}</td>
        <td class="num">{{ database.shards|length }}</td>
        <td>{{ "Active-Active" if database.active_active else "single cluster" }}</td>
        <td class="actions">
          <form method="post" action="{{ url('/database-logs') }}">
            <input type="hidden" name="analysis" value="{{ analysis }}">
            <input type="hidden" name="database" value="{{ database.uid }}">
            <button class="quiet" type="submit">Collect its logs</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="empty">
    No database topology was found here. The package needs its rladmin output or ccs-redis.json.
  </p>
  {% endif %}
  <p class="back"><a href="{{ url('/') }}">Back to the console</a></p>
</section>
""")

_RESULT = template("""
<section class="panel">
  <h2>
    Logs of {{ logs.database.name or ("database " + logs.database.uid) }}
    {% if logs.database.active_active %}<span class="tag kept">Active-Active</span>{% endif %}
  </h2>
  <table>
    <thead>
      <tr>
        <th>Log</th>
        <th>Node</th>
        <th>Role</th>
        <th class="num">Lines</th>
        <th class="num">Size</th>
        <th>Covers</th>
        <th class="num">Parts</th>
      </tr>
    </thead>
    <tbody>
      {% for log in logs.merged %}
      <tr>
        <td><a href="{{ url(links[log.title]) }}">{{ log.title }}</a></td>
        <td>{{ log.node or "—" }}</td>
        <td>{{ log.role or "—" }}</td>
        <td class="num">{{ log.lines }}</td>
        <td class="num">{{ size(log.byte_count) }}</td>
        <td class="note">
          {% if log.first_seen %}{{ stamp(log.first_seen) }} → {{ stamp(log.last_seen) }}
          {% else %}—{% endif %}
        </td>
        <td class="num">{{ log.sources|length }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% if logs.package_files %}
  <h2>What the package itself holds for this database</h2>
  <table>
    <thead><tr><th>File</th><th class="num">Size</th></tr></thead>
    <tbody>
      {% for file in logs.package_files %}
      <tr>
        <td>
          <a class="file" href="{{ url(file_links[file.path|string]) }}">{{ file.path.name }}</a>
        </td>
        <td class="num">{{ size(file.byte_count) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% endif %}

  <p class="back">
    <a href="{{ url(directory) }}">Open the directory</a> ·
    <a href="{{ url('/analyses/' + analysis + '/databases') }}">Another database</a> ·
    <a href="{{ url('/') }}">Back to the console</a>
  </p>
</section>
""")


def render(
    url: Callable[[str], str], analysis: str, databases: Sequence[Database], asked: str = ""
) -> str:
    content = _CONTENT.render(url=url, analysis=analysis, databases=databases, asked=asked)
    return page("Database logs", Markup(content), url)


def render_result(
    url: Callable[[str], str],
    analysis: str,
    logs: DatabaseLogs,
    links: dict[str, str],
    directory: str,
    file_links: dict[str, str] | None = None,
) -> str:
    content = _RESULT.render(
        url=url,
        analysis=analysis,
        logs=logs,
        links=links,
        directory=directory,
        file_links=file_links or {},
        size=size,
        stamp=stamp,
    )
    return page(f"Logs of {logs.database.name or logs.database.uid}", Markup(content), url)
