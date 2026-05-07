#!/usr/bin/env python3
"""
classify_content.py
Phase2 ②情報分類: 各投稿を「コンテキスト軸」と「活動区分軸」の2軸で分類し、
classified_data_YYYYMM.json として保存する。

分類方法：
  1. キーワードベース分類（高速、低コスト）
  2. LLMハイブリッド分類（confidence < 0.7の場合のみ実行）

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
import json, os, re, sys
from datetime import datetime
from pathlib import Path

# Load .env manually
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

try:
    import anthropic
    HAS_CLAUDE = True
except ImportError:
    HAS_CLAUDE = False

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def _get_arg(flag, default=None):
    try:
        idx = sys.argv.index(flag)
        return sys.argv[idx + 1]
    except (ValueError, IndexError):
        return default

_period = _get_arg('--period') or datetime.now().strftime('%Y%m')
INPUT_FILE  = os.path.join(DATA_DIR, f'raw_data_{_period}.json')
OUTPUT_FILE = os.path.join(DATA_DIR, f'classified_data_{_period}.json')

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
        'results', 'fiscal year', 'annual', 'rolled out', 'implemented',
        '発表', '完了', '公開', 'お知らせ', '結果', '実績', '昨年', '達成', '締結'
    ],
    'Doing': [
        'investing', 'building', 'working', 'continuing', 'driving', 'tackling', 'navigating',
        'transforming', 'reshaping', 'rethinking', 'moving', 'optimizing', 'scaling',
        '取り組んでいる', '進めている', '推進中', '実施中', '変革中', '浸透', '定点観測'
    ],
    'Next': [
        'planning', 'will', 'upcoming', '2026', 'expect', 'commit', 'intend', 'going to',
        'schedule', 'conference', 'summit', 'roadmap', 'goal',
        '予定', '計画', '方針', '目指す', 'これから', '来期', '視野に'
    ],
    'Idea': [
        'exploring', 'discussing', 'considering', 'thinking about', 'question', 'who has',
        'how do', 'what if', 'could', 'thought leadership', 'possibility',
        '検討', '考えている', '議論', '模索', '考察', '可能性'
    ],
    'Issue': [
        'challenge', 'issue', 'problem', 'unfortunate', 'concern', 'risk', 'volatile',
        'skills gap', 'lose jobs', 'layoff', 'cuts', 'must not', 'talent gap', 'resignation',
        '課題', '悩み', '懸念', 'リスク', '問題', '困難', 'ボトルネック', '未着手'
    ],
}


class LLMClassifier:
    """Claude APIを使用した精密分類（実行強度優先の原則準拠）"""

    SYSTEM_PROMPT = """あなたはLinkedIn投稿を分析し、以下の2つを判定する専門家です：

【責務1】7つのコンテキスト軸での分類
【責務2】実行レベル（Done/Doing/Next/Idea/Issue）の自動判定

---

## 実行強度の階層（優先順位）
複数の要素が混在する場合は、以下の順序で判定する：
1. **Done**（最強：事実としての結果）→ 数値成果・過去時制
2. **Doing**（強：現在進行中のリソース投入）→ パイロット・試行中
3. **Next**（中：公式な意思決定）→ 予定・計画
4. **Issue**（弱：負の現状分析）→ 課題・停滞
5. **Idea**（最弱：一般論・感想）→ 理想・提案

## 決定打となる言語的トリガー

| ラベル | キーワード | 決定要素 |
|--------|-----------|--------|
| **Done** | Completed, Achieved, 完了, 達成, 公表 | **数値成果**（20%増など）+ **過去の日付** |
| **Doing** | Optimizing, Testing, 推進中, 試行, 展開 | **現在のフェーズ明記**（～の段階にある） |
| **Next** | Decided, Launching, Will, 予定, 決定 | **具体的な開始時期**（来期、Q3など） |
| **Idea** | Should be, Concept, べきである, 理想 | **自社スケジュール/リソースの欠如** |
| **Issue** | Difficulty, Struggling, 課題, 懸念, 不足 | **「～できない」「停滞」の記述** |

## 紛らわしいペアの最終解決ルール

### ① Doing vs Next（現在進行 vs 将来計画）
- **Doing昇格条件**：「We are currently」「パイロット版を運用中」など、**リソースが既に動いている**証拠
- **Next維持条件**：「We will」「Plan to」「来期から」など、**開始のトリガーが未来**

