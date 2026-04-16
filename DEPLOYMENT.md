# CHRO Strategic Insight Engine - Web Deployment Guide

このドキュメントでは、CHRO Strategic Insight Engine ダッシュボードをWebに公開する手順を説明します。

---

## 🚀 デプロイメント方法（推奨: Streamlit Cloud）

### ステップ 1: GitHub リポジトリの準備

```bash
# リポジトリを初期化
git init
git add .
git commit -m "Initial commit: CHRO Strategic Insight Engine"
git remote add origin https://github.com/YOUR_USERNAME/CHRO-Strategic-Insight-Engine.git
git push -u origin main
```

### ステップ 2: Streamlit Cloud でのデプロイ

1. **Streamlit Cloud アカウント作成**
   - https://streamlit.io/cloud にアクセス
   - GitHubアカウントで登録

2. **新しいアプリをデプロイ**
   - "New app" をクリック
   - リポジトリを選択: `CHRO-Strategic-Insight-Engine`
   - ブランチ: `main`
   - メインファイル: `dashboard.py`
   - "Deploy" をクリック

3. **アプリが起動** (~2-3分)
   - 公開URL: `https://share.streamlit.io/YOUR_USERNAME/CHRO-Strategic-Insight-Engine/main/dashboard.py`

### ステップ 3: アクセス制御の設定

**読み取り専用アクセスの有効化:**
1. Streamlit Cloud のアプリ設定で「Share」をクリック
2. 「Public」または「Viewer mode」を選択
3. URLを共有（閲覧のみ可能）

**編集権限の管理:**
- GitHub リポジトリで:
  - Settings → Collaborators → 信頼できるユーザーのみを追加
  - Main ブランチは保護ルールを設定（Pull Request レビュー必須）

---

## 📊 代替デプロイ方法

### Heroku でのデプロイ（無料枠廃止、有料）
```bash
# Heroku CLI をインストール後
heroku login
heroku create your-app-name
git push heroku main
```

### Docker + AWS/GCP でのデプロイ
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "dashboard.py"]
```

---

## 🔐 セキュリティ設定

### 1. secrets.toml による機密情報管理
Streamlit Cloud で使用する場合は `.streamlit/secrets.toml` を作成:
```toml
[database]
user = "your_username"
password = "your_password"
```

GitHub には **絶対にコミットしないこと！**

### 2. 環境変数の設定
Streamlit Cloud の設定で環境変数を追加:
- Settings → Secrets → キーと値を入力

### 3. GitHub Token（必要な場合）
プライベートデータへのアクセスが必要な場合:
```bash
# .streamlit/secrets.toml に追加
github_token = "ghp_xxxxxxxxxxxx"
```

---

## 📈 データ更新方法

### 月次データの追加
1. 新しい期間のデータを集計
2. 以下ファイルを生成:
   - `data/classified_data_202605.json`
   - `data/analytics_phaseA_202605.json`
   - `data/analytics_phaseB_202605.json`
   - `data/analytics_phaseC_202605.json`

3. リポジトリに追加:
```bash
git add data/
git commit -m "Add data for 2026-05 period"
git push origin main
```

4. Streamlit Cloud が自動で再デプロイ

### 自動デプロイの無効化
- Streamlit Cloud 設定で「Rerun script on file change」を無効化

---

## 🧪 ローカル確認

デプロイ前にローカルでテスト:
```bash
streamlit run dashboard.py
```

ブラウザで `http://localhost:8501` を開く

---

## 📋 チェックリスト

- [ ] GitHub リポジトリを作成
- [ ] `requirements.txt` がすべての依存関係を含む
- [ ] `.streamlit/config.toml` が設定済み
- [ ] `.gitignore` で `secrets.toml` と `data/*.docx` を除外
- [ ] ローカルで `streamlit run dashboard.py` で動作確認
- [ ] Streamlit Cloud アカウントを作成
- [ ] アプリをデプロイ
- [ ] 公開URLにアクセス確認
- [ ] GitHub コラボレーター設定（信頼できるユーザーのみ）
- [ ] 月次データ更新プロセスをテスト

---

## 🆘 トラブルシューティング

### 「ModuleNotFoundError: No module named 'streamlit'」
```bash
pip install -r requirements.txt
```

### Streamlit Cloud でデータが見つからない
```bash
# ファイルパスをチェック
# ローカルパスではなく相対パスを使用
Path("data") ✓
Path(__file__).parent / "data" ✓
```

### 日本語が文字化けする
```python
# ファイル先頭に追加
# -*- coding: utf-8 -*-
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

---

## 📞 サポート

- Streamlit Community: https://discuss.streamlit.io
- GitHub Issues: https://github.com/your-username/repo/issues
- Email: your-email@example.com

---

**最終更新:** 2026-04-17
