"""両記法のスライド設定と fragment の HTML 出力を検証する。"""

import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

_REPOSITORY = Path(__file__).resolve().parents[2]


class _Markup(HTMLParser):
    """スライド属性と fragment ごとの内容数を収集する。"""

    def __init__(self) -> None:
        super().__init__()
        self.sections: list[dict[str, str | None]] = []
        self.fragments: list[dict[str, str | int | None]] = []
        self._div_depth = 0
        self._fragment_depth = 0
        self._list_depth = 0
        self.config = ''
        self._in_config = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == 'section':
            self.sections.append(attributes)
        if tag == 'div':
            self._div_depth += 1
            if 'fragment' in (attributes.get('class') or '').split():
                self._fragment_depth = self._div_depth
                self.fragments.append({'action': attributes.get('data-mascot-action'), 'paragraphs': 0, 'items': 0})
        if tag in {'ul', 'ol'}:
            self._list_depth += 1
        if self._fragment_depth and (tag == 'li' or (tag == 'p' and self._list_depth == 0)):
            key = 'paragraphs' if tag == 'p' else 'items'
            self.fragments[-1][key] = int(self.fragments[-1][key] or 0) + 1
        if tag == 'script':
            self._in_config = attributes.get('id') == 'sphinx-revealjs-mascot-config'

    def handle_endtag(self, tag: str) -> None:
        if tag in {'ul', 'ol'}:
            self._list_depth -= 1
        if tag == 'div':
            if self._fragment_depth == self._div_depth:
                self._fragment_depth = 0
            self._div_depth -= 1
        if tag == 'script':
            self._in_config = False

    def handle_data(self, data: str) -> None:
        if self._in_config:
            self.config += data


def _build(source: Path, output: Path, confdir: Path, strict: bool = True, root: str = 'index') -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            '-X',
            'utf8',
            '-m',
            'sphinx',
            *(['-W'] if strict else []),
            '-b',
            'revealjs',
            '-c',
            str(confdir),
            '-D',
            f'root_doc={root}',
            str(source),
            str(output),
        ],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=False,
    )


def test_existing_samples_embed_slide_settings_and_grouped_fragments(tmp_path: Path) -> None:
    result = _build(_REPOSITORY / 'examples', tmp_path / 'output', _REPOSITORY / 'examples', root='slides')
    assert result.returncode == 0, result.stdout + result.stderr
    slides = _Markup()
    slides.feed((tmp_path / 'output/slides.html').read_text(encoding='utf-8'))
    configured = [section for section in slides.sections if 'data-mascot-action' in section]
    assert [section['data-mascot-action'] for section in configured] == ['jump', 'surprise', 'idle']
    assert configured[1]['data-mascot-position'] == 'bottom-left'
    assert configured[1]['data-mascot-facing'] == '1'
    assert configured[2]['data-mascot-position'] == 'center'
    assert configured[2]['data-mascot-x'] == '70'
    assert configured[2]['data-mascot-facing'] == '-1'
    assert 'data-mascot-position' not in slides.sections[-1]
    fragments = _Markup()
    fragments.feed((tmp_path / 'output/fragments.html').read_text(encoding='utf-8'))
    assert [fragment['action'] for fragment in fragments.fragments] == ['surprise', 'jump', None, 'wink']
    assert fragments.fragments[2]['items'] == 2


@pytest.fixture
def source(tmp_path: Path) -> Path:
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'conf.py').write_text(
        f"import sys\nsys.path.insert(0, {str(_REPOSITORY / 'src')!r})\nextensions = ['sphinx_revealjs_mascot', 'myst_parser']\n",
        encoding='utf-8',
    )
    return source