### ② Issue vs Doing（課題報告 vs 対応行動）
- **アクション優先の原則**：「課題X、対策Yを実施中」の場合は→ **Doing**（Issue を内包）
- **純粋なIssue**：解決策に言及せず、ボトルネック分析のみで終わる

### ③ Done vs Idea（自社実績 vs 他社事例・一般論）
- **Done判定の必須条件**：**主語が自社（We/Our）** かつ **過去・完了時制**
- **Idea判定**：主語が三人称（The industry, Others）、または仮定法（should have）

---

## 判定時の推論プロセス

常に以下のステップで判定を実施：
1. **要素分析**：投稿に含まれるキーワード・時制を列挙
2. **優先順位適用**：複数の要素がある場合、実行強度で優先判定
3. **決定打確認**：数値、日付、リソース投入の有無を確認
4. **主語確認**：自社か他社か、一般論か具体的か

---

投稿テキストを分析し、以下の形式で回答してください（JSON形式）：
activity_level: Done|Doing|Next|Idea|Issue
confidence: 0.0-1.0 の数値
reasoning: 判定根拠

---

例：
activity_level: Done
confidence: 0.95
reasoning: 過去形「導入しました」と数値成果「30%削減」から、実行完了と判定
"""

    def __init__(self):
        if HAS_CLAUDE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)
            else:
                self.client = None
        else:
            self.client = None

    def classify_activity(self, text: str) -> dict:
        """LLMで活動区分を精密判定"""
        if not self.client:
            return {'activity': None, 'confidence': 0.0, 'method': 'keyword'}

        try:
            message = self.client.messages.create(
                model="claude-opus-4-7",
                max_tokens=300,
                system=self.SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"以下のLinkedIn投稿を分析してください：\n\n{text}"
                }]
            )

            response_text = message.content[0].text

            result = {}

            # Try JSON parse first (model sometimes returns JSON)
            import re as _re
            json_match = _re.search(r'\{[^{}]+\}', response_text, _re.DOTALL)
            if json_match:
                try:
                    import json as _json
                    parsed = _json.loads(json_match.group())
                    result['activity_level'] = parsed.get('activity_level', parsed.get('activity'))
                    result['confidence'] = float(parsed.get('confidence', 0.5))
                    result['reasoning'] = parsed.get('reasoning', '')
                except Exception:
                    pass

            # Fallback: plain text key: value parsing
            if not result.get('activity_level'):
                for line in response_text.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().strip('"\',')
                        value = value.strip().strip('"\',')
                        if key == 'activity_level':
                            result['activity_level'] = value
                        elif key == 'confidence':
                            try:
                                result['confidence'] = float(value)
                            except ValueError:
                                result['confidence'] = 0.5
                        elif key == 'reasoning':
                            result['reasoning'] = value

            return {
                'activity': result.get('activity_level'),
                'confidence': result.get('confidence', 0.5),
                'reasoning': result.get('reasoning', ''),
                'method': 'llm'
            }
        except Exception as e:
            print(f"[WARNING] LLM分類失敗: {e}")
            return {'activity': None, 'confidence': 0.0, 'method': 'error'}


def classify_post(text: str, use_llm: bool = True) -> dict:
    """テキストをコンテキスト軸・活動区分軸で分類する"""
    if not text:
        return {'context': None, 'activity': None, 'confidence': 0.0}

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

    # Confidence 計算（スコア差分に基づく）
    sorted_scores = sorted(act_scores.values(), reverse=True)
    if len(sorted_scores) >= 2:
        top_score = sorted_scores[0]
        second_score = sorted_scores[1]
        # スコア差が大きいほど信頼度高い（同点や接近 → 低信頼）
        score_gap = top_score - second_score
        act_confidence = min(1.0, (score_gap / (top_score + 1)) * 2) if top_score > 0 else 0.0
    elif sorted_scores:
        # 1つのカテゴリのみがスコアを持つ場合は高信頼
        act_confidence = min(1.0, sorted_scores[0] / 2) if sorted_scores[0] > 0 else 0.0
    else:
        act_confidence = 0.0

    # LLMでの精密判定（confidence < 0.7 かつLLMが利用可能な場合）
    llm_result = None
    if use_llm and act_confidence < 0.7 and HAS_CLAUDE:
        llm_classifier = LLMClassifier()
        llm_result = llm_classifier.classify_activity(text)
        if llm_result['activity']:
            best_act = llm_result['activity']
            act_confidence = llm_result['confidence']

    return {
        'context': best_ctx,
        'activity': best_act,
        'confidence': act_confidence,
        'ctx_scores': ctx_scores,
        'act_scores': act_scores,
        'llm_used': llm_result is not None,
        'llm_reasoning': llm_result.get('reasoning', '') if llm_result else None,
    }


def main(use_llm=False, llm_priority=None):
    """
    Args:
        use_llm: If True, use LLM for low-confidence cases
        llm_priority: 'idea_next' to prioritize Idea/Next pairs only, None for all low-conf
    """
    with open(INPUT_FILE, encoding='utf-8') as f:
        posts = json.load(f)

    classified = []
    llm_applied_count = 0

    for post in posts:
        if not post.get('is_work_related'):
            continue  # 仕事と無関係な投稿はスキップ

        post_action = post.get('post_action', 'posted on the topic')

        # Determine if LLM should be applied to this post
        apply_llm = use_llm
        if use_llm and llm_priority == 'idea_next':
            # Only apply LLM to Idea/Next posts (from previous classification)
            prev_activity = post.get('activity_class')
            apply_llm = (prev_activity in ('Idea', 'Next'))

        result = classify_post(post.get('text', ''), use_llm=apply_llm)

        # posted on the topic / commented on → コンテキスト＋活動区分の両軸を分類
        # shared / liked the post           → コンテキスト軸のみ（活動区分なし）
        if post_action in ('posted on the topic', 'commented on'):
            classified.append({
                **post,
                'context_axis': result['context'],
                'activity_class': result['activity'],
                'confidence_activity': result.get('confidence', 0.0),
                'llm_used': result.get('llm_used', False),
                'llm_reasoning': result.get('llm_reasoning'),
                '_ctx_scores': result['ctx_scores'],
                '_act_scores': result['act_scores'],
            })
        else:
            classified.append({
                **post,
                'context_axis': result['context'],
                'activity_class': None,
                'confidence_activity': 0.0,
                'llm_used': False,
                '_ctx_scores': result['ctx_scores'],
            })

    with open(OUTPUT_FILE, encoding='utf-8', mode='w') as f:
        json.dump(classified, f, ensure_ascii=False, indent=2)

    # 集計表示
    from collections import Counter
    ctx_counter = Counter(p['context_axis'] for p in classified)
    # activity_class が None (shared/liked) を除いてカウント
    act_counter = Counter(p['activity_class'] for p in classified if p.get('activity_class'))
    post_action_counter = Counter(p.get('post_action', 'posted on the topic') for p in classified)
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
    summary_lines.append('--- Post Action Pattern ---')
    for action in ['posted on the topic', 'commented on', 'shared', 'liked the post']:
        count = post_action_counter.get(action, 0)
        summary_lines.append(f'  {action:25s}: {count:3d} {"#" * min(count, 40)}')

    summary_lines.append('')
    summary_lines.append('--- Activity Class (posted on the topic / commented on only) ---')
    for act in ['Done', 'Doing', 'Next', 'Idea', 'Issue']:
        count = act_counter.get(act, 0)
        summary_lines.append(f'  {act:6s}: {count:2d} {"#" * count}')

    summary_lines.append('')
    summary_lines.append('--- By Country ---')
    for country, count in sorted(country_counter.items()):
        summary_lines.append(f'  {country}: {count:2d} {"#" * count}')

    # LLM使用統計
    llm_count = sum(1 for p in classified if p.get('llm_used', False))
    low_conf_count = sum(1 for p in classified if p.get('confidence_activity', 0.0) < 0.7)

    summary_lines.append('')
    summary_lines.append('--- Classification Method ---')
    summary_lines.append(f'  Keyword-based: {len(classified) - llm_count} posts')
    summary_lines.append(f'  LLM-enhanced:  {llm_count} posts (low confidence < 0.7)')
    summary_lines.append(f'  Total:         {len(classified)} posts')

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
    import sys
    # Command-line options:
    # --llm: enable LLM for all low-confidence posts
    # --llm-idea-next: enable LLM only for Idea/Next posts (priority mode)
    use_llm = '--llm' in sys.argv or '--llm-idea-next' in sys.argv
    llm_priority = 'idea_next' if '--llm-idea-next' in sys.argv else None
    main(use_llm=use_llm, llm_priority=llm_priority)
