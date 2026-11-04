import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

class NotificationsTests(unittest.TestCase):
    def test_result_queue_and_delivery_once_without_sound(self):
        for result,expected in [('success','success'),('exit-code','failed'),('signal','canceled')]:
            with self.subTest(result=result), tempfile.TemporaryDirectory() as d:
                p=Path(d);queue=p/'queue';home=p/'home';home.mkdir()
                event=(ROOT/'contrib/notification-event.py').read_text().replace('/var/lib/goblin-backup-notifications',str(queue))
                with patch.object(sys,'argv',['hook']),patch.dict(os.environ,{'SERVICE_RESULT':result}):
                    exec(compile(event,'event-test','exec'),{'__name__':'test'})
                self.assertEqual(json.loads((queue/'latest.json').read_text())['state'],expected)
                client=(ROOT/'contrib/notification-client.py').read_text().replace('/var/lib/goblin-backup-notifications',str(queue)).replace('Path.home()',f'Path({str(home)!r})')
                with patch('subprocess.run',return_value=types.SimpleNamespace(returncode=0)) as notify:
                    exec(compile(client,'client-test','exec'),{'__name__':'test'})
                    self.assertIn('--hint=boolean:suppress-sound:true',notify.call_args.args[0])
                    with self.assertRaises(SystemExit):exec(compile(client,'client-test','exec'),{'__name__':'test'})
                    self.assertEqual(notify.call_count,1)

    def test_failed_delivery_stays_pending(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);queue=p/'queue';queue.mkdir();home=p/'home';home.mkdir()
            (queue/'latest.json').write_text(json.dumps({'id':1,'state':'failed','result':'exit-code'}))
            client=(ROOT/'contrib/notification-client.py').read_text().replace('/var/lib/goblin-backup-notifications',str(queue)).replace('Path.home()',f'Path({str(home)!r})')
            with patch('subprocess.run',return_value=types.SimpleNamespace(returncode=1)):
                exec(compile(client,'client-test','exec'),{'__name__':'test'})
            self.assertFalse((home/'.local/state/goblin-backup-notifications/ack').exists())
