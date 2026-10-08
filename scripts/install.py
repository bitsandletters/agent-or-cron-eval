#!/usr/bin/env python3
"""Install a checkout-local launcher offline, using only Python's standard library."""
import argparse
from pathlib import Path
import stat
import venv

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--venv", default=".venv")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
destination = Path(args.venv).resolve()
if destination.exists():
    raise SystemExit("Choose a new virtual environment path; existing files are never overwritten.")
venv.EnvBuilder(with_pip=False).create(destination)
launcher = destination / "bin" / "cronbench"
launcher.write_text(f"#!{destination / 'bin/python'}\nimport runpy\nrunpy.run_path({str(root / 'cronbench')!r}, run_name='__main__')\n")
launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
print(f"Installed offline: {launcher}\nKeep this checkout at {root}; rerun installation after moving it.")
