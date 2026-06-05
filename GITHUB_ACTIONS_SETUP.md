# GitHub Actions 月次自動実行 セットアップ手順

このリポジトリは毎月**第2営業日**に、SNS収集→分類→分析→戦略→レポートの
パイプライン（`scripts/monthly_pipeline.py`）を **GitHub上で自動実行**します。
ワークフロー定義: [`.github/workflows/monthly-pipeline.yml`](.github/workflows/monthly-pipeline.yml)

ローカルPCを起動していなくても、クラウド上で自動的に毎月回り、生成データを
`main` ブランチへ自動コミット → Streamlit Cloud が再デプロイ、という流れになります。

---

## ✅ 動かすために必要な作業（初回のみ）

### 1. GitHub Secrets にAPIキーを登録する

APIキーはリポジトリには**含めません**（`.env` は追跡解除済み）。
GitHubの暗号化Secretsに登録します。

1. ブラウザで以下を開く:
   `https://github.com/hashiken-minmax/CHRO-Strategic-Insight-Engine/settings/secrets/actions`
2. **New repository secret** を押し、下表の Name と Value を1つずつ登録する。
   （Value はローカルの `.env` に入っている実際の値）

| Secret 名 | 必須 | 用途 |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ 必須 | ②情報分類（Claude）|
| `LINKUPAPI_KEY` | ✅ 必須 | ①LinkedIn収集 |
| `LINKUPAPI_LOGIN_TOKEN` | ✅ 必須 | ①LinkedIn収集（ログイントークン）|
| `EXA_API_KEY` | 任意 | ①公開コンテンツ検索 |
| `COMPOSIO_API_KEY` | 任意 | ①エージェント連携 |
| `TWITTER_BEARER_TOKEN` | 任意 | ①X(Twitter)収集 |
| `TWITTER_API_KEY` | 任意 | 〃 |
| `TWITTER_API_SECRET` | 任意 | 〃 |
| `TWITTER_ACCESS_TOKEN` | 任意 | 〃 |
| `TWITTER_ACCESS_TOKEN_SECRET` | 任意 | 〃 |

> 「任意」のSecretは未登録でも動作します（該当する収集ステップがスキップされるだけ）。

### 2. ワークフローの書き込み権限を確認する

`https://github.com/hashiken-minmax/CHRO-Strategic-Insight-Engine/settings/actions`
→ **Workflow permissions** が **Read and write permissions** になっていることを確認。
（生成データを `main` にコミットするために必要。なっていなければ変更して保存）

---

## 🔴 セキュリティ是正（必ず実施）

`.env`（本番APIキー入り）が初回コミットでGit履歴に入り、GitHubへプッシュ済みです。
追跡解除しても**過去のコミット履歴にはキーが残る**ため、漏洩前提で
**各キーをローテーション（再発行＋旧キー無効化）してください。**

| プロバイダ | 再発行場所 |
|---|---|
| Anthropic | https://console.anthropic.com/settings/keys （旧キーをRevoke→新規発行）|
| LinkupAPI | https://app.linkupapi.com → API Access → API Keys |
| Exa.ai | https://dashboard.exa.ai |
| Composio | https://dashboard.composio.dev |

新しいキーを発行したら、
1. ローカルの `.env` を新キーに更新（`.env` は今後コミットされません）
2. 上記 **GitHub Secrets** も新キーに更新

---

## ▶️ 実行タイミングと手動実行

- **自動**: 毎月1〜6日の朝(JST)に見張りが起動し、**第2営業日のその1日だけ**本体が実行されます。
  第2営業日以外は数秒で終了し、API課金・コミットは発生しません（=二重実行されません）。
- **手動（今すぐ試す / 過去月を埋める）**:
  `https://github.com/hashiken-minmax/CHRO-Strategic-Insight-Engine/actions`
  → **Monthly CHRO Pipeline** → **Run workflow**
  - `force` を **true** にすると第2営業日でなくても即実行
  - `period` に `202605` のように入れるとその月を対象に実行（空欄なら前月）

> 例: 今欠けている **2026年5月分** を埋めるには、`force=true` / `period=202605` で手動実行。

---

## 🔁 仕組みのポイント

- cronは「毎月1〜6日」に絞ってあるため、無駄な空起動は月3〜4回の軽い判定のみ。
- 実処理（API課金が発生する①〜⑤）は `should_run_today()` を通った**月1回だけ**。
- `TZ=Asia/Tokyo` 設定により第2営業日判定は日本時間基準。
- 生成データに差分が無ければコミットしない（空コミットを作らない）。
- scheduled workflow は **mainブランチにある時のみ**起動します。
