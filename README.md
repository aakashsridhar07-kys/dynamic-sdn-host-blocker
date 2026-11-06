# Dynamic SDN Host Blocker

A lab-focused Python prototype for detecting abnormal TCP SYN rates and responding with Open vSwitch (OVS) drop rules in an isolated Oracle VirtualBox environment.

> Status: lab prototype. The OS-Ken controller and Mininet OpenFlow 1.3 topology have been exercised in the Ubuntu lab: three Mininet hosts communicate, a selected host can be blocked through the controller API, unaffected hosts remain reachable, and connectivity returns after unblocking. TCP/UDP socket programs and automated transport tests are included; the socket demo still needs to be run in the user's VM.

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

## Mininet and SDN controller

See [`docs/controller.md`](docs/controller.md) for OS-Ken installation, controller startup, Mininet commands, and the local block/unblock API. The Mininet test network uses `10.20.0.0/24`, separate from the existing VirtualBox lab network.

Install the controller extra with `python -m pip install -e '.[controller]'`. Start the controller with `python -c "from os_ken.base.app_manager import AppManager; AppManager.run_apps(['controller.sdn_controller'])"` before launching `sudo python3 topology/sdn_topology.py`.

## TCP and UDP socket applications

See [`docs/socket-app.md`](docs/socket-app.md) for the concurrent TCP server/client and UDP server/client, JSON message format, and Mininet test commands. The demo uses TCP port `9000` and UDP port `9001`, with the Mininet server at `10.20.0.10`.

Install the project from the repository root with `python -m pip install -e .`. Run socket tests with `python -m unittest discover -s tests -p 'test_socket_*.py' -v`. These tests exercise JSON validation, TCP echo, concurrent TCP clients, and UDP echo on loopback.

See [`docs/socket-app.md`](docs/socket-app.md) for Mininet commands to run the TCP/UDP servers on h3 and clients on h1/h2.

## VirtualBox safety

Use a separate named Internal Network for each endpoint-to-SDN-Core link. SDN-Core may use a separate NAT adapter for package downloads, but never add that NAT adapter to `br0`. Keep test traffic isolated. Use only systems you own or are authorized to test.

## Limitations

The detector focuses on TCP SYN rate, the monitor captures one interface per process, OVS enforcement currently covers IPv4, and live controller-driven flow-statistics polling is not yet implemented. Start in alert-only mode and tune thresholds against measured baseline traffic. See `docs/roadmap.md`.

MIT licensed. See `LICENSE`.
