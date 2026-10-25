"""配布物の内容と、チェックアウトに依存しない Sphinx ビルドを確認する。"""

import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

from sphinx_revealjs_mascot.config import STATES

_REPOSITORY = Path(__file__).resolve().parents[2]


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
        for state in STATES:
            assert (
                archive.read(f'{package}/static/sphinx-revealjs-mascot/images/{state}.png')
                == (_REPOSITORY / f'examples/_static/mascot/joubitaki/{state}.png').read_bytes()
            )
        for name in ['README.md', 'manifest.json', 'NOTICES.txt']:
            assert archive.read(f'{package}/third_party/{name}') == (_REPOSITORY / 'third_party' / name).read_bytes()
        assert archive.read(f'{package}/static/sphinx-revealjs-mascot/LICENSE') == (_REPOSITORY / 'LICENSE').read_bytes()
        assert not any('/tests/' in name or '/scripts/' in name for name in archive.namelist())
    with tarfile.open(sdist) as archive:
        prefix = archive.getnames()[0].split('/')[0]
        for relative in ['pyproject.toml', 'docs/SPEC.md', 'third_party/NOTICES.txt', 'examples/_static/mascot/joubitaki/normal.png']:
            member = archive.extractfile(f'{prefix}/{relative}')
            assert member is not None
            assert member.read() == (_REPOSITORY / relative).read_bytes()


@pytest.mark.parametrize('custom', [False, True])
def test_extracted_wheel_builds_without_repository_imports(artifacts: tuple[Path, Path], tmp_path: Path, custom: bool) -> None:
    wheel, _ = artifacts
    site = tmp_path / 'site'
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(site)
    source = tmp_path / 'source'
    source.mkdir()
    config = "extensions = ['sphinx_revealjs_mascot']\n"
    if custom:
        images = source / 'pictures'
        images.mkdir()
        for index, state in enumerate(STATES):
            original_state = STATES[(index + 1) % len(STATES)]
            (images / f'custom_{state}.png').write_bytes((_REPOSITORY / f'examples/_static/mascot/joubitaki/{original_state}.png').read_bytes())
        config += "revealjs_mascot_image_dir = 'pictures'\nrevealjs_mascot_image_pattern = 'file-name_{state}.png'\n"
    (source / 'conf.py').write_text(config, encoding='utf-8')
    (source / 'index.rst').write_text('Package\n=======\n\nSlide\n-----\n\n.. mascot::\n   :position: top-left\n\nText.\n', encoding='utf-8')
    output = tmp_path / 'html'
    bootstrap = (
        'import sys\nfrom pathlib import Path\n'
        f'sys.path.insert(0, {str(site)!r})\n'
        'import sphinx_revealjs_mascot as mascot\n'
        f'assert Path(mascot.__file__).is_relative_to({str(site)!r})\n'
        'from sphinx.cmd.build import main\n'
        f'sys.exit(main({["-W", "-b", "revealjs", str(source), str(output)]!r}))\n'
    )
    result = subprocess.run(
        [sys.executable, '-I', '-X', 'utf8', '-c', bootstrap],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    html = (output / 'index.html').read_text(encoding='utf-8')
    assert 'data-mascot-position="top-left"' in html
    assert (output / 'third_party/NOTICES.txt').read_bytes() == (_REPOSITORY / 'third_party/NOTICES.txt').read_bytes()
    asset_dir = output / '_static/sphinx-revealjs-mascot'
    assert (asset_dir / 'LICENSE').read_bytes() == (_REPOSITORY / 'LICENSE').read_bytes()
    assert (asset_dir / 'STANDARD-IMAGES.md').is_file()
    for state in STATES:
        original = source / f'pictures/custom_{state}.png' if custom else _REPOSITORY / f'examples/_static/mascot/joubitaki/{state}.png'
        assert (asset_dir / f'images/{state}.png').read_bytes() == original.read_bytes()
