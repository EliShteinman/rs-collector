# rsc — RedisScope collector

Collects a Redis Enterprise cluster support package over SSH and analyzes it with RedisScope.
It ships as a single executable for RHEL 9 x86_64; the target server needs no Python.

## Build

Requires Docker on the build machine. Every Python package it installs is stored in `vendor/`,
so the build pulls no package from the network.

```bash
./build/build.sh          # produces dist/rsc
```

## Install (RHEL 9 x86_64)

Copy the release directory (`dist/rsc`, `config/`, `deploy/`, `.env.example`) to the server and run:

```bash
sudo ./deploy/install.sh
```

The installer creates the `rsc` service user, installs the binary in `/opt/rsc/bin/rsc`,
the configuration in `/etc/rsc/config`, and enables `rsc-serve.service` and
`rsc-cleanup.timer`.

Then fill in:

- `/etc/rsc/config/clusters.yml` — the environments and their clusters
- `/etc/rsc/rsc.env` — `RSC_DATA_ROOT` (the directory all output goes to), SSH user, key or
  password, and the sudo password if one is needed
- `/etc/rsc/config/settings.yml` — the path of the RedisScope executable

Then start the display server: `sudo systemctl start rsc-serve.service`.

## Use

```bash
rsc collect                             # environment -> cluster -> collect -> optional analysis
rsc collect --conn-string redis://db.cluster1.example.com:12000
rsc analyze                             # pick a stored package, pick options, analyze
rsc list                                # stored packages and analyses
rsc pin <name> / rsc unpin <name>       # keep an item beyond the retention period
rsc cleanup [--dry-run]                 # runs daily through the systemd timer
rsc serve                               # the display server (runs as a systemd service)
```

The analyses are published by the display server on the port set in `settings.yml` (3923 by
default).

## Development

```bash
python3.14 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/ruff check .
```
