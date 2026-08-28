import sqlite3
import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "epl_data.db")

# 팀명 매핑 영문 -> 한글 (2026-27 EPL 참가 구단)
TEAM_NAME_MAP = {
    "Manchester United": "맨체스터 유나이티드",
    "Arsenal": "아스널",
    "Manchester City": "맨체스터 시티",
    "Liverpool": "리버풀",
    "Chelsea": "첼시",
    "Tottenham Hotspur": "토트넘 홋스퍼",
    "Tottenham": "토트넘 홋스퍼",
    "Newcastle United": "뉴캐슬 유나이티드",
    "Newcastle": "뉴캐슬 유나이티드",
    "Aston Villa": "아스톤 빌라",
    "West Ham United": "웨스트햄 유나이티드",
    "West Ham": "웨스트햄 유나이티드",
    "Brighton & Hove Albion": "브라이튼",
    "Brighton": "브라이튼",
    "Fulham": "풀럼",
    "Crystal Palace": "크리스탈 팰리스",
    "Everton": "에버턴",
    "Wolverhampton Wanderers": "울버햄튼",
    "Wolves": "울버햄튼",
    "AFC Bournemouth": "본머스",
    "Bournemouth": "본머스",
    "Brentford": "브렌트포드",
    "Nottingham Forest": "노팅엄 포레스트",
    "Leicester City": "레스터 시티",
    "Ipswich Town": "입스위치 타운",
    "Southampton": "사우샘프턴",
    "Leeds United": "리즈 유나이티드",
    "Sunderland": "선덜랜드",
    "Coventry City": "코번트리 시티",
    "Hull City": "헐 시티",
}

from app import calculate_wuv, get_match_prediction, TEAMS_ROSTER

def normalize_team_name(raw_name):
    for key, val in TEAM_NAME_MAP.items():
        if key.lower() in raw_name.lower() or raw_name.lower() in key.lower():
            return val
    return raw_name

