CSS = """
@font-face {
  font-family: "Plex Sans";
  src: url("fonts/plex-sans.woff2") format("woff2");
  font-weight: 100 700;
  font-display: swap;
}

@font-face {
  font-family: "Plex Mono";
  src: url("fonts/plex-mono.woff2") format("woff2");
  font-weight: 400;
  font-display: swap;
}

:root {
  --ink: #16202b;
  --ink-soft: #55697d;
  --page: #eef1f5;
  --panel: #ffffff;
  --rule: #d5dde6;
  --brand: #c3362b;
  --good: #1a6f4a;
  --busy: #8a5300;
  --shadow: 0 1px 0 rgba(22, 32, 43, .04);
  --sans: "Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --mono: "Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e6ecf3;
    --ink-soft: #94a6b8;
    --page: #101720;
    --panel: #18212c;
    --rule: #2a3643;
    --brand: #ef6a5c;
    --good: #4cc38a;
    --busy: #e0a33e;
    --shadow: none;
  }
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--page);
  color: var(--ink);
  font: 400 1rem/1.55 var(--sans);
  -webkit-font-smoothing: antialiased;
}

.masthead {
  display: flex;
  align-items: center;
  gap: .75rem;
  padding: .85rem 1.5rem;
  background: var(--panel);
  border-bottom: 1px solid var(--rule);
}

.mark {
  font-weight: 700;
  letter-spacing: -.01em;
  font-size: 1.05rem;
  color: var(--ink);
  text-decoration: none;
  border-left: 3px solid var(--brand);
  padding-left: .5rem;
}

.masthead .host { font: 400 .82rem/1 var(--mono); color: var(--ink-soft); }
.masthead .spacer { flex: 1; }

main {
  width: 100%;
  padding: 1.5rem;
  display: grid;
  gap: 1.5rem;
}

.state {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  background: var(--panel);
  border: 1px solid var(--rule);
  border-radius: 6px;
  box-shadow: var(--shadow);
  overflow: hidden;
}

.fact { padding: .95rem 1.15rem; border-left: 1px solid var(--rule); }
.fact:first-child { border-left: 0; }
.fact h3 { margin: 0 0 .3rem; font-size: .8rem; font-weight: 600; color: var(--ink-soft); }
.fact p { margin: 0; font-size: 1.05rem; font-weight: 600; }
.note { font-size: .8rem; font-weight: 400; color: var(--ink-soft); }
.fact p.note { margin-top: .25rem; font-size: .8rem; font-weight: 400; }
.fact .path {
  font-family: var(--mono);
  font-size: .72rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.fact .num { font-family: var(--mono); font-size: 1.02rem; }

.meter {
  margin-top: .5rem;
  height: .25rem;
  background: var(--rule);
  border-radius: 2px;
  overflow: hidden;
}
.meter span { display: block; height: 100%; background: var(--ink-soft); }
.meter.tight span { background: var(--brand); }

.panels {
  align-items: start;
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));
}

.panel {
  background: var(--panel);
  border: 1px solid var(--rule);
  border-radius: 6px;
  box-shadow: var(--shadow);
  padding: 1.15rem;
}

.panel > h2 {
  margin: 0 0 .9rem;
  font-size: .98rem;
  font-weight: 700;
}

.panel > h2 .count { color: var(--ink-soft); font-weight: 400; }

form.stack { display: grid; gap: .7rem; }
form.stack label { font-size: .82rem; color: var(--ink-soft); }
form.stack .field { display: grid; gap: .25rem; }

select, input[type="text"] {
  width: 100%;
  padding: .5rem .55rem;
  font: inherit;
  color: inherit;
  background: var(--page);
  border: 1px solid var(--rule);
  border-radius: 4px;
}

select:focus-visible, input:focus-visible, button:focus-visible, a:focus-visible {
  outline: 2px solid var(--brand);
  outline-offset: 2px;
}

.inline { display: flex; align-items: center; gap: .45rem; font-size: .9rem; }

button {
  font: 600 .92rem/1 var(--sans);
  padding: .6rem 1rem;
  color: var(--panel);
  background: var(--ink);
  border: 1px solid var(--ink);
  border-radius: 4px;
  cursor: pointer;
}
button:hover { opacity: .88; }
button.quiet {
  color: var(--ink);
  background: transparent;
  border-color: var(--rule);
  padding: .35rem .6rem;
  font-size: .82rem;
}

a { color: var(--ink); text-decoration-color: var(--rule); text-underline-offset: 2px; }
a.report { font-weight: 600; }

table { width: 100%; border-collapse: collapse; font-size: .9rem; }
th {
  text-align: left;
  font-size: .78rem;
  font-weight: 600;
  color: var(--ink-soft);
  padding: 0 .6rem .45rem 0;
  border-bottom: 1px solid var(--rule);
}
td {
  padding: .55rem .6rem .55rem 0;
  border-bottom: 1px solid var(--rule);
  vertical-align: middle;
}
tr:last-child td { border-bottom: 0; }
td.num, th.num { font-family: var(--mono); text-align: right; white-space: nowrap; }
td.actions { text-align: right; white-space: nowrap; }
td.actions form { display: inline; }
td .name { font-family: var(--mono); font-size: .84rem; color: var(--ink-soft); }
td .note { margin-top: .1rem; }

.tag {
  display: inline-block;
  font-size: .72rem;
  font-weight: 600;
  padding: .1rem .45rem;
  border: 1px solid currentColor;
  border-radius: 3px;
}
.tag.kept { color: var(--brand); }
.tag.running { color: var(--busy); }
.tag.succeeded { color: var(--good); }
.tag.failed, .tag.timed_out { color: var(--brand); }

.pill {
  display: inline-flex;
  align-items: center;
  gap: .4rem;
  font-size: .8rem;
  font-weight: 600;
  padding: .2rem .55rem;
  border: 1px solid var(--rule);
  border-radius: 99px;
}
.pill::before {
  content: "";
  width: .45rem;
  height: .45rem;
  border-radius: 50%;
  background: currentColor;
}
.pill.up { color: var(--good); }
.pill.down { color: var(--brand); }

.empty { margin: 0; color: var(--ink-soft); font-size: .9rem; }

.log {
  margin: 0;
  padding: .85rem;
  background: var(--page);
  border: 1px solid var(--rule);
  border-radius: 4px;
  font: 400 .8rem/1.6 var(--mono);
  white-space: pre-wrap;
  max-height: 60vh;
  overflow: auto;
}

.job-head {
  display: flex;
  align-items: baseline;
  gap: .6rem;
  flex-wrap: wrap;
  margin-bottom: .8rem;
}
.job-head h2 { margin: 0; font-size: .98rem; }
.job-head .when { font: 400 .8rem/1 var(--mono); color: var(--ink-soft); }
.outcome { margin: .9rem 0 0; font-weight: 600; }
.back { font-size: .88rem; }

.logbar {
  display: flex;
  align-items: center;
  gap: .75rem;
  flex-wrap: wrap;
  margin-bottom: .6rem;
}
.logbar input[type="search"] {
  flex: 1 1 14rem;
  min-width: 10rem;
  padding: .4rem .5rem;
  font: inherit;
  color: inherit;
  background: var(--page);
  border: 1px solid var(--rule);
  border-radius: 4px;
}
.logbar .levels { display: flex; gap: .6rem; flex-wrap: wrap; font-size: .82rem; }
.logbar .spacer { flex: 1; }

.loglines {
  border: 1px solid var(--rule);
  border-radius: 4px;
  background: var(--page);
  overflow: auto;
  font: 400 .8rem/1.55 var(--mono);
}
.logline { display: flex; gap: .75rem; padding: 0 .6rem; }
.logline:hover { background: var(--rule); }
.logline .ln {
  flex: 0 0 4.5rem;
  text-align: right;
  color: var(--ink-soft);
  opacity: .65;
  user-select: none;
}
.logline .lt { white-space: pre; flex: 1; }
.loglines.wrap .logline .lt { white-space: pre-wrap; word-break: break-word; }
.logline.error .lt, .logline.critical .lt { color: var(--brand); }
.logline.critical { font-weight: 600; }
.logline.warning .lt { color: var(--busy); }
.logline.debug .lt { opacity: .7; }
.logline.hidden { display: none; }

body.wide { display: flex; flex-direction: column; height: 100vh; }
body.wide main { flex: 1; min-height: 0; padding-bottom: 1rem; }
body.wide .logview { display: flex; flex-direction: column; min-height: 0; }
body.wide .loglines { flex: 1; min-height: 12rem; }

.files { list-style: none; margin: 0; padding: 0; }
.files li { padding: .4rem 0; border-bottom: 1px solid var(--rule); }
.files li:last-child { border-bottom: 0; }
.files a { font-family: var(--mono); font-size: .86rem; }

@media (max-width: 40em) {
  main { padding: 1rem; gap: 1rem; }
  .fact { border-left: 0; border-top: 1px solid var(--rule); }
  .fact:first-child { border-top: 0; }
  table, thead, tbody, tr, td, th { display: block; }
  thead { display: none; }
  tr { padding: .5rem 0; border-bottom: 1px solid var(--rule); }
  td { border: 0; padding: .15rem 0; }
  td.num, td.actions { text-align: left; }
}
"""

