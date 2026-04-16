# 🌐 CHRO Strategic Insight Engine

グローバルCHRO（Chief Human Resource Officer）のSNS投稿を分析する統合インテリジェンスプラットフォーム。

---

## 📋 概要

このプロジェクトは、LinkedIn/Xにおける4カ国（日本、米国、英国、ドイツ）のCHRO投稿 1,157件を分析し、人的資本経営の戦略的トレンドを可視化します。

**主な特徴:**
- 📊 3段階分析フレームワーク (Phase A/B/C)
- 🗺️ 4カ国地域別比較分析
- 🎯 7コンテキスト領域での実行成熟度評価
- 📈 キーワードランキングと4国色分けコーディング
- 💡 ビジネス機会提案（単一 + クロスコンテキスト）

---

## 🏗️ プロジェクト構成

```
CHRO-Strategic-Insight-Engine/
├── dashboard.py                    # Streamlit ダッシュボード
├── scripts/
│   ├── produce_report_unified_ja.py # 統合レポート生成
│   ├── generate_analytics_phaseA.py  # Phase A 分析
│   ├── generate_analytics_phaseB.py  # Phase B 分析
│   ├── generate_analytics_phaseC.py  # Phase C 分析
│   └── classify_posts.py            # Issue 分類
├── data/
│   ├── classified_data_202604.json       # 分類済みポスト（1,157件）
│   ├── analytics_phaseA_202604.json      # Phase A 結果
│   ├── analytics_phaseB_202604.json      # Phase B 結果
│   ├── analytics_phaseC_202604.json      # Phase C 結果
│   └── analytics_unified_202604_*.docx   # 統合レポート（Word）
├── .streamlit/
│   └── config.toml                  # Streamlit 設定
├── requirements.txt                 # Python 依存関係
├── DEPLOYMENT.md                    # Web デプロイ手順
└── README.md                        # このファイル
```

---

## 🚀 クイックスタート

### 1. ローカル環境での実行

```bash
# リポジトリをクローン
git clone https://github.com/your-username/CHRO-Strategic-Insight-Engine.git
cd CHRO-Strategic-Insight-Engine

# 依存関係をインストール
pip install -r requirements.txt

# ダッシュボードを起動
streamlit run dashboard.py
```

ブラウザで `http://localhost:8501` を開く

### 2. 統合レポート生成

```bash
python scripts/produce_report_unified_ja.py
```

出力: `data/analytics_unified_202604_YYYYMMDD_HHMMSS.docx`

---

## 📊 ダッシュボード機能

### Tab 1: 📊 SNS情報
- **SNS Summary**: 4国別投稿数、CHRO数、ビジネス関連率
- **Context Distribution**: 7コンテキスト別投稿分布（4円グラフ）

### Tab 2: 📈 Context×Activity
- **マトリクス分析**: 7コンテキスト × 5アクティビティレベル
- **ヒートマップ**: 実行フェーズの可視化
- **Key Insights**: 支配的なコンテキスト、実行率

### Tab 3: 🔑 キーワード
- **コンテキスト選択**: A&S, TMD, HROPAI, C&E, WTT, HRT, S&G
- **国別ランキング**: 各国のトップキーワード + 出現数
- **グラフ表示**: 棒グラフで可視化

### Tab 4: 🎯 統合分析
- **エグゼクティブサマリー**: 分析期間、主要発見、観察結果
- **地域別プロファイル**: 日本、米国、英国、ドイツの戦略比較
  - 重点領域
  - 投資額・投資率
  - 課題と推奨事項

### Tab 5: 💡 ビジネス機会
- **単一コンテキスト推奨**: 7領域別の推奨施策
- **クロスコンテキスト組合**: 5つの相乗効果戦略

---

## 📈 分析フレームワーク

### Phase A: SNS Information Summary
- 投稿ボリューム（国別、チャネル別）
- コンテキスト分布
- CHRO ネットワーク規模

### Phase B: Context × Activity Matrix
- **7コンテキスト**:
  - A&S (Agenda & Strategy) - 経営戦略
  - TMD (Talent Market & Development) - タレント市場・開発
  - HROPAI (HR Operations & AI) - HR運用・AI
  - C&E (Culture & Engagement) - 組織文化・エンゲージメント
  - WTT (Workforce & Talent Transformation) - 人材変革
  - HRT (HR Transformation) - HR変革
  - S&G (Succession & Governance) - 後継者育成・ガバナンス

