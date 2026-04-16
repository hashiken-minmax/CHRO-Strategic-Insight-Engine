#!/usr/bin/env python3
"""
classify_content.py
Phase2 ②情報分類: 各投稿を「コンテキスト軸」と「活動区分軸」の2軸で分類し、
classified_data_YYYYMM.json として保存する。

コンテキスト軸 (7分類):
  S&G  : Succession & Governance
  A&S  : Agenda & Strategy
  HRT  : HR Transformation
  WTT  : Workforce & Talent Transformation
  TMD  : Talent Market & Development
  HROPAI: HR Operation & AI
  C&E  : Culture & Engagement

活動区分:
  Done  : 完了した取り組み
  Doing : 進行中
  Next  : 着手予定
  Idea  : 検討中
  Issue : 課題・悩み
"""
import json, os, re
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
INPUT_FILE = os.path.join(DATA_DIR, 'raw_data_202604.json')
OUTPUT_FILE = os.path.join(DATA_DIR, 'classified_data_202604.json')

# ─── 分類ロジック（キーワードベース + ルールベース） ─────────────────────────

CONTEXT_KEYWORDS = {
    'S&G': [
        'succession', 'governance', 'board', 'supervisory board', 'contract', 'mandate',
        'サクセッション', '取締役会', '指名', '後継', '役員'
    ],
    'A&S': [
        'strategy', 'business strategy', 'workforce planning', 'talent strategy', 'ROI',
        'investment', 'shareholder', 'earnings', 'financial', 'ebitda', 'value creation',
        '経営戦略', '人材戦略', '企業価値', '投資', '戦略'
    ],
    'HRT': [
        'HR transformation', 'HR function', 'HR restructur', 'people ops', 'HRBP',
        'HR operating', 'HR organ', 'CPO', 'CHRO role', 'merge', 'restructur',
        '人事機能', '人事変革', '人事組織', '人事部門'
    ],
    'WTT': [
        'workforce', 'talent portfolio', 'reskill', 'upskill', 'redepl', 're-skill', 're-deploy',
        'job cuts', 'layoff', 'redundanc', 'workforce reduction', 'roles redesign', 're-design',
        '人材ポートフォリオ', 'リスキリング', '人員削減', 'ワークフォース', '役割再設計'
    ],
    'TMD': [
        'talent market', 'recruiting', 'hiring', 'intern', 'campus', 'career', 'development',
        'learning', 'training', 'skills-first', 'talent marketplace', 'internal mobility',
        'pipeline', 'leadership development', 'L&D',
        '採用', 'キャリア', '人材育成', '育成', '学習', 'リーダーシップ開発', '研修', '内部労働市場'
    ],
    'HROPAI': [
        'AI tool', 'AI platform', 'digital assistant', 'AskHR', 'AI-first', 'AI-driven',
        'AI transformation', 'AI implementation', 'automation', 'AI capex', 'agentic', 'agent',
        'HR tech', 'people analytics', 'AI performance', 'AI skill', '4R',
        'AI活用', 'AI導入', 'デジタル', '人事テック', '業務効率', 'DX'
    ],
    'C&E': [
        'culture', 'engagement', 'purpose', 'value', 'wellbeing', 'inclusion', 'diversity',
        'employee experience', 'belonging', 'uncorporate', 'ceremony', 'community',
        '文化', '企業文化', 'エンゲージメント', 'ウェルビーイング', 'パーパス', 'バリュー',
        'インクルージョン', 'ダイバーシティ', '入社式', '価値観'
    ],
}

ACTIVITY_KEYWORDS = {
    'Done': [
        'announced', 'launched', 'published', 'released', 'completed', 'welcomed', 'saved',
        'achieved', 'recognized', 'extended', 'awarded', 'named', 'handled', 'calculated',
        'results', 'fiscal year', 'annual',
        '発表', '完了', '公開', 'お知らせ', '結果', '実績', '昨年', '達成'
    ],
    'Doing': [
        'investing', 'building', 'working', 'continuing', 'driving', 'tackling', 'navigating',
        'transforming', 'reshaping', 'rethinking', 'moving',
        '取り組んでいる', '進めている', '推進中', '実施中', '変革中'
    ],
    'Next': [
        'planning', 'will', 'upcoming', '2026', 'expect', 'commit', 'intend', 'going to',
        'schedule', 'conference', 'summit',
        '予定', '計画', '方針', '目指す', 'これから'
    ],
    'Idea': [
        'exploring', 'discussing', 'considering', 'thinking about', 'question', 'who has',
        'how do', 'what if', 'could',
        '検討', '考えている', '議論', '模索'
    ],
    'Issue': [
        'challenge', 'issue', 'problem', 'unfortunate', 'concern', 'risk', 'volatile',
        'skills gap', 'lose jobs', 'layoff', 'cuts', 'must not',
        '課題', '悩み', '懸念', 'リスク', '問題', '困難'
    ],
}


