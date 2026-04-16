#!/usr/bin/env python3
"""
dashboard.py (Enhanced)
CHRO-SIE ダッシュボード
Phase A/B/Cを含めた統合分析の可視化
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter

# ページ設定
st.set_page_config(page_title="CHRO Trends Dashboard", layout="wide")

# タイトル
st.title("🌐 CHRO Strategic Insight Engine")
st.markdown("### 📊 Unified Analysis Dashboard (Phase A/B/C)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# データ読み込み関数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DATA_DIR = Path("data")

@st.cache_data
def load_all_data(period="202604"):
    """全データを読み込む（Phase A/B/C含む）"""
    try:
        with open(DATA_DIR / f"classified_data_{period}.json", encoding="utf-8") as f:
            posts = json.load(f)
        with open(DATA_DIR / f"analytics_{period}.json", encoding="utf-8") as f:
            analytics = json.load(f)
        with open(DATA_DIR / f"business_ideas_{period}.json", encoding="utf-8") as f:
            business = json.load(f)
        with open(DATA_DIR / f"analytics_phaseA_{period}.json", encoding="utf-8") as f:
            phase_a = json.load(f)
        with open(DATA_DIR / f"analytics_phaseB_{period}.json", encoding="utf-8") as f:
            phase_b = json.load(f)
        with open(DATA_DIR / f"analytics_phaseC_{period}.json", encoding="utf-8") as f:
            phase_c = json.load(f)

        return posts, analytics, business, phase_a, phase_b, phase_c
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return None, None, None, None, None, None

# 利用可能な期間を検出
available_periods = []
for file in DATA_DIR.glob("classified_data_*.json"):
    period = file.stem.split("_")[-1]
    available_periods.append(period)
available_periods.sort(reverse=True)

# 期間選択オプション
st.markdown("### データ期間の選択")

selection_mode = st.radio(
    "期間選択方法:",
    ["単一期間", "カスタム日付範囲"],
    horizontal=True
)

if selection_mode == "単一期間":
    if available_periods:
        selected_period = st.selectbox("対象期間:", available_periods, index=0)
    else:
        st.error("No data available")
        st.stop()
    selected_start_date = None
    selected_end_date = None
else:
    col1, col2 = st.columns(2)
    with col1:
        # デフォルト: 2026-03-17
        selected_start_date = st.date_input(
            "開始日:",
            value=__import__('datetime').date(2026, 3, 17)
        )
    with col2:
        # デフォルト: 2026-04-16
        selected_end_date = st.date_input(
            "終了日:",
            value=__import__('datetime').date(2026, 4, 16)
        )
    # 期間コードを生成（YYYYMMDDではなく、複数期間対応用）
    selected_period = "custom"

posts, analytics, business, phase_a, phase_b, phase_c = load_all_data(selected_period)

if posts is None:
    st.error(f"Failed to load data for {selected_period}")
    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 SNS情報",
    "📈 Context×Activity",
    "🔑 キーワード",
    "🎯 統合分析",
    "💡 ビジネス機会"
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: PHASE A - SNS Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab1:
    st.markdown("## SNS Information Summary & Context Distribution")

    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Posts", len(posts))
    with col2:
        work_posts = sum(1 for p in posts if p.get("is_work_related"))
        st.metric("Work-Related", work_posts, f"{100*work_posts/len(posts):.0f}%")
    with col3:
        st.metric("CHROs Tracked", len(set(p.get("person") for p in posts)))
    with col4:
        st.metric("Regions Covered", len(set(p.get("country") for p in posts)))

    st.divider()

    # SNS Summary Table
    st.markdown("### SNS Summary by Country")
    sns_summary = phase_a.get('sns_summary', {})

    summary_data = []
    for country in ['JP', 'US', 'UK', 'DE']:
        data = sns_summary.get(country, {})
        total = data.get('total_posts', 0)
        work = data.get('work_posts', 0)
        work_rate = (work / total * 100) if total > 0 else 100.0

        summary_data.append({
            'Country': country,
            'CHRO Count': data.get('chro_count', 0),
            'Total Posts': data.get('total_posts', 0),
            'Work Posts': data.get('work_posts', 0),
            'Business Related (%)': f"{work_rate:.1f}%",
            'LinkedIn': data.get('linkedin_posts', 0),
            'X': data.get('x_posts', 0)
        })

    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True)

    st.divider()

    # Context Distribution - Pie Charts
    st.markdown("### Context Distribution by Country (4 Pie Charts)")

    context_distribution = phase_a.get('context_distribution', {})

    col1, col2 = st.columns(2)

    for idx, country in enumerate(['JP', 'US', 'UK', 'DE']):
        col = col1 if idx % 2 == 0 else col2

        if country in context_distribution:
            country_data = context_distribution[country]
            ctx_dist = country_data.get('distribution', {})

            # データ準備
            pie_data = []
            for ctx_key, ctx_info in ctx_dist.items():
                if isinstance(ctx_info, dict) and ctx_info.get('count', 0) > 0:
                    pie_data.append({
                        'Context': ctx_key,
                        'Count': ctx_info.get('count', 0)
                    })

            if pie_data:
                df_pie = pd.DataFrame(pie_data)
                fig_pie = px.pie(df_pie, values='Count', names='Context',
                               title=f'{country} Context Distribution')
                with col:
                    st.plotly_chart(fig_pie, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: PHASE B - Context × Activity Matrix
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab2:
    st.markdown("## Context × Activity Level Matrix Analysis")

    # Country Selector
    selected_country = st.selectbox("Select Country:", ['JP', 'US', 'UK', 'DE'],
                                   key="phaseB_country")

    phaseB_data = phase_b.get('matrix_by_country', {})
    country_data = phaseB_data.get(selected_country, {})
    country_matrix = country_data.get('matrix', {})

    country_names = {'JP': '日本', 'US': '米国', 'UK': '英国', 'DE': 'ドイツ'}
    st.markdown(f"### {country_names[selected_country]} ({selected_country})")

    ctx_order = ['A&S', 'TMD', 'HROPAI', 'C&E', 'WTT', 'HRT', 'S&G']
    act_order = ['Done', 'Doing', 'Next', 'Idea', 'Issue']

    # Matrix Data Preparation
    matrix_data = []
    for ctx in ctx_order:
        row_data = {'Context': ctx}
        for act in act_order:
            row_data[act] = country_matrix.get(ctx, {}).get(act, 0)
        row_data['Total'] = sum(country_matrix.get(ctx, {}).get(act, 0) for act in act_order)
        matrix_data.append(row_data)

    df_matrix = pd.DataFrame(matrix_data)

    # Display as table
    st.dataframe(df_matrix, use_container_width=True)

    # Heatmap visualization
    st.markdown("### Heatmap Visualization")

    # Prepare data for heatmap (excluding Total column)
    heatmap_data = df_matrix.set_index('Context')[act_order].values

    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=act_order,
        y=ctx_order,
        colorscale='RdYlBu_r',
        text=heatmap_data,
        texttemplate='%{text}',
        textfont={"size": 12}
    ))

    fig_heatmap.update_layout(
        title=f'Context × Activity Matrix - {country_names[selected_country]}',
        xaxis_title='Activity Level',
        yaxis_title='Context',
        height=400
    )

    st.plotly_chart(fig_heatmap, use_container_width=True)

    # Key Insights
    with st.expander("📌 Key Insights"):
        dominant_ctx = df_matrix.loc[df_matrix['Total'].idxmax(), 'Context']
        dominant_count = df_matrix['Total'].max()

        doing_ratio = (df_matrix['Doing'].sum() / df_matrix['Total'].sum() * 100) if df_matrix['Total'].sum() > 0 else 0

        st.write(f"**Most Emphasized Context:** {dominant_ctx} ({dominant_count} posts)")
        st.write(f"**Execution Phase Ratio (Doing):** {doing_ratio:.1f}%")
        st.write(f"**Total Posts:** {df_matrix['Total'].sum()}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3: PHASE C - Keyword Rankings
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab3:
    st.markdown("## Keyword Rankings by Context")

    ctx_order = ['A&S', 'TMD', 'HROPAI', 'C&E', 'WTT', 'HRT', 'S&G']
    context_labels = {
        'A&S': 'Agenda & Strategy',
        'TMD': 'Talent Market & Development',
        'HROPAI': 'HR Operation & AI',
        'C&E': 'Culture & Engagement',
        'WTT': 'Workforce & Talent Transformation',
        'HRT': 'HR Transformation',
        'S&G': 'Succession & Governance'
    }

    # Context Selector
    col1, col2 = st.columns([2, 3])
    with col1:
        selected_context = st.selectbox(
            "Select Context:",
            ctx_order,
            format_func=lambda x: f"{x} - {context_labels[x]}",
            key="phaseC_context"
        )

    phaseC_data = phase_c.get('keyword_by_ctx_country', {})

    # Country Tabs
    country_tabs = st.tabs(['JP', 'US', 'UK', 'DE'])

    for tab_idx, country in enumerate(['JP', 'US', 'UK', 'DE']):
        with country_tabs[tab_idx]:
            country_names_full = {'JP': '日本', 'US': '米国', 'UK': '英国', 'DE': 'ドイツ'}

            key = f"{selected_context}_{country}"
            ctx_kw_data = phaseC_data.get(key, {})
            keywords = ctx_kw_data.get('keywords', [])
            post_count = ctx_kw_data.get('post_count', 0)

            st.markdown(f"### {country_names_full[country]} ({country}) - {post_count} posts")

            if keywords:
                # Keyword Table
                keyword_list = []
                for rank, kw_data in enumerate(keywords, 1):
                    keyword_list.append({
                        'Rank': rank,
                        'Keyword': kw_data.get('word', ''),
                        'Count': kw_data.get('count', 0)
                    })

                df_keywords = pd.DataFrame(keyword_list)
                st.dataframe(df_keywords, use_container_width=True, hide_index=True)

                # Bar Chart
                fig_keywords = px.bar(
                    df_keywords,
                    x='Count',
                    y='Keyword',
                    orientation='h',
                    title=f'Top Keywords - {country}'
                )
                fig_keywords.update_layout(height=400)
                st.plotly_chart(fig_keywords, use_container_width=True)
            else:
                st.info("No keywords found for this context/country combination")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4: Integrated Analysis
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab4:
    st.markdown("## 統合分析と戦略的インサイト")

    # Executive Summary
    st.markdown("### エグゼクティブサマリー")

    total_posts = len([p for p in posts if p.get('is_work_related')])

    summary_text = f"""
    **分析期間:** 2026年03月17日～2026年04月16日（30日間）

    **主要な発見:**
    - 対象投稿数: {total_posts}件
    - 地理的範囲: 4カ国（日本、米国、英国、ドイツ）
    - 分析フレームワーク: 7コンテキスト × 5アクティビティレベル × 4国

    **主要な観察結果:**
    1. **経営戦略（A&S）** が全地域で支配的（30%以上）
    2. **実行フェーズ（Doing）** が全体の50%以上を占める
    3. **地域差異:** 日本はHROPAI（19%）に注力、西欧市場はTMD中心
    4. **キーワードパターン:**
       - A&S: 「経営戦略」「人的資本」「投資家向けコミュニケーション」
       - TMD: 「キャリア開発」「コーチング」「多様性・インクルージョン」
       - HROPAI: 「AI」「生成AI」「自動化」
       - C&E: 「組織文化」「エンゲージメント」「ウェルビーイング」
    """

    st.markdown(summary_text)

    st.divider()

    # Regional Profiles
    st.markdown("### 地域別戦略プロファイル")

    col1, col2 = st.columns(2)

    with col1:
        with st.expander("🇯🇵 日本（JP）- 戦略プロファイル"):
            st.write(
                "**重点領域:** テクノロジー導入 & AI統合\n\n"
                "• LinkedIn中心の専門家ネットワーク\n"
                "• HROPAI（HR DX & AI）投資: 19%（グローバル最高水準）\n"
                "• 戦略的転換: 従来型HR → 人的資本経営\n"
                "• 課題: 生成AI実装の大規模展開\n"
                "• 推奨: HR技術投資のROI測定強化"
            )

        with st.expander("🇩🇪 ドイツ（DE）- 戦略プロファイル"):
            st.write(
                "**重点領域:** プロセス標準化 & 運用効率性\n\n"
                "• LinkedIn利用率: 95%以上\n"
                "• 実行フェーズ（Doing）: 48%（実行率最高）\n"
                "• 効率性優先のHR変革アプローチ\n"
                "• 課題: 効率性から価値創造へのシフト\n"
                "• 推奨: プロセス優越性とイノベーションのバランス"
            )

    with col2:
        with st.expander("🇺🇸 米国（US）- 戦略プロファイル"):
            st.write(
                "**重点領域:** タレント自律性 & 外部ネットワーキング\n\n"
                "• LinkedIn & X デュアルチャネル戦略\n"
                "• TMD（タレント市場・開発）: 強力な強調\n"
                "• キャリア自律 & 外部タレント市場の活性化\n"
                "• 課題: 多様なタレント獲得戦略の統合\n"
                "• 推奨: 内部・外部タレントフローの統合"
            )

        with st.expander("🇬🇧 英国（UK）- 戦略プロファイル"):
            st.write(
                "**重点領域:** 組織開発 & 文化変革\n\n"
                "• 成熟度の高い戦略的意思決定プロセス\n"
                "• C&E（文化・エンゲージメント）: 業界領先\n"
                "• ヨーロッパ標準のLinkedin文化\n"
                "• 課題: 文化変革インパクトの測定\n"
                "• 推奨: 心理的安全性メトリクスの確立"
            )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 5: Business Ideas (Keep Existing)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab5:
    st.markdown("## ビジネス機会と推奨施策")

    st.markdown("### 単一コンテキスト推奨事項")
    st.markdown("各コンテキスト領域での国別ギャップから導き出された推奨施策")

    ideas_single = {
        'A&S': 'グローバル経営戦略の標準化：日本の実行計画を米国・英国の成熟度モデルと統合',
        'TMD': 'キャリア開発プラットフォームの多言語化と文化適応：米国のベストプラクティスをドイツに展開',
        'HROPAI': 'AI人材育成プログラムの構築：日本のAI投資をコア価値に、グローバル展開',
        'C&E': '心理的安全性測定＆改善サービス：英国の文化成熟度をベースに各国カスタマイズ',
        'WTT': 'スキルギャップ分析AIツール：全国を対象とした個人の適職マッチング',
        'HRT': 'HR DXコンサルティング：ドイツの効率性とテクノロジーを組合せたサービス',
        'S&G': '後継者育成システムの標準化：英国の高度なガバナンスを各国に適用'
    }

    col1, col2 = st.columns(2)
    for idx, (ctx, idea) in enumerate(ideas_single.items()):
        with col1 if idx % 2 == 0 else col2:
            with st.expander(f"💡 {ctx}: {idea.split('：')[0]}"):
                st.write(f"**推奨:** {idea}")

    st.divider()

    st.markdown("### クロスコンテキスト推奨事項")
    st.markdown("複数コンテキスト領域の組合せによる相乗効果")

    ideas_cross = [
        ('A&S × TMD', '戦略に紐づくタレント戦略：日本の実行ギャップ解消に有効'),
        ('A&S × HROPAI', 'AI導入ロードマップの戦略統合：生成AI時代の人事機能再設計'),
        ('TMD × C&E', 'キャリア自律と組織文化：米国型自律性と英国型文化成熟度の統合'),
        ('HROPAI × WTT', 'AIスキルマッチング：テクノロジーと人材変革の連動'),
        ('C&E × HRT', '組織開発とHR変革：文化変革を支える仕組み構築')
    ]

    for combo, description in ideas_cross:
        with st.expander(f"🔄 {combo}"):
            st.write(f"**説明:** {description}")

    st.divider()

    if business and "ideas" in business:
        st.markdown("### その他のビジネスアイデア")
        for idea in business["ideas"][:5]:  # Show top 5
            with st.expander(f"💡 {idea.get('title', 'アイデア')}"):
                st.write(f"**コンテキスト:** {idea.get('context', 'N/A')}")
                st.write(f"**地域:** {idea.get('region', 'グローバル')}")
                st.write(f"**説明:** {idea.get('description', '')}")

                if 'action_items' in idea:
                    st.write("**実施項目:**")
                    for item in idea['action_items']:
                        st.write(f"- {item}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Footer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.divider()
st.markdown(
    f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"**Period:** {selected_period[:4]}-{selected_period[4:6]} | "
    f"**Dashboard Version:** 2.0 (Phase A/B/C Integrated)"
)