- **5アクティビティレベル**:
  - Done (完了)
  - Doing (進行中)
  - Next (次のステップ）
  - Idea (アイデア段階)
  - Issue (課題・問題)

### Phase C: Keyword Rankings
- 7コンテキスト × 4国 = 28パターンのキーワードランキング
- 4国全てで出現するキーワード: グレー背景
- 3国以下でのみ出現: 白背景（地域特異性）

---

## 🔍 分析のポイント

### 実行成熟度の評価
**Done / (Done + Doing) の比率**で国別の成熟度を比較
- 例: UK 72% vs Japan 35% → 成熟度ギャップ 37ポイント

### キーワード色分け
- **グレー**: 4国共通テーマ（グローバル優先事項）
- **白**: 3国以下（地域特異的な課題）

### Business Ideas
- **単一コンテキスト**: 各領域の国別ギャップを解消する提案
- **クロスコンテキスト**: 複数領域を組合せた相乗効果

---

## 🌍 Web デプロイ

### Streamlit Cloud（推奨）
詳細は [DEPLOYMENT.md](DEPLOYMENT.md) を参照

```bash
# GitHub にプッシュ
git push origin main

# Streamlit Cloud で自動デプロイ
# URL: https://share.streamlit.io/YOUR_USERNAME/CHRO-Strategic-Insight-Engine/main/dashboard.py
```

### アクセス制御
- **自分**: GitHub コラボレーター（編集権限あり）
- **他人**: 公開 URL（読み取り専用）

---

## 📊 データ定義

### classified_data_202604.json
```json
[
  {
    "id": "unique_id",
    "person": "CHRO 名",
    "company": "企業名",
    "country": "JP|US|UK|DE",
    "date": "YYYY-MM-DD",
    "text": "投稿内容",
    "context_axis": "A&S|TMD|HROPAI|C&E|WTT|HRT|S&G",
    "activity_class": "Done|Doing|Next|Idea|Issue",
    "is_work_related": true,
    "platform": "LinkedIn|X"
  },
  ...
]
```

### analytics_phaseA_202604.json
```json
{
  "sns_summary": {
    "JP": {
      "chro_count": 26,
      "total_posts": 258,
      "work_posts": 258,
      "linkedin_posts": 249,
      "x_posts": 9
    }
  },
  "context_distribution": {
    "JP": {
      "total_posts": 258,
      "distribution": {
        "A&S": {"count": 78, "percentage": 30.2},
        ...
      }
    }
  }
}
```

---

## 🛠️ カスタマイズ

### 色スキーム変更
`.streamlit/config.toml` を編集:
```toml
[theme]
primaryColor = "#FF6B6B"  # 赤系
backgroundColor = "#F5F5F5"
```

### データ期間変更
`dashboard.py` で `selected_period` のデフォルト値を変更

### レポートタイトル/説明
`scripts/produce_report_unified_ja.py` のヘッダーセクションを編集

---

## 📋 月次更新プロセス

```bash
# 1. 新しい期間のデータを集計・分類
python scripts/classify_posts.py --period 202605

# 2. Phase A/B/C 分析実行
python scripts/generate_analytics_phaseA.py --period 202605
python scripts/generate_analytics_phaseB.py --period 202605
python scripts/generate_analytics_phaseC.py --period 202605

# 3. 統合レポート生成
python scripts/produce_report_unified_ja.py --period 202605

# 4. リポジトリに追加・プッシュ
git add data/
git commit -m "Add analytics for 2026-05 period"
git push origin main

# 5. Streamlit Cloud が自動で再デプロイ
```

---

## 📞 サポート

- **質問**: GitHub Issues を開く
- **改善提案**: Pull Request を送信
- **バグ報告**: Issue テンプレートに従う

---

## 📄 ライセンス

このプロジェクトは内部用途専用です。

---

## 👥 チーム

- **データ分析**: CHRO分析チーム
- **開発**: AI Assistant (Claude)
- **品質保証**: User

---

**最終更新:** 2026-04-17  
**バージョン:** 2.0 (コンテキスト中心分析)
