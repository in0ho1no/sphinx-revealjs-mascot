# AI 開発環境

## 正本と入口

共通情報は正本を直接編集します。各ツールの入口には参照と、そのツールでだけ必要なメタデータを置きます。生成コピーやシンボリックリンクの準備は不要です。

| 情報 | 正本 | 読み込みの入口 |
| --- | --- | --- |
| プロジェクトの現状・開始方法 | [README.md](../README.md) | 共通指示から参照 |
| 共通の作業規約 | [AGENTS.md](../AGENTS.md) | Codex は自動読み込み、Claude は [.claude/CLAUDE.md](../.claude/CLAUDE.md) の import、Copilot は [.github/copilot-instructions.md](../.github/copilot-instructions.md) の参照 |
| ファイル種別の規約 | [.github/instructions/](../.github/instructions/) | Copilot は `applyTo`、他のツールは共通指示から参照 |
| スキルの手順 | [.agents/skills/](../.agents/skills/) | Codex/Copilot のスキル検出、Claude は [.claude/skills/](../.claude/skills/) の参照 |
| レビュー・品質修正の方針 | [.agents/roles/](../.agents/roles/) | 共通指示、および各ツールの `agents/` の参照 |
| フックの検査・引数正規化・テスト | [.github/hooks/](../.github/hooks/) | Copilot の hook JSON、Claude の [.claude/hooks/](../.claude/hooks/) のアダプター |
| 依存・静的解析・テストの設定 | [pyproject.toml](../pyproject.toml) | 各ツールの標準的な設定読み込み |

スキルの `name` は呼び出し互換性のため、Claude の入口にも必要です。入口の短い `description` は検出用で、実行手順はリンク先にだけ保持します。`context: fork` など Claude 固有の設定は Claude の入口に限定します。
Copilot が複数の対応ディレクトリから同名スキルを候補表示する場合も、どの入口からも同じ正本へ到達します。旧 `.github/skills/` の本文コピーは保持しません。

レビュー・品質修正の `agents/` は、各ツールの名前・モデル・利用可能ツールの指定を維持しています。Codex では共通指示から役割文書を読みます。Claude/Copilot の agent 定義を Codex 用の設定として読み込ませる必要はありません。

## 権限制御とフック

Claude Code は [.claude/settings.json](../.claude/settings.json)、Copilot は [pre-tool-use.json](../.github/hooks/pre-tool-use.json) と [post-tool-use.json](../.github/hooks/post-tool-use.json) から共通検査を呼び出します。フック起動時には、PATH 上で uv コマンドを実行できる必要があります。  
Claude のプロジェクト環境変数による実行ガードを維持し、共通の監査ログ出力先は `.github/logs/audit.log` です。必要なら `HOOK_LOG_PATH` で変更できます。

これらのフックは Codex へ自動適用されません。Codex は実行環境の sandbox・承認設定と、共通指示に従って作業します。共通指示の参照はフックと同等の強制制御を保証しません。Codex の個人設定や権限を、リポジトリから上書きする設定は追加していません。

## 検証

リポジトリルートから実行します。

```sh
uv run python scripts/check_ai_environment.py
uv run python scripts/check_ai_environment.py --hooks
```

通常の検証はローカル参照、スキル入口、JSON 設定、Python の構文を確認します。`--hooks` は既存のフック回帰検査も実行し、正常・危険入力、両ツールの入力形式、patch 引数、日本語・文字コード、不正入力、監査ログの秘匿を確認します。テストに渡したシェルコマンドや patch 自体は実行しません。
[AI Environment ワークフロー](../.github/workflows/ai-environment.yml) でも同じコマンドを実行します。

各製品の実際の読み込みは、新しいセッションで確認してください。

- Codex: 読み込んだ指示の一覧を尋ね、ルートの `AGENTS.md` と参照先が認識されることを確認する。スキル一覧で `.agents/skills/` のスキルを確認する。
- Claude Code: `/memory` で共通指示の import、スキル一覧で各入口を確認する。
- Copilot: 応答の参照一覧で repository instructions を確認し、共通指示の参照とスキル候補を確認する。

ローカルの構造検証・フック検査は、各製品の認証済みセッションでの読み込み確認を代替しません。

## 配置の根拠

- [Codex の AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [Codex のスキル配置](https://developers.openai.com/codex/skills)
- [Claude Code の import](https://code.claude.com/docs/en/memory)
- [Claude Code のスキル](https://code.claude.com/docs/en/skills)
- [Copilot のスキル配置](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
