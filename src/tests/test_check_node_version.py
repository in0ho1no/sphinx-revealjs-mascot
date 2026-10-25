"""mise で固定した Node.js の更新確認を検証する。"""

import json
import re
import sys
from http.client import BadStatusLine
from pathlib import Path
from unittest.mock import MagicMock

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


@pytest.fixture
def https(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    response = MagicMock()
    response.status = 200
    response.read.return_value = json.dumps(_INDEX).encode('utf-8')
    response.__enter__.return_value = response
    constructor = MagicMock()
    constructor.return_value.getresponse.return_value = response
    monkeypatch.setattr(check_node_version, 'HTTPSConnection', constructor)
    return constructor, response


def test_online_index_uses_only_the_official_https_host_and_path(https: tuple[MagicMock, MagicMock]) -> None:
    constructor, response = https

    assert check_node_version.load_index(None) == _INDEX

    constructor.assert_called_once_with('nodejs.org', timeout=30)
    constructor.return_value.request.assert_called_once_with('GET', '/dist/index.json')
    constructor.return_value.getresponse.assert_called_once_with()
    constructor.return_value.close.assert_called_once_with()
    response.__exit__.assert_called_once()


@pytest.mark.parametrize('status', [301, 302, 303, 307, 308, 400, 403, 404, 500])
def test_redirects_and_http_errors_are_rejected_without_reading_the_body(https: tuple[MagicMock, MagicMock], status: int) -> None:
    constructor, response = https
    response.status = status

    with pytest.raises(ValueError, match=f'HTTP {status}'):
        check_node_version.load_index(None)

    constructor.return_value.request.assert_called_once_with('GET', '/dist/index.json')
    response.read.assert_not_called()
    constructor.return_value.close.assert_called_once_with()
    response.__exit__.assert_called_once()


def test_invalid_online_json_still_closes_the_connection(https: tuple[MagicMock, MagicMock]) -> None:
    constructor, response = https
    response.read.return_value = b'invalid json'

    with pytest.raises(json.JSONDecodeError):
        check_node_version.load_index(None)

    constructor.return_value.close.assert_called_once_with()
    response.__exit__.assert_called_once()


def test_protocol_errors_are_reported_as_check_failure(
    https: tuple[MagicMock, MagicMock], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    constructor, _ = https
    constructor.return_value.getresponse.side_effect = BadStatusLine('invalid response')
    monkeypatch.setattr(sys, 'argv', ['check_node_version.py'])

    assert check_node_version.main() == 2

    assert 'invalid response' in capsys.readouterr().err
    constructor.return_value.close.assert_called_once_with()
