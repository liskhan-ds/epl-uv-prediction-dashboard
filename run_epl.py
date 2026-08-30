

import sqlite3
import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "epl_data.db")

# 팀명 매핑 영문 -> 한글 (공식 EPL 20개 구단)
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
    "Sunderland": "선덜랜드",
    "Burnley": "번리",
    "Leeds United": "리즈 유나이티드",
    "Leeds": "리즈 유나이티드",
    "Coventry City": "코번트리 시티",
    "Coventry": "코번트리 시티",
    "Hull City": "헐 시티",
    "Hull": "헐 시티",
}

# 선수별 시즌/최근 평점(rating) 및 goals_per90 룩업 테이블 (FotMob/공식 API 기준 데이터)



from app import TEAMS_ROSTER

def normalize_team_name(raw_name):
    for key, val in TEAM_NAME_MAP.items():
        if key.lower() in raw_name.lower() or raw_name.lower() in key.lower():
            return val
    return raw_name




def fetch_espn_epl_season_fixtures(date_range="20260815-20260831"):
    # 라운드 1 & 라운드 2 경기 일정만 실시간 수집 (요청 시 추가 확장)
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates={date_range}"
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

def ensure_team_roster(team_name):
    if team_name not in TEAMS_ROSTER:
        TEAMS_ROSTER[team_name] = {
            "starters": [
                {"pos": "GK", "name": f"{team_name} GK", "rating": 6.80},
                {"pos": "DF", "name": f"{team_name} DF1", "rating": 6.80},
                {"pos": "DF", "name": f"{team_name} DF2", "rating": 6.80},
                {"pos": "DF", "name": f"{team_name} DF3", "rating": 6.80},
                {"pos": "DF", "name": f"{team_name} DF4", "rating": 6.80},
                {"pos": "MF", "name": f"{team_name} MF1", "rating": 6.80},
                {"pos": "MF", "name": f"{team_name} MF2", "rating": 6.80},
                {"pos": "MF", "name": f"{team_name} MF3", "rating": 6.80},
                {"pos": "FW", "name": f"{team_name} FW1", "rating": 6.80},
                {"pos": "FW", "name": f"{team_name} FW2", "rating": 6.80},
                {"pos": "FW", "name": f"{team_name} FW3", "rating": 6.80},
            ],
            "subs": [
                {"pos": "FW", "name": f"{team_name} Sub1", "rating": 6.80},
                {"pos": "MF", "name": f"{team_name} Sub2", "rating": 6.80},
                {"pos": "MF", "name": f"{team_name} Sub3", "rating": 6.80},
                {"pos": "DF", "name": f"{team_name} Sub4", "rating": 6.80},
                {"pos": "GK", "name": f"{team_name} Sub5", "rating": 6.80},
            ]
        }


def get_match_prediction(home_team, away_team):
    h_info = calculate_wuv(home_team)
    a_info = calculate_wuv(away_team)
    
    h_total = h_info["team_wuv"] + 0.25
    a_total = a_info["team_wuv"]
    
    gap = h_total - a_total
    
    if abs(gap) <= 0.40:
        winner = "무승부 (Draw)"
        code = "DRAW"
    elif gap > 0.40:
        winner = home_team
        code = "HOME"
    else:
        winner = away_team
        code = "AWAY"
        
    z = gap
    lh = 1.55 * z
    la = -1.55 * z
    ld = 0.35 - 1.25 * abs(z)
    
    eh, ed, ea = np.exp(lh), np.exp(ld), np.exp(la)
    tot = eh + ed + ea
    
    p_home = round((eh / tot) * 100, 1)
    p_draw = round((ed / tot) * 100, 1)
    p_away = round((ea / tot) * 100, 1)
    
    sc_h = int(round(1.35 * (h_total / 11.0)))
    sc_a = int(round(1.35 * (a_total / 11.0)))
    
    if code == "DRAW" and sc_h != sc_a:
        sc_h = sc_a = int(round((sc_h + sc_a) / 2.0))
        return {
        "home_wuv": h_info,
        "away_wuv": a_info,
        "h_total": h_total,
        "a_total": a_total,
        "gap": gap,
        "winner": winner,
        "code": code,
        "p_home": p_home,
        "p_draw": p_draw,
        "p_away": p_away,
        "sc_h": sc_h,
        "sc_a": sc_a
    }

if __name__ == "__main__":
    print(f"🚀 EPL 정규 시즌 파이프라인 시작 (개인 UV 0.1~2.0 & 팀 11.0 WUV 합성 로직 적용)", flush=True)
    run_pipeline()
