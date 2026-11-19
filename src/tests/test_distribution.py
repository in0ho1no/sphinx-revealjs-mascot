"""配布物の内容と、チェックアウトに依存しない Sphinx ビルドを確認する。"""

import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

from sphinx_revealjs_mascot.config import OPTIONAL_STATES, REQUIRED_STATES

_REPOSITORY = Path(__file__).resolve().parents[2]
_STANDARD_IMAGES = 'examples/_static/mascot/joubitaki'
_STANDARD_FILES = [f'{state}.png' for state in REQUIRED_STATES + OPTIONAL_STATES] + ['README.md']


@pytest.fixture(scope='module')
def artifacts(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    destination = tmp_path_factory.mktemp('distribution')
    result = subprocess.run(
        ['uv', '--cache-dir', str(_REPOSITORY / '.uv_cache'), 'build', '--offline', '--no-build-isolation', '--out-dir', str(destination)],
        cwd=_REPOSITORY,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return next(destination.glob('*.whl')), next(destination.glob('*.tar.gz'))


def test_wheel_and_sdist_preserve_assets_and_original_notices(artifacts: tuple[Path, Path]) -> None:
    wheel, sdist = artifacts
    package = 'sphinx_revealjs_mascot'
    with zipfile.ZipFile(wheel) as archive:
        for name in _STANDARD_FILES:
            assert archive.read(f'{package}/images/{name}') == (_REPOSITORY / _STANDARD_IMAGES / name).read_bytes()
        assert not [name for name in archive.namelist() if name.startswith(f'{package}/static/') and name.endswith('.png')]
        for name in ['README.md', 'manifest.json', 'NOTICES.txt']:
            assert archive.read(f'{package}/third_party/{name}') == (_REPOSITORY / 'third_party' / name).read_bytes()
        assert archive.read(f'{package}/static/sphinx-revealjs-mascot/LICENSE') == (_REPOSITORY / 'LICENSE').read_bytes()
        assert not any('/tests/' in name or '/scripts/' in name for name in archive.namelist())
    with tarfile.open(sdist) as archive:
        prefix = archive.getnames()[0].split('/')[0]
        for relative in ['pyproject.toml', 'docs/SPEC.md', 'third_party/NOTICES.txt', *(f'{_STANDARD_IMAGES}/{name}' for name in _STANDARD_FILES)]:
            member = archive.extractfile(f'{prefix}/{relative}')
            assert member is not None
            assert member.read() == (_REPOSITORY / relative).read_bytes()


def _extract_wheel(wheel: Path, site: Path) -> Path:
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(site)
    return site


def _build_with_wheel(site: Path, source: Path, output: Path) -> subprocess.CompletedProcess[str]:
    bootstrap = (
        'import sys\nfrom pathlib import Path\n'
        f'sys.path.insert(0, {str(site)!r})\n'
        'import sphinx_revealjs_mascot as mascot\n'
        f'assert Path(mascot.__file__).is_relative_to({str(site)!r})\n'
        'from sphinx.cmd.build import main\n'
        f'sys.exit(main({["-W", "-b", "revealjs", str(source), str(output)]!r}))\n'
    )
    return subprocess.run(
        [sys.executable, '-I', '-X', 'utf8', '-c', bootstrap],
        cwd=site.parent,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=False,
        timeout=120,
    )


@pytest.mark.parametrize('custom', [False, True])
def test_extracted_wheel_builds_without_repository_imports(artifacts: tuple[Path, Path], tmp_path: Path, custom: bool) -> None:
    site = _extract_wheel(artifacts[0], tmp_path / 'site')
    source = tmp_path / 'source'
    source.mkdir()
    config = "extensions = ['sphinx_revealjs_mascot']\n"
    if custom:
        images = source / 'pictures'
        images.mkdir()
        for index, state in enumerate(REQUIRED_STATES):
            original_state = REQUIRED_STATES[(index + 1) % len(REQUIRED_STATES)]
            (images / f'custom_{state}.png').write_bytes((_REPOSITORY / _STANDARD_IMAGES / f'{original_state}.png').read_bytes())
        config += "revealjs_mascot_image_dir = 'pictures'\nrevealjs_mascot_image_pattern = 'file-name_{state}.png'\n"
    (source / 'conf.py').write_text(config, encoding='utf-8')
    (source / 'index.rst').write_text('Package\n=======\n\nSlide\n-----\n\n.. mascot::\n   :position: top-left\n\nText.\n', encoding='utf-8')
    output = tmp_path / 'html'
    result = _build_with_wheel(site, source, output)
    assert result.returncode == 0, result.stdout + result.stderr
    html = (output / 'index.html').read_text(encoding='utf-8')
    assert 'data-mascot-position="top-left"' in html
    assert (output / 'third_party/NOTICES.txt').read_bytes() == (_REPOSITORY / 'third_party/NOTICES.txt').read_bytes()
    asset_dir = output / '_static/sphinx-revealjs-mascot'
    assert (asset_dir / 'LICENSE').read_bytes() == (_REPOSITORY / 'LICENSE').read_bytes()
    assert (asset_dir / 'STANDARD-IMAGES.md').is_file()
    states = REQUIRED_STATES if custom else REQUIRED_STATES + OPTIONAL_STATES
    for state in states:
        original = source / f'pictures/custom_{state}.png' if custom else _REPOSITORY / _STANDARD_IMAGES / f'{state}.png'
        assert (asset_dir / f'images/{state}.png').read_bytes() == original.read_bytes()
    assert {path.name for path in (asset_dir / 'images').glob('*.png')} == {f'{state}.png' for state in states}


def test_failed_build_keeps_previously_written_images(artifacts: tuple[Path, Path], tmp_path: Path) -> None:
    site = _extract_wheel(artifacts[0], tmp_path / 'site')
    source = tmp_path / 'source'
    pictures = source / 'pictures'
    pictures.mkdir(parents=True)
    for state in (*REQUIRED_STATES, 'happy'):
        (pictures / f'{state}.png').write_bytes(f'custom {state}'.encode())
    (source / 'conf.py').write_text("extensions = ['sphinx_revealjs_mascot']\nrevealjs_mascot_image_dir = 'pictures'\n", encoding='utf-8')
    (source / 'index.rst').write_text('Package\n=======\n\nSlide\n-----\n\n.. mascot::\n   :action: happy\n\nText.\n', encoding='utf-8')
    output = tmp_path / 'html'
    first = _build_with_wheel(site, source, output)
    assert first.returncode == 0, first.stdout + first.stderr
    images = output / '_static/sphinx-revealjs-mascot/images'
    record = output / '.sphinx-revealjs-mascot.json'
    written = {path.name: path.read_bytes() for path in images.iterdir()}
    assert record.is_file()
    (pictures / 'happy.png').unlink()
    second = _build_with_wheel(site, source, output)
    assert second.returncode != 0
    assert "アクション 'happy' には状態画像 'happy' が必要です" in second.stdout + second.stderr
    assert {path.name: path.read_bytes() for path in images.iterdir()} == written
    # 構成の変化で全ページを書き直す途中で失敗したため、次回も全ページを読み直すよう記録は残さない。
    assert not record.exists()
