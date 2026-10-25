"""HTML に同梱する素材の通知を検証してコピーする。"""

import argparse
import sys
from pathlib import Path


def main() -> None:
    """ネットワークを使わず同梱素材の通知を検証する。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='同梱素材の通知を検証する（既定の動作）')
    parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'src'))
    from sphinx_revealjs_mascot.notices import verify

    manifest = verify(root)
    print(f'{len(manifest["components"])} bundled components: verified')


if __name__ == '__main__':
    main()
