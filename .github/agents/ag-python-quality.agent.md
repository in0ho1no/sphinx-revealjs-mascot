---
name: Python Quality
model: Claude Sonnet 5 (copilot)
description: >-
  Pythonコードの静的解析と自動修正を行うエージェント。
  「品質チェックして直して」「ruffとmypyで修正まで」「エラーを全部直して」
  のように品質チェックと修正を一括で依頼されたときに使うこと。
tools:
  - execute
  - read
  - edit
  - search
argument-hint: >-
  対象パス（省略時は src/）、修正してよい範囲（型・スタイルのみ、など）を指定する
---

作業開始時に [共通の役割・手順](../../.agents/roles/python-quality.md) を読み、定義された方針に従う。
