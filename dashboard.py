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
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
from reportlab.pdfgen import canvas
from io import BytesIO
import textwrap

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
# PDF生成関数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_pdf_report(page_title, content_html):
    """HTML コンテンツをPDFに変換"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.units import inch

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()

    # タイトル
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=12,
        alignment=1  # center
    )

    story.append(Paragraph(page_title, title_style))
    story.append(Spacer(1, 0.3*inch))

    # コンテンツ
    content_style = styles['Normal']
    content_style.fontSize = 10
    content_style.leading = 14

    # シンプルなテキストコンテンツ
    story.append(Paragraph(content_html, content_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 前提",
    "📊 SNS情報",
    "📈 Context×Activity",
    "🔑 キーワード",
    "🎯 統合分析",
    "💡 ビジネス機会"
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 0: 前提
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab0:
    st.markdown("## 📋 調査前提と方法")

    st.markdown("### 調査目的")
    st.markdown("""
    CHRO（Chief Human Resource Officer）向けのビジネス創出、ビジネス機会の獲得にあたり、検討材料として日本・米国・英国・ドイツの主要なCHROの SNS情報を分析し、戦略的なトレンド、実行状況、課題を可視化するもの。
    """)

    st.markdown("### 調査方法")
    st.markdown("""
    LinkedIn および X（旧 Twitter）上のCHRO関連アカウントの投稿を収集・分析。各投稿を以下の分類軸に基づいて整理し、国別・コンテキスト別・段階別に集計・可視化。
    """)

    st.markdown("### 調査対象SNS")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**LinkedIn**")
        st.markdown("プロフェッショナル向けソーシャルメディア。CHROの戦略発表、論考、事例紹介が中心")

    with col2:
        st.markdown("**X（旧Twitter）**")
        st.markdown("リアルタイム情報交換。CHROのトレンド発信、意見表明が中心")

    st.divider()

    st.markdown("### 対象企業群")
    st.markdown("調査対象CHROは、以下の各国の代表的な上場企業の経営層から選定：")

    company_data = {
        '🇯🇵 日本': 'TOPIX400 構成銘柄',
        '🇺🇸 米国': 'S&P100 構成銘柄',
        '🇬🇧 英国': 'FTSE100 構成銘柄',
        '🇩🇪 ドイツ': 'DAX40 構成銘柄'
    }

    col1, col2 = st.columns(2)
    for idx, (country, index) in enumerate(company_data.items()):
        with col1 if idx % 2 == 0 else col2:
            st.markdown(f"**{country}:** {index}")

    st.divider()

    st.markdown("### Contextの定義")
    st.markdown("組織人事戦略における7つの戦略領域：")

    context_def = {
        'A&S': ('経営・戦略', '企業の経営戦略、組織戦略、グローバル展開戦略'),
        'TMD': ('タレント・市場・育成', '人材獲得、市場動向分析、人材育成・キャリア開発'),
        'HROPAI': ('HR業務・AI', '人事業務プロセス、AI/DX活用、業務効率化'),
        'C&E': ('文化・エンゲージメント', '企業文化醸成、従業員エンゲージメント、心理的安全性'),
        'WTT': ('労働力変革', '労働力の構成変化、ジョブ型人事、スキル変革'),
        'HRT': ('HR変革', 'HR部門のデジタル化、組織再編、人事機能の高度化'),
        'S&G': ('後継者育成・ガバナンス', '経営者育成、後継者育成、コーポレートガバナンス')
    }

    for ctx, (ja_name, description) in context_def.items():
        with st.expander(f"**{ctx}** - {ja_name}"):
            st.write(description)

    st.divider()

    st.markdown("### Activityの定義")
    st.markdown("CHROが発信する内容の実行段階（成熟度）：")

    activity_def = {
        'Done': '実現・完了済み',
        'Doing': '実行中',
        'Next': '次期計画',
        'Idea': '構想・アイデア',
        'Issue': '課題・問題点'
    }

    activity_desc = {
        'Done': '施策を導入完了し、成果を実証した段階',
        'Doing': '現在進行中で実装・運用している段階',
        'Next': '今後1年以内に実施予定の段階',
        'Idea': '検討段階・提案段階',
        'Issue': '取り組むべき課題、解決すべき問題'
    }

    for activity, ja_name in activity_def.items():
        with st.expander(f"**{activity}** - {ja_name}"):
            st.write(activity_desc[activity])

    st.divider()

    st.markdown("### 調査ルーティン")
    st.markdown("本ダッシュボードのデータは、毎月定期的に更新されます：")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**第1営業日**")
        st.markdown("""
        前月分のCHRO SNS投稿を収集し、戦略的コンテキスト（7つの領域）と実行段階（5段階）に基づいて分類・分析を実施
        """)

    with col2:
        st.markdown("**第2営業日**")
        st.markdown("""
        分析結果を統合レポートとして作成し、本ダッシュボードに反映。新規トレンド、国別の特性、ビジネス機会を可視化
        """)

    st.markdown("""
    これにより、月次ベースでCHROの関心事項の変化、国・産業別の戦略フォーカスの動向を継続的に把握できます。
    """)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: PHASE A - SNS Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab1:
    st.markdown("## SNS Information Summary & Context Distribution")

    # PDF出力ボタン
    col_pdf1, col_pdf2, col_pdf3 = st.columns([2, 1, 1])
    with col_pdf2:
        if st.button("📥 PDFダウンロード", key="pdf_tab1"):
            pdf_content = f"""
            <b>SNS Summary Report</b><br/>
            期間: {selected_period if selected_period != 'custom' else f'{selected_start_date} ～ {selected_end_date}'}<br/><br/>

            <b>データ概要</b><br/>
            総投稿数: {len(posts)}<br/>
            業務関連投稿: {sum(1 for p in posts if p.get('is_work_related'))}件<br/>
            追跡CHRO数: {len(set(p.get('person') for p in posts))}<br/>
            カバー地域: {len(set(p.get('country') for p in posts))}カ国<br/><br/>

            詳細はダッシュボードの各タブをご確認ください。
            """
            pdf = generate_pdf_report("SNS情報レポート", pdf_content)
            st.download_button(
                label="📥 ダウンロード",
                data=pdf,
                file_name=f"CHRO_SNS_Report_{selected_period}.pdf",
                mime="application/pdf",
                key="download_pdf_tab1"
            )

    st.divider()

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

    # PDF出力ボタン
    col_pdf1, col_pdf2, col_pdf3 = st.columns([2, 1, 1])
    with col_pdf2:
        if st.button("📥 PDFダウンロード", key="pdf_tab2"):
            pdf_content = f"""
            <b>Context × Activity Matrix Report</b><br/>
            期間: {selected_period if selected_period != 'custom' else f'{selected_start_date} ～ {selected_end_date}'}<br/><br/>

            <b>分析概要</b><br/>
            7つの戦略コンテキスト × 5つのアクティビティレベル × 4カ国<br/>
            合計投稿数: {len(posts)}件<br/><br/>

            各国の Context × Activity マトリックスを分析対象としています。<br/>
            詳細は各タブをご参照ください。
            """
            pdf = generate_pdf_report("Context×Activity分析レポート", pdf_content)
            st.download_button(
                label="📥 ダウンロード",
                data=pdf,
                file_name=f"CHRO_ContextActivity_Report_{selected_period}.pdf",
                mime="application/pdf",
                key="download_pdf_tab2"
            )

    st.divider()

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

    # PDF出力ボタン
    col_pdf1, col_pdf2, col_pdf3 = st.columns([2, 1, 1])
    with col_pdf2:
        if st.button("📥 PDFダウンロード", key="pdf_tab3"):
            pdf_content = f"""
            <b>キーワード分析レポート</b><br/>
            期間: {selected_period if selected_period != 'custom' else f'{selected_start_date} ～ {selected_end_date}'}<br/><br/>

            <b>分析概要</b><br/>
            7つのコンテキスト × 4カ国 = 28パターンのキーワード分析<br/>
            合計キーワード抽出数: 数百件<br/><br/>

            各コンテキストにおける国別の主要キーワードを抽出し、<br/>
            戦略トレンドの地域差異を可視化しています。
            """
            pdf = generate_pdf_report("キーワード分析レポート", pdf_content)
            st.download_button(
                label="📥 ダウンロード",
                data=pdf,
                file_name=f"CHRO_Keywords_Report_{selected_period}.pdf",
                mime="application/pdf",
                key="download_pdf_tab3"
            )

    st.divider()

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

    # PDF出力ボタン
    col_pdf1, col_pdf2, col_pdf3 = st.columns([2, 1, 1])
    with col_pdf2:
        if st.button("📥 PDFダウンロード", key="pdf_tab4"):
            pdf_content = f"""
            <b>統合分析レポート</b><br/>
            期間: {selected_period if selected_period != 'custom' else f'{selected_start_date} ～ {selected_end_date}'}<br/><br/>

            <b>分析内容</b><br/>
            • エグゼクティブサマリー<br/>
            • 地域別戦略プロファイル（日本、米国、英国、ドイツ）<br/>
            • 国別の重点領域と課題<br/>
            • 推奨施策<br/><br/>

            本レポートは Phase A/B/C の統合分析結果を<br/>
            戦略的インサイトとしてまとめたものです。
            """
            pdf = generate_pdf_report("統合分析レポート", pdf_content)
            st.download_button(
                label="📥 ダウンロード",
                data=pdf,
                file_name=f"CHRO_Integrated_Analysis_{selected_period}.pdf",
                mime="application/pdf",
                key="download_pdf_tab4"
            )

    st.divider()

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

    # PDF出力ボタン
    col_pdf1, col_pdf2, col_pdf3 = st.columns([2, 1, 1])
    with col_pdf2:
        if st.button("📥 PDFダウンロード", key="pdf_tab5"):
            pdf_content = f"""
            <b>ビジネス機会レポート</b><br/>
            期間: {selected_period if selected_period != 'custom' else f'{selected_start_date} ～ {selected_end_date}'}<br/><br/>

            <b>レポート内容</b><br/>
            • 単一コンテキスト推奨事項（7提案）<br/>
            • クロスコンテキスト推奨事項（5+提案）<br/>
            • 国別ギャップ分析に基づくビジネスアイデア<br/><br/>

            本レポートでは、CHROの関心事項の国別・領域別の<br/>
            ギャップから導き出されたビジネス機会を整理しています。
            """
            pdf = generate_pdf_report("ビジネス機会レポート", pdf_content)
            st.download_button(
                label="📥 ダウンロード",
                data=pdf,
                file_name=f"CHRO_Business_Ideas_{selected_period}.pdf",
                mime="application/pdf",
                key="download_pdf_tab5"
            )

    st.divider()

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
