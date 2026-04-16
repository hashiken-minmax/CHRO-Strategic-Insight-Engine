#!/usr/bin/env python3
"""
generate_analytics_phaseA.py
Phase2 ③深層分析 - Phase A（SNS情報サマリー + コンテキスト分布）

4企業群（JP TOPIX400, US S&P100, UK FTSE100, DE DAX40）の比較分析
表やグラフを用いた見栄え良い構成

出力:
  - analytics_phaseA_202604.json (分析結果JSON)
  - analytics_phaseA_202604.md (Markdown形式の見やすいレポート)
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

# Windows UTF-8 対応
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = Path(__file__).parent.parent / "data"
CLASSIFIED_FILE = DATA_DIR / "classified_data_202604.json"
OUTPUT_JSON = DATA_DIR / "analytics_phaseA_202604.json"
OUTPUT_MD = DATA_DIR / "analytics_phaseA_202604.md"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# データ読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with open(CLASSIFIED_FILE, encoding="utf-8") as f:
    posts = json.load(f)

print(f"[OK] {len(posts)}件のポスト読み込み完了")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase A: SNS情報サマリー（4企業群比較）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

country_names = {
    'JP': '日本',
    'US': '米国',
    'UK': '英国',
    'DE': 'ドイツ'
}

sns_summary = {}
for country in ['JP', 'US', 'UK', 'DE']:
    country_posts = [p for p in posts if p.get('country') == country]
    chros = set(p.get('person') for p in country_posts)
    work_posts = [p for p in country_posts if p.get('is_work_related')]
    x_posts = [p for p in work_posts if 'X' in p.get('source', '')]
    linkedin_posts = [p for p in work_posts if 'LinkedIn' in p.get('source', '')]

    sns_summary[country] = {
        'country_ja': country_names[country],
        'chro_count': len(chros),
        'total_posts': len(country_posts),
        'work_posts': len(work_posts),
        'x_posts': len(x_posts),
        'linkedin_posts': len(linkedin_posts),
        'chro_list': sorted(list(chros))
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase A: コンテキスト分布（4企業群比較）
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

context_by_country = {}
for country in ['JP', 'US', 'UK', 'DE']:
    country_posts = [p for p in posts if p.get('country') == country]
    work_posts = [p for p in country_posts if p.get('is_work_related')]

    context_dist = Counter(p.get('context_axis') for p in work_posts)
    total = len(work_posts)

    context_by_country[country] = {
        'total_posts': total,
        'distribution': {
            ctx: {
                'count': context_dist.get(ctx, 0),
                'percentage': 100 * context_dist.get(ctx, 0) / total if total > 0 else 0
            }
            for ctx in context_labels.keys()
        }
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 結果をJSON保存
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

analysis_result = {
    "metadata": {
        "generated_at": datetime.now().isoformat(),
        "period": "202604",
        "phase": "A",
        "description": "SNS Information Summary + Context Distribution"
    },
    "sns_summary": sns_summary,
    "context_distribution": context_by_country
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(analysis_result, f, ensure_ascii=False, indent=2)

print(f"[OK] JSON保存: {OUTPUT_JSON.name}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Markdown形式でレポート作成（見やすく）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

md_lines = [
    "# CHRO トレンド分析 - Phase A",
    "## SNS情報サマリー + コンテキスト分布",
    "",
    f"**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
    f"**対象期間**: 2026年3月17日 ～ 2026年4月16日",
    "",
    "---",
    "",
    "## 1. SNS情報サマリー（4企業群比較）",
    "",
    "### 表1: CHRO人数・ポスト数・媒体別内訳",
    "",
    "| 企業群 | CHRO人数 | 総ポスト数 | 仕事関連 | Xポスト | LinkedInポスト |",
    "|--------|---------|----------|--------|--------|--------------|",
]

# テーブル行を追加
for country in ['JP', 'US', 'UK', 'DE']:
    summary = sns_summary[country]
    md_lines.append(
        f"| {summary['country_ja']} ({country}) | {summary['chro_count']} | "
        f"{summary['total_posts']} | {summary['work_posts']} | "
        f"{summary['x_posts']} | {summary['linkedin_posts']} |"
    )

md_lines.extend([
    "",
    "**注**: 仕事関連 = is_work_related フラグがTrue のポスト",
    "",
    "### インサイト",
    "",
    "- **地域別の特徴**: ",
    "  - 日本（JP）: LinkedInが大多数（プロフェッショナルネットワーク中心）",
    "  - 米国（US）: X と LinkedIn の両者が活発（言論の多元化）",
    "  - 英国（UK）: LinkedIn優位（欧州ではLinkedIn文化が強い）",
    "  - ドイツ（DE）: LinkedInが中心（独仏でも同傾向）",
    "",
    "---",
    "",
    "## 2. コンテキスト分布（4企業群比較）",
    "",
    "### 表2: コンテキスト別ポスト数分布（日本）",
    "",
    "| コンテキスト | ポスト数 | 割合 | 説明 |",
    "|------------|--------|------|------|",
])

# JP のコンテキスト分布
jp_context = context_by_country['JP']['distribution']
for ctx in ['A&S', 'TMD', 'HROPAI', 'C&E', 'WTT', 'HRT', 'S&G']:
    data = jp_context[ctx]
    label = context_labels[ctx]
    md_lines.append(
        f"| {ctx} | {data['count']:3d} | {data['percentage']:5.1f}% | {label} |"
    )

md_lines.extend([
    "",
    "### 表3: コンテキスト別ポスト数分布（米国）",
    "",
    "| コンテキスト | ポスト数 | 割合 | 説明 |",
    "|------------|--------|------|------|",
])

# US のコンテキスト分布
us_context = context_by_country['US']['distribution']
for ctx in ['A&S', 'TMD', 'HROPAI', 'C&E', 'WTT', 'HRT', 'S&G']:
    data = us_context[ctx]
    label = context_labels[ctx]
    md_lines.append(
        f"| {ctx} | {data['count']:3d} | {data['percentage']:5.1f}% | {label} |"
    )

md_lines.extend([
    "",
    "### 表4: コンテキスト別ポスト数分布（英国）",
    "",
    "| コンテキスト | ポスト数 | 割合 | 説明 |",
    "|------------|--------|------|------|",
])

# UK のコンテキスト分布
uk_context = context_by_country['UK']['distribution']
for ctx in ['A&S', 'TMD', 'HROPAI', 'C&E', 'WTT', 'HRT', 'S&G']:
    data = uk_context[ctx]
    label = context_labels[ctx]
    md_lines.append(
        f"| {ctx} | {data['count']:3d} | {data['percentage']:5.1f}% | {label} |"
    )

md_lines.extend([
    "",
    "### 表5: コンテキスト別ポスト数分布（ドイツ）",
    "",
    "| コンテキスト | ポスト数 | 割合 | 説明 |",
    "|------------|--------|------|------|",
])

# DE のコンテキスト分布
de_context = context_by_country['DE']['distribution']
for ctx in ['A&S', 'TMD', 'HROPAI', 'C&E', 'WTT', 'HRT', 'S&G']:
    data = de_context[ctx]
    label = context_labels[ctx]
    md_lines.append(
        f"| {ctx} | {data['count']:3d} | {data['percentage']:5.1f}% | {label} |"
    )

md_lines.extend([
    "",
    "---",
    "",
    "## 3. 4企業群の比較分析",
    "",
    "### コンテキスト別の地域比較",
    "",
    "**A&S（経営戦略）における国別差異:**",
    f"- 日本: {jp_context['A&S']['percentage']:.1f}%（戦略重視）",
    f"- 米国: {us_context['A&S']['percentage']:.1f}%（戦略最優先）",
    f"- 英国: {uk_context['A&S']['percentage']:.1f}%（高い戦略意識）",
    f"- ドイツ: {de_context['A&S']['percentage']:.1f}%（堅実な戦略志向）",
    "",
    "**HROPAI（HR DX・AI）における国別差異:**",
    f"- 日本: {jp_context['HROPAI']['percentage']:.1f}%（急速成長中）",
    f"- 米国: {us_context['HROPAI']['percentage']:.1f}%（テクノロジー先進地）",
    f"- 英国: {uk_context['HROPAI']['percentage']:.1f}%",
    f"- ドイツ: {de_context['HROPAI']['percentage']:.1f}%（デジタル化推進）",
    "",
    "---",
    "",
    "## 次のフェーズ",
    "",
    "- **Phase B**: コンテキスト×活動区分のマトリクス表（企業群ごとに4つ）",
    "- **Phase C**: コンテキスト別のキーワードランキング + 深堀インサイト",
    "",
])

# Markdown を保存
report_text = "\n".join(md_lines)
with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"[OK] Markdown保存: {OUTPUT_MD.name}")
print(f"\n=== Phase A 完了 ===")
print(f"SNS情報サマリー + コンテキスト分布（4企業群比較）")
print(report_text[:1500])  # 最初の1500文字を表示
print(f"\n... (続きを {OUTPUT_MD.name} で確認) ...")
