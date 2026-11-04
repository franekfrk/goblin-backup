#!/usr/bin/python3
"""Per-user delivery. Undelivered events are retried after next login."""
import json,subprocess,os
from pathlib import Path
queue=Path('/var/lib/goblin-backup-notifications/latest.json')
state=Path.home()/'.local/state/goblin-backup-notifications';state.mkdir(parents=True,exist_ok=True)
ack=state/'ack'
try:event=json.loads(queue.read_text())
except (OSError,ValueError):raise SystemExit(0)
if ack.exists() and ack.read_text().strip()==str(event['id']):raise SystemExit(0)
messages={
 'success':('Kopia Goblina gotowa','Backup, weryfikacja danych i próbne odtworzenie zakończone. Zachowywane są 4 ostatnie kopie.'),
 'failed':('Błąd kopii Goblina','Kopia nie zakończyła się poprawnie. Szczegóły: sudo journalctl -u goblin-backup.service -n 60'),
 'canceled':('Kopia Goblina przerwana','Zadanie zostało zatrzymane. Nie traktuj tej próby jako nowej zweryfikowanej kopii.')}
title,body=messages[event['state']]
cmd=['notify-send','--app-name=Goblin Backup','--icon=drive-harddisk','--urgency=normal','--expire-time='+('10000' if event['state']=='success' else '0'),'--hint=boolean:suppress-sound:true',title,body]
r=subprocess.run(cmd,capture_output=True,text=True)
if r.returncode==0:ack.write_text(str(event['id']))
