#!/usr/bin/env python3
"""
generate_analytics_phaseC.py
Phase C⑤深層分析 - コンテキスト別キーワードランキング + 深堀インサイト

7コンテキスト × 4国 = 28セット
人事・ガバナンステーマに関するキーワードのみを抽出
複数単語フレーズを原子単位として扱う

出力:
  - analytics_phaseC_202604.json (キーワード分析結果JSON)
  - analytics_phaseC_202604.md (Markdown形式のキーワードランキング)
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter
import re

# Windows UTF-8 対応
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = Path(__file__).parent.parent / "data"
CLASSIFIED_FILE = DATA_DIR / "classified_data_202604.json"
OUTPUT_JSON = DATA_DIR / "analytics_phaseC_202604.json"
OUTPUT_MD = DATA_DIR / "analytics_phaseC_202604.md"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# コンテキスト別キーワード（keyword_example.docxから抽出）
# 複数単語フレーズを原子単位として扱う
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONTEXT_KEYWORDS = {
    'S&G': [
        # Multi-word phrases first (longer matches take precedence)
        'Succession Plan', 'Executive Management', 'Board of Directors',
        'Leadership Pipeline', 'Skill Matrix', 'Nomination Committee',
        'Next-generation Leader Development', 'Governance Structure',
        'Executive Talent Development', 'Executive Compensation',
        'Sustainability Committee', 'Female Executive Ratio',
        'Independent Outside Director', 'Succession Planning',
        'Tough Assignment', 'Risk Management', 'Management Issues',
        'Critical Positions', 'Audit and Supervisory Committee',
        'Talent Development Committee', 'HR Strategy Meeting',
        'Strategic Talent Allocation', 'Top Management Commitment',
        'ESG-linked Executive Compensation',
        'Sustainable Corporate Value Enhancement',
        'Ito Review on Human Capital', 'Board Oversight',
        # Single words
        'succession', 'governance', 'executive', 'nomination', 'board',
        'leadership', 'talent', 'development', 'compensation', 'committee',
        'risk', 'director', 'planning', 'assignment', 'management',
        'サクセッション', 'ガバナンス', '経営', 'リーダーシップ', 'スキル',
        'リスク管理', 'サステナビリティ'
    ],
    'A&S': [
        # Multi-word phrases
        'Human Capital Management', 'Enhancement of Corporate Value',
        'Business Strategy', 'HR Strategy', 'Talent Portfolio',
        'Human Capital ROI', 'Intangible Assets', 'Mandatory Disclosure',
        'Guidelines for Human Capital Visualization',
        'Investor Engagement', 'Investor Dialogue', 'Integrated Report',
        'Securities Report', 'ESG Investing', 'As-Is to To-Be Gap',
        'Medium-term Management Plan', 'Dynamic Talent Portfolio',
        'Value Creation Story', 'Maximization of Human Capital',
        'Capital Efficiency', 'KPI Management', 'Alignment of HR Strategy',
        'Business Portfolio',
        # Single words (excludes 'strategy' - only multi-word phrases allowed)
        'portfolio', 'roi', 'investor', 'engagement', 'report', 'esg', 'kpi',
        'efficiency', 'value', 'capital',
        '人的資本', '企業価値', '経営戦略', '投資家', 'kpi'
    ],
    'HRT': [
        # Multi-word phrases
        'HR Transformation', 'HR Function Transformation',
        'HR Business Partner', 'Center of Excellence', 'Shared Service Center',
        'Strategic HR', 'Data-driven HR', 'Project Management',
        'HR Capability Improvement', 'Delegation of HR Authority',
        'Process Standardization', 'Agile HR', 'Job-based HR System',
        'Change Agent', 'Organization Development', 'HR Evaluation System',
        'People Analytics', 'Employee Experience', 'Quantification of HR Data',
        'Talent Management System', 'Skill Management', 'HR System Reform',
        'HR Strategy Formulation', 'Human Capital Dashboard',
        'Management by Objectives', 'Objectives and Key Results',
        'OODA Loop', 'HR Digital Transformation',
        # Single words
        'transformation', 'hrbp', 'business partner', 'excellence',
        'strategic', 'data-driven', 'agile', 'change', 'analytics',
        'organization', 'development', 'evaluation', 'system', 'skill',
        'hr変革', 'デジタル', 'プロセス'
    ],
    'WTT': [
        # Multi-word phrases
        'Talent Management', 'Skill Taxonomy', 'Skill Map',
        'Skill Gap Analysis', 'Talent Portfolio Visualization',
        'Technology Utilization', 'People Analytics', 'Turnover Prediction Model',
        'Performance Analysis', 'Employee Database', 'Workforce Visibility',
        'Integrated HR Information Platform', 'Skill Assessment',
        'Visualization of Organizational Condition', 'Cloud HR',
        'HR Technology', 'Matching System', 'Survey Data', 'Talent KPI',
        'HR Data Infrastructure', 'Cross-functional Utilization of Talent Data',
        'Data Governance', 'Big Data Analysis', 'Optimal Talent Allocation',
        'Productivity Tracking', 'Predictive Management', 'Talent Materiality',
        # Single words
        'workforce', 'talent', 'skill', 'analytics', 'dashboard',
        'technology', 'performance', 'data', 'visibility', 'platform',
        'cloud', 'assessment', 'kpi', 'governance', 'optimization',
        'タレント', 'スキル', 'ダッシュボード', 'クラウド'
    ],
    'TMD': [
        # Multi-word phrases
        'Career Autonomy', 'Reskilling', 'Upskilling', 'People Management Skills',
        'Referral Recruiting', 'Alumni', 'Alumni Network', 'Direct Recruiting',
        'Skill-based Hiring', 'Talent Marketplace', 'Internal Labor Market',
        'Internal Job Posting', 'Career Path', 'Employer Branding',
        'On-the-Job Training', '1on1 Meeting', 'Mentoring', 'Coaching',
        'Management Skill Enhancement', 'Acquisition of Professional Talent',
        'Promotion of Women\'s Participation', 'Diversity & Inclusion',
        'Candidate Experience', 'Executive Coaching', 'Potential Hiring',
        'Talent Acquisition Strategy', 'Career Development', 'Microlearning',
        'Professional Talent', 'Autonomous Talent', 'Employability',
        'Cross-boundary Learning', 'Outside Challenge', 'Management Training',
        # Single words (excludes 'development' - only multi-word phrases allowed)
        'career', 'reskilling', 'upskilling', 'recruiting', 'alumni',
        'diversity', 'inclusion', 'coaching', 'training',
        'women', 'participation', 'd&i', 'learning', 'talent',
        'キャリア', 'リスキリング', '採用', '育成', '多様性'
    ],
    'HROPAI': [
        # Multi-word phrases
        'Generative AI', 'Robotic Process Automation', 'AI Interview',
        'AI Screening of Entry Sheets', 'HR DX', 'Operational Efficiency',
        'Business Process Reengineering', 'AI Chatbot', 'Cloud HR System',
        'Smart Labor Management', 'Automated Payroll Calculation',
        'Attendance Management System', 'AI Turnover Prediction',
        'HR-specific AI', 'AI Transfer Simulation', 'Applicant Tracking System',
        'AI Agent', 'Low-code No-code', 'Employee Portal',
        'Remote Work Productivity Visualization', 'Explainable AI',
        'Wearable Sensor Utilization', 'Prompt Engineering',
        'AI Bias', 'Unconscious Bias', 'Information Security',
        'Automated Skill Testing', 'Recruiting Cost Reduction',
        'API for Data Integration', 'AI Communication Analysis',
        # Single words
        'ai', 'generative', 'rpa', 'automation', 'interview', 'dx',
        'efficiency', 'chatbot', 'cloud', 'payroll', 'system',
        'prediction', 'agent', 'security', 'api', 'bias',
        'ai人工知能', '自動化', 'dx'
    ],
    'C&E': [
        # Multi-word phrases
        'Employee Engagement', 'Corporate Culture', 'Organizational Culture',
        'Psychological Safety', 'Purpose Management', 'Well-being',
        'Job Satisfaction', 'Meaning of Work', 'Organizational Activation',
        'Inner Communication', 'Internal Communication', 'Value Survey',
        'AI-Native Organization', 'Engagement Survey', 'Organizational Diagnosis',
        'Flexible Working', 'Mission Vision Value Penetration',
        'Thanks Card', 'Praise Culture', 'Work-Life Balance',
        'Work-Life Integration', 'Organization Development Workshop',
        'Employee Satisfaction', 'Internal PR', 'Internal Newsletter',
        'Culture Transformation', 'Organizational Change', 'Autonomous Organization',
        'Team Building', 'Diversity Management', 'Employee Experience',
        'Sense of Belonging', 'Voice of Employee', 'Motivation Improvement',
        'Peer Bonus', 'Stress Check', 'Open Communication',
        # Single words
        'engagement', 'culture', 'psychological', 'safety', 'purpose',
        'well-being', 'satisfaction', 'communication', 'flexible', 'working',
        'mvv', 'motivation', 'diversity', 'transformation', 'team', 'mindset',
        'エンゲージメント', 'カルチャー', 'ウェルビーイング', 'パーパス'
    ]
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# データ読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with open(CLASSIFIED_FILE, encoding="utf-8") as f:
    posts = json.load(f)

print(f"[OK] {len(posts)}件のポスト読み込み完了")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# キーワード抽出関数（複数単語フレーズを原子単位として扱う）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_keywords_for_context(text, context):
    """
    テキストからコンテキスト固有のキーワードを抽出
    複数単語フレーズを優先的にマッチさせ、原子単位として扱う
    大文字小文字を統一して扱う
    """
    if not text:
        return []

    text_lower = text.lower()
    found_keywords = []

    # キーワードを長さで降順ソート（長いフレーズを先にマッチさせる）
    keywords = sorted(CONTEXT_KEYWORDS.get(context, []),
                     key=len, reverse=True)

    for keyword in keywords:
        # キーワードを小文字に統一
        keyword_lower = keyword.lower()

        # 単語境界を含むパターンで検索
        pattern = r'\b' + re.escape(keyword_lower) + r'\b'

        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
            # 常に小文字版を追加して大文字小文字を統一
            found_keywords.append(keyword_lower)

    return found_keywords

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase C: コンテキスト別キーワードランキング
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

context_labels = {
    'S&G': 'Succession & Governance',
    'A&S': 'Agenda & Strategy',
    'HRT': 'HR Transformation',
    'WTT': 'Workforce & Talent Transformation',
    'TMD': 'Talent Market & Development',
    'HROPAI': 'HR Operation & AI',
    'C&E': 'Culture & Engagement',
}

ctx_order = ['A&S', 'TMD', 'HROPAI', 'C&E', 'WTT', 'HRT', 'S&G']
countries = ['JP', 'US', 'UK', 'DE']

keyword_by_ctx_country = {}

for country in countries:
    country_posts = [p for p in posts if p.get('country') == country and p.get('is_work_related')]

    for ctx in ctx_order:
        ctx_posts = [p for p in country_posts if p.get('context_axis') == ctx]

        if not ctx_posts:
            keyword_by_ctx_country[f"{ctx}_{country}"] = {'keywords': [], 'post_count': 0}
            continue

        # テキストを結合
        all_text = ' '.join(p.get('text', '') for p in ctx_posts)

        # キーワード抽出（コンテキスト固有のキーワードのみ）
        keywords = extract_keywords_for_context(all_text, ctx)
        keyword_counter = Counter(keywords)

        # Top 10
        top_keywords = keyword_counter.most_common(10)

        keyword_by_ctx_country[f"{ctx}_{country}"] = {
            'context': ctx,
            'country': country,
            'post_count': len(ctx_posts),
            'keywords': [{'word': word, 'count': count} for word, count in top_keywords]
        }

print(f"[OK] {len(keyword_by_ctx_country)}コンテキスト×国のキーワード抽出完了（コンテキスト固有キーワード）")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 結果をJSON保存
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

analysis_result = {
    "metadata": {
        "generated_at": datetime.now().isoformat(),
        "period": "202604",
        "phase": "C",
        "description": "Context-based Keyword Ranking (HR & Governance Theme Only) + Deep Insights"
    },
    "keyword_by_ctx_country": keyword_by_ctx_country
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(analysis_result, f, ensure_ascii=False, indent=2)

print(f"[OK] JSON保存: {OUTPUT_JSON.name}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Markdown形式でレポート作成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

md_lines = [
    "# CHRO トレンド分析 - Phase C",
    "## コンテキスト別キーワードランキング（コンテキスト固有キーワード）",
    "",
    f"**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
    f"**対象期間**: 2026年3月17日 ～ 2026年4月16日",
    f"**抽出手法**: 各コンテキスト固有のキーワード（keyword_example.docxから抽出）",
    f"**重要**: 複数単語フレーズ（例：「Audit and Supervisory Committee」）は1単語として計数",
    "",
    "---",
    "",
]

country_names = {'JP': '日本', 'US': '米国', 'UK': '英国', 'DE': 'ドイツ'}

# コンテキスト別にキーワードを表示
for ctx in ctx_order:
    md_lines.extend([
        f"## {ctx}（{context_labels[ctx]}）のキーワードランキング",
        "",
    ])

    for country in countries:
        key = f"{ctx}_{country}"
        data = keyword_by_ctx_country[key]
        post_count = data['post_count']
        keywords = data['keywords']
        country_ja = country_names[country]

        md_lines.append(f"### {country_ja}（{country}）")
        md_lines.append(f"ポスト数: {post_count}件")
        md_lines.append("")

        if keywords:
            md_lines.append("| ランク | キーワード | 出現数 |")
            md_lines.append("|--------|----------|-------|")
            for rank, kw_data in enumerate(keywords, 1):
                word = kw_data['word']
                count = kw_data['count']
                md_lines.append(f"| {rank} | {word} | {count} |")
        else:
            md_lines.append("（該当キーワードがありません）")

        md_lines.append("")

    md_lines.extend([
        "---",
        "",
    ])

# Markdown を保存
report_text = "\n".join(md_lines)
with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"[OK] Markdown保存: {OUTPUT_MD.name}")
print(f"\n=== Phase C 完了（改修版：複数単語フレーズを原子単位として扱う）===")
print(f"コンテキスト別キーワードランキング（7コンテキスト × 4国 = 28セット）")
print(f"抽出手法: 複数単語フレーズを優先的にマッチ（「Audit and Supervisory Committee」は4語として分割せず1語として計数）")
print(report_text[:2000])  # 最初の2000文字を表示
print(f"\n... (続きを {OUTPUT_MD.name} で確認) ...")
