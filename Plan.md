# 初期版の実装計画

## 目的と進行状況

仕様検討と画像制作が完了した状態から、Sphinx 拡張の初期版を段階的に実装する。
まず CSS・JavaScript・画像の自動組み込みと、ビルドした HTML の `file://` による直接表示を確認する。

最小構成の実装と、それに必要な `examples/conf.py` の設定変更は承認済みである。
最小構成の実装・ビルド・自動検証まで完了している。ブラウザでの実表示確認はユーザーが行う。
後続機能の実装にはまだ着手していない。

## 正本と適用する指示

- 作業規約: [AGENTS.md](AGENTS.md)
- 動作・設定・既定値・エラー条件: [docs/SPEC.md](docs/SPEC.md)
- プロジェクトの現状と開始方法: [README.md](README.md)
- 依存・Python 要件・検証設定: [pyproject.toml](pyproject.toml)
- 固定バージョン: [uv.lock](uv.lock)
- 同梱素材の通知と配布手順: [third_party/README.md](third_party/README.md)
- Python の作成・編集: [.github/instructions/python.instructions.md](.github/instructions/python.instructions.md)
- テストの作成・編集: [.github/instructions/python-tests.instructions.md](.github/instructions/python-tests.instructions.md)
- Markdown の作成・編集: [.github/instructions/markdown.instructions.md](.github/instructions/markdown.instructions.md)
- Python 品質検証: [.agents/skills/sk-python-quality/SKILL.md](.agents/skills/sk-python-quality/SKILL.md)

本計画には仕様や設定の既定値を複写せず、各正本を参照する。

## 確認済みの事項

- 初回調査時点では拡張本体は未実装だった。`src/main.py` と対応するテストはテンプレートのサンプルである。
- 実行用依存と Python 品質検証ツールは既存環境に導入されている。
- `pyproject.toml` には配布用の `[build-system]` がない。
- [examples/conf.py](examples/conf.py) は拡張の登録を記述済みだが、未実装のためサンプル全体のビルドは未確認である。
- [examples/slides.md](examples/slides.md) と [examples/fragments.rst](examples/fragments.rst) に専用ディレクティブの利用例がある。
- `examples/_static/mascot/joubitaki/` の画像4枚を実際に確認した。すべて同じ寸法の透過 PNG で、右向きの表情差分として利用できる。
- [scripts/collect_licenses.py](scripts/collect_licenses.py) とサンプルの `build-finished` 処理に、通知の検証・コピー機構がある。
- 既存のライセンス検証は `6 bundled components: verified` で成功した。
- ブラウザによる表示確認はまだ行っていない。

## 実装方針

- 仕様の再検討から始めず、既存仕様に沿って実装する。
- Python 側の設定定義を実行時の一元的な管理箇所とし、解決済みの値を JavaScript に渡す。サンプルに既定値を複写しない。
- ブラウザ用の設定は HTML に埋め込み、通常の JavaScript として読み込む。
- 既存画像を唯一の原本とし、配布先・ビルド出力への取り込みは自動化する。画像の再生成や手作業での重複管理は行わない。
- ライセンス通知の既存処理とテストを引き継ぐ。Python の推移依存全体を収集する構成へ戻さない。
- 表示幅やモーションの細かな値は、実表示を確認して調整する。
- 依存の追加・更新・同期・インストールは行わない。必要になった時点で実装を中断し、必要性とコマンドを先に提示する。インストールはユーザーが行う。
- ファイル削除が必要になった場合は対象パスを示し、ユーザーに判断を委ねる。

## 最小構成の確認

- [x] `src/sphinx_revealjs_mascot/` に拡張の入口と静的ファイルを追加する。
- [x] `examples/conf.py` に、開発中の拡張をソースから参照する設定を加える。
- [x] 拡張が CSS・JavaScript・画像を自動でビルド出力へ組み込む処理を実装する。
- [ ] 専用ディレクティブを使わない最小ソースで、reveal.js と拡張の初期化タイミングを確認する。
- [ ] ビルド出力の HTML を `file://` で直接開き、キャラクターが表示されることを確認する。
- [x] 通知が出力に同梱されることを確認する。

この段階は既存依存とソース参照で進め、配布用ビルドバックエンドの追加は行わない。
表示の確認結果を記録してから、後続機能の実装に進む。

### 最小構成の検証結果

2026-10-25 に実施した検証結果を記録する。

