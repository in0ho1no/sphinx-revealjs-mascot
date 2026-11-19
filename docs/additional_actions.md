# sphinx-revealjs-mascot 追加状態・アクション拡張仕様

## 1. 背景と目的

[`sphinx-revealjs-mascot`](https://github.com/in0ho1no/sphinx-revealjs-mascot) の現行仕様（[`docs/SPEC.md`](https://github.com/in0ho1no/sphinx-revealjs-mascot/blob/develop/docs/SPEC.md)）では、1体のキャラクターに対して4つの基本状態画像（`normal`, `blink`, `sleepy`, `surprise`）を差し替え、スライド遷移・fragment 表示・無操作タイマーに応じたリアクションを表現している。

本仕様は、導入時の手軽さを損なわないよう**既定の必須画像を従来の4枚のまま維持**しつつ、利用者が追加の状態画像を配置した場合にのみ新たな表情とリアクションを有効化する「オプション状態・追加アクション機構」を定義するものである。

## 2. 前提・基本方針

1. **必須画像は4枚のまま据え置き**: 標準同梱画像およびカスタム画像利用時の必須要件は従来の4枚（`normal`, `blink`, `sleepy`, `surprise`）から増やさない。4枚のみを配置した環境では従来と完全に同一の動作とし、後方互換性を保つ。
2. **追加画像はオプション扱い（部分配置の許容）**: オプション状態画像（`happy`, `tilt`, `trouble`, `proud`）は、画像ディレクトリ内に対応するファイルが存在する場合のみ個別に有効化する。追加画像が0枚の構成、必要な1〜3枚だけを追加した構成（5〜7枚）、全4枚を追加した構成（8枚）のいずれでも動作する。
3. **1体表示アーキテクチャの維持**: 複数キャラクターの同時表示は行わず、単一の `#chara`（`img#chara-img`）の画像差し替えと CSS モーションの組み合わせで表現する。
4. **厳格なビルド時検証の維持**: 対応するオプション画像が未配置であるにもかかわらず、スライド原稿のディレクティブでそのアクションを明示指定した場合は、警告ではなくビルドエラーとする。

## 3. キャラクター画像の要件

### 3.1 状態の区分（必須状態とオプション状態）

キャラクターの状態識別子は、必須4状態（`REQUIRED_STATES`）とオプション4状態（`OPTIONAL_STATES`）に分類する。

| 状態の識別子 | 区分 | 画像・ポーズの表現例（小鳥キャラクターの場合） | 主な用途 |
| :--- | :--- | :--- | :--- |
| `normal` | **必須** | 通常の立ち姿（起きている状態） | 待機（`idle`）、ジャンプ（`jump`） |
| `blink` | **必須** | 目を閉じた立ち姿 | 定期まばたき、ウインク（`wink`） |
| `sleepy` | **必須** | 眠そうな姿・目を閉じてうつむく姿 | 無操作時の居眠り（`doze`） |
| `surprise` | **必須** | 目を丸くして驚いた姿 | 驚き（`surprise`）、居眠りからの復帰（`wake`） |
| `happy` | オプション | 目を細めた笑顔で、両翼を広げて喜ぶ姿 | 感謝、祝福、節目の喜び、明るい結論 |
| `tilt` | オプション | 首をコテンと大きく傾げた姿 | 問いかけ、課題提起、疑問の導入 |
| `trouble` | オプション | 羽を落として困った表情になり、汗粒が浮かぶ姿 | 失敗談、苦労話、トラブルの紹介 |
| `proud` | オプション | 胸を張ってキリッとした目つきになる姿 | 工夫した解決策の提示、達成のアピール、決意表明 |

### 3.2 オプション画像の品質・制作指針

- **外形シルエットによる識別性**: 既定の表示幅（画面幅の `16%`）でも変化が伝わるよう、目の描き込みだけでなく「両翼を上げる（`happy`）」「首を傾ける（`tilt`）」「前かがみになる（`trouble`）」「胸を反らす（`proud`）」など外形シルエット自体に差をつける。
- **左右反転（`scaleX(-1)`）への配慮**: 右側配置（`x` 座標が `50%` 超）では `.facing` 要素に水平反転がかかるため、画像内に「？」などの非対称な文字記号を直接描き込むと鏡文字になる。画像内に含める漫符は汗粒やキラキラなど左右反転しても違和感のない図形にとどめる。
- **キャンバス仕様の統一**: 既存の必須4枚と同一のアスペクト比・キャンバスサイズ・足元基準位置・背景透過 PNG で統一する。

### 3.3 ファイル名の指定と検証（`config.py` / `resources.py`）

[`config.py`](https://github.com/in0ho1no/sphinx-revealjs-mascot/blob/develop/src/sphinx_revealjs_mascot/config.py) の `resolve_images(directory, pattern)` における解決・検証ルールを以下のとおり定める。

1. **標準画像使用時（`revealjs_mascot_image_dir` 未指定時）**:
   - [`resources.py`](https://github.com/in0ho1no/sphinx-revealjs-mascot/blob/develop/src/sphinx_revealjs_mascot/resources.py) が返す標準画像ディレクトリから必須4状態（`REQUIRED_STATES`）を解決する。標準同梱アセットは4枚のままとし、オプション画像の同梱は必須としない。
2. **`pattern` が `'{state}.png'` の場合**:
   - `REQUIRED_STATES` の4ファイルすべてが存在することを検証し、1つでも不足していれば `ConfigError` とする。
   - `OPTIONAL_STATES` についてはディレクトリ内にファイルが存在するものだけを `images` 辞書に取り込む。
3. **`pattern` が `'file-name_{state}.png'` または `'{state}_file-name.png'` の場合**:
   - ディレクトリ内の PNG から共通識別子（`file-name` 部分）ごとに状態をグループ化する。
   - `REQUIRED_STATES` をすべて満たすグループがちょうど1組だけ存在することを検証する（0組または2組以上存在する場合は `ConfigError`）。
   - 特定された1組の `file-name` に対応する `OPTIONAL_STATES` のファイルが存在すれば `images` 辞書に取り込む。異なる `file-name` を持つ孤立した状態画像が混在している場合は、設定ミスを防ぐため `ConfigError` とする。

## 4. アクションとディレクティブの仕様

### 4.1 アクション一覧

[`config.py`](https://github.com/in0ho1no/sphinx-revealjs-mascot/blob/develop/src/sphinx_revealjs_mascot/config.py) の `ACTIONS` に、オプション4状態に対応する明示指定可能なアクションを追加する。

| アクション名 | 内容 | 使用画像 | 継続時間 | モーション | 明示指定 | 利用可能条件 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `idle` | 通常待機 | `normal` | 常時 | 揺れ・呼吸 | 可 | 常時 |
| `jump` | 軽く跳ねる | `normal` | `600ms` | `mascot-jump` | 可 | 常時 |
| `wink` | 目を閉じる | `blink` | `180ms` | なし | 可 | 常時 |
| `surprise` | 驚いて少し拡大する | `surprise` | `700ms` | `mascot-surprise` | 可 | 常時 |
| `happy` | 喜んで弾む | `happy` | `900ms` | `mascot-happy` | 可 | `happy` 画像配置時のみ |
| `tilt` | 首を傾げて静止する | `tilt` | `1100ms` | `mascot-tilt` | 可 | `tilt` 画像配置時のみ |
| `trouble` | 縮こまって小刻みに震える | `trouble` | `900ms` | `mascot-trouble` | 可 | `trouble` 画像配置時のみ |
| `proud` | 胸を張って少し拡大する | `proud` | `900ms` | `mascot-proud` | 可 | `proud` 画像配置時のみ |
| `doze` | 居眠りして揺れる | `sleepy` | 無操作中 | `mascot-doze` | 不可 | 内部制御専用 |
| `wake` | 驚いて飛び起きる | `surprise` | `500ms` | `mascot-wake` | 不可 | 内部制御専用 |

### 4.2 ディレクティブでの検証とエラー条件（`directives.py`）

[`directives.py`](https://github.com/in0ho1no/sphinx-revealjs-mascot/blob/develop/src/sphinx_revealjs_mascot/directives.py) の `.. mascot::` および `.. mascot-fragment::` では、`:action:` オプションに対して以下の2段階検証を行う。

| エラー条件 | 検出タイミング | メッセージの方針 |
| :--- | :--- | :--- |
| 未定義のアクション名、または `explicit=False`（`doze`, `wake`）を指定した | ディレクティブ解析時（`_action`） | 明示指定できないアクションである旨と、指定可能なアクション名一覧を `ExtensionError` で示す |
| オプションアクション（例：`:action: happy`）を指定したが、`settings.images` に対応する `happy` 画像が存在しない | `doctree-resolved`（`apply_slide_settings` および fragment 検証時） | 対象ドキュメント名・行番号とともに、該当アクションの利用には対応する状態画像の配置が必要である旨を `ExtensionError` で示す |

## 5. アセット出力・CSS・JavaScript の仕様

### 5.1 設定 JSON と画像コピー（`__init__.py`）

[`__init__.py`](https://github.com/in0ho1no/sphinx-revealjs-mascot/blob/develop/src/sphinx_revealjs_mascot/__init__.py) のビルド処理を、固定4状態前提から解決済み画像（`settings.images`）基準へ変更する。

- **画像コピー（`_copy_images`）**: `settings.images.items()` を走査し、実際に存在する状態画像のみを出力先の `_static/sphinx-revealjs-mascot/images/{state}.png` にコピーする。
- **ページ埋め込み設定（`_page_config`）**: `#sphinx-revealjs-mascot-config` JSON の `images` には解決済みの状態のみを含め、`actions` には使用画像が `settings.images` に存在するアクション定義のみを含める。
- **環境バージョン**: 保持データの構造変更に伴い、`setup(app)` の `env_version` を更新する。

### 5.2 追加リアクションの CSS モーション（`mascot.css`）

[`mascot.css`](https://github.com/in0ho1no/sphinx-revealjs-mascot/blob/develop/src/sphinx_revealjs_mascot/static/sphinx-revealjs-mascot/mascot.css) の `#chara .react` に対して、追加4アクションのアニメーションを定義する。

- **画面端の見切れ防止（`motionGaps` との整合）**: [`mascot.js`](https://github.com/in0ho1no/sphinx-revealjs-mascot/blob/develop/src/sphinx_revealjs_mascot/static/sphinx-revealjs-mascot/mascot.js) の `layout()` は `--mascot-jump-height`（既定 `0.15`）および `--mascot-surprise-scale`（既定 `1.06`）から表示余白を算出している。追加モーションの移動量・拡大率もこの既存パラメータの範囲内に収め、回転方向には `--mascot-facing` を掛けることで左右どちらの配置でも自然な向きで動作させる。
- **各アニメーションの挙動**:
  - `mascot-happy`: `--mascot-jump-height` の範囲内で軽快に2回跳ねつつ、わずかに左右へ揺れる。
  - `mascot-tilt`: `calc(var(--mascot-facing) * -8deg)` へ首を傾けて一時静止し、終盤で元の角度に戻る。
  - `mascot-trouble`: `scaleY(0.96)` で少し縮こまりながら、水平方向に小刻みに震える。
  - `mascot-proud`: `scale(1.05)` で胸を張るように少し拡大し、元のサイズに戻る。

### 5.3 JavaScript 側の状態制御と外部連携 API（`mascot.js`）

[`mascot.js`](https://github.com/in0ho1no/sphinx-revealjs-mascot/blob/develop/src/sphinx_revealjs_mascot/static/sphinx-revealjs-mascot/mascot.js) は、埋め込まれた JSON に存在する画像・アクションのみをプリロードおよび実行対象とする。また、将来任意の外部スクリプトからマスコットを操作できるよう、最小限の公開 API を `window.RevealMascot` として提供する。

- **`runAction(action)` の保護**: 未登録のアクション名や未ロードの画像を参照した場合は例外を出さずに無視する。
- **外部連携用公開メソッド（`window.RevealMascot`）**:
  - `getAvailableActions()`: 現在配置されている画像セットで実行可能な明示アクション名の配列（例：4枚構成なら `['idle', 'jump', 'wink', 'surprise']`）を返す。
  - `trigger(action, { wakeFromDoze = true } = {})`: マスコットが表示中かつ有効なアクションであれば無操作タイマーをリセットして再生する。`wakeFromDoze` が真のときは、`doze` 居眠り中であっても固定の `wake` ではなく指定された `action` で直接復帰させる。
  - `isVisible()`: 現在の表示・非表示状態（真偽値）を返す。

## 6. 変更対象ファイルと検証範囲

### 6.1 変更対象ファイル一覧

| 対象ファイル | 変更内容 |
| :--- | :--- |
| `src/sphinx_revealjs_mascot/config.py` | `REQUIRED_STATES`・`OPTIONAL_STATES` の定義、`resolve_images` の部分一致対応、`ACTIONS` への4アクション追加 |
| `src/sphinx_revealjs_mascot/directives.py` | `doctree-resolved` 時に指定 `:action:` の必要画像が解決済みか検証し、未配置時に `ExtensionError` を送出 |
| `src/sphinx_revealjs_mascot/__init__.py` | `_page_config` と `_copy_images` を `settings.images` 基準に変更、`env_version` のインクリメント |
| `src/sphinx_revealjs_mascot/static/sphinx-revealjs-mascot/mascot.css` | `happy`, `tilt`, `trouble`, `proud` 用の `[data-state]` セレクタと `@keyframes` の追加 |
| `src/sphinx_revealjs_mascot/static/sphinx-revealjs-mascot/mascot.js` | 有効アクションのみの登録と `window.RevealMascot` 公開インターフェースの追加 |

### 6.2 検証範囲（自動テスト項目）

- 標準画像（`revealjs_mascot_image_dir = None`、4枚構成）のままで従来どおりビルドが成功し、出力 JSON にオプション画像が含まれないこと。
- カスタム画像ディレクトリに必須4枚のみ、必須4枚＋一部オプション画像（例：`happy` のみ計5枚）、必須4枚＋全オプション画像（計8枚）を置いた各ケースで、3種類の命名パターンすべてにおいて正常にビルドできること。
- 必須4枚のいずれかが欠けている場合、または異なる `file-name` の画像が混在している場合に `ConfigError` となること。
- 未配置のオプション画像を必要とする `:action:`（例：`happy` 画像がない状態での `:action: happy`）を `.. mascot::` または `.. mascot-fragment::` に指定した際、`ExtensionError` でビルドエラーになること。
- 配置済みのオプション画像を `:action:` に指定した際、HTML の `data-mascot-action` 属性および埋め込み JSON の `actions`・`images` に正しく出力されること。