# rsc — RedisScope collector

Collects a Redis Enterprise cluster support package over SSH and analyzes it with RedisScope.
It ships as a single executable for RHEL 9 x86_64; the server needs no Python and no root.

## Build

On a RHEL 9 x86_64 machine, as a regular user. It needs no Docker and no root:

```bash
./build/build.sh          # produces dist/rsc-release.tar.gz
```

Python 3.14 and every package come from `vendor/`, so the build needs no network.

## Install

Copy `dist/rsc-release.tar.gz` to the server and unpack it wherever you like:

```bash
tar xzf rsc-release.tar.gz
cd rsc-release
```

```
rsc-release/
├── rsc          the program
├── rsc.env      RSC_DATA_ROOT and the SSH settings
└── config/      settings.yml, clusters.yml, logging.yml
```

Fill in:

- `rsc.env` — `RSC_DATA_ROOT` (the directory all output goes to), the SSH user, key or
  password, `RSC_SUDO_PASSWORD` only if `sudo su -` asks for one on the cluster nodes, and
  `RSC_WEB_USER` with `RSC_WEB_PASSWORD` for the login the web interface asks for
- `config/clusters.yml` — the environments and their clusters
- `config/settings.yml` — `analysis.redisscope_binary`, only if `redisscope` is not on the `PATH`

Then:

```bash
./rsc start
```

The display server now runs in the background. It keeps running after you close the
terminal, starts again after the server reboots, and old packages and analyses are removed
daily. `./rsc stop` turns all of that off.

## Upgrade

Unpack the new release somewhere else. Do not unpack it over the old folder, because that
would replace your `rsc.env`. Then:

```bash
./rsc stop
cp <new>/rsc ./rsc
diff <new>/config/settings.yml config/settings.yml    # copy over any new settings
./rsc start
```

## Use

Open `http://<server>:3923/` and everything happens there:

- see whether the interface runs in the background, whether it comes back after a reboot,
  whether it asks for a login, when the cleanup last ran and how much disk is left
- pick a cluster and collect a new support package
- pick a stored package and analyze it, choosing depth, a single database and masking
- watch the log of a running collection or analysis as it happens
- open the finished reports, and keep any package or analysis beyond the retention period
- browse every file RedisScope wrote, including the raw cluster logs it extracted into
  `redisscope_sp/`
- read those logs in a viewer with line numbers, colours by severity, a filter box and a
  toggle per level. Rotated `.gz` logs are unpacked on the way; `?plain=1` shows a log as
  plain text and `?raw=1` downloads the file untouched

The same actions are available on the command line:

```bash
./rsc collect                           # environment -> cluster -> collect -> optional analysis
./rsc collect --conn-string redis://db.cluster1.example.com:12000
./rsc analyze                           # pick a stored package, pick options, analyze
./rsc list                              # stored packages and analyses
./rsc pin <name> / ./rsc unpin <name>   # keep an item beyond the retention period
./rsc start / ./rsc stop                # the web interface in the background
./rsc serve                             # the web interface in the foreground
```

## Who can use it

The web interface asks for a user and a password when `rsc.env` holds them:

```
RSC_WEB_USER=ops
RSC_WEB_PASSWORD=<the password>
```

Every page, file and report is then behind that login, the browser asks for it once per
session, and a refused attempt is written to the rsc log with the user name that was tried.
Setting only one of the two variables is refused at startup, so a typo cannot quietly leave
the interface open. Put them in `rsc.env` rather than exporting them in your shell: after a
reboot the crontab starts rsc without your shell, and `rsc.env` is the only place it reads.

With neither variable set the interface has no login: anyone who can reach the port can
collect, analyze and read everything. rsc then writes a warning to its log and says so on
the console page, under "Who can open it". Restart with `./rsc stop && ./rsc start` after
changing the variables.

There is one login for everyone, not an account per person. It says who may open the
interface, not who did what: a collection is always run by the user that owns the rsc
process, with that user's SSH credentials. Because the password travels in the request,
publish the interface over HTTPS only, as below.

## Behind a reverse proxy

rsc speaks plain HTTP on one port and needs no websockets, so it sits behind NGINX
unchanged. Bind it to localhost first, so the only way in is through the proxy — in
`config/settings.yml`:

```yaml
serve:
  host: 127.0.0.1
  port: 3923
```

Then put this in `/etc/nginx/conf.d/rsc.conf`, with your own host name and certificate:

```nginx
server {
    listen 80;
    server_name rsc.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name rsc.example.com;

    ssl_certificate     /etc/pki/tls/certs/rsc.example.com.crt;
    ssl_certificate_key /etc/pki/tls/private/rsc.example.com.key;

    access_log /var/log/nginx/rsc_access.log;
    error_log  /var/log/nginx/rsc_error.log;

    location / {
        proxy_pass http://127.0.0.1:3923;

        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

What each part is for:

- `proxy_buffering off` sends a report or a log file straight through instead of spooling it
  to disk first, which matters because a package's logs run to tens of megabytes
- `proxy_read_timeout 300s` covers the long requests: collecting a package and starting an
  analysis answer immediately, but a large download does not
- the login needs nothing extra. NGINX passes the `Authorization` header on by default, so
  rsc sees it. Do not add `auth_basic` as well, or the browser will ask twice
- no `client_max_body_size` is needed: nothing is ever uploaded to rsc

Reload with `nginx -t && systemctl reload nginx`. On RHEL, SELinux blocks the proxy until
`setsebool -P httpd_can_network_connect on`, and the firewall needs
`firewall-cmd --permanent --add-service=https && firewall-cmd --reload`.

To publish it under a subpath, tell rsc the prefix. Either set `serve.base_path: "/rsc"` in
`settings.yml`, or let NGINX send it:

```nginx
location /rsc/ {
    proxy_pass http://127.0.0.1:3923/;
    proxy_set_header X-Forwarded-Prefix /rsc;
}
```

Collecting a package needs SSH (port 22) from this server to the cluster nodes, which is
outgoing traffic and unrelated to the proxy.

## Development

```bash
python3.14 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pre-commit install
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/pip-audit -r vendor/requirements.txt --no-deps --disable-pip
```
