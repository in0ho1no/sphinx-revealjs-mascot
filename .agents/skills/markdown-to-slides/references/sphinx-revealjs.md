# sphinx-revealjs での作成手順

## 対象環境と参照元

この参照資料は Sphinx 9.2.0、sphinx-revealjs 3.2.1、MyST-Parser 5.1.0 を対象とする。
記法は sphinx-revealjs のディレクティブと MyST の fenced directive を使用する。

- [sphinx-revealjs の公式ドキュメント](https://sphinx-revealjs.readthedocs.io/en/stable/)
- [MyST のディレクティブ](https://myst-parser.readthedocs.io/en/latest/syntax/roles-and-directives.html)
- [reveal.js の発表者ノート](https://revealjs.com/speaker-view/)

バージョンが異なる場合は、利用先の設定とインストール済みパッケージの仕様を確認する。
本拡張は `sphinx-revealjs` の版番号ではなく、同梱される静的素材の内容を検証する。素材が確認済みの内容と異なる場合はビルドが失敗するため、ライセンス通知の確認が必要である。
このファイルと [キャラクター拡張の参照資料](mascot.md)、[雛形](../assets/starter/) は SKILL と一緒に持ち運べる。元リポジトリのディレクトリ構成を前提としない。

## 雛形と依存

本拡張と組み合わせる場合は `assets/starter/` の中身を、元資料を上書きしない作業先へコピーする。

```text
slides/
├── conf.py
├── index.md
└── _static/
    └── slides.css
```

雛形はインストール済みの `sphinx_revealjs_mascot` と `myst_parser` を読み込む。
本拡張から `sphinx_revealjs` も読み込まれるため、利用先の `src/` を `sys.path` に追加する必要はない。
本拡張を使わない場合は、`extensions` の `sphinx_revealjs_mascot` を `sphinx_revealjs` に置き換え、`mascot` 系のディレクティブとキャラクター用の余白を取り除く。

環境には本拡張、Sphinx、sphinx-revealjs、Markdown 用の MyST-Parser が必要である。
本拡張 0.1.2 の Python 要件は3.14以上。利用先の依存管理を確認し、不足する依存を無断で追加しない。
MyST-Parser は本拡張の実行時依存には含まれない。拡張は提供された wheel などから導入し、PyPI での公開を前提にしない。

雛形の `conf.py` は日本語、ローカル CSS、1280×720のスライド基準寸法、発表者ノート用のプラグインを設定する。
CSS の登録には `revealjs_static_path` と `revealjs_css_files` を使う。
`html_static_path` はこのビルダーの初期化時に置き換えられるため、通常の Sphinx HTML 用設定だけを転用しない。

## Markdown とスライドの境界

MyST は Markdown ファイルをビルド時に HTML へ変換する。ブラウザ側の Markdown プラグインや専用の区切り記法を混ぜない。

雛形では `#` を資料タイトル、`##` を各スライドの見出しに使う。
`###` は縦方向のスライドになるため、本文の小見出しとして安易に残さない。より深い見出しを含む元資料は、順序と階層の意味を保ちながら `##` のスライドへ展開する。
Markdown の `---` は、そのままではスライド区切りにならない。

```markdown
# 資料タイトル

## 最初の話題

- 元資料の要点

## 次の話題

- 続く要点
```

1つの Markdown ファイルが1つの HTML ページになる。単一の発表なら `index.md` にまとめ、`root_doc = 'index'` とする。
別ファイルに分ける場合は、ファイル間のリンクと発表時の移動方法も確認する。

## ノートと段階表示

発表者ノートには `revealjs-notes` を使う。通常の Markdown コメントをノートとして扱う設定には依存しない。

````markdown
## 元資料の見出し

スライド上に残す要点です。

```{revealjs-notes}
元資料にある補足説明をここへ移します。
```
````

ノートは HTML の `aside.notes` に出力され、通常のスライド本文には表示されない。
ノート画面を開くには、雛形のように `RevealNotes` プラグインを登録する。
ノートは閲覧者にも成果物から読めるため、非公開情報の保管場所として扱わない。

本拡張を有効にしている場合、`revealjs-fragments` の表示時も、キャラクターの既定アクションは `wink` になる。
アクションを指定するには [mascot-fragment](mascot.md) を使う。既定の `wink` を抑えたい場合は `:action: idle` を指定して通常の待機状態にする。
ウトウト中の `wake` が優先される場合など、実行条件は参照先を確認する。
元資料にない説明順序を演出のために作らず、段階表示が説明に役立つ場合だけ適用する。

## CSS と図表

- 日本語フォントは雛形のローカルフォント候補から選び、確認する環境にインストールされているものを使う。CDN や外部フォントを追加しない。
- CSS では `1pt = 4/3px` なので、24pt は32 CSS pxに相当する。雛形の本文は36px、コード・表は32pxを基準にする。
- reveal.js は基準寸法から表示倍率を変える。CSS の指定値だけで可読性を判断せず、予定する画面サイズで確認し、小さければ内容を分割する。
- `fit-text` など文字を自動縮小する仕組みで、内容過多を解決しない。
- 雛形の背景・文字・強調は `#ffffff`・`#1f2937`・`#0759b5`。色を変える場合は、使用する文字色と背景の組み合わせのコントラストを再確認する。
- 図はローカルの SVG または画像ファイルにし、MyST の `image` / `figure` で参照する。Markdown に Mermaid のコードを書くだけで描画されるとは扱わない。
- SVG 内のフォント、文字サイズ、数値と単位も検査する。別途ツールや拡張が必要な場合は、利用先の導入状況と承認を確認する。

## ビルドと描画確認

依存が準備済みの uv プロジェクトから実行する。`slides` はコピー先、`slides/_build/revealjs` は出力先の例である。
利用先の構成に合わせてパスを置き換える。

```shell
uv run --frozen --no-sync --offline sphinx-build -E -W --keep-going -b revealjs slides slides/_build/revealjs
```

このコマンドは依存の追加・更新・同期を行わない。ビルドの成功はレイアウトや動作の確認とは区別する。

1. `index.html` をブラウザで開き、スライド枚数、順序、画像・CSS・キャラクターの読み込みを確認する。
2. 同じウィンドウ寸法で各スライドを表示し、スクリーンショットを保存して全枚確認する。fragment の途中と全表示も確認する。
3. 図表、長いコード、日本語の折り返し、フォントの字形、余白とキャラクターの重なりを確認する。
4. 前進・後退と段階表示を操作し、ノートに移した内容も元資料と照合する。

発表者ノートの動作確認にはローカル HTTP サーバーを使う。`file://` でのスライド表示と、別ウィンドウのノート画面の動作は分けて確認する。

```shell
uv run --frozen --no-sync --offline python -m http.server 8000 --bind 127.0.0.1 --directory slides/_build/revealjs
```

`http://127.0.0.1:8000/index.html` を開き、S キーでノート画面を確認する。ポップアップが制限されている場合はブラウザの状態を確認する。
確認後は起動したサーバーを停止する。

## 成果物

編集用の `conf.py`・Markdown・CSS・図表と、ビルド出力フォルダ一式を渡す。
HTML 単体では `_static/` などの依存ファイルが欠ける。本拡張が出力する `third_party/` とライセンス通知も保持する。
スクリーンショットなどの検査結果は、納品するスライドのソースと区別して扱う。
