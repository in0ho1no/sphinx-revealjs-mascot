"""mise で固定した Node.js の更新確認を検証する。"""

import json
import re
import sys
from pathlib import Path

import pytest

from scripts import check_node_version

_REPOSITORY = Path(__file__).resolve().parents[2]
# 実在の公開履歴ではなく、メジャーの違い・セキュリティ版・順序を確かめるための一覧。
_INDEX = [
    {'version': 'v26.1.0', 'date': '2026-10-21', 'security': True},
    {'version': 'v24.3.1', 'date': '2026-10-20', 'security': True},
    {'version': 'v24.3.0', 'date': '2026-10-14', 'security': False},
    {'version': 'v24.2.0', 'date': '2026-09-07', 'security': False},
    {'version': 'v22.9.0', 'date': '2026-10-20', 'security': True},
]


def _run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, pin: str, index: object) -> tuple[int, Path]:
    config = tmp_path / 'mise.toml'
    config.write_text(f'[tools]\nnode = "{pin}"\n', encoding='utf-8')
    index_file = tmp_path / 'index.json'
    index_file.write_text(json.dumps(index), encoding='utf-8')
    body = tmp_path / 'body.md'
    arguments = ['check_node_version.py', '--config', str(config), '--index-file', str(index_file), '--issue-body', str(body)]
    monkeypatch.setattr(sys, 'argv', arguments)
    return check_node_version.main(), body


def test_repository_pins_node_to_an_exact_version() -> None:
    assert len(check_node_version.pinned_version(_REPOSITORY / 'mise.toml')) == 3


@pytest.mark.parametrize('content', ['[tools]\nnode = "24"\n', '[tools]\nnode = "lts"\n', '[tools]\nnode = "24.3"\n', '[tools]\n'])
def test_loose_or_missing_pin_is_rejected(tmp_path: Path, content: str) -> None:
    config = tmp_path / 'mise.toml'
    config.write_text(content, encoding='utf-8')

    with pytest.raises(ValueError, match=r'(?i)node'):
        check_node_version.pinned_version(config)


def test_only_newer_releases_of_the_pinned_major_are_reported() -> None:
    releases = check_node_version.newer_releases((24, 2, 0), _INDEX)

    assert [(release.version, release.security) for release in releases] == [((24, 3, 1), True), ((24, 3, 0), False)]


def test_latest_pin_is_up_to_date_without_issue_body(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    status, body = _run(monkeypatch, tmp_path, '24.3.1', _INDEX)

    assert status == 0
    assert not body.exists()


def test_outdated_pin_writes_issue_body_following_task_template(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    status, body = _run(monkeypatch, tmp_path, '24.2.0', _INDEX)

    assert status == 1
    text = body.read_text(encoding='utf-8')
    template = (_REPOSITORY / '.github/ISSUE_TEMPLATE/task.yml').read_text(encoding='utf-8')
    for label in re.findall(r'^      label: (.+)$', template, flags=re.MULTILINE):
        assert f'### {label}\n' in text
    assert '24.2.0 から 24.3.1 へ' in text
    assert '| 24.3.1 | 2026-10-20 | あり |' in text
    assert 'セキュリティリリースを含む' in text


@pytest.mark.parametrize('index', [[{'date': '2026-10-20'}], {'version': 'v24.3.1'}])
def test_unexpected_index_is_reported_as_check_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, index: object) -> None:
    status, body = _run(monkeypatch, tmp_path, '24.2.0', index)

    assert status == 2
    assert not body.exists()
