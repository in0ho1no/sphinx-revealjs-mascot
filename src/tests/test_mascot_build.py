"""最小の reveal.js ビルドと拡張の静的ファイル出力を確認する。"""

import json
import subprocess
import sys
from dataclasses import asdict
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment

import sphinx_revealjs_mascot as mascot
from sphinx_revealjs_mascot.config import ACTIONS, DEFAULT_ACTIONS, OPTIONAL_STATES, REQUIRED_STATES

_REPOSITORY = Path(__file__).resolve().parents[2]


class _HTMLResources(HTMLParser):
    """HTML に含まれるリソース参照と埋め込み設定を収集する。"""

    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []
        self.config = ''
        self._in_config = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == 'script' or (tag == 'link' and attributes.get('rel') == 'stylesheet'):
            url = attributes.get('src') if tag == 'script' else attributes.get('href')
            if url:
                self.urls.append(url)
        self._in_config = tag == 'script' and attributes.get('id') == 'sphinx-revealjs-mascot-config'

    def handle_endtag(self, tag: str) -> None:
        if tag == 'script':
            self._in_config = False

    def handle_data(self, data: str) -> None:
        if self._in_config:
            self.config += data


@pytest.mark.parametrize('builder', ['revealjs', 'dirrevealjs'])
def test_minimal_build_includes_local_assets_and_notices(tmp_path: Path, builder: str) -> None:
    output = tmp_path / 'output'
    result = subprocess.run(
        [
            sys.executable,
            '-m',
            'sphinx',
            '-W',
            '-b',
            builder,
            '-c',
            str(_REPOSITORY / 'examples'),
            '-D',
            'root_doc=index',
            str(_REPOSITORY / 'examples/minimal'),
            str(output),
        ],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    nested_page = 'nested/second/index.html' if builder == 'dirrevealjs' else 'nested/second.html'
    for filename in ['index.html', nested_page]:
        page = output / filename
        resources = _HTMLResources()
        resources.feed(page.read_text(encoding='utf-8'))
        assert any('sphinx-revealjs-mascot/mascot.css' in url for url in resources.urls)
        assert any('sphinx-revealjs-mascot/mascot.js' in url for url in resources.urls)
        for url in resources.urls:
            assert '://' not in url, url
            assert not url.startswith('//'), url
            assert (page.parent / url.split('?', 1)[0]).is_file(), url
        config = json.loads(resources.config)
        assert config['defaultActions'] == DEFAULT_ACTIONS
        assert config['actions'] == {name: asdict(definition) for name, definition in ACTIONS.items()}
        assert list(config['images']) == list(REQUIRED_STATES + OPTIONAL_STATES)
        for state, url in config['images'].items():
            original = _REPOSITORY / 'examples/_static/mascot/joubitaki' / f'{state}.png'
            assert (page.parent / url).read_bytes() == original.read_bytes()
    assert (output / 'third_party/NOTICES.txt').read_bytes() == (_REPOSITORY / 'third_party/NOTICES.txt').read_bytes()
    assert {path.name for path in (output / 'third_party').iterdir()} == {'README.md', 'manifest.json', 'NOTICES.txt'}


@pytest.mark.parametrize(
    ('previous', 'current', 'builder', 'reread'),
    [
        (None, REQUIRED_STATES, 'revealjs', True),
        (None, REQUIRED_STATES, 'html', False),
        (REQUIRED_STATES, REQUIRED_STATES, 'revealjs', False),
        ((*REQUIRED_STATES, 'badge'), REQUIRED_STATES, 'revealjs', False),
        ((*REQUIRED_STATES, 'happy'), REQUIRED_STATES, 'revealjs', True),
        (REQUIRED_STATES, (*REQUIRED_STATES, 'happy'), 'dirrevealjs', True),
        ((*REQUIRED_STATES, 'happy'), REQUIRED_STATES, 'html', False),
    ],
)
def test_changed_image_states_reread_every_page(
    tmp_path: Path, previous: tuple[str, ...] | None, current: tuple[str, ...], builder: str, reread: bool
) -> None:
    destination = tmp_path / '_static/sphinx-revealjs-mascot/images'
    if previous is not None:
        destination.mkdir(parents=True)
        for name in previous:
            (destination / f'{name}.png').write_bytes(b'')
    settings = SimpleNamespace(images={state: tmp_path / f'{state}.png' for state in current})
    env = SimpleNamespace(domaindata={'sphinx-revealjs-mascot': {'settings': settings}}, found_docs={'nested/second', 'index'})
    app = SimpleNamespace(outdir=str(tmp_path), builder=SimpleNamespace(name=builder), env=env)
    docs = mascot._outdated_by_images(cast(Sphinx, app), cast(BuildEnvironment, env), set(), set(), set())
    assert docs == (['index', 'nested/second'] if reread else [])