@pytest.mark.parametrize('suffix', ['rst', 'md'])
def test_both_formats_preserve_other_section_options_and_group_content(source: Path, tmp_path: Path, suffix: str) -> None:
    if suffix == 'rst':
        content = (
            'Deck\n====\n\nSlide\n-----\n\n.. revealjs-section::\n   :data-background-color: red\n\n'
            '.. mascot::\n   :action: idle\n   :position: top-left\n\n'
            '.. mascot-fragment::\n   :action: wink\n\n   First paragraph.\n\n   Second paragraph.\n\n   - One\n   - Two\n'
        )
    else:
        content = (
            '# Deck\n\n## Slide\n\n```{revealjs-section}\n:data-background-color: red\n```\n\n'
            '```{mascot}\n:action: idle\n:position: top-left\n```\n\n'
            '```{mascot-fragment}\n:action: wink\n\nFirst paragraph.\n\nSecond paragraph.\n\n- One\n- Two\n```\n'
        )
    (source / f'index.{suffix}').write_text(content, encoding='utf-8')
    result = _build(source, tmp_path / 'output', source)
    assert result.returncode == 0, result.stdout + result.stderr
    markup = _Markup()
    markup.feed((tmp_path / 'output/index.html').read_text(encoding='utf-8'))
    section = next(section for section in markup.sections if 'data-mascot-action' in section)
    assert section['data-background-color'] == 'red'
    assert section['data-mascot-position'] == 'top-left'
    assert markup.fragments == [{'action': 'wink', 'paragraphs': 2, 'items': 2}]


@pytest.mark.parametrize('suffix', ['rst', 'md'])
@pytest.mark.parametrize(
    ('directive', 'option', 'message'),
    [
        ('mascot', 'action: doze', '明示指定できないアクション'),
        ('mascot', 'position: 101%, 50%', '不正な表示位置'),
        ('mascot', 'width: 10', '不明な mascot'),
        ('mascot-fragment', 'position: bottom-left', '不明な mascot'),
        ('mascot-fragment', 'action: wake', '明示指定できないアクション'),
    ],
)
def test_invalid_directive_is_build_error_without_warning_as_error(
    source: Path, tmp_path: Path, suffix: str, directive: str, option: str, message: str
) -> None:
    content = (
        f'Deck\n====\n\nSlide\n-----\n\n.. {directive}::\n   :{option}\n'
        if suffix == 'rst'
        else f'# Deck\n\n## Slide\n\n```{{{directive}}}\n:{option}\n```\n'
    )
    (source / f'index.{suffix}').write_text(content, encoding='utf-8')
    result = _build(source, tmp_path / 'output', source, strict=False)
    assert result.returncode != 0
    assert message in result.stdout + result.stderr


def test_custom_configuration_and_images_reach_output(source: Path, tmp_path: Path) -> None:
    image_dir = source / 'pictures'
    image_dir.mkdir()
    originals = _REPOSITORY / 'examples/_static/mascot/joubitaki'
    for path in originals.glob('*.png'):
        (image_dir / f'bird_{path.name}').write_bytes(path.read_bytes())
    with (source / 'conf.py').open('a', encoding='utf-8') as config:
        config.write(
            "revealjs_mascot_image_dir = 'pictures'\nrevealjs_mascot_image_pattern = 'file-name_{state}.png'\n"
            "revealjs_mascot_position = '50%, 40%'\nrevealjs_mascot_width = 12.5\n"
            "revealjs_mascot_idle_timeout = 30\nrevealjs_mascot_toggle_key = 'x'\n"
        )
    (source / 'index.rst').write_text('Deck\n====\n\nSlide\n-----\n\nText.\n', encoding='utf-8')
    result = _build(source, tmp_path / 'output', source)
    assert result.returncode == 0, result.stdout + result.stderr
    markup = _Markup()
    markup.feed((tmp_path / 'output/index.html').read_text(encoding='utf-8'))
    config_values = json.loads(markup.config)
    assert config_values['width'] == 12.5
    assert config_values['position'] == {'anchor': 'center', 'x': 50, 'y': 40, 'facing': 1}
    assert config_values['idleTimeout'] == 30
    assert config_values['toggleKey'] == 'x'
    for state, url in config_values['images'].items():
        assert (tmp_path / 'output' / url).read_bytes() == (image_dir / f'bird_{state}.png').read_bytes()
