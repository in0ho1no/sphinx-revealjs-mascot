# sphinx-revealjs-mascot

Sphinx / sphinx-revealjs のスライドにキャラクターを常駐させる拡張です。
CSS・JavaScript・画像の自動組み込み、設定値の検証、専用ディレクティブ、表示位置と向きの切り替えを実装しています。
ユーザーによる確認で、確認用 HTML を直接開いた際の右下へのキャラクター表示を確認済みです。
モーションとリアクション、キーによる表示切り替えは未実装です。
`src/main.py` と `src/tests/test_main.py` はテンプレートの動作確認用サンプルです。

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

## 最小構成のビルド

必要な依存が導入済みの環境で、リポジトリルートから実行します。
このコマンドは依存の追加・更新・同期を行いません。

```sh
uv run --frozen --no-sync --offline sphinx-build -W -b revealjs -c examples -D root_doc=index examples/minimal examples/_build/minimal
```

出力した `examples/_build/minimal/index.html` をブラウザで直接開いて確認します。
下位フォルダのページは `examples/_build/minimal/nested/second.html` です。
HTML 出力フォルダは、画像・CSS・JavaScript・`third_party` を含む一式で扱います。

この段階の拡張はソースから参照し、標準画像は既存の原本から自動コピーします。
パッケージのインストールによる利用は未対応です。
表示幅は調整・確定前の仮値です。進捗と検証結果は [実装計画](Plan.md) を参照してください。

## 設定と本文指定のサンプル

既存の Markdown と reStructuredText のサンプルもビルドできます。

```sh
uv run --frozen --no-sync --offline sphinx-build -W -b revealjs examples examples/_build/revealjs
```

`examples/_build/revealjs/slides.html` でスライドごとの位置・向きと、指定のないスライドでの既定位置への復帰を確認できます。
戻る操作でも移動先の位置を使います。
`examples/_build/revealjs/fragments.html` では、ディレクティブで囲んだ段落・箇条書きをまとめて段階表示します。
今回の変更のブラウザでの実表示は未確認です。

設定 API と画像の命名形式は [仕様書](docs/SPEC.md#extension-configuration) を参照してください。
アクション指定は HTML の属性へ出力します。リアクション、無操作タイマー、表示切り替えキーの動作は次の実装段階で追加します。
