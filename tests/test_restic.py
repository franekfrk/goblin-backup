import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'bin/goblin-backup'))

@unittest.skipUnless(shutil.which('restic'),'restic not installed')
class ResticIntegration(unittest.TestCase):
    def test_encrypted_repository_excludes_cloud_and_key_and_restores_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);stage=p/'state/current'
            paths=[stage/x for x in ['system','home','dane']]
            for x in paths:x.mkdir(parents=True)
            (stage/'dane/Nextcloud').mkdir()
            (stage/'dane/Nextcloud/not-backed-up.txt').write_text('cloud fixture')
            (stage/'home/document.txt').write_text('restore fixture')
            secrets=stage/'system/etc/goblin-backup';secrets.mkdir(parents=True)
            (secrets/'repository.key').write_text('excluded fixture')
            key=p/'test.key';key.write_text('temporary integration test password')
            c={'state_dir':str(p/'state'),'password_file':'/etc/goblin-backup/repository.key',
               'sources':[{'name':'system','path':'/','snapshot_parent':'/.goblin-backup-snapshots'},
                          {'name':'home','path':'/home','snapshot_parent':'/home/.goblin-backup-snapshots'},
                          {'name':'dane','path':'/dane','snapshot_parent':'/dane/.goblin-backup-snapshots','exclude':['Nextcloud']}]}
            excludes=p/'excludes';excludes.write_text('\n'.join(API['patterns'](c,stage)))
            env=os.environ.copy();env.update(RESTIC_REPOSITORY=str(p/'repo'),RESTIC_PASSWORD_FILE=str(key),RESTIC_CACHE_DIR=str(p/'cache'))
            def restic(*args):return subprocess.check_output(['restic',*map(str,args)],env=env,text=True,stderr=subprocess.PIPE)
            restic('init')
            restic('backup','--exclude-file',excludes,*paths)
            listing=restic('ls','--json','latest')
            nodes=[json.loads(x).get('path','') for x in listing.splitlines()]
            self.assertIn(str(stage/'home/document.txt'),nodes)
            self.assertFalse(any('/Nextcloud' in x or '/etc/goblin-backup' in x for x in nodes))
            restic('check','--read-data')
            target=p/'restore';restic('restore','latest','--target',target)
            self.assertEqual((target/str(stage/'home/document.txt').lstrip('/')).read_text(),'restore fixture')
            self.assertNotIn(b'restore fixture',(p/'repo/config').read_bytes())
