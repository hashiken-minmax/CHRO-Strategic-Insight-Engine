#!/usr/bin/env python3
"""
monthly_pipeline.py
毎月第2営業日に①～⑤のパイプラインを自動実行

①SNSデータ収集 → ②情報分類 → ③深層分析A → ④戦略立案 → ⑤レポート作成
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import json

# Windows UTF-8 対応
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
SKILLS_DIR = PROJECT_DIR / "skills"
DATA_DIR = PROJECT_DIR / "data"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 第2営業日判定ロジック
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def is_business_day(date):
    """営業日判定（月～金）"""
    return date.weekday() < 5  # 0-4 = 月～金

def get_second_business_day(year, month):
    """指定年月の第2営業日を取得"""
    date = datetime(year, month, 1)
    business_days = 0

    while business_days < 2:
        if is_business_day(date):
            business_days += 1
            if business_days == 2:
                return date
        date += timedelta(days=1)

    return None

def should_run_today():
    """今日が第2営業日かチェック"""
    today = datetime.now()
    second_biz_day = get_second_business_day(today.year, today.month)

    return today.date() == second_biz_day.date() if second_biz_day else False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# パイプライン実行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_pipeline(force=False, period=None):
    """①～⑥のパイプラインを順番に実行"""

    today = datetime.now()
    print(f"[START] パイプライン実行開始: {today.strftime('%Y年%m月%d日 %H:%M:%S')}")

    # 営業日判定（--force で強制実行）
    if force:
        print(f"[FORCE] 強制実行モード（営業日チェックをスキップ）")
    elif not should_run_today():
        second_biz_day = get_second_business_day(today.year, today.month)
        print(f"[SKIP] 今日は第2営業日ではありません（次回: {second_biz_day.strftime('%Y年%m月%d日')}）")
        return

    # 対象期間: 引数があればそれを使用、なければ前月のYYYYMM
    if period is None:
        prev_month = (today.replace(day=1) - timedelta(days=1))
        period = prev_month.strftime("%Y%m")
    print(f"[OK] 対象期間: {period}")
    print()

    steps = [
        ("①SNSデータ収集",       str(SKILLS_DIR / "last30days.py"),                     ["--period", period]),
        ("②情報分類",             str(SCRIPTS_DIR / "classify_content.py"),              ["--period", period]),
        ("③分析データ生成",        str(SCRIPTS_DIR / "generate_analytics.py"),            ["--period", period]),
        ("③深層分析（Phase A）",  str(SCRIPTS_DIR / "generate_analytics_phaseA.py"),     ["--period", period]),
        ("③深層分析（Phase C）",  str(SCRIPTS_DIR / "generate_analytics_phaseC.py"),     ["--period", period]),
        ("④戦略立案",             str(SCRIPTS_DIR / "ideate_business_strategy.py"),      ["--period", period]),
        ("⑤レポート作成",         str(SCRIPTS_DIR / "produce_report_phaseA_with_charts.py"), ["--period", period]),
    ]

    success_count = 0
    failed_steps = []

    for step_name, script_path, extra_args in steps:
        print(f"\n{'='*60}")
        print(f"[RUN] {step_name}")
        print(f"{'='*60}")

        try:
            result = subprocess.run(
                [sys.executable, script_path] + extra_args,
                cwd=str(PROJECT_DIR),
                capture_output=False,
                timeout=600  # 10分タイムアウト
            )

            if result.returncode == 0:
                print(f"[OK] {step_name} 完了")
                success_count += 1
            else:
                print(f"[ERR] {step_name} 失敗（終了コード: {result.returncode}）")
                failed_steps.append(step_name)

        except subprocess.TimeoutExpired:
            print(f"[ERR] {step_name} タイムアウト")
            failed_steps.append(step_name)
        except Exception as e:
            print(f"[ERR] {step_name} エラー: {e}")
            failed_steps.append(step_name)

    # ━━ 実行結果サマリー ━━
    total = len(steps)
    print(f"\n{'='*60}")
    print(f"[SUMMARY] パイプライン実行結果")
    print(f"{'='*60}")
    print(f"成功: {success_count}/{total}")

    if failed_steps:
        print(f"失敗: {', '.join(failed_steps)}")
    else:
        print(f"[OK] 全ステップが成功しました！")

    print(f"\n完了時刻: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")

if __name__ == '__main__':
    force = '--force' in sys.argv
    try:
        period_idx = sys.argv.index('--period')
        period = sys.argv[period_idx + 1]
    except (ValueError, IndexError):
        period = None
    run_pipeline(force=force, period=period)
