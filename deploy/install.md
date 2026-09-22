# Installing rsc on RHEL 9

## 1. Build the executable

On a machine with Docker:

```bash
./build/build.sh
```

`dist/rsc` is a single file with no external dependency. The Python packages come from
`vendor/wheels`, the build tools from `vendor/build-wheels`.

## 2. Copy the release to the server

```bash
tar czf rsc-release.tar.gz dist/rsc config deploy .env.example
scp rsc-release.tar.gz admin@server:/tmp/
ssh admin@server 'mkdir -p /tmp/rsc-release && tar xzf /tmp/rsc-release.tar.gz -C /tmp/rsc-release'
```

## 3. Install

```bash
ssh admin@server 'sudo /tmp/rsc-release/deploy/install.sh'
```

What the installer does:

| Path | Content |
|---|---|
| `/opt/rsc/bin/rsc` | the executable |
| `/usr/local/bin/rsc` | symbolic link to it |
| `/etc/rsc/config/` | `settings.yml`, `clusters.yml`, `logging.yml`, `copyparty.conf` |
| `/etc/rsc/rsc.env` | SSH and sudo secrets, mode 0640, owned by `root:rsc` |
| `/etc/systemd/system/` | `rsc-serve.service`, `rsc-cleanup.service`, `rsc-cleanup.timer` |
| `/etc/profile.d/rsc.sh` | exports `RSC_CONFIG_DIR` for interactive use |

An existing configuration file is never overwritten: the new one is written next to it with a
`.new` suffix.

## 4. Configure

`/etc/rsc/rsc.env`:

```
RSC_DATA_ROOT=/mnt/storage/rsc
RSC_SSH_USER=svc_redis
RSC_SSH_KEY_PATH=/etc/rsc/id_ed25519
RSC_SSH_PASSWORD=
RSC_SUDO_PASSWORD=
```

`RSC_DATA_ROOT` is the directory all output goes to. rsc creates `packages/`, `analyses/`,
`locks/` and `logs/` under it.

Set `RSC_SUDO_PASSWORD` only when `sudo su -` asks for a password on the cluster nodes.

`/etc/rsc/config/settings.yml` holds `analysis.redisscope_binary` — the path of the installed
RedisScope executable.

`/etc/rsc/config/clusters.yml` holds the clusters:

```yaml
environments:
  production:
    - fqdn: cluster1.example.com
      nodes:
        - node1.cluster1.example.com
        - node2.cluster1.example.com
```

## 5. Start and check

```bash
sudo systemctl start rsc-serve.service
rsc list
systemctl status rsc-serve.service
systemctl list-timers rsc-cleanup.timer
curl -sI http://localhost:3923/analyses/ | head -1
```

## Upgrade

Build a new binary, copy it over, and:

```bash
sudo install -m 0755 dist/rsc /opt/rsc/bin/rsc
sudo systemctl restart rsc-serve.service
```
