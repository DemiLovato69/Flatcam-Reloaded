"""Verify that a packaged FlatCAM starts with all of its UI assets."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


executable = Path(sys.argv[1]).resolve()
bundle = executable.parents[2] if executable.parent.name == 'MacOS' else executable.parent
expected = {path.name for path in Path('share').iterdir() if path.is_file()}
included = {path.name for path in bundle.rglob('*') if path.parent.name == 'share' and path.is_file()}
missing = expected - included
assert not missing, f'Missing bundled assets: {sorted(missing)}'

with tempfile.TemporaryDirectory() as home:
    log_path = Path(home) / 'startup.log'
    env = dict(os.environ, HOME=home)
    with log_path.open('w+') as log:
        process = subprocess.Popen([str(executable)], cwd=home, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                log.seek(0)
                if 'END of constructor. Releasing control.' in log.read():
                    assert process.poll() is None, 'FlatCAM exited after startup'
                    break
                if process.poll() is not None:
                    raise RuntimeError(f'FlatCAM exited with {process.returncode}')
                time.sleep(0.5)
            else:
                raise TimeoutError('FlatCAM did not finish starting within 90 seconds')
        except (AssertionError, RuntimeError, TimeoutError):
            log.seek(0)
            print(log.read(), file=sys.stderr)
            raise
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

print(f'{executable} started with {len(expected)} assets')
