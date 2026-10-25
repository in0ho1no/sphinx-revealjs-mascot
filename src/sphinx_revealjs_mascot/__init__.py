"""reveal.js のスライドへキャラクターを自動で組み込む Sphinx 拡張。"""

import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.osutil import relative_uri
from sphinx.util.typing import ExtensionMetadata

from sphinx_revealjs_mascot.config import CONFIG_DEFAULTS, DEFAULT_ACTIONS, STATES, Settings, resolve_settings
from sphinx_revealjs_mascot.directives import (
    MascotDirective,
    MascotFragment,
    MascotFragmentDirective,
    MascotSettings,
    apply_slide_settings,
    depart_fragment,
    visit_fragment,
)

_ASSET_NAME = 'sphinx-revealjs-mascot'
_STATIC_DIR = Path(__file__).parent / 'static'
# 配布パッケージ化までは、画像を複製して保守せず既存の原本を参照する。
_IMAGE_DIR = Path(__file__).resolve().parents[2] / 'examples/_static/mascot/joubitaki'


def _settings(app: Sphinx) -> Settings:
    """現在のビルドで解決済みの設定を返す。"""
    return cast(Settings, app.env.domaindata[_ASSET_NAME]['settings'])


def _is_revealjs(app: Sphinx) -> bool:
    """reveal.js 用の HTML ビルダーか判定する。"""
    return app.builder.name in {'revealjs', 'dirrevealjs'}


def _configure_assets(app: Sphinx) -> None:
    """画像の存在を確認し、拡張の CSS・JavaScript を登録する。"""
    if not _is_revealjs(app):
        return
    app.env.domaindata[_ASSET_NAME] = {'settings': resolve_settings(app.config, Path(app.confdir), _IMAGE_DIR)}
    app.add_static_dir(_STATIC_DIR)
    app.add_css_file(f'{_ASSET_NAME}/mascot.css')
    app.add_js_file(f'{_ASSET_NAME}/mascot.js', loading_method='defer')


def _page_config(app: Sphinx, pagename: str, templatename: str, context: dict[str, Any], doctree: nodes.document | None) -> None:
    """解決済みの設定とページからの相対画像 URL を HTML に埋め込む。"""
    if not _is_revealjs(app):
        return
    page_uri = app.builder.get_target_uri(pagename)
    settings = _settings(app)
    config = {
        'images': {state: relative_uri(page_uri, f'_static/{_ASSET_NAME}/images/{state}.png') for state in STATES},
        'width': settings.width,
        'position': asdict(settings.position),
        'idleTimeout': settings.idle_timeout,
        'toggleKey': settings.toggle_key,
        'defaultActions': DEFAULT_ACTIONS,
    }
    body = json.dumps(config, ensure_ascii=True).replace('<', r'\u003c')
    app.add_js_file(None, body=body, type='application/json', id='sphinx-revealjs-mascot-config')


def _copy_images(app: Sphinx, exception: Exception | None) -> None:
    """成功したビルドへ標準画像の原本をそのままコピーする。"""
    if exception is not None or not _is_revealjs(app):
        return
    destination = Path(app.outdir) / '_static' / _ASSET_NAME / 'images'
    destination.mkdir(parents=True, exist_ok=True)
    for state, source in _settings(app).images.items():
        shutil.copyfile(source, destination / f'{state}.png')


def setup(app: Sphinx) -> ExtensionMetadata:
    """拡張の静的ファイルとページ設定の出力処理を登録する。"""
    app.setup_extension('sphinx_revealjs')
    for name, default in CONFIG_DEFAULTS.items():
        # 既定値からの型推定では小数幅を警告するため、型と範囲はまとめて検証する。
        app.add_config_value(name, default, 'env', types=(cast(type, Any),))
    app.add_node(MascotSettings)
    app.add_node(MascotFragment, html=(visit_fragment, depart_fragment))
    app.add_directive('mascot', MascotDirective)
    app.add_directive('mascot-fragment', MascotFragmentDirective)
    app.connect('doctree-resolved', apply_slide_settings)
    app.connect('builder-inited', _configure_assets)
    app.connect('html-page-context', _page_config)
    app.connect('build-finished', _copy_images)
    return {'env_version': 2, 'parallel_read_safe': True, 'parallel_write_safe': True}