def classify_post(text: str) -> dict:
    """テキストをコンテキスト軸・活動区分軸で分類する"""
    if not text:
        return {'context': None, 'activity': None}

    text_lower = text.lower()

    # コンテキスト軸スコアリング
    ctx_scores = {k: 0 for k in CONTEXT_KEYWORDS}
    for ctx, keywords in CONTEXT_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                ctx_scores[ctx] += 1

    # 活動区分スコアリング
    act_scores = {k: 0 for k in ACTIVITY_KEYWORDS}
    for act, keywords in ACTIVITY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                act_scores[act] += 1

    # 最高スコアを選択（同点の場合は優先順位で解決）
    ctx_priority = ['HROPAI', 'WTT', 'HRT', 'A&S', 'TMD', 'C&E', 'S&G']
    act_priority = ['Done', 'Doing', 'Next', 'Idea', 'Issue']

    best_ctx = max(ctx_scores, key=lambda k: (ctx_scores[k], -ctx_priority.index(k) if k in ctx_priority else -99))
    best_act = max(act_scores, key=lambda k: (act_scores[k], -act_priority.index(k) if k in act_priority else -99))

    # スコアが0の場合はデフォルト
    if ctx_scores[best_ctx] == 0:
        best_ctx = 'A&S'  # デフォルト
    if act_scores[best_act] == 0:
        best_act = 'Doing'  # デフォルト

    return {
        'context': best_ctx,
        'activity': best_act,
        'ctx_scores': ctx_scores,
        'act_scores': act_scores,
    }


def main():
    with open(INPUT_FILE, encoding='utf-8') as f:
        posts = json.load(f)

    classified = []
    for post in posts:
        if not post.get('is_work_related'):
            continue  # 仕事と無関係な投稿はスキップ

        result = classify_post(post.get('text', ''))
        classified.append({
            **post,
            'context_axis': result['context'],
            'activity_class': result['activity'],
            '_ctx_scores': result['ctx_scores'],
            '_act_scores': result['act_scores'],
        })

    with open(OUTPUT_FILE, encoding='utf-8', mode='w') as f:
        json.dump(classified, f, ensure_ascii=False, indent=2)

    # 集計表示
    from collections import Counter
    ctx_counter = Counter(p['context_axis'] for p in classified)
    act_counter = Counter(p['activity_class'] for p in classified)
    country_counter = Counter(p['country'] for p in classified)

    ctx_labels = {
        'S&G': 'Succession & Governance',
        'A&S': 'Agenda & Strategy',
        'HRT': 'HR Transformation',
        'WTT': 'Workforce & Talent Transformation',
        'TMD': 'Talent Market & Development',
        'HROPAI': 'HR Operation & AI',
        'C&E': 'Culture & Engagement',
    }

    # Write summary to file to avoid encoding issues
    summary_lines = [
        f'=== Classified: {len(classified)} posts ===',
        '',
        '--- Context Axis ---',
    ]
    for ctx, label in ctx_labels.items():
        count = ctx_counter.get(ctx, 0)
        summary_lines.append(f'  {ctx:8s} ({label:40s}): {count:2d} {"#" * count}')

    summary_lines.append('')
    summary_lines.append('--- Activity Class ---')
    for act in ['Done', 'Doing', 'Next', 'Idea', 'Issue']:
        count = act_counter.get(act, 0)
        summary_lines.append(f'  {act:6s}: {count:2d} {"#" * count}')

    summary_lines.append('')
    summary_lines.append('--- By Country ---')
    for country, count in sorted(country_counter.items()):
        summary_lines.append(f'  {country}: {count:2d} {"#" * count}')

    summary_lines.append('')
    summary_lines.append(f'[OK] Saved: {OUTPUT_FILE}')

    summary_text = '\n'.join(summary_lines)

    summary_path = os.path.join(DATA_DIR, 'classify_summary_202604.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_text)

    # Print ASCII-safe version
    for line in summary_lines:
        print(line.encode('ascii', errors='replace').decode('ascii'))

if __name__ == '__main__':
    main()
