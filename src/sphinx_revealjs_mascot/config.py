"""拡張設定と画像セットを検証し、ブラウザ用の値に正規化する。"""

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sphinx.config import Config
from sphinx.errors import ConfigError

STATES = ('normal', 'blink', 'sleepy', 'surprise')


@dataclass(frozen=True)
class Action:
    """状態画像・継続時間（ミリ秒）・指定可否・CSS モーションの有無を定義する。"""

    image: str
    duration: int = 0
    explicit: bool = True
    motion: bool = False


ACTIONS = {
    'idle': Action('normal'),
    'jump': Action('normal', duration=600, motion=True),
    'wink': Action('blink', duration=180),
    'surprise': Action('surprise', duration=700, motion=True),
    'doze': Action('sleepy', explicit=False, motion=True),
    'wake': Action('surprise', duration=500, explicit=False, motion=True),
}
DEFAULT_ACTIONS = {'slide': 'jump', 'fragment': 'wink'}
MOTION = {
    'sway_angle': 1.5,
    'sway_duration': 3700,
    'breath_scale': 1.015,
    'breath_duration': 2900,
    'jump_height': 0.15,
    'surprise_scale': 1.06,
    'wake_height': 0.08,
    'wake_angle': 3,
    'doze_min_angle': 2,
    'doze_max_angle': 8,
    'doze_duration': 4800,
    'sleep_rise': 0.4,
    'sleep_right': 0.1,
    'sleep_duration': 2400,
    'edge_gap': 12,
}
IMAGE_PATTERNS = ('{state}.png', 'file-name_{state}.png', '{state}_file-name.png')
CONFIG_DEFAULTS: dict[str, Any] = {
    'revealjs_mascot_image_dir': None,
    'revealjs_mascot_image_pattern': IMAGE_PATTERNS[0],
    'revealjs_mascot_position': 'bottom-right',
    'revealjs_mascot_width': 16,
    'revealjs_mascot_idle_timeout': 45,
    'revealjs_mascot_toggle_key': 'm',
}
_COORDINATES = re.compile(r'([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*%\s*,\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*%')


@dataclass(frozen=True)
class Position:
    """画面上の基準位置と向きを保持する。"""

    anchor: str
    x: float
    y: float
    facing: int


def parse_position(value: object) -> Position:
    """定型位置または画面幅・高さの割合による座標を検証する。"""
    if isinstance(value, str):
        value = value.strip()
        if value in {'bottom-right', 'bottom-left', 'top-right', 'top-left'}:
            vertical, horizontal = value.split('-')
            x = 100.0 if horizontal == 'right' else 0.0
            y = 100.0 if vertical == 'bottom' else 0.0
            return Position(value, x, y, -1 if x > 50 else 1)
        match = _COORDINATES.fullmatch(value)
        if match:
            x, y = map(float, match.groups())
            if 0 <= x <= 100 and 0 <= y <= 100:
                return Position('center', x, y, -1 if x > 50 else 1)
    raise ConfigError(f'不正な表示位置です（定型位置または 0〜100% の x%, y% を指定）: {value!r}')


def positive_number(name: str, value: object, maximum: float | None = None) -> float:
    """有限の正の数値と、指定された上限を検証する。"""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            number = float(value)
        except OverflowError:
            number = math.inf
        if math.isfinite(number) and number > 0 and (maximum is None or number <= maximum):
            return number
    limit = f'、上限 {maximum:g}' if maximum is not None else ''
    raise ConfigError(f'{name} は有限の正の数値で指定してください{limit}: {value!r}')


def resolve_images(directory: Path, pattern: str) -> dict[str, Path]:
    """指定した命名形式で完全な画像セットを1つ検出する。"""
    if pattern not in IMAGE_PATTERNS:
        raise ConfigError(f'revealjs_mascot_image_pattern が不正です: {pattern!r}。指定可能: {IMAGE_PATTERNS}')
    if not directory.is_dir():
        raise ConfigError(f'画像フォルダが存在しません: {directory}')
    if pattern == IMAGE_PATTERNS[0]:
        images = {state: directory / pattern.format(state=state) for state in STATES}
        missing = [str(path) for path in images.values() if not path.is_file()]
        if missing:
            raise ConfigError('必要な画像が不足しています: ' + ', '.join(missing))
        return images

    candidates: dict[str, dict[str, Path]] = {}
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        for state in STATES:
            fixed = f'_{state}.png' if pattern == IMAGE_PATTERNS[1] else f'{state}_'
            if pattern == IMAGE_PATTERNS[1] and path.name.endswith(fixed):
                common = path.name[: -len(fixed)]
            elif pattern == IMAGE_PATTERNS[2] and path.name.startswith(fixed) and path.name.endswith('.png'):
                common = path.name[len(fixed) : -4]
            else:
                continue
            if common:
                candidates.setdefault(common, {})[state] = path
    complete = [images for images in candidates.values() if set(images) == set(STATES)]
    if len(complete) > 1:
        raise ConfigError(f'画像セットが複数見つかりました。フォルダを分けてください: {directory}')
    if complete:
        return complete[0]
    filenames = ', '.join(path.name for images in candidates.values() for path in images.values())
    if len(candidates) > 1:
        raise ConfigError(f'4種類の画像が共通のfile-nameで揃っていません: {directory}: {filenames}')
    found = next(iter(candidates.values()), {})
    missing_states = ', '.join(state for state in STATES if state not in found)
    raise ConfigError(f'必要な画像が不足しています: {directory}: {missing_states}。候補: {filenames or "なし"}')


@dataclass(frozen=True)
class Settings:
    """検証済みの設定と、採用する画像ファイルを保持する。"""

    images: dict[str, Path]
    position: Position
    width: float
    idle_timeout: float
    toggle_key: str


def resolve_settings(config: Config, confdir: Path, standard_images: Path) -> Settings:
    """conf.py の設定を検証し、相対画像パスを解決する。"""
    directory = config.revealjs_mascot_image_dir
    if directory is not None and not isinstance(directory, (str, Path)):
        raise ConfigError('revealjs_mascot_image_dir は画像フォルダのパスまたは None で指定してください')
    image_dir = standard_images if directory is None else confdir / directory
    pattern = config.revealjs_mascot_image_pattern
    if not isinstance(pattern, str):
        raise ConfigError('revealjs_mascot_image_pattern は文字列で指定してください')
    key = config.revealjs_mascot_toggle_key
    if not isinstance(key, str) or len(key) != 1 or not key.isprintable() or key.isspace():
        raise ConfigError('revealjs_mascot_toggle_key は単一の文字キーで指定してください')
    return Settings(
        images=resolve_images(image_dir.resolve(), pattern),
        position=parse_position(config.revealjs_mascot_position),
        width=positive_number('revealjs_mascot_width', config.revealjs_mascot_width, maximum=100),
        idle_timeout=positive_number('revealjs_mascot_idle_timeout', config.revealjs_mascot_idle_timeout),
        toggle_key=key,
    )
