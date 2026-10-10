"""Rates from OpenFlow counter snapshots."""
from dataclasses import dataclass
@dataclass(frozen=True)
class FlowRate:
    packets_per_second: float
    bytes_per_second: float
def counter_delta(previous_packets, previous_bytes, current_packets, current_bytes, elapsed_seconds):
    if elapsed_seconds <= 0: raise ValueError("elapsed_seconds must be positive")
    p=current_packets-previous_packets; b=current_bytes-previous_bytes
    if p < 0: p=current_packets
    if b < 0: b=current_bytes
    return FlowRate(p/elapsed_seconds, b/elapsed_seconds)
