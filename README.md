# rsc — RedisScope collector

Collects a Redis Enterprise cluster support package over SSH and analyzes it with RedisScope.
It ships as a single executable for RHEL 9 x86_64; the server needs no Python and no root.

## Build

On a RHEL 9 x86_64 machine, as a regular user. It needs no Docker and no root:

```bash
./build/fetch-python.sh   # once: downloads Python 3.14 into .build/python
./build/build.sh          # produces dist/rsc-release.tar.gz
```

The Python packages come from `vendor/`, so the build itself downloads nothing.

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
└── config/      settings.yml, clusters.yml, logging.yml, copyparty.conf
```

Fill in:

- `rsc.env` — `RSC_DATA_ROOT` (the directory all output goes to), the SSH user, key or
  password, and `RSC_SUDO_PASSWORD` only if `sudo su -` asks for one on the cluster nodes
- `config/clusters.yml` — the environments and their clusters
- `config/settings.yml` — `analysis.redisscope_binary`, the path of RedisScope

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

```bash
./rsc collect                           # environment -> cluster -> collect -> optional analysis
./rsc collect --conn-string redis://db.cluster1.example.com:12000
./rsc analyze                           # pick a stored package, pick options, analyze
./rsc list                              # stored packages and analyses
./rsc pin <name> / ./rsc unpin <name>   # keep an item beyond the retention period
./rsc start / ./rsc stop                # the display server in the background
```

The analyses are published at `http://<server>:3923/analyses/` (the port is in
`settings.yml`).

## Development

```bash
python3.14 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pre-commit install
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/pip-audit -r vendor/requirements.txt --no-deps --disable-pip
```
