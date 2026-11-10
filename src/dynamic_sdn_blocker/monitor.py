"""Capture initial TCP SYNs and optionally enforce blocks through OS-Ken."""
import argparse
import json
import threading
import time

from .blocklist import Blocklist
from .detector import SynRateDetector
from .event_logger import EventLogger


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/thresholds.json")
    parser.add_argument("--interface", required=True, nargs="+",
                        help="One or more interfaces to capture (shared detector)")
    parser.add_argument("--enforce", action="store_true",
                        help="Apply blocks; default is alert-only")
    parser.add_argument("--controller-url",
                        help="Use the OS-Ken API instead of direct OVS rules")
    args = parser.parse_args()

    try:
        from scapy.all import IP, TCP, sniff
    except ImportError:
        parser.error("Scapy required; install with pip install -e '.[capture]'")

    with open(args.config, encoding="utf-8") as config_file:
        config = json.load(config_file)

    detector = SynRateDetector(
        config["lab_cidr"],
        float(config["syn_rate_threshold"]),
        float(config["window_seconds"]),
        int(config.get("consecutive_windows", 1)),
        config.get("ignored_ips", []),
    )
    blocklist = Blocklist(config.get("database", "data/security_events.db"))
    logger = EventLogger(config.get("event_log", "data/events.jsonl"))
    detector_lock = threading.Lock()

    controller = None
    ovs = None
    controller_url = args.controller_url or config.get("controller_url")
    if args.enforce and controller_url:
        from .controller_client import ControllerClient
        controller = ControllerClient(controller_url)
        health = controller.health()
        print(f"Controller API ready: {health}")
    elif args.enforce:
        from .ovs import OVSRuleManager
        ovs = OVSRuleManager(config.get("bridge", "br0"), config["lab_cidr"])

    duration = float(config.get("block_seconds", 300))

    def handle(packet):
        if IP not in packet or TCP not in packet:
            return
        flags = int(packet[TCP].flags)
        # Initial SYN only: SYN set, ACK clear.
        if not (flags & 0x02) or (flags & 0x10):
            return

        with detector_lock:
            detection = detector.observe_syn(packet[IP].src, time.monotonic())
        if detection is None:
            return

        source_ip = detection.source_ip
        logger.log(
            "detection", source_ip=source_ip,
            rate_per_second=detection.rate_per_second,
            window_seconds=detection.window_seconds,
            reason=detection.reason,
        )
        blocklist.block(source_ip, duration, detection.reason)
        if not args.enforce:
            print(f"[ALERT] {source_ip}: {detection.rate_per_second:.1f} SYN/s (alert-only)")
            return

        try:
            if controller is not None:
                result = controller.block(source_ip, int(duration))
                logger.log("block_applied", source_ip=source_ip,
                           duration_seconds=duration, enforcement="controller",
                           controller_response=result)
            else:
                ovs.block(source_ip)
                logger.log("block_applied", source_ip=source_ip,
                           duration_seconds=duration, enforcement="ovs",
                           bridge=ovs.bridge)
            print(f"[BLOCKED] {source_ip}: {detection.rate_per_second:.1f} SYN/s")
        except Exception as exc:
            logger.log("block_failed", source_ip=source_ip, error=str(exc))
            print(f"[ERROR] Could not block {source_ip}: {exc}")

    interfaces = args.interface
    print("Monitoring interfaces: " + ", ".join(interfaces)
          + "; enforcement=" + ("ON" if args.enforce else "OFF"))
    try:
        sniff(
            iface=interfaces if len(interfaces) > 1 else interfaces[0],
            filter="tcp[tcpflags] & tcp-syn != 0",
            prn=handle,
            store=False,
        )
    except KeyboardInterrupt:
        print("Stopping monitor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
