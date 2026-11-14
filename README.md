# Dynamic SDN Host Blocker

A Mininet-based Python project for detecting abnormal TCP SYN rates and
responding with OpenFlow drop rules through an SDN controller. The project
runs its network experiment entirely inside Mininet; it does not use a
separate VirtualBox host-facing network or physical endpoint VMs.

> Status: the Ubuntu Mininet lab has demonstrated end-to-end automatic SYN
> detection, JSONL event logging, controller-driven host blocking, selective
> blocking (h1 blocked while h2 remains reachable), and automatic recovery
> after the temporary OpenFlow rule expires. TCP and UDP socket communication
> between Mininet hosts has also been tested successfully.

## Features

- Rolling-window TCP initial SYN counting by source IP
- Shared detector across multiple Mininet switch-facing interfaces
- Configurable threshold, window and consecutive-window trigger
- SQLite temporary blocklist and JSON Lines security event log
- Alert-only by default; optional controller API enforcement
- OS-Ken OpenFlow 1.3 controller with manual block/unblock API
- Automatic temporary IPv4 source blocking through the controller API
- Concurrent TCP and UDP socket client/server examples
- Unit tests and GitHub Actions

## Mininet lab topology

The experiment uses one Mininet switch and three Mininet hosts:

| Mininet host | Role | IP address |
|---|---|---|
| h1 | Client A | 10.20.0.1 |
| h2 | Client B | 10.20.0.2 |
| h3 | TCP/UDP server | 10.20.0.10 |

The Open vSwitch switch is named s1 and connects to the local OS-Ken
controller at 127.0.0.1:6653 using OpenFlow 1.3. The Mininet hosts are
virtual hosts created by Mininet, not separate VirtualBox VMs.

## Requirements and setup

Use an Ubuntu environment with Python 3, Open vSwitch, Mininet, Scapy and
OS-Ken. VirtualBox may be used to run the Ubuntu environment, but the project
network topology and experiments are Mininet-only.

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

## Start the controller and Mininet

Start the OS-Ken controller, then launch the topology:

```bash
python -c "from os_ken.base.app_manager import AppManager; AppManager.run_apps(['controller.sdn_controller'])"
sudo python3 topology/sdn_topology.py
```

If your terminal has trouble with the one-line controller command, see
[controller instructions](docs/controller.md) for the interactive Python
alternative and API checks.

## TCP SYN detection and dynamic blocking

The Mininet-specific configuration is
config/mininet-thresholds.json. Start the monitor on the switch-facing
interfaces:

```bash
sudo .venv/bin/python -m dynamic_sdn_blocker.monitor \
  --config config/mininet-thresholds.json \
  --interface s1-eth1 s1-eth2 s1-eth3
```

This runs in alert-only mode and logs detections. Add --enforce to send
detected source IPs to the controller's localhost API and install temporary
OpenFlow drop rules:

```bash
sudo .venv/bin/python -m dynamic_sdn_blocker.monitor \
  --config config/mininet-thresholds.json \
  --interface s1-eth1 s1-eth2 s1-eth3 \
  --enforce
```

See [controller and automatic SYN protection](docs/controller.md) and
[Mininet validation notes](docs/mininet-validation.md) for detailed commands
and event-log locations.

## TCP and UDP socket applications

See [socket application instructions](docs/socket-app.md) for concurrent
TCP/UDP servers and clients, JSON message format, and Mininet test commands.
The demo uses TCP port 9000 and UDP port 9001, with the Mininet server
at 10.20.0.10.

## Verified Mininet demonstration

The following behaviors have been exercised in the Ubuntu Mininet lab:

- Three-host Mininet topology and controller connectivity.
- TCP and UDP client/server requests between h1/h2 and h3.
- SYN detection from h1 and a corresponding JSONL detection event.
- Automatic controller API enforcement against h1.
- h1 blocked while h2 retained connectivity.
- h1 connectivity restored after the temporary OpenFlow rule expired.

The normal Mininet configuration uses 30 SYN/s, a 5-second window, two
consecutive qualifying windows, and a 120-second block. A separate local
test configuration was used for the short-duration functional demonstration;
it is not committed as the default configuration.

## Limitations

Detection is based on initial TCP SYN rate and captures only the interfaces
specified to one monitor process. Enforcement drops IPv4 traffic from the
detected source. The standalone SQLite blocklist and controller's temporary
flow state are separate; automatic reconciliation between their expiry
records remains future work. Live flow-statistics polling, IPv6 support and
deployment hardening are also future work. See [roadmap](docs/roadmap.md).

MIT licensed. See LICENSE.
