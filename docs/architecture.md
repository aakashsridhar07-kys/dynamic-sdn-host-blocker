# Lab architecture

Use an SDN-Core VM with Open vSwitch and one host-facing virtual NIC per endpoint. Attach each endpoint NIC to a separate named VirtualBox **Internal Network** also attached to SDN-Core. A separate NAT adapter may be used for package downloads, but never add it to the OVS bridge.

Example addresses: Client A `10.10.0.11`, Client B `10.10.0.12`, server `10.10.0.100`.

Scapy captures initial TCP SYN packets on one selected ingress interface. The detector tracks rolling-window counts within the lab CIDR, logs detections to JSONL and SQLite, and optionally installs IPv4 source drop flows with `--enforce`. The monitor currently captures one interface per process; controller-driven live flow statistics are not implemented yet. Use an isolated lab you own or are authorized to test.
