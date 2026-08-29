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

POSITION_BASE_UV = {
    "GK": {"att_uv": 0.15, "def_uv": 0.50}, "G": {"att_uv": 0.15, "def_uv": 0.50},
    "DF": {"att_uv": 0.35, "def_uv": 0.55}, "D": {"att_uv": 0.35, "def_uv": 0.55},
    "MF": {"att_uv": 0.45, "def_uv": 0.45}, "M": {"att_uv": 0.45, "def_uv": 0.45},
    "FW": {"att_uv": 0.65, "def_uv": 0.25}, "F": {"att_uv": 0.65, "def_uv": 0.25},
}

PLAYER_UV_LOOKUP = {
    "Erling Haaland": {"att_uv": 0.90, "def_uv": 0.20},
    "Mohamed Salah": {"att_uv": 0.85, "def_uv": 0.25},
    "Bukayo Saka": {"att_uv": 0.80, "def_uv": 0.35},
    "Cole Palmer": {"att_uv": 0.85, "def_uv": 0.30},
    "Son Heung-Min": {"att_uv": 0.80, "def_uv": 0.30},
    "Heung-Min Son": {"att_uv": 0.80, "def_uv": 0.30},
    "Phil Foden": {"att_uv": 0.75, "def_uv": 0.35},
    "Bruno Fernandes": {"att_uv": 0.70, "def_uv": 0.35},
    "Alexander Isak": {"att_uv": 0.80, "def_uv": 0.20},
    "Ollie Watkins": {"att_uv": 0.80, "def_uv": 0.25},
    "Jarrod Bowen": {"att_uv": 0.75, "def_uv": 0.30},
    "Gabriel Martinelli": {"att_uv": 0.65, "def_uv": 0.30},
    "Kai Havertz": {"att_uv": 0.60, "def_uv": 0.35},
    "Marcus Rashford": {"att_uv": 0.65, "def_uv": 0.25},
    "Alejandro Garnacho": {"att_uv": 0.60, "def_uv": 0.30},
    "Rasmus Højlund": {"att_uv": 0.60, "def_uv": 0.25},
    "Rasmus Hojlund": {"att_uv": 0.60, "def_uv": 0.25},
    "Luis Díaz": {"att_uv": 0.70, "def_uv": 0.30},
    "Luis Diaz": {"att_uv": 0.70, "def_uv": 0.30},
    "Darwin Núñez": {"att_uv": 0.65, "def_uv": 0.25},
    "Darwin Nunez": {"att_uv": 0.65, "def_uv": 0.25},
    "Nicolas Jackson": {"att_uv": 0.65, "def_uv": 0.25},
    "Pedro Neto": {"att_uv": 0.65, "def_uv": 0.30},
    "Dominic Solanke": {"att_uv": 0.65, "def_uv": 0.25},
    "Anthony Gordon": {"att_uv": 0.70, "def_uv": 0.30},
    "Leon Bailey": {"att_uv": 0.70, "def_uv": 0.25},
    "Rodri": {"att_uv": 0.55, "def_uv": 0.65},
    "Declan Rice": {"att_uv": 0.50, "def_uv": 0.60},
    "Martin Ødegaard": {"att_uv": 0.75, "def_uv": 0.35},
    "Martin Odegaard": {"att_uv": 0.75, "def_uv": 0.35},
    "Bernardo Silva": {"att_uv": 0.65, "def_uv": 0.45},
    "Alexis Mac Allister": {"att_uv": 0.55, "def_uv": 0.45},
    "Dominik Szoboszlai": {"att_uv": 0.60, "def_uv": 0.40},
    "Moisés Caicedo": {"att_uv": 0.40, "def_uv": 0.60},
    "Enzo Fernández": {"att_uv": 0.55, "def_uv": 0.45},
    "James Maddison": {"att_uv": 0.70, "def_uv": 0.30},
    "Virgil van Dijk": {"att_uv": 0.35, "def_uv": 0.65},
    "William Saliba": {"att_uv": 0.30, "def_uv": 0.65},
    "Gabriel Magalhães": {"att_uv": 0.35, "def_uv": 0.60},
    "Trent Alexander-Arnold": {"att_uv": 0.65, "def_uv": 0.40},
    "Rúben Dias": {"att_uv": 0.30, "def_uv": 0.65},
    "Josko Gvardiol": {"att_uv": 0.45, "def_uv": 0.55},
    "Cristian Romero": {"att_uv": 0.35, "def_uv": 0.60},
    "Alisson Becker": {"att_uv": 0.25, "def_uv": 0.60},
    "David Raya": {"att_uv": 0.25, "def_uv": 0.55},
    "Ederson": {"att_uv": 0.30, "def_uv": 0.50},
}