def fetch_espn_epl_season_fixtures():
    # 2026-27 EPL 정규 시즌 일정표 수집 (2026년 8월 21일 개막 ~ 11월 7일)
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates=20260815-20261130"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            events = res.json().get("events", [])
            events.sort(key=lambda x: x["date"])
            return events
    except Exception as e:
        print(f"⚠️ ESPN API 요청 오류: {e}")
    return []

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        uk_date TEXT,
        kst_date TEXT,
        round_name TEXT,
        home_team TEXT NOT NULL,
        visit_team TEXT NOT NULL,
        predicted_winner TEXT NOT NULL,
        predicted_gap REAL NOT NULL,
        prob_home REAL NOT NULL,
        prob_draw REAL NOT NULL,
        prob_away REAL NOT NULL,
        home_uv REAL NOT NULL,
        visit_uv REAL NOT NULL,
        score_home INTEGER,
        score_away INTEGER,
        actual_winner TEXT,
        actual_score_home INTEGER,
        actual_score_away INTEGER,
        is_correct INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, home_team, visit_team) ON CONFLICT REPLACE
    )
    """)
    cursor.execute("PRAGMA table_info(predictions)")
    cols = [col[1] for col in cursor.fetchall()]
    for c in ["uk_date", "kst_date", "round_name"]:
        if c not in cols:
            cursor.execute(f"ALTER TABLE predictions ADD COLUMN {c} TEXT")
    conn.commit()
    conn.close()

def parse_timezones(utc_iso_str):
    dt_utc = datetime.fromisoformat(utc_iso_str.replace("Z", "+00:00"))
    
    # 영국 현지 시각
    uk_offset = 1 if 4 <= dt_utc.month <= 10 else 0
    dt_uk = dt_utc + timedelta(hours=uk_offset)
    
    # 한국 시각 (KST)
    dt_kst = dt_utc + timedelta(hours=9)
    
    uk_date_str = dt_uk.strftime("%Y-%m-%d %H:%M (영국)")
    kst_date_str = dt_kst.strftime("%Y-%m-%d %H:%M (KST)")
    
    return dt_uk.strftime("%Y-%m-%d"), uk_date_str, kst_date_str, dt_uk

def ensure_team_roster(team_name):
    if team_name not in TEAMS_ROSTER:
        TEAMS_ROSTER[team_name] = {
            "starters": [
                {"pos": "GK", "name": f"{team_name} GK", "att_uv": 0.15, "def_uv": 0.45},
                {"pos": "DF", "name": f"{team_name} DF1", "att_uv": 0.30, "def_uv": 0.45},
                {"pos": "DF", "name": f"{team_name} DF2", "att_uv": 0.25, "def_uv": 0.50},
                {"pos": "DF", "name": f"{team_name} DF3", "att_uv": 0.25, "def_uv": 0.50},
                {"pos": "DF", "name": f"{team_name} DF4", "att_uv": 0.35, "def_uv": 0.40},
                {"pos": "MF", "name": f"{team_name} MF1", "att_uv": 0.40, "def_uv": 0.45},
                {"pos": "MF", "name": f"{team_name} MF2", "att_uv": 0.40, "def_uv": 0.45},
                {"pos": "MF", "name": f"{team_name} MF3", "att_uv": 0.55, "def_uv": 0.35},
                {"pos": "FW", "name": f"{team_name} FW1", "att_uv": 0.60, "def_uv": 0.25},
                {"pos": "FW", "name": f"{team_name} FW2", "att_uv": 0.60, "def_uv": 0.25},
                {"pos": "FW", "name": f"{team_name} FW3", "att_uv": 0.65, "def_uv": 0.20},
            ],
            "subs": [
                {"pos": "FW", "name": f"{team_name} Sub1", "att_uv": 0.50, "def_uv": 0.20},
                {"pos": "MF", "name": f"{team_name} Sub2", "att_uv": 0.40, "def_uv": 0.30},
                {"pos": "MF", "name": f"{team_name} Sub3", "att_uv": 0.35, "def_uv": 0.35},
                {"pos": "DF", "name": f"{team_name} Sub4", "att_uv": 0.20, "def_uv": 0.40},
                {"pos": "GK", "name": f"{team_name} Sub5", "att_uv": 0.10, "def_uv": 0.35},
            ]
        }

def run_pipeline():
    init_db()
    
    events = fetch_espn_epl_season_fixtures()
    print(f"📡 수집된 2026-27 EPL 시즌 정규 경기 수: {len(events)} 경기")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    synced_count = 0
    total_rounds = len(events) // 10
    
    for r_idx in range(total_rounds):
        r_events = events[r_idx*10 : (r_idx+1)*10]
        
        _, first_uk_str, _, dt_first_uk = parse_timezones(r_events[0]["date"])
        _, last_uk_str, _, dt_last_uk = parse_timezones(r_events[-1]["date"])
        
        # 2자리 패딩 적용 (Round 01, Round 02 ... Round 10)
        round_title = f"Round {r_idx+1:02d} ({dt_first_uk.strftime('%Y-%m-%d')} ~ {dt_last_uk.strftime('%m-%d')})"
        
        for event in r_events:
            try:
                status_type = event["status"]["type"]["name"]
                match_date_utc = event["date"]
                
                uk_day, uk_str, kst_str, _ = parse_timezones(match_date_utc)
                
                competition = event["competitions"][0]
                competitors = competition["competitors"]
                
                home_comp = [c for c in competitors if c.get("homeAway") == "home"][0]
                away_comp = [c for c in competitors if c.get("homeAway") == "away"][0]
                
                home_raw = home_comp["team"]["displayName"]
                away_raw = away_comp["team"]["displayName"]
                
                home_team = normalize_team_name(home_raw)
                away_team = normalize_team_name(away_raw)
                
                ensure_team_roster(home_team)
                ensure_team_roster(away_team)
                
                pred = get_match_prediction(home_team, away_team)
                
                actual_winner = ""
                actual_sc_h = None
                actual_sc_a = None
                is_correct = None
                
                if status_type in ["STATUS_FULL_TIME", "STATUS_FINAL", "STATUS_AFTER_EXTRA_TIME"]:
                    actual_sc_h = int(home_comp.get("score", 0))
                    actual_sc_a = int(away_comp.get("score", 0))
                    
                    if actual_sc_h > actual_sc_a:
                        actual_winner = home_team
                    elif actual_sc_a > actual_sc_h:
                        actual_winner = away_team
                    else:
                        actual_winner = "무승부 (Draw)"
                        
                    is_correct = 1 if (pred["winner"] == actual_winner) else 0
                    
                cursor.execute("""
                INSERT INTO predictions (
                    date, uk_date, kst_date, round_name, home_team, visit_team,
                    predicted_winner, predicted_gap, prob_home, prob_draw, prob_away,
                    home_uv, visit_uv, score_home, score_away, actual_winner,
                    actual_score_home, actual_score_away, is_correct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date, home_team, visit_team) DO UPDATE SET
                    uk_date=excluded.uk_date,
                    kst_date=excluded.kst_date,
                    round_name=excluded.round_name,
                    predicted_winner=excluded.predicted_winner,
                    predicted_gap=excluded.predicted_gap,
                    prob_home=excluded.prob_home,
                    prob_draw=excluded.prob_draw,
                    prob_away=excluded.prob_away,
                    home_uv=excluded.home_uv,
                    visit_uv=excluded.visit_uv,
                    score_home=excluded.score_home,
                    score_away=excluded.score_away,
                    actual_winner=excluded.actual_winner,
                    actual_score_home=excluded.actual_score_home,
                    actual_score_away=excluded.actual_score_away,
                    is_correct=excluded.is_correct
                """, (
                    uk_day, uk_str, kst_str, round_title, home_team, away_team,
                    pred["winner"], pred["gap"], pred["p_home"], pred["p_draw"], pred["p_away"],
                    pred["h_total"], pred["a_total"], pred["sc_h"], pred["sc_a"],
                    actual_winner, actual_sc_h, actual_sc_a, is_correct
                ))
                
                synced_count += 1
                status_disp = f"실제: {actual_sc_h}-{actual_sc_a} {actual_winner}" if actual_winner else "대기중"
                print(f"  ✓ [{round_title}] {home_team} vs {away_team} -> 예측: {pred['winner']} ({status_disp})")
                
            except Exception as ex:
                print(f"❌ 경기 동기화 실패: {ex}")
                
    conn.commit()
    conn.close()
    print(f"🎉 성공적으로 2026-27 EPL 시즌 {synced_count}개 경기를 epl_data.db에 적재하였습니다!")

if __name__ == "__main__":
    print(f"🚀 2026-27 EPL 시즌 파이프라인 시작 (Round 01 ~ Round 10 2자리 표기 적용)")
    run_pipeline()
