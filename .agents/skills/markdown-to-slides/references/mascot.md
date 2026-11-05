# sphinx-revealjs-mascot の使い方

## 対象と参照元

本拡張は sphinx-revealjs のスライド上にキャラクターを常駐表示する。スライド本文のデザインや、本文を検出した位置の自動回避は行わない。

- 対象バージョン: sphinx-revealjs-mascot 0.1.1
- 対応内容の基準: `a1cab9b20ccab102edfdf405de70b7ecc4917e71`
- 仕様の正本: [リポジトリの仕様書](https://github.com/in0ho1no/sphinx-revealjs-mascot/blob/develop/docs/SPEC.md)
- この資料の対応時点: [基準コミットの仕様書](https://github.com/in0ho1no/sphinx-revealjs-mascot/blob/a1cab9b20ccab102edfdf405de70b7ecc4917e71/docs/SPEC.md)

以下はスライド作成に必要な使い方の抜粋である。リポジトリ外へコピーしても使えるよう、正本の閲覧なしで基本的な設定と記述ができる範囲を含める。
利用するバージョンが異なる場合や設定を拡張する場合は、利用先の仕様と照合する。

## 有効化

インストール済みの拡張を `conf.py` で有効にする。Markdown を使う場合は MyST-Parser も必要になる。

```python
extensions = ['myst_parser', 'sphinx_revealjs_mascot']
```

`sphinx_revealjs` は本拡張から読み込まれる。
標準キャラクターは同梱されるので、画像・CSS・JavaScript の手動コピーや HTML テンプレートの変更は不要である。
本拡張を有効にして `revealjs` または `dirrevealjs` ビルダーで出力する。

## 全体設定

初期設定のまま利用できる。変更が必要な値だけを `conf.py` に書く。

| 設定名 | 指定方法 |
| --- | --- |
| `revealjs_mascot_position` | `'bottom-right'`、`'bottom-left'`、`'top-right'`、`'top-left'`、または `'70%, 60%'` のような座標 |
| `revealjs_mascot_width` | 画面幅に対する割合を、0より大きく100以下の数値で指定。全スライド共通 |
| `revealjs_mascot_idle_timeout` | ウトウトに入るまでの秒数。正の数値 |
| `revealjs_mascot_toggle_key` | 表示・非表示の切り替えに使う単一の文字キー |
| `revealjs_mascot_image_dir` | 独自画像のフォルダ。相対パスは `conf.py` の場所を基準に解決 |
| `revealjs_mascot_image_pattern` | 独自画像の命名形式。後述の3形式から選ぶ |

標準設定では右下に表示し、対象イベントが45秒発生しないとウトウトする。M キーで表示を切り替える。
位置や表示切り替えを変える例は次のとおり。

```python
revealjs_mascot_position = 'bottom-left'
revealjs_mascot_toggle_key = 'c'
```

表示幅とモーションの細かな既定値はこの資料に転記しない。調整する場合は、利用する版の `config.py` と画面上の描画を確認する。

## スライドごとの指定

MyST Markdown では、スライドの見出し直後に `mascot` を1つ置く。設定そのものは本文に表示されない。

````markdown
## 元資料の見出し

```{mascot}
:action: surprise
:position: bottom-left
```

元資料の内容をここに配置します。
````

- `action` は `idle`・`jump`・`wink`・`surprise` から選ぶ。`doze` と `wake` は内部処理専用なので指定しない。
- `position` は全体設定と同じ形式で指定する。表示位置から向きが自動で決まり、向きを直接指定するオプションはない。
- 位置指定のないスライドは `conf.py` の位置へ戻る。直前のスライドの位置は引き継がない。
- 任意座標は画像の中心位置で、各軸0〜100%。端に近い指定では画像が画面外へ出ることがある。
- スライド単位の幅変更はできない。`width` や `facing` など未提供のオプションを作らない。

reStructuredText を使う既存資料では、同じ内容を次のように指定する。

```rst
元資料の見出し
--------------

.. mascot::
   :action: surprise
   :position: bottom-left

元資料の内容をここに配置します。
```

## 段階表示とリアクション

`mascot-fragment` で囲んだ内容全体が、1つの fragment として表示される。
別々のタイミングで見せる場合は、ブロックを分ける。

````markdown
## 元資料の見出し

```{mascot-fragment}
:action: wink

- 元資料の要点
- 同時に示す要点
```

```{mascot-fragment}
:action: jump

続いて示す内容です。
```
````

fragment に指定できるオプションは `action` だけで、位置はスライドの設定に従う。
reStructuredText では `.. mascot-fragment::` の下に、オプションと本文をインデントする。

アクションを省略すると、前進によるスライド移動は `jump`、fragment の表示は `wink` になる。
アクション指定で元資料にない警告や評価を暗示しない。穏やかに表示したい箇所では `idle` を使う。

後退と fragment の非表示では新しいリアクションを開始しない。
ウトウト中は復帰の `wake` が優先され、そのきっかけのイベントに指定されたアクションは実行されない。
マウス移動だけではウトウトのタイマーはリセットされない。

## 本文と重ならない配置

キャラクターはスライド本文の外側の `document.body` に固定表示され、画面寸法を基準に配置される。
本文は reveal.js の倍率で拡大・縮小されるため、本文の余白とキャラクターの領域は予定する画面比率で確認する。

- 雛形は右側に余白を設け、右下表示を想定する。余白は本文との重なりを自動で保証するものではない。
- キャラクターを左側へ移す場合は、そのスライドの本文を右へ寄せるなど、対応する CSS も調整する。
- 跳躍、回転、呼吸、ウトウト中の「Zzz」まで含めて図表・文字と重ならないようにする。
- 定型位置には画面内に収めるための余白が付く。本文との重なりは利用者側で回避する。
- 画像要素の DOM や拡張の CSS・JavaScript を直接書き換えず、公開された位置・幅設定と本文側のスタイルで調整する。

## 独自キャラクターを指定された場合

通常は標準キャラクターを使う。差し替えを求められた場合だけ、背景透過 PNG の4状態を用意する。
全状態でサイズと立ち位置を揃え、右向きの全身画像とする。

```text
character/
├── normal.png
├── blink.png
├── sleepy.png
└── surprise.png
```

```python
revealjs_mascot_image_dir = 'character'
revealjs_mascot_image_pattern = '{state}.png'
```

命名形式は `'{state}.png'`・`'file-name_{state}.png'`・`'{state}_file-name.png'` の3つ。
後ろ2つの `file-name` は設定値にそのまま書く識別子で、具体名へ置き換えない。
実ファイルの共通名は4状態で揃える。例として `bird_normal.png` などを使うなら、設定は `'file-name_{state}.png'` となる。
画像が欠けたり不正だったりする場合は、標準画像で補完されずビルドエラーになる。

## 動作確認と配布

ビルド方法と全スライドの画像確認は [sphinx-revealjs の作成手順](sphinx-revealjs.md) に従う。
加えて、標準画像または指定した独自画像が表示されること、前進・fragment 表示時のアクション、後退時の位置を確認する。
設定時間を待ってウトウトと復帰を確認し、切り替えキーで非表示・再表示できることも確認する。
再表示では現在のスライドの位置で `idle` に戻る。発表者ノート画面へのキャラクター表示は提供されない。

ビルド出力は HTML・画像・CSS・JavaScript・`third_party/`・ライセンス通知を含む一式で渡す。
標準画像や第三者素材の通知を取り除かない。
