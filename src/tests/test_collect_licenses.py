"""HTML と一緒に配布する通知の検証と同梱を確認する。"""

import hashlib
import io
import json
from importlib.metadata import version
from pathlib import Path

import pytest
from sphinx.application import Sphinx

from scripts import collect_licenses


@pytest.fixture
def notice_repository(tmp_path: Path) -> Path:
    root = tmp_path / 'repository'
    notices = root / 'third_party'
    notices.mkdir(parents=True)
    (notices / 'NOTICES.txt').write_bytes(b'original notice\n')
    (notices / 'README.md').write_text('# Notices\n', encoding='utf-8')
    manifest = {
        'source_distribution': {'name': 'sphinx-revealjs', 'version': version('sphinx-revealjs')},
        'notice': {'path': 'NOTICES.txt', 'sha256': hashlib.sha256(b'original notice\n').hexdigest()},
        'components': [{'name': 'example'}],
    }
    (notices / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    return root


def test_export_preserves_original_bytes_and_omits_unrelated_files(notice_repository: Path, tmp_path: Path) -> None:
    (notice_repository / 'third_party/obsolete.txt').write_bytes(b'unrelated')
    destination = tmp_path / 'output'

    collect_licenses.export_notices(notice_repository, destination)

    assert (destination / 'NOTICES.txt').read_bytes() == b'original notice\n'
    assert (destination / 'manifest.json').read_bytes() == (notice_repository / 'third_party/manifest.json').read_bytes()
    assert {path.name for path in destination.iterdir()} == {'README.md', 'manifest.json', 'NOTICES.txt'}


def test_unrelated_lock_update_does_not_invalidate_notices(notice_repository: Path) -> None:
    (notice_repository / 'uv.lock').write_bytes(b'changed-unrelated-dependency')

    collect_licenses.verify(notice_repository)


def test_asset_provider_update_prevents_export(notice_repository: Path, tmp_path: Path) -> None:
    manifest_path = notice_repository / 'third_party/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['source_distribution']['version'] = '0.0.0'
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    destination = tmp_path / 'output'

    with pytest.raises(ValueError, match='同梱素材の通知を再確認'):
        collect_licenses.export_notices(notice_repository, destination)

    assert not destination.exists()


@pytest.mark.parametrize('content', [b'changed notice', None])
def test_missing_or_changed_notice_is_rejected(notice_repository: Path, content: bytes | None) -> None:
    if content is None:
        manifest_path = notice_repository / 'third_party/manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest['notice']['path'] = 'missing.txt'
        manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    else:
        (notice_repository / 'third_party/NOTICES.txt').write_bytes(content)

    with pytest.raises(ValueError, match='欠落・変更'):
        collect_licenses.verify(notice_repository)


def test_notice_cannot_escape_output_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match='フォルダ外'):
        collect_licenses._inside(tmp_path, '../outside.txt')


def test_revealjs_build_includes_third_party_notices(tmp_path: Path) -> None:
    repository = Path(__file__).resolve().parents[2]
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'index.rst').write_text('Example\n=======\n\nSlide\n-----\n\nContent.\n', encoding='utf-8')
    output = tmp_path / 'output'
    warnings = io.StringIO()
    app = Sphinx(
        srcdir=source,
        confdir=repository / 'examples',
        outdir=output,
        doctreedir=tmp_path / 'doctrees',
        buildername='revealjs',
        confoverrides={'extensions': ['sphinx_revealjs'], 'root_doc': 'index'},
        status=io.StringIO(),
        warning=warnings,
        warningiserror=True,
        freshenv=True,
    )

    app.build(force_all=True)

    assert app.statuscode == 0, warnings.getvalue()
    assert (output / 'index.html').is_file()
    assert (output / 'third_party/NOTICES.txt').read_bytes() == (repository / 'third_party/NOTICES.txt').read_bytes()
    assert {path.name for path in (output / 'third_party').iterdir()} == {'README.md', 'manifest.json', 'NOTICES.txt'}
