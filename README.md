# sphinx-revealjs-mascot

Sphinx / sphinx-revealjs のスライドにキャラクターを常駐させる拡張です。
CSS・JavaScript・画像の自動組み込み、設定値の検証、専用ディレクティブ、表示位置と向きの切り替えを実装しています。
ユーザーによる確認で、確認用 HTML を直接開いた際の右下へのキャラクター表示を確認済みです。
待機モーション、リアクション、ウトウトと復帰、キーによる表示切り替えも実装済みです。これらの実表示はまだ未確認です。
`src/main.py` と `src/tests/test_main.py` はテンプレートの動作確認用サンプルです。

初期版の仕様と利用サンプルへの案内は [仕様書](docs/SPEC.md) を参照してください。
第三者ライブラリ・同梱素材の表示保持と更新手順は [ライセンスの扱い](third_party/README.md) を参照してください。

## 開発の開始

[pyproject.toml](pyproject.toml) の Python 要件を満たす環境と uv、[mise](https://mise.jdx.dev/) を用意し、リポジトリルートで実行します。

```sh
mise trust
mise install
uv sync --locked
uv run python src/main.py
```

pyright は、[mise.toml](mise.toml) で固定した Node.js を PATH から使います。
mise の shims フォルダ (Windows の既定は `%LOCALAPPDATA%\mise\shims`) を PATH に追加するか、シェルで `mise activate` を有効にしてください。
管理外の Node.js を使わないよう、pyright が Node.js を自動取得する nodeenv は依存から除外しています。
以前に作られた `~/.cache/pyright-python/nodeenv` が残っていると、PATH に `node` がないときにその Node.js が使われるため、削除してください。

Python の規約・品質検証は [共通指示](AGENTS.md) から参照できます。
AI 設定の配置と各ツールでの確認方法は [AI 開発環境](docs/ai-environment.md) を参照してください。

## 依存の更新監視

依存の更新漏れを防ぐため、毎週金曜 17:30 (Asia/Tokyo) に次の確認を行います。

- Dependabot が GitHub Actions・Docker イメージ・Python 依存 (uv) の更新を `develop` 向けの PR にします。
- [Node.js Version](.github/workflows/node-version.yml) が [mise.toml](mise.toml) で固定した Node.js を同じメジャーの最新版と比べ、新しい版があれば Issue を作成・更新します。

定期実行は既定ブランチの `main` に workflow がある場合だけ起動し、`develop` の `mise.toml` を確認します。
手動実行では、選んだブランチの `mise.toml` を確認します。
mise で固定した Node.js は、開発時の pyright の実行に使います。

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
ユーザーによる実表示確認で、左右反転・位置の上書き・既定位置への復帰を確認済みです。
fragment のまとめ表示については、ブラウザでの確認報告はまだありません。

設定 API と画像の命名形式は [仕様書](docs/SPEC.md#extension-configuration) を参照してください。
アクション指定はスライド・fragment のイベントから実行します。

## モーションと状態遷移の確認

ビルド後に上記の HTML を再読み込みして確認します。

1. スライドを操作せず、揺れ・呼吸・ランダムなまばたきを確認する。
2. スライドを進め、指定したアクションと、指定を省略した場合の動作を確認する。
3. fragment を表示し、本文のまとまりと指定したアクションを確認する。
4. スライドを戻る・fragment を非表示にする操作で、新しいリアクションを始めないことを確認する。
5. 設定時間だけ対象イベントを発生させずに待ち、ウトウトと「Zzz」を確認する。続く対象イベントでは復帰を優先する。
6. 設定した表示切り替えキーで非表示にし、スライド移動後に再表示すると、現在の位置設定で通常の待機から再開することを確認する。

設定と既定値、対象イベントの定義は仕様書を参照してください。
表示幅・周期・振れ幅・リアクションの長さは調整前の値です。
自動テストによる状態遷移の検証と、ブラウザでの描画・操作確認は区別して [実装計画](Plan.md) に記録しています。
