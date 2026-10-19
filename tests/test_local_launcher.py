"""Exercise the real local launcher with fake tools; no inference or server bind."""

import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest


class LocalLauncherTests(unittest.TestCase):
    def test_openrouter_key_reaches_local_runner_without_google_or_old_key(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copyfile(Path(__file__).resolve().parents[1] / 'run_local_test.sh', root / 'run_local_test.sh')
            (root / '.venv/bin').mkdir(parents=True)
            (root / 'game/node_modules').mkdir(parents=True)
            (root / 'tools').mkdir()
            tools = {
                '.venv/bin/python': '#!/bin/sh\n[ "$1 $2" = "-m backend.local_dev" ] || exit 9\n[ -n "$OPENROUTER_API_KEY" ] || exit 8\nprintf "local-runner-ready\\n"\n',
                'tools/npm': '#!/bin/sh\nexit 0\n',
            }
            for name, content in tools.items():
                path = root / name
                path.write_text(content)
                path.chmod(0o700)
            result = subprocess.run(['bash', str(root / 'run_local_test.sh'), '--port', '8001'],
                env={'PATH': str(root / 'tools') + os.pathsep + os.defpath,
                     'OPENROUTER_API_KEY': 'offline-placeholder'},
                stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('local-runner-ready', result.stdout)
