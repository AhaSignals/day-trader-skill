"""Run the bundled pure-Python wheel without pip or network access."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def activate():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name:
            raise ValueError('Invalid bundle path')
        path = ROOT / name
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError('Invalid bundle member')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Bundle hash mismatch')
    wheel = ROOT / 'vendor/ahasignals_pit-0.5.0-py3-none-any.whl'
    if wheel.relative_to(ROOT).as_posix() not in manifest['files']:
        raise ValueError('Wheel missing from manifest')
    sys.path.insert(0, str(wheel))


if __name__ == '__main__':
    try:
        activate()
    except Exception:
        raise SystemExit('Bundle verification failed. Download the complete versioned archive again.')
    if sys.argv[1:] == ['mcp']:
        from ahasignals_pit.workflow_mcp import main
    else:
        from ahasignals_pit.workflow_cli import main
    sys.exit(main())
