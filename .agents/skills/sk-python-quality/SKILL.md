---
name: sk-python-quality
description: >-
  Pythonコードの静的解析を行い品質を確認する。
  「コードをチェックして」「品質確認して」「ruffで見て」「mypyで型チェック」「pyrightで見て」「Lintして」
  「このコード問題ある?」「静的解析して」のようにPythonコードの確認を依頼されたとき、
  またはPythonファイルを開いた状態で品質に関する質問があるときは、
  明示されなくても必ずこのスキルを使うこと。
---

# Python品質チェッカー

ruff・mypy・pyrightを使ってPythonコードを静的解析し、問題点を優先度付きで報告する。

## 対象パスを決める

以下の優先順位で決定する:

| 優先順位 | 条件 | 対象パス |
|---|---|---|
| 1 | ユーザーが明示した | 指定されたパス |
| 2 | 直前に編集操作がある | 編集したファイル(複数なら含む最小ディレクトリ) |
| 3 | `pyproject.toml` に `[tool.ruff] src = [...]` がある | そのパス |
| 4 | `src/` ディレクトリが存在する | `src/` |
| 5 | 上記いずれも該当しない | `.`(カレントディレクトリ) |

対象が広すぎてチェックに時間がかかりそうな場合はユーザーに確認してから実行する。

## 実行環境

[Python 規約](../../../.github/instructions/python.instructions.md) に従い、以下の `<ランナー>` は `uv run` とする。

ツールが見つからない場合は `uv sync --locked` による環境構築状況を確認し、未実行として報告する。依存追加は [共通指示](../../../AGENTS.md) に従う。

pyright は mise で固定した Node.js を PATH から使う。PATH に `node` がないと `nodeenv failed` で失敗する。このとき表示される `pyright[nodejs]` の導入案内には従わず、[README](../../../README.md) の開発の開始に沿って mise の準備状況を確認し、未実行として報告する。

## 実行手順

### ruffでスタイル・バグ検出

```text
<ランナー> ruff check <対象パス>
```

- `--fix` オプションは、品質修正まで依頼されている場合に使用する

### ruffでフォーマットチェック

```text
<ランナー> ruff format --check <対象パス>
```

- ファイルを変更せず、フォーマットが必要なファイル名のみを検出する
- 実際のフォーマット適用(`ruff format`)は、品質修正まで依頼されている場合に実行する

### mypyで型チェック

```text
<ランナー> mypy <対象パス>
```

- `mypy.ini` または `pyproject.toml` の `[tool.mypy]` セクションがあれば自動的に読み込まれる

### pyrightで型チェック

```text
<ランナー> pyright <対象パス>
```

- `pyproject.toml` の `[tool.pyright]` セクションがあれば自動的に読み込まれる

## レポート形式

以下のフォーマットで出力する。問題が0件のセクションは省略してよい。

```markdown
## Python品質チェック結果

### 🔴 ruff check
- `src/main.py:12` E501 行が長すぎます(120文字 > 88文字)
- `src/utils.py:34` F401 `os`がインポートされているが使用されていません

### 🔵 ruff format
- `src/utils.py` フォーマットが必要です

### 🟡 mypy
- `src/main.py:8` error: 引数の型が一致しません (expected "str", got "int")

### 🟡 pyright
- `src/main.py:8` Argument of type "Literal[1]" cannot be assigned to parameter of type "str"

### ✅ サマリー

| ツール        | 件数 |
|---------------|------|
| ruff check    | 2件  |
| ruff format   | 1件  |
| mypy          | 1件  |
| pyright       | 1件  |
```

問題が一切ない場合は「✅ ruff check・ruff format・mypy・pyright ともに問題は検出されませんでした」とだけ出力する。

## 注意事項

- ファイルパスは相対パスで表示する
- ruff check の warning(W系)は🟡で表示し、error(E/F系)は🔴で表示する
- 修正を依頼されていない場合は、自動修正・フォーマットのコマンドを提案するにとどめる
- mypyのエラーが多い場合(20件超)は件数のみ示し、上位5件を抜粋する
- pyrightのエラーが多い場合(20件超)は件数のみ示し、上位5件を抜粋する
