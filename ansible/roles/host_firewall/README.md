# host_firewall

The role installs a host firewall on the `docker_hosts` group (9 hosts) and on the
`firewall_only_hosts` group (`core-01`). The firewall starts in
**observe mode**: it records the traffic that it would drop, and it drops nothing new.
A later step switches a host to enforce mode, after a person reviews the records.

## What the role installs

| Item | Path on the host |
|---|---|
| nft table file | `/etc/homelab-fw/homelab-fw.nft` |
| systemd unit | `/etc/systemd/system/homelab-fw.service` |

The table is `inet homelab_fw`. It is separate from the tables that Docker and
`nftables.service` write. A separate table means Docker never changes it. A drop in any table
is final, so the table works in front of the Docker rules.

**Warning: the role never touches `/etc/nftables.conf` or `nftables.service`, and it never
runs `flush ruleset`.** On the LXC hosts, `/etc/nftables.conf` starts with `flush ruleset`.
A restart or reload of `nftables.service` deletes all Docker rules and this table. The role
also never installs the `nftables` package, because the package can enable that service. The
role fails with a clear message when `/usr/sbin/nft` is missing. All 10 hosts have the binary
(checked 2026-10-09).

## How the table works

| Chain | Hook | Traffic |
|---|---|---|
| `input` | input, priority `filter - 5` | Host processes: sshd, host-network containers, `docker-proxy` (IPv6 published ports) |
| `dnat_new` | none (called from `forward`) | New connections to Docker published ports |
| `forward` | forward, priority `filter - 5` | Sends new DNAT packets to `dnat_new`. Accepts all other forwarded packets. |

Docker publishes ports with DNAT, so IPv4 traffic to a published port uses the forward hook.
The `dnat_new` chain matches the original destination port with `ct original proto-dst`.
Container egress and container-to-container traffic do not change.

Rule order in `input` and `dnat_new`:

1. Established and related traffic, loopback (`input` only), ICMP and ICMPv6.
2. Hawser rules (hosts with `host_firewall_hawser: true`). These rules are enforced in every mode.
3. Accept from `host_firewall_container_cidrs` (containers on this host).
4. Accept rules from the rule list (see "Rule list").
5. Final action for a new connection: add the tuple (source, protocol, port) to the set
   `would_drop_v4` or `would_drop_v6`, write a rate-limited log line, then `accept`
   (observe mode) or `drop` (enforce mode).

The role does not filter outbound traffic.

### Hawser rules

Before this role, `iptables` rules in `DOCKER-USER` (IPv4) and `ip6tables` rules in `INPUT`
(IPv6) protected port 2376. They were manual and did not survive a reboot. The table now holds
the same rules, and they are enforced in observe mode too:

- tcp/2376 from `192.168.50.105` (Dockhand): accept. Any other IPv4 source: drop.
- tcp/2376 over IPv6: drop.

After the table loads, the role removes the manual rules, but only when they exist.

## Hosts covered

| Group | Hosts | Note |
|---|---|---|
| `docker_hosts` | `telemetry-prod-01`, `plane-prod-01`, `coolify-prod-01`, `garage-prod-01`, `forgejo-prod-01`, `docker-prod-01`, `docker-prod-02`, `proxy-prod-01`, `komodo-prod-01` | Also get `provision-baseline.yml`. |
| `firewall_only_hosts` | `core-01` | Only this role runs here. See below. |

`core-01` is a Raspberry Pi 4 (arm64) that is not in `docker_hosts`. The Docker and Periphery
roles must not run on it, so `provision-baseline.yml` never targets it. `core-01` serves DNS
(AdGuard) to every VLAN. **Warning: a wrong rule for port 53 on `core-01` takes down DNS for
the whole network.** Its rules are in `ansible/inventory/host_vars/core-01.yml`. Port 53 is open
to `any`, and the web UI on port 80 is open to the ADMIN VLAN only.
`nas-01` is not covered (TOS manages its own chains there).

## Variables

| Variable | Default | Meaning |
|---|---|---|
| `host_firewall_enforce` | `false` | `false` is observe mode. `true` is enforce mode. |
| `host_firewall_hawser` | `false` | `true` on hosts with a Hawser agent. Set in `host_vars`. |
| `host_firewall_container_cidrs` | `172.16.0.0/12` | Container sources. `coolify-prod-01` adds `10.0.0.0/8`. |
| `host_firewall_common_rules` | SSH | Rules for every host. |
| `host_firewall_periphery_rules` | 8120 | Added unless `periphery_managed` is `false`. |
| `host_firewall_host_rules` | `[]` | Rules for one host. Set in `host_vars`. |
| `host_firewall_set_timeout` | `8d` | The time that an element stays in a would-drop set. |
| `host_firewall_set_size` | `16384` | The maximum number of elements in each set. |

