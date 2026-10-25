"""設定値と画像セットの検証を確認する。"""

from pathlib import Path

import pytest
from sphinx.config import Config
from sphinx.errors import ConfigError

from sphinx_revealjs_mascot.config import CONFIG_DEFAULTS, IMAGE_PATTERNS, STATES, parse_position, resolve_images, resolve_settings


def _image_set(directory: Path, common: str = '', suffix: bool = False) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = {}
    for state in STATES:
        name = f'{state}_{common}' if suffix else f'{common}_{state}'
        path = directory / (f'{name}.png' if common else f'{state}.png')
        path.write_bytes(f'image: {state}, {common}'.encode())
        paths[state] = path
    return paths


@pytest.mark.parametrize(
    ('value', 'anchor', 'x', 'y', 'facing'),
    [
        ('bottom-right', 'bottom-right', 100, 100, -1),
        ('top-right', 'top-right', 100, 0, -1),
        ('bottom-left', 'bottom-left', 0, 100, 1),
        ('top-left', 'top-left', 0, 0, 1),
        ('0%,100%', 'center', 0, 100, 1),
        ('50%, 60%', 'center', 50, 60, 1),
        (' 70.5%, 60% ', 'center', 70.5, 60, -1),
    ],
)
def test_position_normalizes_anchor_and_facing(value: str, anchor: str, x: float, y: float, facing: int) -> None:
    position = parse_position(value)
    assert (position.anchor, position.x, position.y, position.facing) == (anchor, x, y, facing)


@pytest.mark.parametrize('value', ['left', '-1%, 0%', '101%, 50%', '50, 50', 'nan%, 0%', '', None, 50])
def test_invalid_position_is_rejected(value: object) -> None:
    with pytest.raises(ConfigError, match='不正な表示位置'):
        parse_position(value)


@pytest.mark.parametrize(
    ('pattern', 'common', 'suffix'), [(IMAGE_PATTERNS[0], '', False), (IMAGE_PATTERNS[1], 'bird', False), (IMAGE_PATTERNS[2], 'bird', True)]
)
def test_image_set_is_detected_for_each_pattern(tmp_path: Path, pattern: str, common: str, suffix: bool) -> None:
    expected = _image_set(tmp_path, common, suffix)
    (tmp_path / 'unrelated.png').write_bytes(b'other')
    assert resolve_images(tmp_path, pattern) == expected


def test_missing_images_are_not_replaced_by_standard_images(tmp_path: Path) -> None:
    (tmp_path / 'normal.png').write_bytes(b'normal')
    with pytest.raises(ConfigError, match=r'blink\.png.*sleepy\.png.*surprise\.png'):
        resolve_images(tmp_path, IMAGE_PATTERNS[0])


@pytest.mark.parametrize('suffix', [False, True])
def test_multiple_complete_image_sets_are_rejected(tmp_path: Path, suffix: bool) -> None:
    _image_set(tmp_path, 'bird', suffix)
    _image_set(tmp_path, 'dog', suffix)
    with pytest.raises(ConfigError, match='画像セットが複数見つかりました'):
        resolve_images(tmp_path, IMAGE_PATTERNS[2 if suffix else 1])


def test_mixed_common_names_show_candidate_files(tmp_path: Path) -> None:
    (tmp_path / 'bird_normal.png').write_bytes(b'normal')
    (tmp_path / 'dog_blink.png').write_bytes(b'blink')
    with pytest.raises(ConfigError, match=r'共通のfile-name.*bird_normal\.png.*dog_blink\.png'):
        resolve_images(tmp_path, IMAGE_PATTERNS[1])


def test_incomplete_named_set_reports_missing_states(tmp_path: Path) -> None:
    (tmp_path / 'normal_bird.png').write_bytes(b'normal')
    with pytest.raises(ConfigError, match='blink, sleepy, surprise'):
        resolve_images(tmp_path, IMAGE_PATTERNS[2])


def test_missing_directory_and_invalid_pattern_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match='画像フォルダが存在しません'):
        resolve_images(tmp_path / 'missing', IMAGE_PATTERNS[0])
    with pytest.raises(ConfigError, match='image_pattern が不正'):
        resolve_images(tmp_path, 'bird_{state}.png')


def _config(values: dict[str, object]) -> Config:
    config = Config(config=values)
    for name, default in CONFIG_DEFAULTS.items():
        config.add(name, default, 'env', types=())
    return config


def test_custom_image_directory_is_relative_to_confdir(tmp_path: Path) -> None:
    images = _image_set(tmp_path / 'conf/pictures')
    settings = resolve_settings(
        _config({'revealjs_mascot_image_dir': 'pictures', 'revealjs_mascot_width': 12.5, 'revealjs_mascot_position': '50%, 50%'}),
        tmp_path / 'conf',
        tmp_path / 'unused-standard',
    )
    assert settings.images == images
    assert settings.width == 12.5
    assert settings.position.facing == 1


@pytest.mark.parametrize(
    ('name', 'value'),
    [
        ('width', 0),
        ('width', 101),
        ('width', True),
        ('width', '16'),
        ('width', float('nan')),
        ('idle_timeout', -1),
        ('idle_timeout', False),
        ('idle_timeout', float('inf')),
        ('toggle_key', ''),
        ('toggle_key', 'Enter'),
        ('toggle_key', ' '),
        ('toggle_key', None),
        ('image_dir', 1),
        ('image_pattern', None),
    ],
)
def test_invalid_configuration_fails_early(tmp_path: Path, name: str, value: object) -> None:
    _image_set(tmp_path)
    with pytest.raises(ConfigError, match=f'revealjs_mascot_{name}'):
        resolve_settings(_config({f'revealjs_mascot_{name}': value}), tmp_path, tmp_path)