TEAMS_ROSTER = {}

def normalize_team_name(raw_name):
    for key, val in TEAM_NAME_MAP.items():
        if key.lower() in raw_name.lower() or raw_name.lower() in key.lower():
            return val
    return raw_name

def fetch_espn_epl_season_fixtures():
    # 2026-27 EPL 정규 시즌 실시간 경기 수집
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

def get_player_uv(p_name, pos_abbr):
    for name_key, uv_val in PLAYER_UV_LOOKUP.items():
        if name_key.lower() in p_name.lower() or p_name.lower() in name_key.lower():
            return uv_val
    pos_clean = pos_abbr.upper() if pos_abbr else "MF"
    return POSITION_BASE_UV.get(pos_clean, POSITION_BASE_UV["MF"])

def fetch_official_match_roster(event_id):
    summary_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event={event_id}"
    try:
        res = requests.get(summary_url, timeout=5)
        if res.status_code == 200:
            rosters = res.json().get("rosters", [])
            live_rosters = {}
            for t_rost in rosters:
                tname = normalize_team_name(t_rost.get("team", {}).get("displayName", ""))
                r_entries = t_rost.get("roster", [])
                st_list = []
                sub_list = []
                for p in r_entries:
                    ath = p.get("athlete", {})
                    p_name = ath.get("displayName") or "Unknown Player"
                    pos_abbr = p.get("position", {}).get("abbreviation") or ath.get("position", {}).get("abbreviation", "MF")
                    uv_data = get_player_uv(p_name, pos_abbr)
                    p_item = {"pos": pos_abbr, "name": p_name, "att_uv": uv_data["att_uv"], "def_uv": uv_data["def_uv"]}
                    if p.get("starter"):
                        st_list.append(p_item)
                    else:
                        sub_list.append(p_item)
                if st_list:
                    live_rosters[tname] = {"starters": st_list[:11], "subs": sub_list[:5]}
            return live_rosters
    except Exception as e:
        pass
    return {}

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

def calculate_wuv(team_name):
    ensure_team_roster(team_name)
    team = TEAMS_ROSTER[team_name]
    
    st_df = pd.DataFrame(team["starters"])
    st_att = st_df["att_uv"].sum()
    st_def = st_df["def_uv"].sum()
    st_total = st_att + st_def
    
    sub_df = pd.DataFrame(team["subs"])
    sub_att_raw = sub_df["att_uv"].sum()
    sub_def_raw = sub_df["def_uv"].sum()
    
    sub_att_scaled = sub_att_raw * (11.0 / 5.0)
    sub_def_scaled = sub_def_raw * (11.0 / 5.0)
    sub_total_scaled = sub_att_scaled + sub_def_scaled
    
    wuv_att = 0.85 * st_att + 0.15 * sub_att_scaled
    wuv_def = 0.85 * st_def + 0.15 * sub_def_scaled
    wuv_total = wuv_att + wuv_def
    
    return {
        "st_att": st_att,
        "st_def": st_def,
        "st_total": st_total,
        "sub_att_raw": sub_att_raw,
        "sub_def_raw": sub_def_raw,
        "sub_att_scaled": sub_att_scaled,
        "sub_def_scaled": sub_def_scaled,
        "sub_total_scaled": sub_total_scaled,
        "wuv_att": wuv_att,
        "wuv_def": wuv_def,
        "wuv_total": wuv_total,
        "st_df": st_df,
        "sub_df": sub_df
    }