The file `defaults/main.yml` also has named addresses (`host_firewall_addr_admin`,
`host_firewall_addr_proxy`, and others). Use these names in rules.

### Rule list

Each entry has these keys:

```yaml
- ports: [3000, 3001]         # published ports (the port that the client uses)
  proto: tcp                  # tcp, udp, or a list of both
  sources: ["{{ host_firewall_addr_proxy }}"]   # "any", or IPv4 and IPv6 CIDRs
  admin: true                 # optional, default true: also allow the ADMIN VLAN
  comment: web services behind traefik
```

Put fleet rules in the role defaults. Put host rules in `ansible/inventory/host_vars/<host>.yml`.
A source with a colon is an IPv6 CIDR. The role renders IPv4 and IPv6 sources as separate rules.

## Run the role

The role is **not** part of `provision-baseline.yml`. It applies only when someone runs the
playbook on purpose.

```bash
cd ansible
ansible-playbook playbooks/host-firewall.yml --check --diff -l <host>   # preview
ansible-playbook playbooks/host-firewall.yml -l <host>                  # apply, observe mode
```

A re-run with no template change does not reload the table. When the template changes, the
handler loads the file with `nft -f`. The file replaces the table in one atomic step, so no
gap occurs in the Hawser rules. **A reload clears the would-drop sets.** Read the sets before
you change a rule.

## Review the would-drop records

The sets are the main review source. In an LXC container the kernel log goes to the Proxmox
host, so the log line is a second source only.

```bash
sudo nft list set inet homelab_fw would_drop_v4
sudo nft list set inet homelab_fw would_drop_v6
```

Each element is `source . protocol . port` with a packet counter and an expiry time. For all
`docker_hosts`, run `make firewall-review` from the repository root. For `core-01`, run the
`nft list set` commands on the host.

For each element, decide one of two actions:

- The traffic is real and wanted: add a rule to `host_firewall_host_rules` (or the defaults).
- The traffic is not wanted: leave it. Enforce mode drops it.

Observe a full week first. Nightly and weekly jobs (the rsync job at 22:30, backups) do not
appear in a short sample.

Known gaps to watch for in the sets:

| Host | Port | Note |
|---|---|---|
| `docker-prod-01` | 111 (`rpcbind`) | Not allowed on purpose. |
| `docker-prod-02` | 5355 (LLMNR) | Not allowed on purpose. |
| `docker-prod-02` | 4000 (litellm) | Allowed from the proxy and ADMIN. Other clients show in the sets. |
| `telemetry-prod-01` | 8181 (influxdb) | Docker bridges are allowed. External writers are unknown. |
| `garage-prod-01` | 3901 | The Garage RPC port is not allowed. A self-connection uses loopback. |

## Switch a host to enforce mode

1. Review the sets on the host for at least one week. Add a rule for each wanted element.
2. Set `host_firewall_enforce: true` in `ansible/inventory/host_vars/<host>.yml`.
3. Run `ansible-playbook playbooks/host-firewall.yml --check --diff -l <host>`. Read the diff.
4. Open a console that does not use SSH (the Proxmox console) before you apply.
   A wrong rule can lock out SSH.
5. Apply with `-l <host>`.
6. Test from a client: SSH, the host web UIs, a Komodo deploy, and the Dockhand agent.

## Rollback

```bash
sudo systemctl stop homelab-fw
```

The stop deletes the table `inet homelab_fw`. All Docker rules stay. To go back to observe
mode, set `host_firewall_enforce: false` and run the playbook again. To disable the unit at
boot, run `sudo systemctl disable homelab-fw`.

**Warning: the stop also removes the Hawser rules.** The old manual rules are gone. Run the
playbook again soon, or add the manual rules from `stacks/hawser/README.md` again.

## Limits

- The firewall does not filter outbound traffic.
- Invalid packets (`ct state invalid`) are not dropped.
- The role manages only the hosts in `docker_hosts` and `firewall_only_hosts` (`core-01`).
  `nas-01` keeps the manual Hawser rules, which do not survive a reboot.
- A restart of `nftables.service` (LXC hosts) deletes the table. Check with
  `sudo nft list tables` after such a restart, and run `sudo systemctl restart homelab-fw`.
