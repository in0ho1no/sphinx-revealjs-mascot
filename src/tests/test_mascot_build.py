"""最小の reveal.js ビルドと拡張の静的ファイル出力を確認する。"""

import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

from sphinx_revealjs_mascot import _STATES

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
        assert set(config['images']) == set(_STATES)
        for state, url in config['images'].items():
            original = _REPOSITORY / 'examples/_static/mascot/joubitaki' / f'{state}.png'
            assert (page.parent / url).read_bytes() == original.read_bytes()
    assert (output / 'third_party/NOTICES.txt').read_bytes() == (_REPOSITORY / 'third_party/NOTICES.txt').read_bytes()
    assert {path.name for path in (output / 'third_party').iterdir()} == {'README.md', 'manifest.json', 'NOTICES.txt'}
