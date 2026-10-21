---
applyTo: "src/tests/**/*.py"
description: "Python の pytest ベースのテストファイルを編集・作成するときの補足ルール。"
---

- テストは pytest を使用する
- テストファイル名は test_*.py とする
- テストは読みやすさを優先し、必要な前提だけを明示する
- テスト追加・変更後は必要最小限の pytest を実行して確認する
- 全体の実行コマンドは `uv run pytest` とする。対象の設定は `pyproject.toml` を参照する
