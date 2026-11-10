# Dynamic SDN Host Blocker

A lab-focused Python prototype for detecting abnormal TCP SYN rates and
responding with OpenFlow drop rules in an isolated VirtualBox and Mininet lab.

> Status: the OS-Ken controller and Mininet OpenFlow 1.3 topology have been
> exercised in the Ubuntu lab. Three Mininet hosts communicate, a selected
> host can be blocked through the controller API, unaffected hosts remain
> reachable, and connectivity returns after unblocking. TCP/UDP socket
> programs and transport tests are included. Automatic multi-interface SYN
> monitoring now has a controller API integration path; live packet-capture
> enforcement still needs verification in the user's VM.

## Features

- Rolling-window TCP initial SYN counting by source IP
- Shared detector across multiple capture interfaces
- Configurable threshold, window and consecutive-window trigger
- SQLite temporary blocklist and JSON Lines security event log
- Alert-only by default; optional controller API or direct OVS enforcement
- OS-Ken OpenFlow 1.3 controller with manual block/unblock API
- Concurrent TCP and UDP socket client/server examples
- Unit tests and GitHub Actions

## Setup

Recommended: Ubuntu Server VM, Python 3.10+, VirtualBox, Open vSwitch,
Mininet, Scapy and OS-Ken.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip openvswitch-switch mininet
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[controller,capture]'
```

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## VirtualBox host-facing monitor

The original `config/thresholds.json` remains configured for the separate
`10.10.0.0/24` VirtualBox lab. See [architecture](docs/architecture.md).
Start in alert-only mode; add `--enforce` only after validating the isolated
network.

## Mininet controller and automatic detection

The Mininet topology uses `10.20.0.0/24`, separate from the VirtualBox lab.
The dedicated `config/mininet-thresholds.json` preserves that separation.
Start the OS-Ken controller and Mininet topology, then run the monitor with
the switch-facing interfaces:

```bash
sudo .venv/bin/python -m dynamic_sdn_blocker.monitor \
  --config config/mininet-thresholds.json \
  --interface s1-eth1 s1-eth2 s1-eth3
```

This is alert-only. Add `--enforce` to send detected source IPs to the
controller's existing localhost API and install temporary OpenFlow drop rules.
See [controller and automatic SYN protection](docs/controller.md) for the
complete commands and event-log locations.

## TCP and UDP socket applications

See [socket application instructions](docs/socket-app.md) for concurrent
TCP/UDP servers and clients, JSON message format, and Mininet test commands.
The demo uses TCP port `9000` and UDP port `9001`, with the Mininet server
at `10.20.0.10`.

## VirtualBox safety

Use separate named Internal Networks for endpoint-to-SDN-Core links. SDN-Core
may use a separate NAT adapter for package downloads, but never add that NAT
adapter to `br0`. Keep test traffic isolated and use only systems you own or
are authorized to test.

## Limitations

Detection is based on initial TCP SYN rate and captures only the interfaces
specified to one monitor process. Enforcement drops IPv4 traffic from the
detected source. Live flow-statistics polling and automatic expiry
reconciliation between the standalone SQLite blocklist and controller state
remain future work. See [roadmap](docs/roadmap.md).

MIT licensed. See `LICENSE`.
