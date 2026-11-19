"""インストール先または開発用チェックアウトから同梱素材を参照する。"""

from pathlib import Path

ASSET_NAME = 'sphinx-revealjs-mascot'
PACKAGE_DIR = Path(__file__).resolve().parent
STATIC_DIR = PACKAGE_DIR / 'static'


def standard_image_directory() -> Path:
    """配布物の標準画像、または開発中の画像原本の所在を返す。"""
    # 静的ファイルのフォルダに置くと、Sphinx が検証の前に一括コピーし、失敗したビルドでも出力済みの画像を上書きする。
    bundled = PACKAGE_DIR / 'images'
    if bundled.is_dir():
        return bundled
    return PACKAGE_DIR.parents[1] / 'examples/_static/mascot/joubitaki'


def notice_root() -> Path:
    """第三者通知フォルダを含むパッケージまたはチェックアウトを返す。"""
    if (PACKAGE_DIR / 'third_party').is_dir():
        return PACKAGE_DIR
    return PACKAGE_DIR.parents[1]


def project_license() -> Path:
    """同梱または原本のプロジェクトライセンスを返す。"""
    bundled = STATIC_DIR / ASSET_NAME / 'LICENSE'
    if bundled.is_file():
        return bundled
    return PACKAGE_DIR.parents[1] / 'LICENSE'
