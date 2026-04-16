#!/usr/bin/env python3
"""
generate_analytics_phaseB.py
Phase B④深層分析 - コンテキスト × 活動区分のマトリクス分析

4企業群（JP, US, UK, DE）について、コンテキスト×活動区分のマトリクスを作成
7コンテキスト × 5活動区分 = 各企業群ごとに1つのマトリクス表

出力:
  - analytics_phaseB_202604.json (マトリクス分析結果JSON)
  - analytics_phaseB_202604.md (Markdown形式のマトリクス表)
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Windows UTF-8 対応
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = Path(__file__).parent.parent / "data"
CLASSIFIED_FILE = DATA_DIR / "classified_data_202604.json"
OUTPUT_JSON = DATA_DIR / "analytics_phaseB_202604.json"
OUTPUT_MD = DATA_DIR / "analytics_phaseB_202604.md"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# データ読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with open(CLASSIFIED_FILE, encoding="utf-8") as f:
    posts = json.load(f)

print(f"[OK] {len(posts)}件のポスト読み込み完了")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase B: コンテキスト × 活動区分のマトリクス分析
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

activity_labels = {
    'Done': '完了',
    'Doing': '進行中',
    'Next': '着手予定',
    'Idea': '検討中',
    'Issue': '課題・懸念'
}

ctx_order = ['A&S', 'TMD', 'HROPAI', 'C&E', 'WTT', 'HRT', 'S&G']
activity_order = ['Done', 'Doing', 'Next', 'Idea', 'Issue']

matrix_by_country = {}

for country in ['JP', 'US', 'UK', 'DE']:
    country_posts = [p for p in posts if p.get('country') == country and p.get('is_work_related')]

    # マトリクス初期化
    matrix = {}
    for ctx in ctx_order:
        matrix[ctx] = {}
        for act in activity_order:
            matrix[ctx][act] = 0

    # マトリクスに集計
    for post in country_posts:
        ctx = post.get('context_axis')
        act = post.get('activity_class')  # JSONファイルのフィールド名は activity_class

        if ctx in matrix and act in matrix[ctx]:
            matrix[ctx][act] += 1

    # 行合計と列合計を計算
    row_totals = {}
    col_totals = {act: 0 for act in activity_order}

    for ctx in ctx_order:
        row_total = sum(matrix[ctx].values())
        row_totals[ctx] = row_total
        for act in activity_order:
            col_totals[act] += matrix[ctx][act]

    grand_total = sum(row_totals.values())

    matrix_by_country[country] = {
        'matrix': matrix,
        'row_totals': row_totals,
        'col_totals': col_totals,
        'grand_total': grand_total,
        'total_posts': len(country_posts)
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 結果をJSON保存
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

analysis_result = {
    "metadata": {
        "generated_at": datetime.now().isoformat(),
        "period": "202604",
        "phase": "B",
        "description": "Context × Activity Matrix Analysis"
    },
    "matrix_by_country": {}
}

for country, data in matrix_by_country.items():
    analysis_result["matrix_by_country"][country] = {
        "matrix": data['matrix'],
        "row_totals": data['row_totals'],
        "col_totals": data['col_totals'],
        "grand_total": data['grand_total'],
        "total_posts": data['total_posts']
    }

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(analysis_result, f, ensure_ascii=False, indent=2)

print(f"[OK] JSON保存: {OUTPUT_JSON.name}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Markdown形式でレポート作成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

md_lines = [
    "# CHRO トレンド分析 - Phase B",
    "## コンテキスト × 活動区分のマトリクス分析",
    "",
    f"**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
    f"**対象期間**: 2026年3月17日 ～ 2026年4月16日",
    "",
    "---",
    "",
]

country_names = {'JP': '日本', 'US': '米国', 'UK': '英国', 'DE': 'ドイツ'}

for country in ['JP', 'US', 'UK', 'DE']:
    data = matrix_by_country[country]
    matrix = data['matrix']
    row_totals = data['row_totals']
    col_totals = data['col_totals']
    grand_total = data['grand_total']

    country_ja = country_names[country]

    md_lines.extend([
        f"## {country_ja}（{country}）のコンテキスト × 活動区分マトリクス",
        "",
        f"**総ポスト数**: {grand_total}件",
        "",
        "| コンテキスト | Done | Doing | Next | Idea | Issue | 計 |",
        "|------------|------|-------|------|------|-------|-----|",
    ])

    # データ行
    for ctx in ctx_order:
        row_data = [
            f"**{ctx}**",
            str(matrix[ctx]['Done']),
            str(matrix[ctx]['Doing']),
            str(matrix[ctx]['Next']),
            str(matrix[ctx]['Idea']),
            str(matrix[ctx]['Issue']),
            str(row_totals[ctx])
        ]
        md_lines.append("| " + " | ".join(row_data) + " |")

    # 合計行
    col_row = ["**合計**"]
    for act in activity_order:
        col_row.append(str(col_totals[act]))
    col_row.append(str(grand_total))
    md_lines.append("| " + " | ".join(col_row) + " |")

    md_lines.extend([
        "",
        "### インサイト",
        "",
    ])

    # インサイト生成
    if grand_total > 0:
        # 最大値を抽出
        max_cell = {'ctx': None, 'act': None, 'value': 0}
        for ctx in ctx_order:
            for act in activity_order:
                if matrix[ctx][act] > max_cell['value']:
                    max_cell = {'ctx': ctx, 'act': act, 'value': matrix[ctx][act]}

        # 最多活動区分
        max_activity = max(activity_order, key=lambda x: col_totals[x])
        max_activity_count = col_totals[max_activity]

        # 最多コンテキスト
        max_context = max(ctx_order, key=lambda x: row_totals[x])
        max_context_count = row_totals[max_context]

        md_lines.extend([
            f"- **最多コンテキスト**: {max_context} ({max_context_count}件, {100*max_context_count/grand_total:.1f}%)",
            f"- **最多活動区分**: {activity_labels[max_activity]} ({max_activity_count}件, {100*max_activity_count/grand_total:.1f}%)",
            f"- **最大セル**: {max_cell['ctx']} × {activity_labels[max_cell['act']]} ({max_cell['value']}件)",
            "",
            "---",
            "",
        ])
    else:
        md_lines.extend([
            "（ポスト数がありません）",
            "",
            "---",
            "",
        ])

# 最後に全体の比較分析
md_lines.extend([
    "## 4企業群の比較分析",
    "",
    "### コンテキスト別の国別比較",
    "",
])

for ctx in ctx_order:
    md_lines.append(f"**{ctx}（{context_labels[ctx]}）**")
    for country in ['JP', 'US', 'UK', 'DE']:
        count = matrix_by_country[country]['row_totals'][ctx]
        total = matrix_by_country[country]['grand_total']
        pct = 100 * count / total if total > 0 else 0
        country_ja = country_names[country]
        md_lines.append(f"- {country_ja}: {count}件（{pct:.1f}%）")
    md_lines.append("")

md_lines.extend([
    "### 活動区分別の国別比較",
    "",
])

for act in activity_order:
    md_lines.append(f"**{activity_labels[act]}（{act}）**")
    for country in ['JP', 'US', 'UK', 'DE']:
        count = matrix_by_country[country]['col_totals'][act]
        total = matrix_by_country[country]['grand_total']
        pct = 100 * count / total if total > 0 else 0
        country_ja = country_names[country]
        md_lines.append(f"- {country_ja}: {count}件（{pct:.1f}%）")
    md_lines.append("")

# Markdown を保存
report_text = "\n".join(md_lines)
with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"[OK] Markdown保存: {OUTPUT_MD.name}")
print(f"\n=== Phase B 完了 ===")
print(f"コンテキスト × 活動区分のマトリクス分析（4企業群比較）")
print(report_text[:2000])  # 最初の2000文字を表示
print(f"\n... (続きを {OUTPUT_MD.name} で確認) ...")
