"""mise.toml で固定した Node.js が、同じメジャーの最新版か確認する。"""

# GitHub Actions では uv を使わず標準の python3 で実行するため、3.12 で動く構文と標準ライブラリに留める。

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from http.client import HTTPException, HTTPSConnection
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
_VERSION = re.compile(r'v?(\d+)\.(\d+)\.(\d+)')

type Version = tuple[int, int, int]
type Index = list[dict[str, Any]]


@dataclass(frozen=True)
class Release:
    """公開された Node.js の版と、セキュリティリリースかどうかを保持する。"""

    version: Version
    date: str
    security: bool


def format_version(version: Version) -> str:
    """版を major.minor.patch 形式の文字列にする。"""
    return '.'.join(map(str, version))


def parse_version(value: str) -> Version:
    """24.22.1 または v24.22.1 形式の版を解釈する。"""
    match = _VERSION.fullmatch(value.strip())
    if not match:
        raise ValueError(f'Node.js の版は major.minor.patch で固定してください: {value!r}')
    major, minor, patch = map(int, match.groups())
    return major, minor, patch


def pinned_version(config: Path) -> Version:
    """mise.toml の [tools] に固定した Node.js の版を返す。"""
    tools = tomllib.loads(config.read_text(encoding='utf-8')).get('tools')
    value = tools.get('node') if isinstance(tools, dict) else None
    if not isinstance(value, str):
        raise ValueError(f'{config.name} の [tools] に node の版を文字列で指定してください')
    return parse_version(value)


def newer_releases(pinned: Version, index: Index) -> list[Release]:
    """固定した版より新しい、同じメジャーの公開版を新しい順に返す。"""
    releases: list[Release] = []
    for entry in index:
        version = parse_version(entry['version'])
        if version[0] == pinned[0] and version > pinned:
            releases.append(Release(version, entry['date'], entry.get('security') is True))
    return sorted(releases, key=lambda release: release.version, reverse=True)


def issue_body(pinned: Version, releases: list[Release]) -> str:
    """Task テンプレートの項目に沿って、更新を促す Issue 本文を作る。"""
    current = format_version(pinned)
    latest = format_version(releases[0].version)
    if any(release.security for release in releases):
        urgency = 'セキュリティリリースを含むため、早めに更新してください。'
    else:
        urgency = 'セキュリティリリースは含みません。'
    lines = [
        '### 種別',
        '',
        '設定・開発フロー',
        '',
        '### 目的',
        '',
        f'mise.toml で固定した Node.js {current} より新しい同じメジャーの版が公開されています。{urgency}',
        '',
        '### 作業内容',
        '',
        f'mise.toml の node を {current} から {latest} へ更新します。公開済みの新しい版は次のとおりです。',
        '',
        '| 版 | 公開日 | セキュリティリリース |',
        '| --- | --- | --- |',
        *(f'| {format_version(release.version)} | {release.date} | {"あり" if release.security else "なし"} |' for release in releases),
        '',
        '### 完了条件',
        '',
        f'- [ ] mise.toml の node が {latest} 以降になっている',
        '- [ ] 更新後の Node.js で開発環境の検証が通る',
        '',
        '### 振る舞いの変化',
        '',
        'なし',
        '',
        '### 対象範囲',
        '',
        'mise.toml',
        '',
        '### 起票者',
        '',
        '自動 (Node.js Version workflow)',
        '',
        '### 起票前の確認',
        '',
        '- [x] 既存 Issue に重複がないか検索した',
        '- [x] トークン・パスワード等の機密情報を伏字化した',
        '',
    ]
    return '\n'.join(lines)


def load_index(index_file: Path | None) -> Index:
    """公開版の一覧を、指定されたファイルまたは nodejs.org から読み込む。"""
    if index_file is not None:
        return cast(Index, json.loads(index_file.read_text(encoding='utf-8')))
    # 汎用 URL の処理とリダイレクト追従は、公式の取得先以外を許すため使わない。
    connection = HTTPSConnection('nodejs.org', timeout=30)
    try:
        connection.request('GET', '/dist/index.json')
        with connection.getresponse() as response:
            if response.status != 200:
                raise ValueError(f'nodejs.org の公開版一覧を取得できません: HTTP {response.status}')
            return cast(Index, json.load(response))
    finally:
        connection.close()


def main() -> int:
    """固定した版が最新なら 0、新しい版があれば 1、確認できなければ 2 を返す。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'mise.toml', help='Node.js を固定した mise の設定')
    parser.add_argument('--index-file', type=Path, help='nodejs.org の代わりに読み込む公開版一覧の JSON')
    parser.add_argument('--issue-body', type=Path, help='新しい版がある場合に Issue 本文を書き出すファイル')
    arguments = parser.parse_args()
    try:
        pinned = pinned_version(arguments.config)
        releases = newer_releases(pinned, load_index(arguments.index_file))
    except (OSError, HTTPException, ValueError, KeyError, TypeError) as error:
        print(f'Node.js の版を確認できません: {error}', file=sys.stderr)
        return 2
    if not releases:
        print(f'Node.js {format_version(pinned)}: up to date')
        return 0
    print(f'Node.js {format_version(pinned)}: {format_version(releases[0].version)} is available')
    if arguments.issue_body is not None:
        arguments.issue_body.write_text(issue_body(pinned, releases), encoding='utf-8')
    return 1


if __name__ == '__main__':
    sys.exit(main())
