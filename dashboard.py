#!/usr/bin/env python3
"""
dashboard.py (Enhanced v3)
CHRO-SIE ダッシュボード
Phase A/B/C + ポスト行動パターン分類 対応版
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter, defaultdict
from io import BytesIO
import sys
import re
from pathlib import Path as PathlibPath

# 統合レポート生成関数をインポート
sys.path.insert(0, str(PathlibPath(__file__).parent / "scripts"))
try:
    from produce_report_unified_ja import generate_unified_report
except ImportError as e:
    generate_unified_report = None
    print(f"Warning: Could not import generate_unified_report: {e}")

# ページ設定
st.set_page_config(page_title="CHRO Trends Dashboard", layout="wide")

# タイトル
st.title("🌐 CHRO Strategic Insight Engine")
st.markdown("### 📊 Unified Analysis Dashboard (Phase A/B/C)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 定数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COUNTRIES = ['JP', 'US', 'UK', 'DE']
COUNTRY_NAMES = {'JP': '日本', 'US': '米国', 'UK': '英国', 'DE': 'ドイツ'}
CTX_ORDER = ['A&S', 'TMD', 'HROPAI', 'C&E', 'WTT', 'HRT', 'S&G']
ACT_ORDER = ['Done', 'Doing', 'Next', 'Idea', 'Issue']

CONTEXT_LABELS = {
    'A&S': 'Agenda & Strategy',
    'TMD': 'Talent Market & Development',
    'HROPAI': 'HR Operation & AI',
    'C&E': 'Culture & Engagement',
    'WTT': 'Workforce & Talent Transformation',
    'HRT': 'HR Transformation',
    'S&G': 'Succession & Governance',
}

# ポスト行動パターン（収集対象の4パターン）
POST_ACTIONS_ACTIVE = ['posted on the topic', 'commented on', 'shared', 'liked the post']
POST_ACTIONS_EXEC   = ['posted on the topic', 'commented on']  # 実行フェーズ分析対象
POST_ACTION_LABELS = {
    'posted on the topic': 'ポスト投稿',
    'commented on':        'コメント',
    'shared':              'シェア',
    'liked the post':      'いいね',
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# データ読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DATA_DIR = Path("data")

@st.cache_data
def load_all_data(period="202604", use_v2=False):
    try:
        # Use v2 classified data if available and requested
        v2_file = DATA_DIR / f"classified_data_{period}_v2.json"
        if use_v2 and v2_file.exists():
            classified_file = v2_file
        else:
            classified_file = DATA_DIR / f"classified_data_{period}.json"
        with open(classified_file, encoding="utf-8") as f:
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ヘルパー関数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_post_action_dist(posts):
    """国別 × ポスト行動パターン の分布を集計"""
    dist = defaultdict(lambda: defaultdict(int))
    for p in posts:
        country = p.get('country', 'Unknown')
        action  = p.get('post_action', 'posted on the topic')
        if action in POST_ACTIONS_ACTIVE and country in COUNTRIES:
            dist[country][action] += 1
    return dist

def build_exec_matrix(posts, context):
    """posted on the topic / commented on のみで Activity × Country マトリクスを構築"""
    matrix = defaultdict(lambda: defaultdict(int))
    for p in posts:
        if p.get('post_action') not in POST_ACTIONS_EXEC:
            continue
        if p.get('context_axis') != context:
            continue
        country = p.get('country', 'Unknown')
        act     = p.get('activity_class')
        if act and country in COUNTRIES:
            matrix[country][act] += 1
    return matrix

def build_context_dist_from_posts(posts):
    """全パターンを対象にコンテキスト分布を集計"""
    dist = defaultdict(lambda: defaultdict(int))
    for p in posts:
        country = p.get('country', 'Unknown')
        ctx     = p.get('context_axis')
        if ctx and country in COUNTRIES:
            dist[country][ctx] += 1
    return dist

def build_context_activity_matrix_by_country(posts, country):
    """指定国のContext × Activity マトリクスを構築（posted/commented のみ）"""
    matrix = defaultdict(lambda: defaultdict(int))
    for p in posts:
        if p.get('post_action') not in POST_ACTIONS_EXEC:
            continue
        if p.get('country') != country:
            continue
        ctx = p.get('context_axis')
        act = p.get('activity_class')
        if ctx and act and ctx in CTX_ORDER and act in ACT_ORDER:
            matrix[ctx][act] += 1
    return matrix

def normalize_heatmap_data_by_row(matrix, row_keys, col_keys):
    """行ごとに正規化したZ値行列を生成"""
    z_values = []
    for row_key in row_keys:
        row_values = [matrix[row_key].get(col_key, 0) for col_key in col_keys]
        max_val = max(row_values) if row_values and max(row_values) > 0 else 1
        normalized = [v / max_val for v in row_values]
        z_values.append(normalized)
    return z_values

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 期間選択
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

available_periods = sorted(
    set(
        m.group(1) for f in DATA_DIR.glob("classified_data_*.json")
        if (m := re.match(r'classified_data_(\d{6})', f.stem))
    ),
    reverse=True
)

st.markdown("### データ期間の選択")
selection_mode = st.radio("期間選択方法:", ["単一期間", "カスタム日付範囲"], horizontal=True)

if selection_mode == "単一期間":
    if available_periods:
        selected_period = st.selectbox("対象期間:", available_periods, index=0)
    else:
        st.error("No data available")
        st.stop()
    selected_start_date = None
    selected_end_date   = None
    data_period         = selected_period
else:
    col1, col2 = st.columns(2)
    with col1:
        selected_start_date = st.date_input("開始日:", value=__import__('datetime').date(2026, 3, 17))
    with col2:
        selected_end_date = st.date_input("終了日:", value=__import__('datetime').date(2026, 4, 16))
    selected_period = "custom"
    data_period     = available_periods[0] if available_periods else "202604"

# v2分類データを使用（新分類データが正式データ）
use_v2 = True

posts, analytics, business, phase_a, phase_b, phase_c = load_all_data(data_period, use_v2=use_v2)
if posts is None:
    st.error(f"Failed to load data for {selected_period}")
    st.stop()

# 集計（キャッシュ不要の軽量処理）
post_action_dist  = build_post_action_dist(posts)
ctx_dist_all      = build_context_dist_from_posts(posts)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB設定（7タブ）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 前提",
    "📊 SNS情報",
    "🥧 Context",
    "📈 Context×Activity",
    "🔑 キーワード",
    "🎯 統合分析",
    "💡 ビジネス機会",
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
    for country, index in [("🇯🇵 日本", "TOPIX400"), ("🇺🇸 米国", "S&P100"),
                            ("🇬🇧 英国", "FTSE100"), ("🇩🇪 ドイツ", "DAX40")]:
        st.markdown(f"**{country}:** {index} 構成銘柄")

    st.divider()

    st.markdown("### ポスト行動パターン分類（6パターン）")
    st.markdown("収集した各投稿を以下6パターンに分類し、うち2パターンは収集対象外として除外：")

    pattern_info = [
        ("✅ posted on the topic", "CHROが自らトピックについて投稿した内容", "収集対象・コンテキスト＋活動区分 両軸で分析"),
        ("✅ commented on",        "他者の投稿へのコメント",                  "収集対象・コンテキスト＋活動区分 両軸で分析"),
        ("✅ shared",              "他者の投稿をシェア・リポスト",             "収集対象・コンテキスト軸のみ分析"),
        ("✅ liked the post",      "他者の投稿へのいいね",                     "収集対象・コンテキスト軸のみ分析"),
        ("❌ Profile/Company info only", "プロフィール・会社概要ページの情報のみ", "収集対象外（除外）"),
        ("❌ No post action mentioned",  "投稿行動が不明・内容が不十分",          "収集対象外（除外）"),
    ]
    for pat, desc, note in pattern_info:
        with st.expander(f"**{pat}**"):
            st.write(f"**内容:** {desc}")
            st.write(f"**分析方針:** {note}")

    st.divider()

    st.markdown("### Contextの定義（7領域）")
    context_def = {
        'A&S':    ('経営・戦略',          '企業の経営戦略、組織戦略、グローバル展開戦略'),
        'TMD':    ('タレント・市場・育成', '人材獲得、市場動向分析、人材育成・キャリア開発'),
        'HROPAI': ('HR業務・AI',          '人事業務プロセス、AI/DX活用、業務効率化'),
        'C&E':    ('文化・エンゲージメント','企業文化醸成、従業員エンゲージメント、心理的安全性'),
        'WTT':    ('労働力変革',           '労働力の構成変化、ジョブ型人事、スキル変革'),
        'HRT':    ('HR変革',              'HR部門のデジタル化、組織再編、人事機能の高度化'),
        'S&G':    ('後継者育成・ガバナンス','経営者育成、後継者育成、コーポレートガバナンス'),
    }
    for ctx, (ja_name, description) in context_def.items():
        with st.expander(f"**{ctx}** - {ja_name}"):
            st.write(description)

    st.divider()

    st.markdown("### Activityの定義（posted on the topic / commented on のみ適用）")
    activity_def = {
        'Done':  ('実現・完了済み',   '施策を導入完了し、成果を実証した段階'),
        'Doing': ('実行中',           '現在進行中で実装・運用している段階'),
        'Next':  ('次期計画',         '今後1年以内に実施予定の段階'),
        'Idea':  ('構想・アイデア',   '検討段階・提案段階'),
        'Issue': ('課題・問題点',     '取り組むべき課題、解決すべき問題'),
    }
    for activity, (ja_name, desc) in activity_def.items():
        with st.expander(f"**{activity}** - {ja_name}"):
            st.write(desc)

    st.divider()
    st.markdown("### 調査ルーティン")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**第1営業日:** 前月分CHRO SNS投稿を収集・分類・分析")
    with col2:
        st.markdown("**第2営業日:** 統合レポート作成・ダッシュボード反映")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: SNS情報
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab1:
    st.markdown("## 📊 SNS Information Summary")

    st.divider()

    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    total_posts = len(posts)
    work_posts  = sum(1 for p in posts if p.get("is_work_related"))
    with col1:
        st.metric("Total Posts (収集済み)", total_posts)
    with col2:
        st.metric("Work-Related", work_posts,
                  f"{100*work_posts/total_posts:.0f}%" if total_posts > 0 else "—")
    with col3:
        st.metric("CHROs Tracked", len(set(p.get("person") for p in posts)))
    with col4:
        st.metric("Regions Covered", len(set(p.get("country") for p in posts if p.get("country") in COUNTRIES)))

    st.divider()

    # SNS Summary Table
    st.markdown("### SNS Summary by Country")
    sns_summary = phase_a.get('sns_summary', {})
    summary_data = []
    for country in COUNTRIES:
        data  = sns_summary.get(country, {})
        total = data.get('total_posts', 0)
        work  = data.get('work_posts', 0)
        rate  = f"{work/total*100:.1f}%" if total > 0 else "—"
        summary_data.append({
            '国':              COUNTRY_NAMES[country],
            'CHRO数':          data.get('chro_count', 0),
            '投稿数(収集計)':  total,
            'ビジネス関連数':  work,
            'ビジネス関連率':  rate,
            'LinkedIn':        data.get('linkedin_posts', 0),
            'X':               data.get('x_posts', 0),
        })
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

    st.divider()

    # ── ポスト行動パターン別 国別分布表 ──────────────────────────────────────
    st.markdown("### ポスト行動パターン別 投稿数分布（国別）")
    st.caption(
        "収集対象4パターン（Profile/Company info only・No post action mentioned は除外済み）"
    )

    pa_rows = []
    for country in COUNTRIES:
        row = {'国': COUNTRY_NAMES[country]}
        subtotal = 0
        for action in POST_ACTIONS_ACTIVE:
            cnt        = post_action_dist.get(country, {}).get(action, 0)
            row[POST_ACTION_LABELS[action]] = cnt
            subtotal  += cnt
        row['合計'] = subtotal
        pa_rows.append(row)

    df_pa = pd.DataFrame(pa_rows)
    st.dataframe(df_pa, use_container_width=True, hide_index=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: Context（新設）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab2:
    st.markdown("## 🥧 Context Distribution by Country")
    st.caption("全4ポスト行動パターン（ポスト投稿・コメント・シェア・いいね）を対象に集計")

    st.divider()

    # Context Distribution Pie Charts（4カ国）統一色パレット
    st.markdown("### Context Distribution by Country (4 Pie Charts)")

    # 統一された色パレット（7つのコンテキストに対応）
    CTX_COLORS = px.colors.qualitative.Set2[:7]

    col1, col2 = st.columns(2)
    for idx, country in enumerate(COUNTRIES):
        col = col1 if idx % 2 == 0 else col2
        ctx_data = ctx_dist_all.get(country, {})

        # CTX_ORDER順でソート
        pie_data = [
            {'Context': ctx, 'Count': ctx_data.get(ctx, 0)}
            for ctx in CTX_ORDER
            if ctx_data.get(ctx, 0) > 0
        ]
        if pie_data:
            df_pie = pd.DataFrame(pie_data)
            fig_pie = px.pie(
                df_pie, values='Count', names='Context',
                title=f'{COUNTRY_NAMES[country]}（{country}）Context Distribution',
                color_discrete_sequence=CTX_COLORS,
                category_orders={'Context': CTX_ORDER}
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            with col:
                st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    st.markdown("#### 国別インサイト")
    insight_map = {
        'JP': "HROPAIへの高い注目（AI/DX推進）が特徴。A&Sと並んで上位に位置し、日本企業のHR DX加速を反映。",
        'US': "TMD（タレント市場・育成）とA&Sが拮抗。キャリア自律・採用競争が引き続き最優先課題。",
        'UK': "C&E（文化・エンゲージメント）の比率が他国より高く、組織文化への戦略的投資が目立つ。",
        'DE': "A&Sが支配的で経営効率・戦略議論が中心。プロセス標準化・WTT（労働力変革）にも注力。",
    }
    for country in COUNTRIES:
        ctx_data = ctx_dist_all.get(country, {})
        if sum(ctx_data.values()) == 0:
            continue
        with st.expander(f"**{COUNTRY_NAMES[country]}（{country}）**"):
            st.write(insight_map.get(country, "データ収集中"))

    st.divider()

    # コンテキスト別 国比較バーチャート
    st.markdown("### コンテキスト別 国間投稿数比較")
    bar_data = []
    for ctx in CTX_ORDER:
        for country in COUNTRIES:
            bar_data.append({
                'Context': ctx,
                '国':      COUNTRY_NAMES[country],
                '件数':    ctx_dist_all.get(country, {}).get(ctx, 0),
            })
    df_bar = pd.DataFrame(bar_data)
    if not df_bar.empty and df_bar['件数'].sum() > 0:
        fig_bar = px.bar(
            df_bar, x='Context', y='件数', color='国',
            barmode='group',
            title='コンテキスト別 国間比較（全パターン対象）',
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3: Context × Activity
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab3:
    st.markdown("## 📈 Context × Activity Matrix Analysis")
    st.info(
        "⚠️ 実行フェーズ（Activity）分析は **「posted on the topic」「commented on」** パターンのみを対象とします。"
        "「shared」「liked the post」はコンテキスト分類のみのため除外。"
    )

    st.divider()

    selected_country = st.selectbox("Select Country:", COUNTRIES, key="phaseB_country",
                                    format_func=lambda c: f"{c} — {COUNTRY_NAMES[c]}")

    st.markdown(f"### {COUNTRY_NAMES[selected_country]}（{selected_country}）")

    # classified_data から直接マトリクスを構築（posted / commented のみ）
    matrix_data = []
    all_ctx_totals = {}
    for ctx in CTX_ORDER:
        exec_matrix = build_exec_matrix(posts, ctx)
        row = {'Context': ctx}
        for act in ACT_ORDER:
            row[act] = exec_matrix.get(selected_country, {}).get(act, 0)
        row['合計'] = sum(row[act] for act in ACT_ORDER)
        all_ctx_totals[ctx] = row['合計']
        matrix_data.append(row)

    df_matrix = pd.DataFrame(matrix_data)

    st.markdown("### Heatmap Visualization")
    # 行ごと正規化したZ値を計算
    raw_values = df_matrix.set_index('Context')[ACT_ORDER].values
    normalized_z = []
    for row in raw_values:
        max_val = max(row) if max(row) > 0 else 1
        normalized_z.append([v / max_val for v in row])

    fig_heatmap = go.Figure(data=go.Heatmap(
        z=normalized_z,
        x=ACT_ORDER,
        y=CTX_ORDER,
        colorscale='Blues',
        text=raw_values,
        texttemplate='%{text}',
        textfont={"size": 12},
        hovertemplate='Context: %{y}<br>Activity: %{x}<br>件数: %{text}<extra></extra>',
    ))
    fig_heatmap.update_layout(
        title=f'Context × Activity Matrix — {COUNTRY_NAMES[selected_country]} (posted + commented only)',
        xaxis_title='Activity Level',
        yaxis_title='Context',
        height=420,
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    with st.expander("📌 Key Insights"):
        total_sum = df_matrix['合計'].sum()
        if total_sum > 0:
            dominant_ctx   = df_matrix.loc[df_matrix['合計'].idxmax(), 'Context']
            dominant_count = df_matrix['合計'].max()
            doing_ratio    = df_matrix['Doing'].sum() / total_sum * 100
            st.write(f"**最多コンテキスト:** {dominant_ctx}（{CONTEXT_LABELS.get(dominant_ctx, '')}）— {dominant_count}件")
            st.write(f"**実行中（Doing）比率:** {doing_ratio:.1f}%")
            st.write(f"**集計対象投稿数（posted + commented）:** {total_sum}件")
        else:
            st.write("データなし（post_action フィールドが付与された後のデータが必要）")

    st.divider()

    # コンテキスト別比較ヒートマップ（7つのコンテキスト別）
    st.markdown("### コンテキスト別比較 — Context × 国別 Activity（posted + commented）")
    st.caption("各コンテキストについて、4国のActivity分布を比較（各国内で行ごと正規化）")

    # 7つのコンテキストを2×4 gridで配置
    cols_grid = st.columns(4)
    col_idx = 0

    for ctx_idx, ctx in enumerate(CTX_ORDER):
        # 4列ごとに新しい行を作成
        if ctx_idx % 4 == 0 and ctx_idx > 0:
            cols_grid = st.columns(4)
            col_idx = 0

        with cols_grid[col_idx]:
            # コンテキスト別のマトリクスを構築（行=国, 列=Activity）
            matrix = defaultdict(lambda: defaultdict(int))
            for p in posts:
                if p.get('post_action') not in POST_ACTIONS_EXEC:
                    continue
                if p.get('context_axis') != ctx:
                    continue
                country = p.get('country', 'Unknown')
                act = p.get('activity_class')
                if act and country in COUNTRIES:
                    matrix[country][act] += 1

            # Heatmapデータを構築（行=国, 列=Activity、各国内で正規化）
            z_values = []
            text_values = []
            for country in COUNTRIES:
                row_values = [matrix[country].get(act, 0) for act in ACT_ORDER]
                max_val = max(row_values) if row_values and max(row_values) > 0 else 1
                z_values.append([v / max_val for v in row_values])
                text_values.append([str(v) for v in row_values])

            fig_hm = go.Figure(
                data=go.Heatmap(
                    z=z_values,
                    x=ACT_ORDER,
                    y=[COUNTRY_NAMES[c] for c in COUNTRIES],
                    colorscale='Blues',
                    showscale=(ctx_idx == 0),  # 最初のチャートだけscaleを表示
                    text=text_values,
                    texttemplate='%{text}',
                    textfont={"size": 11},
                    hovertemplate='国: %{y}<br>Activity: %{x}<br>件数: %{text}<extra></extra>',
                )
            )
            fig_hm.update_layout(
                title=f'{ctx} — {CONTEXT_LABELS[ctx]}',
                xaxis_title='Activity Level',
                yaxis_title='Country',
                height=320,
                margin=dict(l=80, r=50, t=60, b=50)
            )

            st.plotly_chart(fig_hm, use_container_width=True)
            col_idx += 1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4: キーワード
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab4:
    st.markdown("## 🔑 Keyword Rankings by Context")
    st.caption("キーワード分析は全4ポスト行動パターン（ポスト投稿・コメント・シェア・いいね）を対象とします")

    st.divider()

    selected_context = st.selectbox(
        "Select Context:",
        CTX_ORDER,
        format_func=lambda x: f"{x} — {CONTEXT_LABELS[x]}",
        key="phaseC_context",
    )

    phaseC_data = phase_c.get('keyword_by_ctx_country', {})

    st.markdown("### キーワード ランキング（国別比較）")
    st.caption("4国のキーワード出現ランキングを横並びで比較")

    # 上段：4国ランキング表を1行4列で表示
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]

    keyword_tables = {}  # 後で棒グラフで使用するため保存
    all_keywords_by_country = {}  # クロス国キーワード判定用

    # 各国のキーワード表を事前に構築
    for country in COUNTRIES:
        key = f"{selected_context}_{country}"
        ctx_kw_data = phaseC_data.get(key, {})
        keywords = ctx_kw_data.get('keywords', [])
        post_count = ctx_kw_data.get('post_count', 0)

        if post_count == 0:
            post_count = sum(
                1 for p in posts
                if p.get('country') == country and p.get('context_axis') == selected_context
            )

        if keywords:
            keyword_list = [
                {'順位': rank, 'キーワード': kw.get('word', ''), '出現数': kw.get('count', 0)}
                for rank, kw in enumerate(keywords, 1)
            ]
            df_kw = pd.DataFrame(keyword_list).head(10)
            keyword_tables[country] = df_kw
            all_keywords_by_country[country] = set(df_kw['キーワード'].str.lower())
        else:
            # phaseC未生成の場合、classified_dataから簡易集計
            import re
            country_ctx_posts = [
                p for p in posts
                if p.get('country') == country
                and p.get('context_axis') == selected_context
            ]
            if country_ctx_posts:
                word_counter: Counter = Counter()
                stop_words = {'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for',
                              'of', 'with', 'is', 'are', 'was', 'be', 'as', 'by', 'we', 'our',
                              'it', 'this', 'that', 'have', 'has', 'from', 'not', 'i', 'you'}
                for p in country_ctx_posts:
                    words = re.findall(r'\b[a-zA-Z\u3040-\u9fff]{3,}\b', p.get('text', ''))
                    for w in words:
                        if w.lower() not in stop_words:
                            word_counter[w.lower()] += 1
                if word_counter:
                    top_words = word_counter.most_common(10)
                    df_kw2 = pd.DataFrame(top_words, columns=['キーワード', '出現数'])
                    df_kw2.insert(0, '順位', range(1, len(df_kw2) + 1))
                    keyword_tables[country] = df_kw2
                    all_keywords_by_country[country] = set(df_kw2['キーワード'].str.lower())

    # クロス国キーワード（4つの国すべてに登場）を特定
    cross_country_keywords = set()
    if len(all_keywords_by_country) == 4:
        cross_country_keywords = set.intersection(*all_keywords_by_country.values())

    # 表を4列で表示
    for col_idx, country in enumerate(COUNTRIES):
        with cols[col_idx]:
            st.markdown(f"**{COUNTRY_NAMES[country]}（{country}）**")

            if country in keyword_tables:
                df_kw = keyword_tables[country]
                post_count = sum(
                    1 for p in posts
                    if p.get('country') == country and p.get('context_axis') == selected_context
                )
                st.caption(f"対象投稿数: {post_count}件")

                # HTML表を構築（ヘッダー行を薄い青、クロス国キーワードを薄いグレー）
                html_table = '<table style="width:100%; border-collapse:collapse; border:1px solid #ddd; font-size:0.9em;">'
                html_table += '<tr style="background-color: #e6f2ff; font-weight:bold;">'
                html_table += '<th style="padding:8px; border:1px solid #ddd; text-align:center;">順位</th>'
                html_table += '<th style="padding:8px; border:1px solid #ddd; text-align:left;">キーワード</th>'
                html_table += '<th style="padding:8px; border:1px solid #ddd; text-align:center;">出現数</th>'
                html_table += '</tr>'

                for _, row in df_kw.iterrows():
                    kw = str(row['キーワード']).lower()
                    bg_color = '#f0f0f0' if kw in cross_country_keywords else 'white'
                    html_table += f'<tr style="background-color: {bg_color};">'
                    html_table += f'<td style="padding:8px; border:1px solid #ddd; text-align:center;">{row["順位"]}</td>'
                    html_table += f'<td style="padding:8px; border:1px solid #ddd;">{row["キーワード"]}</td>'
                    html_table += f'<td style="padding:8px; border:1px solid #ddd; text-align:center;">{row["出現数"]}</td>'
                    html_table += '</tr>'

                html_table += '</table>'
                st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.info("No data")

    st.divider()

    # 下段：4つの棒グラフを上から順に
    for country in COUNTRIES:
        if country not in keyword_tables:
            continue

        df_chart = keyword_tables[country]
        if 'キーワード' in df_chart.columns and '出現数' in df_chart.columns:
            df_chart_top15 = df_chart.head(15)
            fig_kw = px.bar(
                df_chart_top15, x='出現数', y='キーワード', orientation='h',
                title=f'{COUNTRY_NAMES[country]}（{country}） — {selected_context}',
                color='出現数', color_continuous_scale='Blues',
            )
            fig_kw.update_layout(height=450, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_kw, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 5: 統合分析
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab5:
    st.markdown("## 🎯 統合分析と戦略的インサイト")

    st.divider()

    # エグゼクティブサマリー
    st.markdown("### エグゼクティブサマリー")

    exec_posts = [p for p in posts if p.get('post_action') in POST_ACTIONS_EXEC]
    all_active = [p for p in posts if p.get('post_action') in POST_ACTIONS_ACTIVE]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("収集済み投稿（全4パターン）", len(all_active))
    with col2:
        st.metric("実行分析対象（posted/commented）", len(exec_posts))
    with col3:
        shared_liked = sum(1 for p in posts if p.get('post_action') in ['shared', 'liked the post'])
        st.metric("シェア・いいね（コンテキストのみ）", shared_liked)
    with col4:
        issue_posts = sum(1 for p in posts if p.get('activity_class') == 'Issue')
        st.metric("Issue分類（課題）", issue_posts)

    st.divider()

    summary_text = f"""
