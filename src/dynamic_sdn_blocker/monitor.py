import argparse,json,time
from .blocklist import Blocklist
from .detector import SynRateDetector
from .event_logger import EventLogger
def main():
 p=argparse.ArgumentParser(); p.add_argument('--config',default='config/thresholds.json'); p.add_argument('--interface',required=True); p.add_argument('--enforce',action='store_true'); a=p.parse_args()
 try: from scapy.all import IP,TCP,sniff
 except ImportError: p.error("Scapy required; install with pip install -e '.[capture]'")
 with open(a.config,encoding='utf-8') as f: c=json.load(f)
 d=SynRateDetector(c['lab_cidr'],float(c['syn_rate_threshold']),float(c['window_seconds']),int(c.get('consecutive_windows',1)),c.get('ignored_ips',[])); bl=Blocklist(c.get('database','data/security_events.db')); log=EventLogger(c.get('event_log','data/events.jsonl')); ovs=None
 if a.enforce:
  from .ovs import OVSRuleManager
  ovs=OVSRuleManager(c.get('bridge','br0'),c['lab_cidr'])
 def handle(pkt):
  if IP not in pkt or TCP not in pkt: return
  flags=int(pkt[TCP].flags)
  if flags&2 and not flags&16:
   hit=d.observe_syn(pkt[IP].src,time.monotonic())
   if hit:
    log.log('detection',source_ip=hit.source_ip,rate_per_second=hit.rate_per_second,reason=hit.reason); duration=float(c.get('block_seconds',300)); bl.block(hit.source_ip,duration,hit.reason)
    if ovs is None: print(f'[ALERT] {hit.source_ip}: {hit.rate_per_second:.1f} SYN/s (alert-only)')
    else:
     try: ovs.block(hit.source_ip); log.log('block_applied',source_ip=hit.source_ip,duration_seconds=duration,bridge=ovs.bridge)
     except Exception as e: log.log('block_failed',source_ip=hit.source_ip,error=str(e))
 print('Monitoring '+a.interface+'; enforcement='+('ON' if a.enforce else 'OFF'))
 try: sniff(iface=a.interface,filter='tcp[tcpflags] & tcp-syn != 0',prn=handle,store=False)
 except KeyboardInterrupt: print('Stopping monitor.')
 return 0
if __name__=='__main__': raise SystemExit(main())
