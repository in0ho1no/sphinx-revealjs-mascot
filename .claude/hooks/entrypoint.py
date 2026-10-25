"""Claude Code adapter for the shared hook entrypoint."""

import runpy
from pathlib import Path

_shared = runpy.run_path(str(Path(__file__).resolve().parents[2] / '.github' / 'hooks' / 'entrypoint.py'))
find_repo_root = _shared['find_repo_root']


def main() -> None:
    """Keep Claude's project guard before dispatching the shared inspection."""
    _shared['main'](require_claude_project=True)


if __name__ == '__main__':
    main()
