"""reveal.js のスライドへキャラクターを自動で組み込む Sphinx 拡張。"""

import json
import shutil
from pathlib import Path
from typing import Any

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
from sphinx.util.osutil import relative_uri
from sphinx.util.typing import ExtensionMetadata

_STATES = ('normal', 'blink', 'sleepy', 'surprise')
_ASSET_NAME = 'sphinx-revealjs-mascot'
_STATIC_DIR = Path(__file__).parent / 'static'
# 配布パッケージ化までは、画像を複製して保守せず既存の原本を参照する。
_IMAGE_DIR = Path(__file__).resolve().parents[2] / 'examples/_static/mascot/joubitaki'
_PREVIEW_WIDTH = 16


def _is_revealjs(app: Sphinx) -> bool:
    """reveal.js 用の HTML ビルダーか判定する。"""
    return app.builder.name in {'revealjs', 'dirrevealjs'}


def _configure_assets(app: Sphinx) -> None:
    """画像の存在を確認し、拡張の CSS・JavaScript を登録する。"""
    if not _is_revealjs(app):
        return
    missing = [_IMAGE_DIR / f'{state}.png' for state in _STATES if not (_IMAGE_DIR / f'{state}.png').is_file()]
    if missing:
        raise ExtensionError('標準画像が見つかりません: ' + ', '.join(str(path) for path in missing))
    app.add_static_dir(_STATIC_DIR)
    app.add_css_file(f'{_ASSET_NAME}/mascot.css')
    app.add_js_file(f'{_ASSET_NAME}/mascot.js', loading_method='defer')


def _page_config(app: Sphinx, pagename: str, templatename: str, context: dict[str, Any], doctree: nodes.document | None) -> None:
    """ページからの相対画像 URL と仮の表示幅を HTML に埋め込む。"""
    if not _is_revealjs(app):
        return
    page_uri = app.builder.get_target_uri(pagename)
    config = {
        'images': {state: relative_uri(page_uri, f'_static/{_ASSET_NAME}/images/{state}.png') for state in _STATES},
        'width': _PREVIEW_WIDTH,
    }
    body = json.dumps(config, ensure_ascii=True).replace('<', r'\u003c')
    app.add_js_file(None, body=body, type='application/json', id='sphinx-revealjs-mascot-config')


def _copy_images(app: Sphinx, exception: Exception | None) -> None:
    """成功したビルドへ標準画像の原本をそのままコピーする。"""
    if exception is not None or not _is_revealjs(app):
        return
    destination = Path(app.outdir) / '_static' / _ASSET_NAME / 'images'
    destination.mkdir(parents=True, exist_ok=True)
    for state in _STATES:
        shutil.copyfile(_IMAGE_DIR / f'{state}.png', destination / f'{state}.png')


def setup(app: Sphinx) -> ExtensionMetadata:
    """拡張の静的ファイルとページ設定の出力処理を登録する。"""
    app.setup_extension('sphinx_revealjs')
    app.connect('builder-inited', _configure_assets)
    app.connect('html-page-context', _page_config)
    app.connect('build-finished', _copy_images)
    return {'parallel_read_safe': True, 'parallel_write_safe': True}
