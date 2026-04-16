#!/usr/bin/env python3
"""
generate_analytics.py
Phase2 ③深層分析: 国別比較、時系列分析、キーワード分析、役割分析

出力:
  - analytics_202604.json (詳細分析結果)
  - analytics_summary_202604.txt (テキストサマリー)
"""
import json
import os
from pathlib import Path
from collections import Counter
from datetime import datetime
import re

DATA_DIR = Path(__file__).parent.parent / "data"
INPUT_FILE = DATA_DIR / "classified_data_202604.json"
OUTPUT_FILE = DATA_DIR / "analytics_202604.json"
SUMMARY_FILE = DATA_DIR / "analytics_summary_202604.txt"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# データ読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with open(INPUT_FILE, encoding="utf-8") as f:
    posts = json.load(f)

print(f"[OK] Loaded {len(posts)} posts from {INPUT_FILE.name}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 国別傾向分析
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

by_country = {}
for post in posts:
    country = post.get("country", "Unknown")
    if country not in by_country:
        by_country[country] = {
            "count": 0,
            "context": Counter(),
            "activity": Counter(),
            "texts": []
        }
    by_country[country]["count"] += 1
    by_country[country]["context"][post.get("context_axis")] += 1
    by_country[country]["activity"][post.get("activity_class")] += 1
    by_country[country]["texts"].append(post.get("text", ""))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. キーワード抽出（全体）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_keywords(texts, top_n=30):
    """テキストから頻出キーワードを抽出"""
    all_words = []
    stopwords = {
        "the", "a", "is", "are", "and", "or", "of", "in", "to", "for",
        "we", "our", "your", "that", "this", "as", "be", "by", "at",
        "に", "を", "で", "が", "は", "の", "と", "も", "から", "など",
        "it", "from", "on", "with", "an", "have", "been", "was", "were"
    }

    for text in texts:
        if not text:
            continue
        # Split by whitespace and punctuation
        words = re.findall(r'\b\w+\b', text.lower())
        all_words.extend([w for w in words if w not in stopwords and len(w) > 2])

    return Counter(all_words).most_common(top_n)

global_keywords = extract_keywords([p.get("text", "") for p in posts])

# Country-specific keywords
country_keywords = {}
for country, data in by_country.items():
    country_keywords[country] = extract_keywords(data["texts"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. コンテキスト軸の国別比較
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
for country, data in by_country.items():
    context_by_country[country] = {
        ctx: data["context"].get(ctx, 0)
        for ctx in context_labels.keys()
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 役割分析：労務管理中心 vs 経営パートナー
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# キーワードベース分類
admin_keywords = [
    "compliance", "payroll", "benefits", "policy", "hr operations",
    "給与", "人事手続", "労務", "採用事務", "勤務管理"
]
strategic_keywords = [
    "strategy", "transformation", "talent", "culture", "leadership", "innovation",
    "戦略", "変革", "人材戦略", "リーダーシップ", "経営", "AI", "組織"
]

def classify_role_focus(text):
    """投稿の焦点を分類：Admin（労務管理）vs Strategic（経営パートナー）"""
    if not text:
        return "Unknown"
    text_lower = text.lower()
    admin_score = sum(1 for kw in admin_keywords if kw.lower() in text_lower)
    strategic_score = sum(1 for kw in strategic_keywords if kw.lower() in text_lower)

    if strategic_score > admin_score:
        return "Strategic"
    elif admin_score > strategic_score:
        return "Admin"
    else:
        return "Neutral"

role_focus = Counter(classify_role_focus(p.get("text", "")) for p in posts)
role_focus_by_country = {}
for country, data in by_country.items():
    role_counts = Counter(classify_role_focus(text) for text in data["texts"])
    role_focus_by_country[country] = dict(role_counts)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 結果を JSON で保存
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

analytics = {
    "metadata": {
        "generated_at": datetime.now().isoformat(),
        "total_posts": len(posts),
        "period": "202604"
    },
    "country_overview": {
        country: {
            "count": data["count"],
            "context_dist": dict(data["context"]),
            "activity_dist": dict(data["activity"]),
            "role_focus": role_focus_by_country.get(country, {}),
            "top_keywords": [(kw, count) for kw, count in country_keywords[country][:15]]
        }
        for country, data in by_country.items()
    },
    "global_metrics": {
        "context_distribution": dict(Counter(p.get("context_axis") for p in posts)),
        "activity_distribution": dict(Counter(p.get("activity_class") for p in posts)),
        "role_focus_distribution": dict(role_focus),
        "top_keywords": [(kw, count) for kw, count in global_keywords[:20]]
    },
    "context_by_country": context_by_country
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(analytics, f, ensure_ascii=False, indent=2)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テキストサマリーを出力
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

summary_lines = [
    "=== CHRO-SIE Analytics Summary (202604) ===",
    "",
    f"Total Posts: {len(posts)}",
    "",
    "--- By Country ---",
]

for country in sorted(by_country.keys()):
    data = by_country[country]
    summary_lines.append(f"\n{country}: {data['count']} posts")

    # Top context
    top_ctx = data["context"].most_common(2)
    for ctx, count in top_ctx:
        label = context_labels.get(ctx, ctx)
        summary_lines.append(f"  - {ctx} ({label}): {count}")

    # Top keywords
    top_kw = country_keywords[country][:5]
    keywords_str = ", ".join(f"{kw}({cnt})" for kw, cnt in top_kw)
    summary_lines.append(f"  - Keywords: {keywords_str}")

summary_lines.extend([
    "",
    "--- Role Focus Analysis ---",
    f"Strategic (Emerging/Transformational): {role_focus['Strategic']}",
    f"Admin (Operational/Compliance): {role_focus['Admin']}",
    f"Neutral: {role_focus['Neutral']}",
])

summary_text = "\n".join(summary_lines)
with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
    f.write(summary_text)

# Print summary
for line in summary_lines:
    try:
        print(line.encode('utf-8', errors='replace').decode('utf-8'))
    except:
        print(line.encode('ascii', errors='replace').decode('ascii'))

print(f"\n[OK] Saved: {OUTPUT_FILE}")
print(f"[OK] Saved: {SUMMARY_FILE}")
