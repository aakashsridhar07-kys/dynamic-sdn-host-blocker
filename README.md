# Dynamic SDN Host Blocker

A lab-focused Python prototype for detecting abnormal TCP SYN rates and responding with Open vSwitch (OVS) drop rules in an isolated Oracle VirtualBox environment.

> Status: starter/MVP. SYN-rate detection, SQLite blocklist, JSONL event logging, OVS rule adapter, flow-counter rate helper, unit tests, and CI are included. A dedicated OpenFlow controller and live switch flow-statistics polling remain planned integration work.

## Features

- Rolling-window TCP initial SYN counting by source IP
- Configurable threshold and consecutive-window trigger
- CIDR checks for detector and OVS rules
- SQLite persistent temporary blocklist
- JSON Lines event log
- Alert-only by default; enforcement requires `--enforce`
- Flow-counter delta helper, unit tests, and GitHub Actions

## Setup

Recommended: Ubuntu Server VM, Python 3.10+, VirtualBox, Open vSwitch and Scapy.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip openvswitch-switch
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[capture]'
```

Edit `config/thresholds.json` for your lab. Sample addresses are Client A `10.10.0.11`, Client B `10.10.0.12`, server `10.10.0.100`.

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Live monitoring (alert-only):

```bash
sudo .venv/bin/python -m dynamic_sdn_blocker.monitor --config config/thresholds.json --interface <HOST_FACING_INTERFACE>
```

After validating the isolated topology, add `--enforce` to enable OVS rules. Inspect them with `sudo ovs-ofctl -O OpenFlow13 dump-flows br0`.

## VirtualBox safety

Use a separate named Internal Network for each endpoint-to-SDN-Core link. SDN-Core may use a separate NAT adapter for package downloads, but never add that NAT adapter to `br0`. Keep test traffic isolated. Use only systems you own or are authorized to test.

## Limitations

The detector focuses on TCP SYN rate, the monitor captures one interface per process, OVS enforcement currently covers IPv4, and live controller-driven flow-statistics polling is not yet implemented. Start in alert-only mode and tune thresholds against measured baseline traffic. See `docs/roadmap.md`.

MIT licensed. See `LICENSE`.
