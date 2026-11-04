#!/usr/bin/python3
"""Root service hook: queue a small status event, never credentials or logs."""
import argparse,json,os,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--failure',action='store_true');a=p.parse_args()
result='failed' if a.failure else os.environ.get('SERVICE_RESULT','unknown')
state='success' if result=='success' else 'failed'
if result=='signal':state='canceled'
queue=Path('/var/lib/goblin-backup-notifications');queue.mkdir(mode=0o755,exist_ok=True);queue.chmod(0o755)
event={'id':time.time_ns(),'state':state,'result':result}
tmp=queue/'latest.tmp';tmp.write_text(json.dumps(event));tmp.chmod(0o644);tmp.replace(queue/'latest.json')