**分析期間:** 2026年03月17日～2026年04月16日（30日間）

**分析フレームワーク:**
- ポスト行動パターン: 6分類（うち2パターン除外）→ **4パターンを収集・分析**
- コンテキスト軸: **7領域**（全4パターン対象）
- 活動区分軸: **5段階**（posted on the topic / commented on パターンのみ）
- 対象国: **4カ国**（日本・米国・英国・ドイツ）

**主要な観察結果:**
1. **経営戦略（A&S）** が全地域で支配的（全パターン合算で30%以上）
2. **実行フェーズ（Doing）** が posted / commented の50%以上を占める
3. **シェア・いいね** に見るコンテキスト分布も経営戦略・タレント開発が中心
4. **地域差:** 日本はHROPAI（AI/DX）, 米国はTMD, 英国はC&E, ドイツはA&Sに注力
    """
    st.markdown(summary_text)

    st.divider()

    # 地域別戦略プロファイル
    st.markdown("### 地域別戦略プロファイル")
    col1, col2 = st.columns(2)

    profiles = {
        'JP': ("🇯🇵 日本", "テクノロジー導入 & AI統合",
               "• HROPAIが全国最高水準（AI/DX推進）\n"
               "• posted on the topic で具体的な施策発信が多い\n"
               "• shared/liked でも同テーマが上位 → 関心の高さを補強\n"
               "• 課題: 生成AI実装の大規模展開"),
        'US': ("🇺🇸 米国", "タレント自律性 & 外部ネットワーキング",
               "• TMD（タレント市場・育成）とA&Sが拮抗\n"
               "• LinkedIn & X のデュアルチャネル活用\n"
               "• commented on でのエンゲージメントが活発\n"
               "• 課題: 多様なタレント獲得戦略の統合"),
        'UK': ("🇬🇧 英国", "組織開発 & 文化変革",
               "• C&E（文化・エンゲージメント）が業界領先\n"
               "• liked the post でも文化・ウェルビーイング関連が多数\n"
               "• 成熟度の高い戦略的意思決定プロセス\n"
               "• 課題: 文化変革インパクトの測定"),
        'DE': ("🇩🇪 ドイツ", "プロセス標準化 & 運用効率性",
               "• A&Sが支配的、経営効率・戦略議論が中心\n"
               "• LinkedIn利用率: 95%以上\n"
               "• shared で実践的な事例・ツール記事が多い\n"
               "• 課題: 効率性から価値創造へのシフト"),
    }
    for idx, (country, (label, focus, detail)) in enumerate(profiles.items()):
        with (col1 if idx % 2 == 0 else col2):
            with st.expander(f"**{label} — {focus}**"):
                st.markdown(detail)

    st.divider()

    # ポストパターン別サマリー
    st.markdown("### ポスト行動パターン別 分析サマリー")
    pattern_summary = [
        ("posted on the topic", "コンテキスト＋活動区分 両軸",
         "CHROの積極的な情報発信。戦略の「今」を最も直接的に反映。"),
        ("commented on", "コンテキスト＋活動区分 両軸",
         "他者との対話。テーマへの共感・反論・補足から関心の深さが分かる。"),
        ("shared", "コンテキスト軸のみ",
         "共有・拡散行動。「注目すべき情報」を選ぶ行為自体がアジェンダを示す。"),
        ("liked the post", "コンテキスト軸のみ",
         "いいね行動。最小コストの賛意表明。量的には大きく、関心の裾野を把握できる。"),
    ]
    for action, axes, insight in pattern_summary:
        with st.expander(f"**{action}** — 分析軸: {axes}"):
            st.write(f"**インサイト:** {insight}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 6: ビジネス機会
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab6:
    st.markdown("## 💡 ビジネス機会と推奨施策")
    st.caption("コンテキスト分析・実行フェーズ・キーワードから導出した推奨施策")

    st.divider()

    st.markdown("### 単一コンテキスト推奨事項")
    st.markdown("各コンテキスト領域での国別ギャップから導き出された推奨施策")

    ideas_single = {
        'A&S':    'グローバル経営戦略の標準化：日本の実行計画を米国・英国の成熟度モデルと統合',
        'TMD':    'キャリア開発プラットフォームの多言語化と文化適応：米国のベストプラクティスをドイツに展開',
        'HROPAI': 'AI人材育成プログラムの構築：日本のAI投資をコア価値に、グローバル展開',
        'C&E':    '心理的安全性測定＆改善サービス：英国の文化成熟度をベースに各国カスタマイズ',
        'WTT':    'スキルギャップ分析AIツール：全国を対象とした個人の適職マッチング',
        'HRT':    'HR DXコンサルティング：ドイツの効率性とテクノロジーを組合せたサービス',
        'S&G':    '後継者育成システムの標準化：英国の高度なガバナンスを各国に適用',
    }
    col1, col2 = st.columns(2)
    for idx, (ctx, idea) in enumerate(ideas_single.items()):
        with (col1 if idx % 2 == 0 else col2):
            with st.expander(f"💡 {ctx} — {CONTEXT_LABELS[ctx]}"):
                st.write(f"**推奨:** {idea}")
                # ポストパターン別ボリューム参照
                total_ctx = sum(ctx_dist_all.get(c, {}).get(ctx, 0) for c in COUNTRIES)
                st.caption(f"関連投稿数（全パターン合計）: {total_ctx}件")

    st.divider()

    st.markdown("### クロスコンテキスト推奨事項")
    ideas_cross = [
        ('A&S × TMD',    '戦略に紐づくタレント戦略：日本の実行ギャップ解消に有効',
         'posted / commented の両パターンで共鳴が高い'),
        ('A&S × HROPAI', 'AI導入ロードマップの戦略統合：生成AI時代の人事機能再設計',
         '日本・米国でいずれも上位コンテキストの組み合わせ'),
        ('TMD × C&E',    'キャリア自律と組織文化：米国型自律性と英国型文化成熟度の統合',
         'liked the post パターンで両テーマの支持が広い'),
        ('HROPAI × WTT', 'AIスキルマッチング：テクノロジーと人材変革の連動',
         '実行フェーズ Doing が最多、今すぐ需要がある'),
        ('C&E × HRT',    '組織開発とHR変革：文化変革を支える仕組み構築',
         'shared パターンでの拡散が多く関心が広い'),
    ]
    for combo, desc, evidence in ideas_cross:
        with st.expander(f"🔄 {combo}"):
            st.write(f"**説明:** {desc}")
            st.caption(f"根拠: {evidence}")

    st.divider()

    if business and "ideas" in business:
        st.markdown("### その他のビジネスアイデア（データ由来）")
        for idea in business["ideas"][:5]:
            with st.expander(f"💡 {idea.get('title', 'アイデア')}"):
                st.write(f"**コンテキスト:** {idea.get('context', 'N/A')}")
                st.write(f"**地域:** {idea.get('region', 'グローバル')}")
                st.write(f"**説明:** {idea.get('description', '')}")
                if 'action_items' in idea:
                    st.write("**実施項目:**")
                    for item in idea['action_items']:
                        st.write(f"- {item}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# サイドバー：統合レポート出力
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown("---")

    st.markdown("### 📄 統合レポート")
    st.markdown("全タブデータをまとめたPDFレポートを出力")
    st.caption("レポートには今回の変更（行動パターン分類・新規ページ・全パターンIssue一覧）が反映されます")

    if st.button("📥 統合レポートをPDF出力", key="unified_report_button"):
        if generate_unified_report is None:
            st.error("❌ 統合レポート機能が利用できません")
        else:
            try:
                if selected_period == "custom":
                    collection_end_date = selected_end_date.strftime("%Y%m%d")
                else:
                    year  = int(selected_period[:4])
                    month = int(selected_period[4:6])
                    from datetime import timedelta
                    next_month      = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
                    last_day        = (next_month - timedelta(days=1)).day
                    collection_end_date = f"{year}{month:02d}{last_day:02d}"

                with st.spinner("📝 レポートを生成中..."):
                    pdf_buffer = generate_unified_report(
                        period=data_period,
                        collection_end_date=collection_end_date,
                        return_format="pdf",
                    )
                    if pdf_buffer is not None:
                        try:
                            # BytesIO objectから bytes に変換
                            if hasattr(pdf_buffer, 'getvalue'):
                                pdf_bytes = pdf_buffer.getvalue()
                            else:
                                pdf_bytes = pdf_buffer

                            # PDF形式の検証（PDFファイルは%PDFで始まる）
                            if isinstance(pdf_bytes, bytes) and pdf_bytes.startswith(b'%PDF'):
                                st.success("✅ レポート生成完了！")
                                st.download_button(
                                    label="📥 ダウンロード",
                                    data=pdf_bytes,
                                    file_name=f"CHRO_Strategic_Insight_Engine_{collection_end_date}.pdf",
                                    mime="application/pdf",
                                    key="download_unified_pdf",
                                )
                            else:
                                # PDF形式でない場合（おそらくdocx）
                                st.warning("⚠️ PDF変換エラー：DocXファイルで代替出力します")
                                st.download_button(
                                    label="📥 ダウンロード（DOCX形式）",
                                    data=pdf_bytes,
                                    file_name=f"CHRO_Strategic_Insight_Engine_{collection_end_date}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key="download_unified_docx",
                                )
                                st.info("💡 LibreOfficeをインストールするとPDF形式で出力できます")
                        except Exception as e:
                            st.error(f"❌ ファイル処理エラー: {str(e)}")
                    else:
                        st.error("❌ レポート生成に失敗しました")
                        st.info("コンソールでエラーメッセージを確認してください")
            except Exception as e:
                st.error(f"❌ エラー: {str(e)}")
                import traceback
                traceback.print_exc()

    st.markdown("---")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Footer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.divider()
st.markdown(
    f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"**Period:** {selected_period[:4]}-{selected_period[4:6] if len(selected_period) >= 6 else '--'} | "
    f"**Dashboard Version:** 3.0 (Post Action Pattern対応)"
)
