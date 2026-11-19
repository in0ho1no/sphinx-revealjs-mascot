"""reveal.js のスライドへキャラクターを自動で組み込む Sphinx 拡張。"""

import json
import shutil
from collections.abc import Set
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.util.osutil import relative_uri
from sphinx.util.typing import ExtensionMetadata

from sphinx_revealjs_mascot.config import (
    ACTIONS,
    CONFIG_DEFAULTS,
    DEFAULT_ACTIONS,
    MOTION,
    OPTIONAL_STATES,
    REQUIRED_STATES,
    Settings,
    resolve_settings,
)
from sphinx_revealjs_mascot.directives import (
    MascotDirective,
    MascotFragment,
    MascotFragmentDirective,
    MascotSettings,
    apply_slide_settings,
    check_action_images,
    depart_fragment,
    visit_fragment,
)
from sphinx_revealjs_mascot.notices import export_notices, verify
from sphinx_revealjs_mascot.resources import ASSET_NAME as _ASSET_NAME
from sphinx_revealjs_mascot.resources import STATIC_DIR as _STATIC_DIR
from sphinx_revealjs_mascot.resources import notice_root, project_license, standard_image_directory

_STATE_RECORD = '.sphinx-revealjs-mascot.json'


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
    verify(notice_root())
    app.env.domaindata[_ASSET_NAME] = {'settings': resolve_settings(app.config, Path(app.confdir), standard_image_directory())}
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
        'images': {state: relative_uri(page_uri, f'_static/{_ASSET_NAME}/images/{state}.png') for state in settings.images},
        'width': settings.width,
        'position': asdict(settings.position),
        'idleTimeout': settings.idle_timeout,
        'toggleKey': settings.toggle_key,
        'defaultActions': DEFAULT_ACTIONS,
        'actions': {name: asdict(definition) for name, definition in ACTIONS.items() if definition.image in settings.images},
        'motion': MOTION,
    }
    body = json.dumps(config, ensure_ascii=True).replace('<', r'\u003c')
    app.add_js_file(None, body=body, type='application/json', id='sphinx-revealjs-mascot-config')


def _image_destination(app: Sphinx) -> Path:
    """状態画像の出力先を返す。"""
    return Path(app.outdir, '_static', _ASSET_NAME, 'images')


def _check_actions(app: Sphinx, doctree: nodes.document, docname: str) -> None:
    """スライド・fragment に指定したアクションの状態画像が解決済みか検証する。"""
    if _is_revealjs(app):
        check_action_images(doctree, docname, _settings(app).images)


def _state_record(app: Sphinx) -> Path:
    """HTML に埋め込んだ状態の記録ファイルを返す。"""
    return Path(app.outdir, _STATE_RECORD)


def _recorded_states(app: Sphinx) -> set[str] | None:
    """前回成功したビルドの記録から状態の集合を読む。記録がない・壊れている場合は None を返す。"""
    try:
        record = json.loads(_state_record(app).read_text(encoding='utf-8'))
    except OSError, ValueError:
        return None
    states = record.get('states') if isinstance(record, dict) else None
    if not isinstance(states, list) or not all(isinstance(state, str) for state in states):
        return None
    return set(states)


def _outdated_by_images(app: Sphinx, env: BuildEnvironment, added: Set[str], changed: Set[str], removed: Set[str]) -> list[str]:
    """利用できる状態が前回の成功したビルドから変わった場合、全ページを読み直して指定を再検証する。"""
    if not _is_revealjs(app):
        return []
    # 環境は書き出しの前に保存され、失敗したビルドでも更新済みになるため、成功したビルドの最後に書く記録と比べる。
    # 出力先に残った画像から推測すると、画像を一部消した場合に前回の HTML の構成と食い違う。
    # 記録がなく前回の構成を確認できない場合も、既存ページの指定を見逃さないよう全ページを読み直す。
    if _recorded_states(app) == set(_settings(app).images):
        return []
    # 記録を残したまま書き出しが中断すると、元の構成に戻した次のビルドで記録と一致し、一部のページだけが別の構成のまま残る。
    # 成功したビルドの最後に書き直すまで記録を取り除き、中断後のビルドでも全ページを読み直す。
    _state_record(app).unlink(missing_ok=True)
    return sorted(env.found_docs)


def _copy_images(app: Sphinx, exception: Exception | None) -> None:
    """成功したビルドへ選択した画像と配布用の通知をコピーする。"""
    if exception is not None or not _is_revealjs(app):
        return
    destination = _image_destination(app)
    destination.mkdir(parents=True, exist_ok=True)
    images = _settings(app).images
    # 前回のビルドで出力した画像は上書きされずに残る。
    # 利用者が静的ファイルとして同じフォルダへ置いた画像を消さないよう、削除は解決しなかった状態名の画像に限る。
    for state in REQUIRED_STATES + OPTIONAL_STATES:
        if state not in images:
            (destination / f'{state}.png').unlink(missing_ok=True)
    for state, source in images.items():
        shutil.copyfile(source, destination / f'{state}.png')
    shutil.copyfile(project_license(), destination.parent / 'LICENSE')
    shutil.copyfile(standard_image_directory() / 'README.md', destination.parent / 'STANDARD-IMAGES.md')
    export_notices(notice_root(), Path(app.outdir) / 'third_party')
    # 出力が途中で失敗した場合に次のビルドで全ページを読み直すよう、記録は最後に更新する。
    _state_record(app).write_text(json.dumps({'states': list(images)}), encoding='utf-8')


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
    # スライド設定の統合で設定ノードが取り除かれる前に、行番号付きで検証する。
    app.connect('doctree-resolved', _check_actions, priority=400)
    app.connect('doctree-resolved', apply_slide_settings)
    app.connect('builder-inited', _configure_assets)
    app.connect('env-get-outdated', _outdated_by_images)
    app.connect('html-page-context', _page_config)
    app.connect('build-finished', _copy_images)
    return {'env_version': 5, 'parallel_read_safe': True, 'parallel_write_safe': True}
