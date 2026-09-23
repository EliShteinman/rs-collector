CSS = """
:root { color-scheme: light dark; --gap: 1rem; }
body { margin: 0; font: 15px/1.5 system-ui, sans-serif; }
header { display: flex; align-items: baseline; gap: .6rem;
         padding: var(--gap); border-bottom: 1px solid #8884; }
.brand { font-weight: 700; text-decoration: none; color: inherit; }
.subtitle { color: #8a8a8a; }
main { display: grid; gap: var(--gap); padding: var(--gap); max-width: 60rem; }
.card { border: 1px solid #8884; border-radius: 8px; padding: var(--gap); }
h2 { margin: 0 0 var(--gap); font-size: 1.05rem; }
form { display: grid; gap: .5rem; max-width: 34rem; }
label { font-size: .85rem; color: #8a8a8a; }
label.checkbox { color: inherit; display: flex; align-items: center; gap: .4rem; }
select, input[type=text], input:not([type]) { padding: .45rem; border-radius: 6px;
        border: 1px solid #8886; background: transparent; color: inherit; }
button, .button { justify-self: start; padding: .5rem 1rem; border-radius: 6px;
        border: 1px solid #8886; background: #2f6feb; color: #fff; cursor: pointer;
        text-decoration: none; }
ul.rows { list-style: none; margin: 0; padding: 0; display: grid; gap: .35rem; }
ul.rows li { display: flex; gap: .6rem; align-items: baseline; flex-wrap: wrap; }
.when { color: #8a8a8a; font-size: .85rem; }
.status { font-size: .75rem; text-transform: uppercase; letter-spacing: .04em;
        border: 1px solid #8886; border-radius: 99px; padding: 0 .5rem; }
.status.running { border-color: #d29922; color: #d29922; }
.status.succeeded { border-color: #3fb950; color: #3fb950; }
.status.failed, .status.timed_out { border-color: #f85149; color: #f85149; }
pre { background: #8881; border-radius: 6px; padding: .75rem; overflow-x: auto;
      max-height: 26rem; overflow-y: auto; white-space: pre-wrap; }
.empty { color: #8a8a8a; }
.outcome { font-weight: 600; }
"""

JAVASCRIPT = """
(function () {
  var card = document.querySelector('[data-log-url]');
  if (!card) { return; }
  var logUrl = card.dataset.logUrl;
  var log = document.getElementById('job-log');
  var status = document.getElementById('job-status');
  var outcome = document.getElementById('job-outcome');
  var report = document.getElementById('job-report');
  var next = log.textContent ? log.textContent.replace(/\\n$/, '').split('\\n').length : 0;

  function poll() {
    fetch(logUrl + '?from=' + next, { headers: { 'Accept': 'application/json' } })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (data.lines.length) {
          log.textContent += data.lines.join('\\n') + '\\n';
          log.scrollTop = log.scrollHeight;
          next += data.lines.length;
        }
        status.textContent = data.status;
        status.className = 'status ' + data.status;
        outcome.textContent = data.outcome || '';
        if (data.report_url && !report.querySelector('a')) {
          var link = document.createElement('a');
          link.className = 'button';
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
