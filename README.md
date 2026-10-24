# sphinx-revealjs-mascot

Claude Code・Codex・GitHub Copilot を併用する Python 開発環境です。
現在はテンプレートを clone した初期状態で、`src/main.py` と `src/tests/test_main.py` は動作確認用のサンプルです。Sphinx/reveal.js の機能はまだ実装していません。

初期版の仕様と利用サンプルへの案内は [仕様書](docs/SPEC.md) を参照してください。
第三者ライブラリ・同梱素材の表示保持と更新手順は [ライセンスの扱い](third_party/README.md) を参照してください。

## 開発の開始

[pyproject.toml](pyproject.toml) の Python 要件を満たす環境と uv を用意し、リポジトリルートで実行します。

```sh
uv sync --locked
uv run python src/main.py
```

Python の規約・品質検証は [共通指示](AGENTS.md) から参照できます。
AI 設定の配置と各ツールでの確認方法は [AI 開発環境](docs/ai-environment.md) を参照してください。