JAVASCRIPT = """
(function () {
  var view = document.querySelector('[data-log-view]');
  if (view) {
    var lines = Array.prototype.slice.call(view.querySelectorAll('.logline'));
    var filter = document.getElementById('log-filter');
    var wrap = document.getElementById('log-wrap');
    var box = document.getElementById('log-lines');
    var count = document.getElementById('log-count');
    var toggles = Array.prototype.slice.call(view.querySelectorAll('.level-toggle'));

    function apply() {
      var needle = filter.value.toLowerCase();
      var wanted = {};
      toggles.forEach(function (toggle) { wanted[toggle.value] = toggle.checked; });
      var shown = 0;
      lines.forEach(function (line) {
        var body = line.querySelector('.lt');
        var text = (body ? body.textContent : '').toLowerCase();
        var keep = wanted[line.dataset.level] !== false && text.indexOf(needle) !== -1;
        line.classList.toggle('hidden', !keep);
        if (keep) { shown += 1; }
      });
      count.textContent = shown === lines.length
        ? ''
        : 'Showing ' + shown + ' of ' + lines.length + ' lines.';
    }

    filter.addEventListener('input', apply);
    toggles.forEach(function (toggle) { toggle.addEventListener('change', apply); });
    wrap.addEventListener('change', function () { box.classList.toggle('wrap', wrap.checked); });
    box.scrollTop = box.scrollHeight;
  }
})();

(function () {
  var card = document.querySelector('[data-log-url]');
  if (!card) { return; }
  var logUrl = card.dataset.logUrl;
  var log = document.getElementById('job-log');
  var status = document.getElementById('job-status');
  var outcome = document.getElementById('job-outcome');
  var report = document.getElementById('job-report');
  var next = parseInt(card.dataset.nextLine || '0', 10);

  function poll() {
    fetch(logUrl + '?from=' + next, { headers: { 'Accept': 'application/json' } })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (data.lines.length) {
          log.textContent += data.lines.join('\\n') + '\\n';
          log.scrollTop = log.scrollHeight;
        }
        if (typeof data.next_line === 'number') {
          next = data.next_line;
        }
        status.textContent = data.status;
        status.className = 'tag ' + data.status;
        outcome.textContent = data.outcome || '';
        if (data.report_url && !report.querySelector('a')) {
          var link = document.createElement('a');
          link.className = 'report';
          link.href = data.report_url;
          link.textContent = 'Open the report';
          report.appendChild(link);
        }
        if (data.status === 'running') { setTimeout(poll, 1000); }
      })
      .catch(function () { setTimeout(poll, 3000); });
  }

  poll();
})();
"""
