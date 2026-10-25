"""mise で固定した Node.js で、ブラウザ用スクリプトの状態遷移テストを実行する。"""

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path

import pytest

from scripts.check_node_version import format_version, parse_version, pinned_version
from sphinx_revealjs_mascot.config import ACTIONS, DEFAULT_ACTIONS, STATES

_REPOSITORY = Path(__file__).resolve().parents[2]
_RUNTIME_TEST = Path(__file__).with_name('test_mascot_runtime.cjs')


@pytest.fixture(scope='module')
def node() -> str:
    path = shutil.which('node')
    if path is None:
        pytest.fail('PATH に node がありません。README の開発の開始に沿って mise を準備してください。')
    return path


def test_node_matches_the_version_pinned_by_mise(node: str) -> None:
    expected = pinned_version(_REPOSITORY / 'mise.toml')
    result = subprocess.run([node, '--version'], cwd=_REPOSITORY, capture_output=True, text=True, check=False, timeout=60)

    assert result.returncode == 0, result.stderr
    assert parse_version(result.stdout) == expected, f'{result.stdout.strip()} は mise.toml の {format_version(expected)} と異なります'


def test_browser_script_state_transitions(node: str) -> None:
    contract = {
        'actions': {name: asdict(action) for name, action in ACTIONS.items()},
        'defaults': DEFAULT_ACTIONS,
        'states': STATES,
        'explicit': [name for name, action in ACTIONS.items() if action.explicit],
    }
    result = subprocess.run(
        [node, '--test', '--test-reporter=tap', str(_RUNTIME_TEST)],
        cwd=_REPOSITORY,
        env={**os.environ, 'SPHINX_REVEALJS_MASCOT_CONTRACT': json.dumps(contract)},
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=False,
        timeout=120,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    summary = dict(re.findall(r'^# (tests|pass) (\d+)$', result.stdout, flags=re.MULTILINE))
    assert int(summary.get('tests', 0)) > 0, result.stdout
    assert summary['pass'] == summary['tests'], result.stdout
