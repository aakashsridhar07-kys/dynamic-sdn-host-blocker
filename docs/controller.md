# SDN controller

The controller uses OS-Ken and OpenFlow 1.3. It is designed for the Mininet
topology in `topology/sdn_topology.py`.

## Install

From the repository root on Ubuntu:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip openvswitch-switch mininet
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[controller]'
```

Use the virtual environment; do not use `sudo pip`.

## Start the controller

With the virtual environment active:

```bash
python -c "from os_ken.base.app_manager import AppManager; AppManager.run_apps(['controller.sdn_controller'])"
```

The OpenFlow listener uses port 6653. The host management API listens only
on `127.0.0.1:8080`.

Check API health in another terminal:

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

## Block and unblock a host

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

## API

- `GET /health`: controller API health.
- `GET /v1/blocks`: current block list.
- `POST /v1/blocks`: JSON body `{"ip":"10.20.0.1","block_seconds":300}`.
- `DELETE /v1/blocks/{ipv4}`: remove a block.

The API binds to loopback only and has no authentication. Do not expose port
8080 to an untrusted network.

## Scope and verification

The controller provides a basic MAC-learning switch and IPv4 source blocking.
The pure validation helpers have unit tests. End-to-end behavior still needs
to be verified in the Ubuntu VM with a live OS-Ken process, OVS, and Mininet.
This is a lab prototype, not a production network controller.
