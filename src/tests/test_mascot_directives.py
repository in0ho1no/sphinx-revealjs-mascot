"""両記法のスライド設定と fragment の HTML 出力を検証する。"""

import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest

from sphinx_revealjs_mascot.config import ACTIONS, OPTIONAL_STATES, REQUIRED_STATES

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


_PLAIN_SLIDE = 'Deck\n====\n\nSlide\n-----\n\nText.\n'


def _use_custom_images(source: Path, states: tuple[str, ...], filename: str = '{state}.png', pattern: str = '{state}.png') -> Path:
    image_dir = source / 'pictures'
    image_dir.mkdir()
    for state in states:
        (image_dir / filename.format(state=state)).write_bytes(f'custom {state}'.encode())
    with (source / 'conf.py').open('a', encoding='utf-8') as config:
        config.write(f"revealjs_mascot_image_dir = 'pictures'\nrevealjs_mascot_image_pattern = {pattern!r}\n")
    return image_dir


def _output(output: Path) -> tuple[_Markup, dict[str, Any], set[str]]:
    markup = _Markup()
    markup.feed((output / 'index.html').read_text(encoding='utf-8'))
    files = {path.name for path in (output / '_static/sphinx-revealjs-mascot/images').iterdir()}
    return markup, json.loads(markup.config), files


@pytest.mark.parametrize(
    ('pattern', 'filename', 'optional'),
    [
        ('{state}.png', '{state}.png', ()),
        ('file-name_{state}.png', 'bird_{state}.png', ('happy',)),
        ('{state}_file-name.png', '{state}_bird.png', OPTIONAL_STATES),
    ],
)
def test_custom_images_in_output_match_resolved_states(source: Path, tmp_path: Path, pattern: str, filename: str, optional: tuple[str, ...]) -> None:
    states = REQUIRED_STATES + optional
    image_dir = _use_custom_images(source, states, filename, pattern)
    (image_dir / 'logo.png').write_bytes(b'unrelated')
    (source / 'index.rst').write_text(_PLAIN_SLIDE, encoding='utf-8')
    output = tmp_path / 'output'
    result = _build(source, output, source)
    assert result.returncode == 0, result.stdout + result.stderr
    _, config, files = _output(output)
    assert list(config['images']) == list(states)
    assert list(config['actions']) == [name for name, action in ACTIONS.items() if action.image in states]
    assert files == {f'{state}.png' for state in states}
    for state in states:
        assert (output / f'_static/sphinx-revealjs-mascot/images/{state}.png').read_bytes() == f'custom {state}'.encode()


@pytest.mark.parametrize(
    ('suffix', 'content'),
    [
        ('rst', 'Deck\n====\n\nSlide\n-----\n\n.. mascot::\n   :action: happy\n\n.. mascot-fragment::\n   :action: happy\n\n   Text.\n'),
        ('md', '# Deck\n\n## Slide\n\n```{mascot}\n:action: happy\n```\n\n```{mascot-fragment}\n:action: happy\n\nText.\n```\n'),
    ],
)
def test_optional_action_with_its_image_reaches_slide_fragment_and_config(source: Path, tmp_path: Path, suffix: str, content: str) -> None:
    _use_custom_images(source, (*REQUIRED_STATES, 'happy'))
    (source / f'index.{suffix}').write_text(content, encoding='utf-8')
    result = _build(source, tmp_path / 'output', source)
    assert result.returncode == 0, result.stdout + result.stderr
    markup, config, _ = _output(tmp_path / 'output')
    assert [section['data-mascot-action'] for section in markup.sections if 'data-mascot-action' in section] == ['happy']
    assert [fragment['action'] for fragment in markup.fragments] == ['happy']
    assert 'happy' in config['actions']
    assert 'happy' in config['images']
    assert 'tilt' not in config['actions']


@pytest.mark.parametrize(
    ('suffix', 'content'),
    [
        ('rst', 'Deck\n====\n\nSlide\n-----\n\n.. mascot::\n   :action: tilt\n\nText.\n'),
        ('md', '# Deck\n\n## Slide\n\n```{mascot-fragment}\n:action: tilt\n\nText.\n```\n'),
    ],
)
def test_optional_action_without_its_image_is_build_error(source: Path, tmp_path: Path, suffix: str, content: str) -> None:
    _use_custom_images(source, (*REQUIRED_STATES, 'happy'))
    (source / f'index.{suffix}').write_text(content, encoding='utf-8')
    result = _build(source, tmp_path / 'output', source, strict=False)
    assert result.returncode != 0
    assert re.search(rf"index\.{suffix}:\d+: アクション 'tilt' には状態画像 'tilt' が必要です", result.stdout + result.stderr)


def test_missing_image_error_points_to_the_included_file(source: Path, tmp_path: Path) -> None:
    _use_custom_images(source, REQUIRED_STATES)
    (source / 'slide.inc').write_text('Slide\n-----\n\nOne.\n\nTwo.\n\n.. mascot::\n   :action: tilt\n', encoding='utf-8')
    (source / 'index.rst').write_text('Deck\n====\n\n.. include:: slide.inc\n', encoding='utf-8')
    result = _build(source, tmp_path / 'output', source, strict=False)
    assert result.returncode != 0
    assert re.search(r"slide\.inc:8: アクション 'tilt' には状態画像 'tilt' が必要です", result.stdout + result.stderr)


def test_incremental_build_follows_optional_images_and_keeps_other_static_files(source: Path, tmp_path: Path) -> None:
    image_dir = _use_custom_images(source, REQUIRED_STATES)
    badge = source / '_static/sphinx-revealjs-mascot/images/badge.png'
    badge.parent.mkdir(parents=True)
    badge.write_bytes(b'badge')
    with (source / 'conf.py').open('a', encoding='utf-8') as conf:
        conf.write("revealjs_static_path = ['_static']\n")
    (source / 'index.rst').write_text(_PLAIN_SLIDE, encoding='utf-8')
    output = tmp_path / 'output'
    happy = image_dir / 'happy.png'
    for states in (REQUIRED_STATES, (*REQUIRED_STATES, 'happy'), REQUIRED_STATES):
        if 'happy' in states:
            happy.write_bytes(b'happy')
        else:
            happy.unlink(missing_ok=True)
        result = _build(source, output, source)
        assert result.returncode == 0, result.stdout + result.stderr
        _, config, files = _output(output)
        assert list(config['images']) == list(states)
        assert files == {f'{state}.png' for state in states} | {'badge.png'}


def test_removing_an_optional_image_in_use_fails_the_next_build(source: Path, tmp_path: Path) -> None:
    image_dir = _use_custom_images(source, (*REQUIRED_STATES, 'happy'))
    (source / 'index.rst').write_text('Deck\n====\n\nSlide\n-----\n\n.. mascot::\n   :action: happy\n\nText.\n', encoding='utf-8')
    output = tmp_path / 'output'
    first = _build(source, output, source)
    assert first.returncode == 0, first.stdout + first.stderr
    (image_dir / 'happy.png').unlink()
    second = _build(source, output, source, strict=False)
    assert second.returncode != 0
    assert "アクション 'happy' には状態画像 'happy' が必要です" in second.stdout + second.stderr
