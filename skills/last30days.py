#!/usr/bin/env python3
"""
skills/last30days.py
CHRO-SIE Phase2 データ収集スキル

各CHROのX(Twitter)・LinkedInから直近30日間の投稿全文を取得する。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
必要なAPIキー・認証情報（取得方法は README_SETUP.md 参照）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【X (Twitter) - 公式API】
  TWITTER_BEARER_TOKEN      : developer.x.com で取得
  TWITTER_API_KEY           : 同上
  TWITTER_API_SECRET        : 同上
  TWITTER_ACCESS_TOKEN      : 同上
  TWITTER_ACCESS_TOKEN_SECRET: 同上

【LinkedIn - LinkupAPI キー方式】
  LINKUPAPI_KEY             : LinkupAPI Dashboard → API Access → API Keys で取得
  ※ 完全自動化対応・セキュア

【LinkedIn - ブラウザセッション方式（非推奨）】
  LINKEDIN_EMAIL            : LinkedInログインメール
  LINKEDIN_PASSWORD         : LinkedInパスワード
  ※ stickerdaniel/linkedin-mcp-server が初回ログイン後にCookieを保存

【Exa.ai - 公開コンテンツ検索】
  EXA_API_KEY               : dashboard.exa.ai で取得（無料1000req/月）

【非公式 twikit（コスト0、ToS注意）】
  TWITTER_USERNAME          : @ハンドル
  TWITTER_EMAIL             : メールアドレス
  TWITTER_PASSWORD          : パスワード
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
import csv
import datetime
import time
import sys
import re
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Windows コンソールを UTF-8 対応に
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ─── 設定 ────────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent.parent
MASTER_LIST = PROJECT_DIR / "master_list.csv"
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# .env ファイルを読み込む
load_dotenv(PROJECT_DIR / ".env")

def _get_arg(flag, default=None):
    try:
        idx = sys.argv.index(flag)
        return sys.argv[idx + 1]
    except (ValueError, IndexError):
        return default

_end_arg   = _get_arg('--end-date')
_start_arg = _get_arg('--start-date')
_period_arg = _get_arg('--period')

TODAY      = datetime.date.fromisoformat(_end_arg)   if _end_arg   else datetime.date.today()
START_DATE = datetime.date.fromisoformat(_start_arg) if _start_arg else TODAY - datetime.timedelta(days=30)
YYYYMM     = _period_arg if _period_arg else TODAY.strftime("%Y%m")

# 環境変数から認証情報を取得
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
EXA_API_KEY = os.getenv("EXA_API_KEY")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
LINKUPAPI_KEY = os.getenv("LINKUPAPI_KEY")
LINKUPAPI_LOGIN_TOKEN = os.getenv("LINKUPAPI_LOGIN_TOKEN")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_EMAIL_UNOFFICIAL = os.getenv("TWITTER_EMAIL")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")


# ─── ヘルパー: X API メタデータからポスト行動を判定 ────────────────────────────
def classify_post_action_from_x_metadata(tweet: dict) -> str:
    """
    X API v2 のメタデータ（in_reply_to_user_id, referenced_tweets）から
    ポスト行動パターンを正確に判定する
    """
    # リプライかどうか
    if tweet.get("in_reply_to_user_id"):
        return "commented on"

    # referenced_tweets をチェック（リツイート、引用など）
    referenced = tweet.get("referenced_tweets", [])
    if referenced:
        for ref in referenced:
            ref_type = ref.get("type", "")
            # retweeted または quoted は "shared" に分類
            if ref_type in ("retweeted", "quoted"):
                return "shared"

    # 上記いずれでもない → 原始投稿
    return "posted on the topic"


# ─── モジュール1: X API v2（公式）────────────────────────────────────────────
def fetch_x_official(handle: str, person: str, company: str, country: str) -> list[dict]:
    """
    X API v2 の Recent Search を使って直近投稿を取得する。
    Bearer Token が必要。
    メタデータ (in_reply_to_user_id, referenced_tweets) も取得し、
    ポスト行動パターンを正確に判定する。
    """
    if not TWITTER_BEARER_TOKEN:
        return []

    try:
        import requests
    except ImportError:
        print("[ERROR] requests ライブラリが必要: pip install requests")
        return []

    handle_clean = handle.lstrip("@")
    query = f"from:{handle_clean} -is:retweet"
    start_time = START_DATE.isoformat() + "T00:00:00Z"

    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    params = {
        "query": query,
        "start_time": start_time,
        "max_results": 100,
        "tweet.fields": "created_at,text,public_metrics,entities,in_reply_to_user_id,referenced_tweets",
        "expansions": "author_id,referenced_tweets.id",
        "user.fields": "name,username",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[ERROR] X API 取得失敗 ({handle}): {e}")
        return []

    posts = []
    for tweet in data.get("data", []):
        # ポスト行動パターンを API メタデータから判定
        post_action = classify_post_action_from_x_metadata(tweet)

        posts.append({
            "account": f"@{handle_clean}",
            "person": person,
            "company": company,
            "country": country,
            "date": tweet.get("created_at", "")[:10],
            "text": tweet.get("text", ""),
            "is_work_related": None,  # 後段のLLMフィルタリングで判定
            "post_action": post_action,  # API メタデータから判定
            "source": "X",
            "tweet_id": tweet.get("id"),
            "likes": tweet.get("public_metrics", {}).get("like_count"),
            "retweets": tweet.get("public_metrics", {}).get("retweet_count"),
            "in_reply_to_user_id": tweet.get("in_reply_to_user_id"),  # 参考用に保持
            "referenced_tweets": tweet.get("referenced_tweets"),  # 参考用に保持
        })

    print(f"[X-API] @{handle_clean}: {len(posts)} posts")
    return posts


# ─── ヘルパー: twikit メタデータからポスト行動を判定 ──────────────────────────
def classify_post_action_from_twikit(tweet) -> str:
    """
    twikit オブジェクトのメタデータからポスト行動パターンを判定
    """
    # リプライかどうか
    if hasattr(tweet, "in_reply_to_user_id") and tweet.in_reply_to_user_id:
        return "commented on"

    # リツイートかどうか
    if hasattr(tweet, "is_retweet") and tweet.is_retweet:
        return "shared"

    # 引用ツイートかどうか
    if hasattr(tweet, "quoted_tweet") and tweet.quoted_tweet:
        return "shared"

    # 上記いずれでもない → 原始投稿
    return "posted on the topic"


# ─── モジュール2: twikit（非公式、ToS注意）────────────────────────────────────
def fetch_x_twikit(handle: str, person: str, company: str, country: str) -> list[dict]:
    """
    twikit ライブラリを使った非公式Twitter取得。
    APIキー不要・コスト0 だが X の利用規約に反する可能性あり。
    セットアップ: pip install twikit
    メタデータからポスト行動パターンを判定。
    """
    try:
        import asyncio
        from twikit import Client
    except ImportError:
        print("[INFO] twikit 未インストール: pip install twikit")
        return []

    if not (TWITTER_USERNAME and TWITTER_EMAIL_UNOFFICIAL and TWITTER_PASSWORD):
        print("[INFO] TWITTER_USERNAME/EMAIL/PASSWORD が未設定（twikit用）")
        return []

    async def _fetch():
        client = Client("ja")
        cookies_path = PROJECT_DIR / ".twikit_cookies.json"

        try:
            if cookies_path.exists():
                client.load_cookies(str(cookies_path))
            else:
                await client.login(
                    auth_info_1=TWITTER_USERNAME,
                    auth_info_2=TWITTER_EMAIL_UNOFFICIAL,
                    password=TWITTER_PASSWORD,
                )
                client.save_cookies(str(cookies_path))

            handle_clean = handle.lstrip("@")
            user = await client.get_user_by_screen_name(handle_clean)
            tweets = await user.get_tweets("Tweets", count=50)

            results = []
            for tweet in tweets:
                tweet_date = tweet.created_at_datetime.date() if hasattr(tweet, "created_at_datetime") else None
                if tweet_date and tweet_date < START_DATE:
                    continue

                # ポスト行動パターンを twikit メタデータから判定
                post_action = classify_post_action_from_twikit(tweet)

                results.append({
                    "account": f"@{handle_clean}",
                    "person": person,
                    "company": company,
                    "country": country,
                    "date": str(tweet_date) if tweet_date else "",
                    "text": tweet.text,
                    "is_work_related": None,
                    "post_action": post_action,  # メタデータから判定
                    "source": "X",
                    "tweet_id": tweet.id,
                    "likes": getattr(tweet, "favorite_count", None),
                    "retweets": getattr(tweet, "retweet_count", None),
                    "in_reply_to_user_id": getattr(tweet, "in_reply_to_user_id", None),
                    "is_retweet": getattr(tweet, "is_retweet", None),
                })
            return results
        except Exception as e:
            print(f"[ERROR] twikit 取得失敗 ({handle}): {e}")
            return []

    import asyncio
    try:
        posts = asyncio.run(_fetch())
        print(f"[twikit] @{handle.lstrip('@')}: {len(posts)} posts")
        return posts
    except Exception as e:
        print(f"[ERROR] twikit asyncio失敗: {e}")
        return []


# ─── モジュール3: LinkedIn（LinkupAPI）────────────────────────────────────
def fetch_linkedin_linkupapi(linkedin_url: str, person: str, company: str, country: str) -> list[dict]:
    """
    LinkupAPI Search Posts エンドポイントを使ったLinkedIn投稿取得

    事前セットアップ（月初の手動作業）:
      1. python scripts/get_linkedin_token.py を実行
      2. LinkedIn メール・パスワードを入力（ファイルに保存されない）
      3. login_token が .env に自動保存される

    参照: https://docs.linkupapi.com → Content & Posts → Search Posts
    """
    if not LINKUPAPI_KEY:
        print("[WARN] LINKUPAPI_KEY が設定されていません")
        return []

    if not LINKUPAPI_LOGIN_TOKEN:
        print("[WARN] LINKUPAPI_LOGIN_TOKEN が設定されていません")
        print("       月初に: python scripts/get_linkedin_token.py を実行してください")
        return []

    try:
        import requests
    except ImportError:
        print("[ERROR] requests ライブラリが必要: pip install requests")
        return []

    try:
        if not linkedin_url or "linkedin.com" not in linkedin_url:
            print(f"[WARN] LinkedIn URL が無効: {linkedin_url}")
            return []

        print(f"[LinkupAPI-LinkedIn] {linkedin_url} の投稿を取得中...")

        # Search Posts エンドポイント（プロフィール別投稿取得）
        endpoint = "https://api.linkupapi.com/v1/posts/search"
        headers = {
            "x-api-key": LINKUPAPI_KEY,
            "Content-Type": "application/json"
        }

        # 国コードマッピング（master_list の country → LinkupAPI country code）
        country_map = {"US": "US", "UK": "UK", "JP": "US", "DE": "DE"}
        proxy_country = country_map.get(country, "US")

        payload = {
            "linkedin_url": linkedin_url,
            "total_results": 50,
            "login_token": LINKUPAPI_LOGIN_TOKEN,
            "country": proxy_country,
            "sort_by": "date_posted",
        }

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print(f"[ERROR] LinkupAPI 認証失敗: login_token が無効または期限切れです")
                print(f"       → python scripts/get_linkedin_token.py を再実行してください")
            elif response.status_code == 402:
                print(f"[ERROR] LinkupAPI クレジット不足")
            else:
                print(f"[ERROR] LinkupAPI エラー ({response.status_code}): {e}")
                print(f"       レスポンス: {response.text[:200]}")
            return []
        except Exception as e:
            print(f"[ERROR] LinkupAPI リクエスト失敗: {e}")
            return []

        # レスポンス処理（Search Posts: data.posts[]）
        posts = []
        posts_raw = data.get("data", {}).get("posts", []) if isinstance(data, dict) else []

        if not posts_raw:
            print(f"[LinkupAPI-LinkedIn] {linkedin_url}: 投稿なし（プロフィール非公開または投稿なし）")
            return []

        for post in posts_raw:
            post_date = post.get("date") or post.get("posted_date", "")
            post_text = post.get("text") or post.get("commentary") or post.get("content", "")

            reactions = post.get("likes", 0) or post.get("reactions", 0) or 0
            comments = post.get("comments", 0) or 0
            shares = post.get("shares", 0) or 0

            # 日付フィルタ（30日以内）
            if post_date:
                try:
                    post_dt = datetime.date.fromisoformat(post_date[:10])
                    if post_dt < START_DATE:
                        continue
                except ValueError:
                    pass

            posts.append({
                "account": linkedin_url,
                "person": person,
                "company": company,
                "country": country,
                "date": post_date[:10] if post_date else "",
                "text": post_text,
                "is_work_related": None,
                "post_action": "posted on the topic",
                "source": "LinkedIn",
                "url": post.get("url") or linkedin_url,
                "likes": reactions,
                "comments_count": comments,
                "shares_count": shares,
                "post_type": post.get("type", "regular"),
            })

        print(f"[LinkupAPI-LinkedIn] {linkedin_url}: {len(posts)} posts取得")
        return posts

    except Exception as e:
        print(f"[ERROR] LinkupAPI LinkedIn 取得失敗 ({linkedin_url}): {e}")
        import traceback
        traceback.print_exc()
        return []


# ─── モジュール4: Exa.ai（公開コンテンツ検索）────────────────────────────────
def fetch_exa(handle_or_url: str, person: str, company: str, country: str, source_type: str) -> list[dict]:
    """
    Exa.ai を使って公開SNSコンテンツを検索する。
    全文取得ではなく、公開インデックス上のコンテンツを取得。
    API: dashboard.exa.ai (1,000req/月無料)
    """
    if not EXA_API_KEY:
        print("[INFO] EXA_API_KEY が未設定")
        return []

    try:
        import requests
    except ImportError:
        return []

    # 検索クエリ構築
    if source_type == "X":
        domain = "twitter.com"
        query = f'site:{domain} from:{handle_or_url.lstrip("@")} "{person}"'
    else:
        domain = "linkedin.com"
        query = f'site:{domain}/in/ "{person}" "{company}"'

    start_published = START_DATE.isoformat()

    url = "https://api.exa.ai/search"
    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "numResults": 10,
        "includeDomains": [domain],
        "startPublishedDate": start_published,
        "contents": {
            "text": {"maxCharacters": 3000},
            "highlights": {"numSentences": 5},
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[ERROR] Exa API 失敗 ({person}): {e}")
        return []

    posts = []
    for result in data.get("results", []):
        text = result.get("text", "") or ""
        if len(text) < 50:
            continue
        posts.append({
            "account": handle_or_url,
            "person": person,
            "company": company,
            "country": country,
            "date": (result.get("publishedDate") or "")[:10],
            "text": text[:3000],
            "is_work_related": None,
            "source": f"{source_type}(Exa)",
            "url": result.get("url"),
            "exa_score": result.get("score"),
        })

    print(f"[Exa] {person} ({source_type}): {len(posts)} posts")
    return posts


# ─── 仕事関連フィルタリング（LLMベース）─────────────────────────────────────
PERSONAL_KEYWORDS = [
    "lunch", "dinner", "birthday", "vacation", "holiday", "weekend",
    "家族", "ランチ", "夕食", "誕生日", "旅行", "休暇", "趣味", "プライベート"
]
WORK_KEYWORDS = [
    "HR", "CHRO", "talent", "workforce", "strategy", "AI", "people", "culture",
    "organization", "leadership", "employee", "skill", "learning", "diversity",
    "人事", "人材", "採用", "組織", "戦略", "キャリア", "研修", "変革"
]

def is_work_related_simple(text: str) -> bool:
    """簡易フィルタリング（APIを使わないキーワードベース判定）"""
    if not text:
        return False
    text_lower = text.lower()
    personal_score = sum(1 for kw in PERSONAL_KEYWORDS if kw.lower() in text_lower)
    work_score = sum(1 for kw in WORK_KEYWORDS if kw.lower() in text_lower)
    if personal_score > 0 and work_score == 0:
        return False
    if len(text) < 30:
        return False
    return True


# ─── ポスト行動パターン分類 ─────────────────────────────────────────────────
POST_ACTION_EXCLUDED = frozenset({"Profile/Company info only", "No post action mentioned"})

def classify_post_action(text: str) -> str:
    """
    ポストを以下6パターンに分類して返す:
      Profile/Company info only / posted on the topic / commented on /
      shared / liked the post / No post action mentioned
    """
    if not text or len(text.strip()) < 30:
        return "Profile/Company info only"

    text_lower = text.lower()

    # liked the post パターン
    if any(kw in text_lower for kw in [
        "liked this", "likes this", "reacted to", "liked a post",
        "likes a post", " liked a ", "you liked", "celebrated this",
    ]):
        return "liked the post"

    # shared パターン
    if any(kw in text_lower for kw in [
        "shared a post", "shared an article", "shared a video",
        "reshared", "reposted", " shared this",
    ]):
        return "shared"

    # commented on パターン
    if any(kw in text_lower for kw in [
        "commented on", "replied to", "left a comment on", "replied:",
    ]):
        return "commented on"

    # Profile/Company info only パターン（プロフィール・会社情報のみ）
    profile_kws = [
        "about us", "company overview", "follow us on",
        "founded in", "headquartered in", "employees worldwide",
        "プロフィール", "会社概要",
    ]
    if any(kw in text_lower for kw in profile_kws) and len(text) < 400:
        return "Profile/Company info only"

    # No post action mentioned（投稿行動不明・短すぎる）
    if len(text.strip()) < 100:
        return "No post action mentioned"

    return "posted on the topic"


# ─── マスターリスト読み込み ───────────────────────────────────────────────────
def load_targets() -> list[dict]:
    """master_list.csv からX/LinkedInアカウントを持つCHROリストを読み込む"""
    targets = []
    with open(MASTER_LIST, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("X_URL") or row.get("LinkedIn_URL"):
                targets.append({
                    "person": row["氏名"],
                    "company": row["企業名"],
                    "country": row["国"],
                    "x_url": row.get("X_URL", ""),
                    "linkedin_url": row.get("LinkedIn_URL", ""),
                })
    return targets


# ─── メイン実行 ───────────────────────────────────────────────────────────────
def main():
    print(f"=== last30days スキル実行 ({START_DATE} 〜 {TODAY}) ===")
    print()

    # 利用可能なモジュールを確認
    available_modules = []
    if TWITTER_BEARER_TOKEN:
        available_modules.append("X-API-v2(公式・7日)")
    if TWITTER_USERNAME and TWITTER_PASSWORD:
        available_modules.append("twikit(非公式)")
    if EXA_API_KEY:
        available_modules.append("Exa(公開コンテンツ)")
    if LINKEDIN_EMAIL and LINKEDIN_PASSWORD:
        available_modules.append("LinkedIn-MCP(ブラウザ)")

    if not available_modules:
        print("[ERROR] 有効な認証情報がありません。.env ファイルを設定してください。")
        print("  必要な設定: README_SETUP.md を参照")
        return

    print(f"[OK] 利用可能なモジュール: {', '.join(available_modules)}")
    print()

    targets = load_targets()
    print(f"[OK] Total CHROs: {len(targets)}")
    print()

    all_posts = []

    for target in targets:
        person = target["person"]
        company = target["company"]
        country = target["country"]
        x_url = target["x_url"]
        li_url = target["linkedin_url"]

        # X投稿取得
        if x_url:
            handle = x_url.split("/")[-1].split("?")[0]
            posts = []

            # 優先順位: 公式API → twikit → Exa
            if TWITTER_BEARER_TOKEN:
                posts = fetch_x_official(handle, person, company, country)
            if not posts and TWITTER_USERNAME:
                posts = fetch_x_twikit(handle, person, company, country)
            if not posts and EXA_API_KEY:
                posts = fetch_exa(f"@{handle}", person, company, country, "X")

            filtered_x = []
            for p in posts:
                action = classify_post_action(p.get("text", ""))
                p["post_action"] = action
                if action not in POST_ACTION_EXCLUDED:
                    p["is_work_related"] = is_work_related_simple(p.get("text", ""))
                    filtered_x.append(p)
            print(f"  [filter] X: {len(posts)} → {len(filtered_x)} posts (excluded {len(posts)-len(filtered_x)})")
            all_posts.extend(filtered_x)

        # LinkedIn投稿取得
        if li_url and "linkedin.com" in li_url:
            posts = []

            # 優先順位: LinkupAPI → Exa
            if os.getenv("LINKUPAPI_KEY"):
                posts = fetch_linkedin_linkupapi(li_url, person, company, country)
            if not posts and EXA_API_KEY:
                posts = fetch_exa(li_url, person, company, country, "LinkedIn")

            filtered_li = []
            for p in posts:
                action = classify_post_action(p.get("text", ""))
                p["post_action"] = action
                if action not in POST_ACTION_EXCLUDED:
                    p["is_work_related"] = is_work_related_simple(p.get("text", ""))
                    filtered_li.append(p)
            print(f"  [filter] LinkedIn: {len(posts)} → {len(filtered_li)} posts (excluded {len(posts)-len(filtered_li)})")
            all_posts.extend(filtered_li)

        time.sleep(0.5)  # レートリミット対策

    # 結果保存
    output_path = DATA_DIR / f"raw_data_{YYYYMM}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2, default=str)

    work_posts = [p for p in all_posts if p.get("is_work_related")]
    print(f"=== Completed ===")
    print(f"Total posts: {len(all_posts)}")
    print(f"Work-related: {len(work_posts)}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
