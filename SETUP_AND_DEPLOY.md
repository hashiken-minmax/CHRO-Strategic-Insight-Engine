# 🚀 GitHub & Streamlit Cloud デプロイ手順

このドキュメントは、**ユーザーが実施すべき最小限の手順**を記載しています。

---

## 📋 前提条件

以下が準備されていることを確認してください：

- ✅ Git がインストール済み (または GitHub Desktop)
- ✅ GitHub アカウント を保有
- ✅ Streamlit Cloud アカウント を作成済み (https://streamlit.io/cloud)

---

## 🔧 ステップ 1: GitHub リポジトリを作成（ユーザー作業）

**所要時間: 2分**

1. https://github.com/new にアクセス
2. 以下を入力:
   - **Repository name**: `CHRO-Strategic-Insight-Engine`
   - **Description**: `Global CHRO SNS Analysis Platform`
   - **Visibility**: `Public` (読み取り専用アクセス用)
3. 「Create repository」をクリック

**作成後、表示されるコマンドをメモ** (以下のステップで使用)

---

## 💻 ステップ 2: ローカルから GitHub へプッシュ（ユーザー作業）

**所要時間: 3分**

コマンドプロンプトで実行:

```bash
cd C:\Users\hashi\Documents\CHRO-Strategic-Insight-Engine

# Git 初期化
git init

# GitHub の新リポジトリをリモートとして追加
git remote add origin https://github.com/YOUR_USERNAME/CHRO-Strategic-Insight-Engine.git
git branch -M main

# 全ファイルをステージング
git add .

# コミット
git commit -m "Initial commit: CHRO Strategic Insight Engine - Context-based analysis platform"

# GitHub へプッシュ
git push -u origin main
```

**完了後:** GitHub リポジトリにファイルが反映される

---

## 🌐 ステップ 3: Streamlit Cloud でデプロイ（ユーザー作業）

**所要時間: 5分**

1. https://streamlit.io/cloud にアクセス
2. GitHub アカウントで **Sign in** をクリック
3. GitHub で認可を許可
4. Streamlit Cloud ダッシュボードで **「New app」** をクリック
5. 以下を設定:
   - **Repository**: `YOUR_USERNAME/CHRO-Strategic-Insight-Engine`
   - **Branch**: `main`
   - **Main file path**: `dashboard.py`
6. 「Deploy」をクリック

**待機: 2-3分 でアプリが起動**

```
🎉 デプロイ完了！

公開 URL:
https://share.streamlit.io/YOUR_USERNAME/CHRO-Strategic-Insight-Engine/main/dashboard.py
```

---

## 🔐 ステップ 4: アクセス制御設定（ユーザー作業）

**所要時間: 2分**

### A) 自分の編集権限を保持

GitHub > Settings > Collaborators で確認（デフォルトは自分が所有者）

### B) 他人に読み取り専用アクセスを付与

**方法 1: 公開 URL を共有（最も簡単）**
```
https://share.streamlit.io/YOUR_USERNAME/CHRO-Strategic-Insight-Engine/main/dashboard.py
```
- 誰でもアクセス可
- 閲覧のみ（編集不可）

**方法 2: GitHub で Collaborator として追加**
1. GitHub > Settings > Collaborators
2. 「Add people」をクリック
3. GitHub ユーザー名を入力
4. 権限を「Read」に設定（編集不可）

---

## ✅ 動作確認

公開 URL にアクセスして以下を確認：

- [ ] ダッシュボードが起動
- [ ] 5つのタブが表示（SNS情報、Context×Activity、キーワード、統合分析、ビジネス機会）
- [ ] SNS Summary 表に LinkedIn/X の数が表示
- [ ] すべてのテキストが日本語で表示
- [ ] グラフが正常にレンダリング

---

## 📊 月次データ更新手順

新しい期間のデータを追加する場合：

```bash
# 1. 新しい期間のデータファイルを data/ に配置
#    - classified_data_202605.json
#    - analytics_phaseA_202605.json
#    - analytics_phaseB_202605.json
#    - analytics_phaseC_202605.json

# 2. ローカルで動作確認
streamlit run dashboard.py

# 3. GitHub へプッシュ
git add data/
git commit -m "Add analytics for 2026-05 period"
git push origin main

# 4. Streamlit Cloud が自動で再デプロイ（2-3分待機）
```

---

## 🆘 トラブルシューティング

### Q: 「ModuleNotFoundError」が出る
**A:** `requirements.txt` が自動インストールされています。1-2分待ってページをリロード

### Q: 日本語が文字化けしている
**A:** Streamlit Cloud を再起動
- Streamlit Cloud ダッシュボード > App menu > Reboot app

### Q: データが更新されない
**A:** キャッシュをクリア
- Streamlit Cloud ダッシュボード > App menu > Clear cache

### Q: URL にアクセスできない
**A:** Streamlit Cloud ダッシュボードで「Manage app」 > 再起動

---

## 📞 サポート

問題が発生した場合：
1. Streamlit Cloud ダッシュボードのログを確認
2. GitHub リポジトリで Issue を作成
3. Streamlit コミュニティに質問: https://discuss.streamlit.io

---

## 🎯 完了チェックリスト

```
デプロイ前：
□ Git がインストール済み
□ GitHub アカウント作成
□ Streamlit Cloud アカウント作成

GitHub 設定：
□ リポジトリ作成
□ git push 実行
□ GitHub にファイルが反映されたことを確認

Streamlit Cloud：
□ 「New app」で デプロイ
□ 公開 URL が生成された
□ ダッシュボードが起動

アクセス制御：
□ 公開 URL を共有 または Collaborator を追加
□ 他人がアクセス可能なことを確認

動作確認：
□ ダッシュボードすべてのタブが表示可
□ データが正しく表示
□ 日本語テキストが正常

完了！
```

---

**最終更新:** 2026-04-17  
**所要時間:** 15分（初回設定）