- `examples/minimal/` に、専用ディレクティブを使わない reStructuredText と Markdown の最小ソースを追加した。
- README に記載した最小構成のビルドは、`-W` による警告のエラー扱いで成功した。
- pytest は全体で `12 passed`。`sphinx-revealjs` 内部の非推奨 API 使用による警告が1件ある。
- 新しいビルドテストでは `revealjs` と `dirrevealjs` の出力を確認した。下位フォルダのページも含め、CSS・JavaScript の参照先がローカルに存在することを検証した。
- 各ページへ埋め込んだ画像 URL の参照先と、原本4枚とのバイト単位の一致を確認した。
- 既存の通知検証とコピー処理を維持し、ビルド出力への同梱を確認した。通知検証は `6 bundled components: verified` だった。
- `src/` と `examples/conf.py` の ruff check・ruff format のチェック・mypy・pyright はすべて成功した。
- 既存環境の Node.js による `node --check` で JavaScript の構文確認が成功した。拡張のビルド・利用には Node.js を要求しない。
- JavaScript は DOM の読み込み完了と reveal.js の準備完了を待つ構成にしたが、ブラウザでの初期化タイミングは未確認である。
- Chrome の操作は Computer Use のアクセス承認で拒否された。ツールの応答は `Computer Use was not approved to use Google Chrome` だった。
- Chrome・Edge での実表示、画像の向き・大きさ、スライド操作、実行時のネットワーク要求、投影・画面共有は未確認である。

再現用のビルドコマンドと出力先は README を参照する。
表示幅は Python 側の仮値として管理し、ブラウザ確認後に調整・確定する。

## 設定と本文指定の実装

- [ ] 設定の登録・検証と、独自画像セットの検出・エラー処理を実装する。
- [ ] `mascot` と `mascot-fragment` を実装する。
- [ ] スライド単位の指定と、複数の内容をまとめた fragment が正しく HTML に反映されることを確認する。
- [ ] 表示位置、スライドごとの上書きと既定位置への復帰を実装する。
- [ ] 初期表示・スライド移動・再表示時に、適用位置から左右の向きを決める。
- [ ] 文字・記号を左右反転の対象から分離する。
- [ ] 既存の Markdown と reStructuredText のサンプルをビルドする。

## モーションと状態遷移の実装

- [ ] 揺れ・呼吸・ランダムなまばたきを実装する。
- [ ] 各リアクションと、スライド・fragment のイベント処理を実装する。
- [ ] 無操作タイマー、ウトウト、復帰を実装する。
- [ ] 最新のアクションへの切り替えと、以前の完了処理の取り消しを実装する。
- [ ] 戻る操作と fragment の非表示時の処理を実装する。
- [ ] キーによる表示切り替え、非表示中の停止、再表示時の再初期化を実装する。

詳細な条件と優先順位は仕様書に従う。

## 調整・検証・配布設定

- [ ] 標準画像で表示幅・余白・モーションを調整し、決定した既定値を仕様書に反映する。
- [ ] 設定・画像の異常系、ディレクティブ、ビルド出力、状態遷移について影響範囲に応じたテストを行う。
- [ ] 既存のライセンス関連テストと通知検証を実行する。
- [ ] `sk-python-quality` に従い、ruff check・ruff format のチェック・mypy・pyright を実行する。
- [ ] Chrome と Edge で `file://` の直接表示と操作を確認する。
- [ ] ブラウザごとの確認範囲と、投影・画面共有などの未確認範囲を明示する。
- [ ] 配布パッケージ化に必要なビルドバックエンド、画像取り込み方法、設定変更案を具体化する。
- [ ] ビルド用依存が必要な場合は、必要性とコマンドを提示し、ユーザーによる導入を待つ。
- [ ] 配布物に拡張のコード・CSS・JavaScript・標準画像が含まれることを確認する。
- [ ] 実装結果に合わせて README の現状・開始方法を更新する。

実行可能な検証では `uv run --frozen --no-sync --offline` を使用し、依存の自動同期を避ける。
検証対象とコマンドは各段階の変更範囲に合わせて選ぶ。

## 承認が必要な範囲

最小構成の実装と `examples/conf.py` の設定変更は承認済みである。
ブラウザでの実表示確認はユーザーが担当するため、Chrome 操作のアクセス承認は求めない。
[AGENTS.md](AGENTS.md) の、大きな変更と設定ファイル変更に関する事前確認の規定は引き続き適用する。

その後も、依存追加、破壊的変更、複数ファイルにまたがる大規模リファクタ、未承認の設定・開発フロー変更が必要になった場合は、実施前に確認する。
