"""Copy the self-contained review Skill; never overwrite an existing install."""
import argparse, shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dest',required=True);a=p.parse_args()
source=Path(__file__).resolve().parents[1]/'earnings-review'
target=Path(a.dest).expanduser()/'earnings-review'
if target.exists(): raise SystemExit('Existing skill preserved. Choose a new directory or manage upgrades explicitly.')
shutil.copytree(source,target,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
print('Installed earnings-review. Run scripts/selftest.py in the installed Skill directory.')
