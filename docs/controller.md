# SDN controller and automatic SYN protection

The controller uses OS-Ken and OpenFlow 1.3. It is designed for
`topology/sdn_topology.py`. Its localhost HTTP API is the single enforcement
path for both manual blocks and automatic SYN detections.

## Install

From the repository root on Ubuntu:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip openvswitch-switch mininet
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[controller,capture]'
```

Use the virtual environment; do not use `sudo pip`.

## Start the controller

With the virtual environment active:

```bash
python -c "from os_ken.base.app_manager import AppManager; AppManager.run_apps(['controller.sdn_controller'])"
```

If shell quoting is inconvenient, this equivalent interactive Python method
also works:

```python
from os_ken.base.app_manager import AppManager
import controller.sdn_controller
AppManager.run_apps([controller.sdn_controller.__name__])
```

The OpenFlow listener uses port 6653. The management API listens only on
`127.0.0.1:8080`. Check it from another terminal:

```bash
curl http://127.0.0.1:8080/health
```

## Start Mininet

In a second terminal, from the repository root:

```bash
sudo python3 topology/sdn_topology.py
```

At the Mininet prompt:

```text
nodes
pingall
sh ovs-vsctl get-controller s1
sh ovs-ofctl -O OpenFlow13 dump-flows s1
```

Start the controller before Mininet. Exit Mininet with `exit`.

## Existing manual block and unblock API

In a third terminal:

```bash
curl -X POST http://127.0.0.1:8080/v1/blocks \
  -H 'Content-Type: application/json' \
  -d '{"ip":"10.20.0.1","block_seconds":60}'

curl http://127.0.0.1:8080/v1/blocks
curl -X DELETE http://127.0.0.1:8080/v1/blocks/10.20.0.1
```

A duration of `0` means no automatic expiry. The controller installs a
high-priority IPv4 source drop rule with a dedicated cookie. Unblocking
deletes only rules carrying that cookie, preserving unrelated switch rules.
These endpoints remain available when automatic monitoring is enabled.

## Automatic SYN-rate detection in Mininet

The Mininet configuration is separate from the original VirtualBox
`config/thresholds.json`. It uses `10.20.0.0/24`, ignores the server address,
and writes to separate database and JSONL files:

- SQLite: `data/mininet_security_events.db`
- JSON Lines: `data/mininet_events.jsonl`

Find the switch-facing interfaces from a host terminal while Mininet is up:

```bash
ip -br link
sudo ovs-vsctl list-ports s1
```

Start with alert-only mode. Replace the example interface names with those
shown by the commands above:

```bash
sudo .venv/bin/python -m dynamic_sdn_blocker.monitor \
  --config config/mininet-thresholds.json \
  --interface s1-eth1 s1-eth2 s1-eth3
```

The monitor shares one rolling-window detector across all listed interfaces.
It counts initial TCP SYN packets (SYN set, ACK clear) by source IP. Alert-only
is the default and does not install flows.

After checking the alert rate and confirming the controller health endpoint,
enable enforcement:

```bash
sudo .venv/bin/python -m dynamic_sdn_blocker.monitor \
  --config config/mininet-thresholds.json \
  --interface s1-eth1 s1-eth2 s1-eth3 \
  --enforce
```

When the configured threshold is reached, the monitor records a detection,
updates its SQLite blocklist, and sends the source IP and configured duration
to the controller's existing `POST /v1/blocks` API. The controller installs
the drop rule on its connected OpenFlow switch. If the API is unavailable,
the monitor logs `block_failed`; it does not silently claim the host was
blocked. The original direct-OVS monitor mode remains available when
`--enforce` is used without a controller URL.

Inspect automatic events:

```bash
tail -f data/mininet_events.jsonl
curl http://127.0.0.1:8080/v1/blocks
```

The API binds to loopback only and has no authentication. Do not expose port
8080 to an untrusted network. Run SYN-rate tests only inside the isolated
Mininet lab. Tune thresholds against normal traffic before enforcement.

## API

- `GET /health`: controller API health.
- `GET /v1/blocks`: current block list.
- `POST /v1/blocks`: JSON body `{"ip":"10.20.0.1","block_seconds":300}`.
- `DELETE /v1/blocks/{ipv4}`: remove a block.

## Verified Mininet results

The Ubuntu VM demonstration verified:

- The controller connected to Mininet switch `s1`, and `pingall` succeeded.
- TCP and UDP socket clients communicated with the h3 server.
- Scapy captured initial SYN traffic from h1 (`10.20.0.1`).
- The detector emitted an alert and wrote a detection record to
  `data/mininet_events.jsonl`.
- With enforcement enabled and a separate short-duration test config, the
  monitor reported `[BLOCKED]` and the controller applied the block.
- h1 was blocked while h2 remained able to communicate with h3.
- h1 connectivity returned after the temporary rule expired.

The short-duration functional test used a separate local configuration.
The committed `config/mininet-thresholds.json` remains at 30 SYN/s, a
5-second window, two consecutive qualifying windows, and a 120-second block.
See [Mininet validation notes](mininet-validation.md).

## Scope and limitations

The controller provides a basic MAC-learning switch and IPv4 source blocking.
The monitor can capture multiple interfaces in one process and call the
controller API for enforcement. The controller's temporary OpenFlow rule
expiry was demonstrated in the Mininet VM. Reconciliation of the separate
SQLite blocklist expiry state with controller flow state is not implemented.
This is a lab prototype, not a production network controller.
