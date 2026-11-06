#!/usr/bin/env python3
"""Mininet topology for the Dynamic SDN Host Blocker project.

Topology:
    h1 (10.20.0.1) --+
    h2 (10.20.0.2) --+-- s1 (OpenFlow 1.3) -- RemoteController
    h3 (10.20.0.10) -+

The controller must be listening at 127.0.0.1:6653 before starting
this topology. The 10.20.0.0/24 subnet is intentionally separate from
the project's existing 10.10.0.0/24 VirtualBox lab network.
"""

from mininet.cli import CLI
from mininet.log import info, setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.topo import Topo


class SDNTopology(Topo):
    """Two clients and one server connected to a single OVS switch."""

    def build(self):
        switch = self.addSwitch(
            "s1",
            cls=OVSSwitch,
            protocols="OpenFlow13",
        )

        hosts = (
            ("h1", "10.20.0.1/24", "00:00:00:00:00:01"),
            ("h2", "10.20.0.2/24", "00:00:00:00:00:02"),
            ("h3", "10.20.0.10/24", "00:00:00:00:00:10"),
        )

        for name, ip, mac in hosts:
            host = self.addHost(name, ip=ip, mac=mac)
            self.addLink(host, switch)


def run():
    """Start the topology and expose the Mininet CLI."""
    net = Mininet(
        topo=SDNTopology(),
        controller=None,
        switch=OVSSwitch,
        autoSetMacs=False,
        build=False,
    )

    net.addController(
        "c0",
        controller=RemoteController,
        ip="127.0.0.1",
        port=6653,
    )

    try:
        net.build()
        net.start()

        info("\n*** Dynamic SDN Host Blocker topology is running\n")
        info("*** Hosts: h1=10.20.0.1, h2=10.20.0.2, h3=10.20.0.10\n")
        info("*** Switch: s1 (OpenFlow 1.3)\n")
        info("*** Remote controller: 127.0.0.1:6653\n")
        info("*** Try: pingall, nodes, net, sh ovs-vsctl show\n\n")

        CLI(net)
    finally:
        net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    run()
