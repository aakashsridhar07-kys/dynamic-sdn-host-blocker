import ipaddress, time
from collections import defaultdict, deque
from dataclasses import dataclass

@dataclass(frozen=True)
class Detection:
    source_ip: str
    rate_per_second: float
    window_seconds: float
    reason: str

class SynRateDetector:
    def __init__(self, lab_cidr, threshold_per_second=30, window_seconds=5, consecutive_windows=2, ignored_ips=None):
        if threshold_per_second <= 0 or window_seconds <= 0 or consecutive_windows < 1: raise ValueError('threshold/window must be positive')
        self.network=ipaddress.ip_network(lab_cidr,strict=False); self.threshold=float(threshold_per_second); self.window=float(window_seconds); self.consecutive_windows=int(consecutive_windows)
        self.ignored={str(ipaddress.ip_address(x)) for x in (ignored_ips or [])}; self.events=defaultdict(deque); self.over=defaultdict(int); self.alerted=set()
    def observe_syn(self, source_ip, timestamp=None):
        try: ip=ipaddress.ip_address(source_ip)
        except ValueError: return None
        source=str(ip)
        if ip.version!=4 or ip not in self.network or source in self.ignored: return None
        now=time.monotonic() if timestamp is None else float(timestamp); q=self.events[source]; q.append(now)
        while q and q[0] < now-self.window: q.popleft()
        rate=len(q)/self.window; self.over[source]=self.over[source]+1 if rate>=self.threshold else 0
        if rate<self.threshold: self.alerted.discard(source)
        if self.over[source]>=self.consecutive_windows and source not in self.alerted:
            self.alerted.add(source); return Detection(source,rate,self.window,'tcp_syn_rate_threshold')
        return None
    def snapshot_rate(self, source_ip, timestamp=None):
        source=str(ipaddress.ip_address(source_ip)); now=time.monotonic() if timestamp is None else float(timestamp); q=self.events[source]
        while q and q[0] < now-self.window: q.popleft()
        return len(q)/self.window
