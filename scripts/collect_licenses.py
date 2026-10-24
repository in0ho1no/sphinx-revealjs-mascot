"""HTML に同梱する素材の通知を検証してコピーする。"""

import argparse
import hashlib
import json
import shutil
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

type Record = dict[str, Any]


def _inside(root: Path, relative: str) -> Path:
    """通知フォルダ内に収まるパスを返す。"""
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f'通知フォルダ外のパスです: {relative}')
    return target


def verify(root: Path) -> Record:
    """同梱素材の配布元の版と、通知のハッシュを確認する。"""
    output = root / 'third_party'
    manifest = cast(Record, json.loads((output / 'manifest.json').read_text(encoding='utf-8')))
    package = manifest['source_distribution']
    if version(package['name']) != package['version']:
        raise ValueError('sphinx-revealjs が更新されています。同梱素材の通知を再確認してください。')
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


def main() -> None:
    """ネットワークを使わず同梱素材の通知を検証する。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='同梱素材の通知を検証する（既定の動作）')
    parser.parse_args()
    manifest = verify(Path(__file__).resolve().parents[1])
    print(f'{len(manifest["components"])} bundled components: verified')


if __name__ == '__main__':
    main()
