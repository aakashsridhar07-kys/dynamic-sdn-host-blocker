import ipaddress, sqlite3, time
from pathlib import Path
class Blocklist:
 def __init__(self,database):
  self.path=database
  if database != ':memory:': Path(database).parent.mkdir(parents=True,exist_ok=True)
  with self._connect() as c: c.execute('CREATE TABLE IF NOT EXISTS blocklist (ip TEXT PRIMARY KEY, reason TEXT NOT NULL, created_at REAL NOT NULL, expires_at REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1)')
 def _connect(self): return sqlite3.connect(self.path,timeout=10)
 def block(self,ip,duration_seconds,reason):
  ip=str(ipaddress.ip_address(ip))
  if duration_seconds<=0: raise ValueError('duration_seconds must be positive')
  now=time.time()
  with self._connect() as c: c.execute('INSERT INTO blocklist VALUES(?,?,?,?,1) ON CONFLICT(ip) DO UPDATE SET reason=excluded.reason,created_at=excluded.created_at,expires_at=excluded.expires_at,active=1',(ip,reason,now,now+duration_seconds))
 def is_blocked(self,ip,now=None):
  ip=str(ipaddress.ip_address(ip)); now=time.time() if now is None else now
  with self._connect() as c: row=c.execute('SELECT expires_at,active FROM blocklist WHERE ip=?',(ip,)).fetchone()
  return bool(row and row[1] and row[0]>now)
 def unblock(self,ip):
  ip=str(ipaddress.ip_address(ip))
  with self._connect() as c: cur=c.execute('UPDATE blocklist SET active=0 WHERE ip=? AND active=1',(ip,))
  return cur.rowcount>0
 def expire(self,now=None):
  now=time.time() if now is None else now
  with self._connect() as c: cur=c.execute('UPDATE blocklist SET active=0 WHERE active=1 AND expires_at<=?',(now,))
  return cur.rowcount
