import ipaddress, subprocess
class OVSRuleManager:
 COOKIE='0xD1A0'
 def __init__(self,bridge='br0',lab_cidr='10.10.0.0/24',executable='ovs-ofctl',runner=subprocess.run): self.bridge,self.network,self.executable,self.runner=bridge,ipaddress.ip_network(lab_cidr,strict=False),executable,runner
 def _ip(self,value):
  ip=ipaddress.ip_address(value)
  if ip.version!=4 or ip not in self.network: raise ValueError('source IP outside configured IPv4 lab CIDR')
  return str(ip)
 def block(self,source_ip):
  ip=self._ip(source_ip); cmd=[self.executable,'-O','OpenFlow13','add-flow',self.bridge,f'cookie={self.COOKIE},priority=40000,ip,nw_src={ip},actions=drop']
  return self.runner(cmd,check=True,capture_output=True,text=True).stdout.strip()
 def unblock(self,source_ip):
  ip=self._ip(source_ip); cmd=[self.executable,'-O','OpenFlow13','del-flows',self.bridge,f'cookie={self.COOKIE}/-1,ip,nw_src={ip}']
  return self.runner(cmd,check=True,capture_output=True,text=True).stdout.strip()
