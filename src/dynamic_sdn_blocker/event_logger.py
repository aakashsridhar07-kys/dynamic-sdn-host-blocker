import json
from datetime import datetime, timezone
from pathlib import Path
class EventLogger:
 def __init__(self,path): self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
 def log(self,event_type,**fields):
  row={'timestamp':datetime.now(timezone.utc).isoformat(),'event':event_type,**fields}
  with self.path.open('a',encoding='utf-8') as f: f.write(json.dumps(row,sort_keys=True,default=str)+'\n')