def get_match_prediction(home_team, away_team):
    h_info = calculate_wuv(home_team)
    a_info = calculate_wuv(away_team)
    
    h_att = h_info["wuv_att"] + 0.15
    h_def = h_info["wuv_def"] + 0.10
    h_total = h_info["wuv_total"] + 0.25
    
    a_att = a_info["wuv_att"]
    a_def = a_info["wuv_def"]
    a_total = a_info["wuv_total"]
    
    gap = h_total - a_total
    
    if abs(gap) <= 0.4:
        winner = "무승부 (Draw)"
        code = "DRAW"
    elif gap > 0.4:
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
    
    xg_h = 1.35 * (h_att / 5.5) * (5.5 / a_def)
    xg_a = 1.35 * (a_att / 5.5) * (5.5 / h_def)
    sc_h = int(round(xg_h))
    sc_a = int(round(xg_a))
    
    if code == "DRAW" and sc_h != sc_a:
        avg_s = int(round((xg_h + xg_a) / 2.0))
        sc_h, sc_a = avg_s, avg_s
        
    return {
        "home_wuv": h_info,
        "away_wuv": a_info,
        "h_att": h_att,
        "h_def": h_def,
        "h_total": h_total,
        "a_att": a_att,
        "a_def": a_def,
        "a_total": a_total,
        "gap": gap,
        "winner": winner,
        "code": code,
        "p_home": p_home,
        "p_draw": p_draw,
        "p_away": p_away,
        "xg_h": xg_h,
        "xg_a": xg_a,
        "sc_h": sc_h,
        "sc_a": sc_a
    }

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
    uk_offset = 1 if 4 <= dt_utc.month <= 10 else 0
    dt_uk = dt_utc + timedelta(hours=uk_offset)
    dt_kst = dt_utc + timedelta(hours=9)
    uk_date_str = dt_uk.strftime("%Y-%m-%d %H:%M (영국)")
    kst_date_str = dt_kst.strftime("%Y-%m-%d %H:%M (KST)")
    return dt_uk.strftime("%Y-%m-%d"), uk_date_str, kst_date_str, dt_uk

def run_pipeline():
    init_db()
    
    events = fetch_espn_epl_season_fixtures()
    print(f"📡 수집된 EPL 공식 정규 시즌 경기 수: {len(events)} 경기", flush=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    synced_count = 0
    total_rounds = len(events) // 10
    
    for r_idx in range(total_rounds):
        r_events = events[r_idx*10 : (r_idx+1)*10]
        
        _, first_uk_str, _, dt_first_uk = parse_timezones(r_events[0]["date"])
        _, last_uk_str, _, dt_last_uk = parse_timezones(r_events[-1]["date"])
        
        round_title = f"Round {r_idx+1:02d} ({dt_first_uk.strftime('%Y-%m-%d')} ~ {dt_last_uk.strftime('%m-%d')})"
        
        for event in r_events:
            try:
                event_id = event["id"]
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
                
                # ESPN Live Official Roster API 동적 동기화
                live_rosters = fetch_official_match_roster(event_id)
                if home_team in live_rosters:
                    TEAMS_ROSTER[home_team] = live_rosters[home_team]
                else:
                    ensure_team_roster(home_team)

                if away_team in live_rosters:
                    TEAMS_ROSTER[away_team] = live_rosters[away_team]
                else:
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
                print(f"  ✓ [{round_title}] {home_team} vs {away_team} -> 예측: {pred['winner']} ({status_disp})", flush=True)
                
            except Exception as ex:
                print(f"❌ 경기 동기화 실패: {ex}", flush=True)
                
    conn.commit()
    conn.close()
    print(f"🎉 성공적으로 EPL 공식 정규 시즌 {synced_count}개 경기를 epl_data.db에 적재하였습니다!", flush=True)

if __name__ == "__main__":
    print(f"🚀 EPL 정규 시즌 파이프라인 시작 (공식 Real EPL 20개 구단)", flush=True)
    run_pipeline()
