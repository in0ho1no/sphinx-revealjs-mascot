# sphinx-revealjs-mascot

Sphinx / sphinx-revealjs のスライドにキャラクターを常駐させる拡張です。
CSS・JavaScript・標準画像を自動で組み込み、スライドや fragment の進行に合わせてキャラクターを動かします。

- スライドごとの表示位置と、位置に応じた向きの切り替え
- 待機モーション、リアクション、ウトウトと復帰
- キーによる表示・非表示の切り替え、独自キャラクターへの差し替え

## 拡張を利用する <a id="extension-usage"></a>

配布された wheel を、利用先の Sphinx プロジェクトへ導入します。uv を使う環境では、例えば次のように指定します。
Python 要件と実行時依存は wheel のメタデータに含まれます。ソースから wheel を作成する手順は [配布パッケージの作成](docs/development.md#distribution-build) を参照してください。

```sh
uv add /path/to/sphinx_revealjs_mascot-0.1.1-py3-none-any.whl
```

利用先の `conf.py` で拡張を有効にします。`sphinx_revealjs` は本拡張から読み込みます。

```python
extensions = ['sphinx_revealjs_mascot']
```

標準キャラクターはパッケージに同梱します。ソースリポジトリのパス指定や、CSS・JavaScript・画像の手動コピーは不要です。
Markdown で記述する場合は、利用先に MyST-Parser も導入し、`extensions` に `myst_parser` を追加します。
設定・専用ディレクティブ・独自画像の要件は [仕様書](docs/SPEC.md) を参照してください。

ビルドした HTML は、画像・CSS・JavaScript・`third_party/`・ライセンス通知を含む出力フォルダ一式で配布します。
第三者ライブラリ・同梱素材の表示保持と更新手順は [ライセンスの扱い](third_party/README.md) を参照してください。

## AI で Markdown をスライドにする <a id="ai-slide-authoring"></a>

用意済みの Markdown をスライドへ変換する [markdown-to-slides SKILL](.agents/skills/markdown-to-slides/SKILL.md) を用意しています。
元資料の意味と順序を保つ変換ルール、図表・デザインの方針、完成前の検査手順をまとめています。内容の企画や構成の提案は対象外です。

| ファイル・フォルダ | 役割 |
| --- | --- |
| [SKILL.md](.agents/skills/markdown-to-slides/SKILL.md) | 出力形式に共通する変換方針と、参照資料を読む条件 |
| [references/sphinx-revealjs.md](.agents/skills/markdown-to-slides/references/sphinx-revealjs.md) | MyST の記法、ビルド、ノート、描画・操作の確認方法 |
| [references/mascot.md](.agents/skills/markdown-to-slides/references/mascot.md) | 本拡張の設定、ディレクティブ、キャラクターと本文の配置 |
| [assets/starter/](.agents/skills/markdown-to-slides/assets/starter/) | 日本語表示・発表者ノート・キャラクター用の余白を備えた雛形 |

AI には、元資料と使用する形式を指定して依頼します。

```text
.agents/skills/markdown-to-slides/SKILL.md を読み、source.md を
sphinx-revealjs と sphinx-revealjs-mascot を使うスライドへ変換してください。
編集用ソースとビルド出力一式を slides/ に用意してください。
```

別プロジェクトへ持ち運ぶ場合のコピー範囲と読み込み方法は [SKILL の持ち運び](docs/ai-environment.md#portable-slide-skill) を参照してください。
拡張と Markdown 用の依存は利用先で準備します。ビルドの成功と、ブラウザでの描画・操作の確認は区別してください。

## 最小構成のビルド <a id="minimal-build"></a>

リポジトリのサンプルで動作を確認できます。[開発環境を準備](docs/development.md#setup) した後、リポジトリルートから実行します。
このコマンドは依存の追加・更新・同期を行いません。

```sh
uv run --frozen --no-sync --offline sphinx-build -W -b revealjs -c examples -D root_doc=index examples/minimal examples/_build/minimal
```

`examples/_build/minimal/index.html` をブラウザで直接開きます。下位ページは `examples/_build/minimal/nested/second.html` です。
設定・段階表示・表示位置のサンプルと、モーションの詳しい確認手順は [開発と検証](docs/development.md) を参照してください。

## 開発の開始

環境構築、Node.js の PATH、テスト・品質検証、配布物の作成、依存の更新監視は [開発と検証](docs/development.md) にまとめています。
依存・Python 要件・検証設定の正本は [pyproject.toml](pyproject.toml) です。

| 文書 | 内容 |
| --- | --- |
| [仕様書](docs/SPEC.md) | 動作、利用者向け設定、既定値、エラー条件 |
| [実装・検証の記録](docs/Plan.md) | 設計判断と自動テスト・ブラウザ確認の範囲 |
| [共通指示](AGENTS.md) | 作業規約と Python・Markdown の規約への参照 |
| [AI 開発環境](docs/ai-environment.md) | 各 AI ツールの入口、SKILL の持ち運び、フックの配置と検証 |

## リリース

`pyproject.toml` のバージョンに対応する `v` で始まるタグ (例: `v0.1.1`) を push すると、GitHub Actions がタグのコミットから wheel とソース配布物をビルドし、両方を draft GitHub Release に添付します。
Release を公開するまでは、リポジトリへのアクセス権がある人だけが配布物を取得できます。PyPI への公開は行いません。
