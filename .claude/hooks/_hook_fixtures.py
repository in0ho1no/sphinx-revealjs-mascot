"""Compatibility entrypoint; implementation lives in .github/hooks/_hook_fixtures.py."""

import runpy
from pathlib import Path

_target = Path(__file__).resolve().parents[2] / '.github' / 'hooks' / '_hook_fixtures.py'
globals().update(runpy.run_path(str(_target), run_name=__name__))
