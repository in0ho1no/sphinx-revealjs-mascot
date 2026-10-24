"""利用サンプルで共用する Sphinx 設定。仕様の正本は docs/SPEC.md。"""

import sys
from pathlib import Path

from sphinx.application import Sphinx

project = 'sphinx-revealjs-mascot examples'
extensions = ['sphinx_revealjs', 'myst_parser', 'sphinx_revealjs_mascot']
root_doc = 'slides'
language = 'ja'
exclude_patterns = ['_build']


def _export_notices(app: Sphinx, exception: Exception | None) -> None:
    """成功したビルドへ第三者ライセンスを同梱する。"""
    if exception is not None:
        return
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from scripts.collect_licenses import export_notices

    export_notices(root, Path(app.outdir) / 'third_party')


def setup(app: Sphinx) -> None:
    """配布用通知を同梱する処理を登録する。"""
    app.connect('build-finished', _export_notices)
