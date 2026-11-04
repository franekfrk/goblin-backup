import runpy
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT / 'bin/goblin-backup'))

class ConfigTests(unittest.TestCase):
    def config(self, text=None):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'config.toml'
            p.write_text(text or (ROOT/'examples/config.toml').read_text())
            return API['load_config'](p)

    def test_example_is_valid(self):
        self.assertEqual(len(self.config()['sources']),3)

    def test_exclusions_do_not_hide_staging_ancestor(self):
        c=self.config();stage=Path(c['state_dir'])/'current'
        patterns=API['patterns'](c,stage)
        self.assertIn(str(stage/'dane/Nextcloud'),patterns)
        self.assertIn(str(stage/'system/etc/goblin-backup'),patterns)
        self.assertIn(str(stage/'system/var/lib/goblin-backup-public'),patterns)
        self.assertNotIn(str(stage),patterns)
        self.assertNotIn(c['state_dir'],patterns)
        self.assertNotIn('**/var/lib/goblin-backup-public',patterns)

    def test_rejects_traversal(self):
        with self.assertRaises(ValueError):
            self.config((ROOT/'examples/config.toml').read_text().replace('exclude = ["Nextcloud"]','exclude = ["../secrets"]'))

    def test_rejects_key_on_destination(self):
        with self.assertRaises(ValueError):
            self.config((ROOT/'examples/config.toml').read_text().replace('/etc/goblin-backup/repository.key','/mnt/backup/repository.key'))

    def test_rejects_duplicate_source_names(self):
        with self.assertRaises(ValueError):
            self.config((ROOT/'examples/config.toml').read_text().replace('name = "home"','name = "system"'))

if __name__=='__main__':unittest.main()
