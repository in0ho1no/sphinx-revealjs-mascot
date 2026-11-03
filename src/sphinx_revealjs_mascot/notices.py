"""HTML に同梱する素材の通知を検証してコピーする。"""

import hashlib
import json
import shutil
from importlib.metadata import distribution
from pathlib import Path
from typing import Any, cast

type Record = dict[str, Any]


def _inside(root: Path, relative: str) -> Path:
    """通知フォルダ内に収まるパスを返す。"""
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f'通知フォルダ外のパスです: {relative}')
    return target


def _revealjs_static_path(package_name: str) -> Path:
    """インストール済み配布物の Reveal.js 素材のパスを返す。"""
    return Path(str(distribution(package_name).locate_file('sphinx_revealjs/_static/revealjs')))


def _tree_sha256(root: Path) -> str:
    """ディレクトリ内のファイルパスと内容から安定したハッシュを計算する。"""
    if not root.is_dir():
        raise ValueError(f'同梱素材のフォルダがありません: {root}')
    files = sorted(path for path in root.rglob('*') if path.is_file())
    if not files:
        raise ValueError(f'同梱素材がありません: {root}')

    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(root).as_posix().encode('utf-8')
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, 'big'))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, 'big'))
        digest.update(content)
    return digest.hexdigest()


def verify(root: Path) -> Record:
    """同梱素材の内容と、通知のハッシュを確認する。"""
    output = root / 'third_party'
    manifest = cast(Record, json.loads((output / 'manifest.json').read_text(encoding='utf-8')))
    package = manifest['source_distribution']
    static_assets = _revealjs_static_path(package['name'])
    if _tree_sha256(static_assets) != manifest['static_assets_sha256']:
        raise ValueError('sphinx-revealjs の同梱素材が更新されています。ライセンス通知を再確認してください。')
    notice = manifest['notice']
    source = _inside(output, notice['path'])
    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != notice['sha256']:
        raise ValueError(f'通知が欠落・変更されています: {source}')
    return manifest


def export_notices(root: Path, destination: Path) -> None:
    """検証済みの通知だけをビルド出力へコピーする。"""
    manifest = verify(root)
    source = root / 'third_party'
    for relative in ['README.md', 'manifest.json', manifest['notice']['path']]:
        target = _inside(destination, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_inside(source, relative), target)
