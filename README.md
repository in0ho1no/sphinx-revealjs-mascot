# sphinx-revealjs-mascot

Sphinx / sphinx-revealjs のスライドにキャラクターを常駐させる拡張です。
CSS・JavaScript・画像の自動組み込み、設定値の検証、専用ディレクティブ、表示位置と向きの切り替えを実装しています。
待機モーション、リアクション、ウトウトと復帰、キーによる表示切り替えも実装済みです。

初期版の仕様と利用サンプルへの案内は [仕様書](docs/SPEC.md) を参照してください。
第三者ライブラリ・同梱素材の表示保持と更新手順は [ライセンスの扱い](third_party/README.md) を参照してください。

## 開発の開始

[pyproject.toml](pyproject.toml) の Python 要件を満たす環境と uv、[mise](https://mise.jdx.dev/) を用意し、リポジトリルートで実行します。
手元と CI で使う Python は、[.python-version](.python-version) で 3.14 系に揃えています。

```sh
mise trust
mise install
uv sync --locked
```

準備後は、下記の「最小構成のビルド」または「テストと品質検証」を実行します。
VS Code の「Python デバッガー: サンプルのビルド」でも Sphinx ビルドを実行できます。

pyright と pytest は、[mise.toml](mise.toml) で固定した Node.js を PATH から使います。
mise の shims フォルダ (Windows の既定は `%LOCALAPPDATA%\mise\shims`) を PATH に追加するか、シェルで `mise activate` を有効にしてください。
管理外の Node.js を使わないよう、pyright が Node.js を自動取得する nodeenv は依存から除外しています。
PATH に `node` がない場合、pyright は `nodeenv failed` で失敗します。表示される `pyright[nodejs]` の導入案内には従わず、PATH を確認してください。
以前に作られた `~/.cache/pyright-python/nodeenv` が残っていると、PATH に `node` がないときにその Node.js が使われるため、削除してください。

Python の規約・品質検証は [共通指示](AGENTS.md) から参照できます。
AI 設定の配置と各ツールでの確認方法は [AI 開発環境](docs/ai-environment.md) を参照してください。

## テストと品質検証

リポジトリルートで実行します。

```sh
uv run pytest
```

pytest は、ブラウザ用スクリプトの状態遷移テスト [test_mascot_runtime.cjs](src/tests/test_mascot_runtime.cjs) も、固定した Node.js で実行します。
PATH に `node` がない場合や、`node` の版が `mise.toml` と異なる場合は、テストを失敗にします。
静的解析の手順は [sk-python-quality](.agents/skills/sk-python-quality/SKILL.md) を参照してください。

pull request と `develop` への push では、[Tests](.github/workflows/tests.yml) が依存を同期し、ruff・mypy・pyright・pytest を実行します。
`tests` は `develop` の必須チェックです。必須チェックの設定は [gh-RequiredCI.json](git-setup/gh-RequiredCI.json) を正本とし、[gh-enable-push-protection-win.bat](git-setup/gh-enable-push-protection-win.bat) で GitHub に反映します。

## 依存の更新監視

uv による依存解決には、[pyproject.toml](pyproject.toml) の `exclude-newer` で公開後の待機期間を設けています。
待機設定の導入で既存環境を巻き戻さないよう、一部の依存には確認済みの版の公開日時を上限とする一時例外があります。
待機期間が満了した後は `exclude-newer-package` の該当する例外を解除し、lockfile を更新してください。
例外が残っている間、その日時より後に公開された対象パッケージは選択されません。解除日は設定のコメントを参照してください。

依存の更新漏れを防ぐため、毎週金曜 17:30 (Asia/Tokyo) に次の確認を行います。

- Dependabot が GitHub Actions・Docker イメージ・Python 依存 (uv) の更新を `develop` 向けの PR にします。
- [Node.js Version](.github/workflows/node-version.yml) が [mise.toml](mise.toml) で固定した Node.js を同じメジャーの最新版と比べ、新しい版があれば Issue を作成・更新します。

Node.js の更新確認は開発用依存の Requests を使い、Tests と同じ `uv.lock` に従った環境で実行します。
取得先は公式の HTTPS URL に固定し、証明書検証・タイムアウトを有効にします。リダイレクトは追従せず、環境由来の認証情報・CA・プロキシ設定は使用しません。

定期実行は既定ブランチの `main` に workflow がある場合だけ起動し、`develop` の `mise.toml` を確認します。
手動実行では、選んだブランチの `mise.toml` を確認します。
Tests でも同じ確認を行い、新しい版があれば失敗にせず警告を表示します。

## 最小構成のビルド

必要な依存が導入済みの環境で、リポジトリルートから実行します。
このコマンドは依存の追加・更新・同期を行いません。

```sh
uv run --frozen --no-sync --offline sphinx-build -W -b revealjs -c examples -D root_doc=index examples/minimal examples/_build/minimal
```

出力した `examples/_build/minimal/index.html` をブラウザで直接開いて確認します。
下位フォルダのページは `examples/_build/minimal/nested/second.html` です。
HTML 出力フォルダは、画像・CSS・JavaScript・`third_party` を含む一式で扱います。

開発用サンプルはソースから参照し、標準画像は既存の原本から自動コピーします。
別の Sphinx プロジェクトでは、下記の配布パッケージを利用できます。
表示幅とモーションは現在の値を初版の既定値としています。確認範囲と保守上の判断は [実装・検証の記録](docs/Plan.md) を参照してください。

## 設定と本文指定のサンプル

既存の Markdown と reStructuredText のサンプルもビルドできます。

```sh
uv run --frozen --no-sync --offline sphinx-build -W -b revealjs examples examples/_build/revealjs
```

`examples/_build/revealjs/slides.html` でスライドごとの位置・向きと、指定のないスライドでの既定位置への復帰を確認できます。
戻る操作でも移動先の位置を使います。
`examples/_build/revealjs/fragments.html` では、ディレクティブで囲んだ段落・箇条書きをまとめて段階表示します。

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
表示幅・周期・振れ幅・リアクションの長さは現在の値を初版の既定値としています。
自動テストとブラウザでの描画・操作の確認範囲は、[実装・検証の記録](docs/Plan.md) を参照してください。

## 表示幅と余白の確認

`examples/_build/revealjs/positions.html` に、四隅と任意座標を切り替えるサンプルがあります。
定型位置の余白は画像の実寸とモーションの最大変位から計算し、「Zzz」も含めて画面内に収めます。
指定幅では収まらない場合は表示幅に上限を適用します。この上限は任意座標を含む全スライドで共通です。
任意座標では、指定した中心位置から画像の一部が画面外に出ることを許容します。

横長の画面や大きな幅を確認する場合は、別の出力先へビルドします。`25` は確認用の値です。

```sh
uv run --frozen --no-sync --offline sphinx-build -E -W -b revealjs -D revealjs_mascot_width=25 examples examples/_build/wide
```

## 配布パッケージの作成と利用

開発環境を準備済みの状態で、wheel とソース配布物を作成します。依存の追加・更新・同期は行いません。

```sh
uv build --offline --no-build-isolation
```

`dist/` に生成された wheel を別の Sphinx プロジェクトへ渡し、利用者がその環境で導入します。
たとえば uv を使う環境では `uv add /path/to/sphinx_revealjs_mascot-0.1.0-py3-none-any.whl` を実行します。
Python 要件と実行時依存は wheel のメタデータに含まれます。

利用先の `conf.py` では、拡張を有効にします。`sphinx_revealjs` は本拡張から読み込みます。

```python
extensions = ['sphinx_revealjs_mascot']
```

標準キャラクターはパッケージに同梱します。独自キャラクターを使う場合は、利用先で4状態の画像を用意し、仕様書の画像設定を指定します。
ソースリポジトリのパス指定や、CSS・JavaScript・画像の手動コピーは不要です。
ビルドした HTML には MIT License、標準画像の説明、第三者素材の通知も自動で出力します。HTML 出力フォルダ一式を配布してください。

自動テストでは wheel を一時フォルダへ展開し、チェックアウトを参照せずに標準画像・独自画像それぞれの Sphinx ビルドを確認します。
別環境へのインストールとブラウザでの実表示は、このテストの対象外です。
