"""OS-Ken OpenFlow 1.3 controller with a localhost host-blocking API.

Run from the repository root with:
    osken-manager controller/sdn_controller.py

The HTTP API listens on 127.0.0.1:8080 and is deliberately loopback-only.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import (
    CONFIG_DISPATCHER,
    DEAD_DISPATCHER,
    MAIN_DISPATCHER,
    set_ev_cls,
)
from os_ken.lib.packet import ether_types, ethernet, ipv4, packet
from os_ken.ofproto import ofproto_v1_3

from controller.security_policy import normalize_ipv4, validate_block_seconds

LOG = logging.getLogger("dynamic_sdn_controller")
BLOCK_COOKIE = 0xD1A0B10C00000001
BLOCK_COOKIE_MASK = 0xFFFFFFFFFFFFFFFF
BLOCK_PRIORITY = 50000
LEARN_PRIORITY = 10
HTTP_HOST = "127.0.0.1"
HTTP_PORT = 8080


class DynamicSDNController(app_manager.OSKenApp):
    """Learning switch plus an HTTP interface for temporary IPv4 blocks."""

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datapaths = {}
        self.mac_to_port = {}
        self.blocked_hosts = {}
        self.state_lock = threading.RLock()
        self.httpd = None
        self.http_thread = None
        self._start_http_api()

    def _start_http_api(self):
        app = self

        class APIHandler(BaseHTTPRequestHandler):
            def _send(self, status, payload):
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                path = urlparse(self.path).path
                if path == "/health":
                    self._send(200, {"status": "ok", "controller": "dynamic-sdn-host-blocker"})
                elif path == "/v1/blocks":
                    self._send(200, {"blocked": app.list_blocks()})
                else:
                    self._send(404, {"error": "not found"})

            def do_POST(self):
                if urlparse(self.path).path != "/v1/blocks":
                    self._send(404, {"error": "not found"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length <= 0 or length > 4096:
                        raise ValueError("Request body must be between 1 and 4096 bytes")
                    data = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(data, dict):
                        raise ValueError("JSON body must be an object")
                    ip = normalize_ipv4(data.get("ip"))
                    seconds = validate_block_seconds(data.get("block_seconds", 300))
                    app.block_host(ip, seconds)
                    self._send(200, {"status": "blocked", "ip": ip, "block_seconds": seconds})
                except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    self._send(400, {"error": str(exc)})

            def do_DELETE(self):
                prefix = "/v1/blocks/"
                path = urlparse(self.path).path
                if not path.startswith(prefix):
                    self._send(404, {"error": "not found"})
                    return
                try:
                    ip = normalize_ipv4(path[len(prefix):])
                    removed = app.unblock_host(ip)
                    status = "unblocked" if removed else "not_blocked"
                    self._send(200, {"status": status, "ip": ip})
                except ValueError as exc:
                    self._send(400, {"error": str(exc)})

            def log_message(self, fmt, *args):
                LOG.info("API %s - %s", self.address_string(), fmt % args)

        self.httpd = ThreadingHTTPServer((HTTP_HOST, HTTP_PORT), APIHandler)
        self.http_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.http_thread.start()
        LOG.info("Host-blocking API listening on http://%s:%s", HTTP_HOST, HTTP_PORT)

    def close(self):
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
        super().close()

    def list_blocks(self):
        now = time.time()
        with self.state_lock:
            expired = [
                ip for ip, expiry in self.blocked_hosts.items()
                if expiry and expiry <= now
            ]
            for ip in expired:
                del self.blocked_hosts[ip]
            return [
                {"ip": ip, "expires_at": expiry or None}
                for ip, expiry in sorted(self.blocked_hosts.items())
            ]

    def is_blocked(self, ip):
        if not ip:
            return False
        now = time.time()
        with self.state_lock:
            expiry = self.blocked_hosts.get(ip)
            if expiry is None:
                return False
            if expiry and expiry <= now:
                del self.blocked_hosts[ip]
                return False
            return True

    def block_host(self, ip, block_seconds=300):
        ip = normalize_ipv4(ip)
        block_seconds = validate_block_seconds(block_seconds)
        expiry = time.time() + block_seconds if block_seconds else 0
        with self.state_lock:
            self.blocked_hosts[ip] = expiry
            datapaths = list(self.datapaths.values())
        for datapath in datapaths:
            self._install_drop(datapath, ip, block_seconds)
        LOG.warning("Blocked host %s for %s seconds", ip, block_seconds or "indefinitely")

    def unblock_host(self, ip):
        ip = normalize_ipv4(ip)
        with self.state_lock:
            existed = ip in self.blocked_hosts
            self.blocked_hosts.pop(ip, None)
            datapaths = list(self.datapaths.values())
        for datapath in datapaths:
            self._remove_drop(datapath, ip)
        LOG.info("Unblocked host %s", ip)
        return existed

    def _install_drop(self, datapath, ip, block_seconds):
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_src=ip)
        datapath.send_msg(parser.OFPFlowMod(
            datapath=datapath,
            cookie=BLOCK_COOKIE,
            table_id=0,
            command=datapath.ofproto.OFPFC_ADD,
            idle_timeout=0,
            hard_timeout=block_seconds,
            priority=BLOCK_PRIORITY,
            match=match,
            instructions=[],
        ))

    def _remove_drop(self, datapath, ip):
        ofp = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_src=ip)
        datapath.send_msg(parser.OFPFlowMod(
            datapath=datapath,
            cookie=BLOCK_COOKIE,
            cookie_mask=BLOCK_COOKIE_MASK,
            table_id=ofp.OFPTT_ALL,
            command=ofp.OFPFC_DELETE,
            out_port=ofp.OFPP_ANY,
            out_group=ofp.OFPG_ANY,
            match=match,
        ))

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_handler(self, ev):
        datapath = ev.datapath
        with self.state_lock:
            if ev.state == MAIN_DISPATCHER:
                self.datapaths[datapath.id] = datapath
            elif ev.state == DEAD_DISPATCHER:
                self.datapaths.pop(datapath.id, None)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofp = datapath.ofproto
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
        instructions = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        datapath.send_msg(parser.OFPFlowMod(
            datapath=datapath,
            priority=0,
            match=match,
            instructions=instructions,
        ))
        for item in self.list_blocks():
            remaining = 0
            if item["expires_at"]:
                remaining = max(1, int(item["expires_at"] - time.time()))
            self._install_drop(datapath, item["ip"], remaining)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofp = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None or eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt and self.is_blocked(ip_pkt.src):
            return

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][eth.src] = in_port
        out_port = self.mac_to_port[dpid].get(eth.dst, ofp.OFPP_FLOOD)
        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofp.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=eth.dst)
            instructions = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
            datapath.send_msg(parser.OFPFlowMod(
                datapath=datapath,
                priority=LEARN_PRIORITY,
                idle_timeout=300,
                match=match,
                instructions=instructions,
            ))

        data = None if msg.buffer_id != ofp.OFP_NO_BUFFER else msg.data
        datapath.send_msg(parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        ))
