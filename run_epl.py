

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


def calculate_player_uv(player_data):
    p_name_raw = player_data.get("name", "")
    p_name = normalize_player_name(p_name_raw) if "normalize_player_name" in globals() else p_name_raw.strip()
    
    rating = 6.80
    goals_per90 = 0.0
    position = player_data.get("pos", "M")
    
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT rating, goals_per90, position FROM player_stats WHERE player_name = ? OR player_name LIKE ?", (p_name, f"%{p_name}%"))
            row = cursor.fetchone()
            if row:
                rating = row[0]
                goals_per90 = row[1]
                position = row[2]
            conn.close()
        except Exception:
            pass
            
    pos_clean = "GK" if position in ["G", "GK"] else ("DF" if position in ["D", "DF"] else ("MF" if position in ["M", "MF"] else "FW"))
    
    if pos_clean == "GK":
        raw_uv = 1.0 + (rating - 6.8) * 0.60
    elif pos_clean == "DF":
        raw_uv = 1.0 + (rating - 6.8) * 0.55
    elif pos_clean == "MF":
        raw_uv = 1.0 + (rating - 6.8) * 0.50
    else: # FW
        raw_uv = 1.0 + (rating - 6.8) * 0.50 + (goals_per90 * 0.25)
        
    return round(min(max(raw_uv, 0.1), 2.0), 3)

def get_team_roster(team_name):
    if not os.path.exists("rosters_2026.json"):
        return {"starters": [], "subs": []}
    with open("rosters_2026.json", "r", encoding="utf-8") as f:
        rosters = json.load(f)
        
    normalized_map = {normalize_team_name(k): v for k, v in rosters.items()}
    norm_tname = normalize_team_name(team_name)
    plist = normalized_map.get(norm_tname, [])
    
    gks = [p for p in plist if p.get("pos") in ["G", "GK"]]
    dfs = [p for p in plist if p.get("pos") in ["D", "DF"]]
    mfs = [p for p in plist if p.get("pos") in ["M", "MF"]]
    fws = [p for p in plist if p.get("pos") in ["F", "FW"]]
    
    starters = gks[:1] + dfs[:4] + mfs[:3] + fws[:3]
    subs = (gks[1:2] + dfs[4:6] + mfs[3:5] + fws[3:5])[:5]
    return {"starters": starters, "subs": subs}

def calculate_wuv(team_name):
    roster = get_team_roster(team_name)
    starters = roster.get("starters", [])
    subs = roster.get("subs", [])
    
    st_uvs = [calculate_player_uv(p) for p in starters]
    sub_uvs = [calculate_player_uv(p) for p in subs]
    
    st_avg = sum(st_uvs) / len(st_uvs) if st_uvs else 1.0
    sub_avg = sum(sub_uvs) / len(sub_uvs) if sub_uvs else 1.0
    
    team_wuv = round(11.0 * (0.85 * st_avg + 0.15 * sub_avg), 2)
    
    # Position detail breakdown
    pos_sums = {"GK": 0.0, "DF": 0.0, "MF": 0.0, "FW": 0.0}
    starters_detail = []
    for p in starters:
        uv = calculate_player_uv(p)
        pos = p.get("pos", "M")
        pos_clean = "GK" if pos in ["G","GK"] else ("DF" if pos in ["D","DF"] else ("MF" if pos in ["M","MF"] else "FW"))
        pos_sums[pos_clean] += uv
        starters_detail.append({"name": p.get("name"), "pos": pos_clean, "uv": uv})
        
    st_tot_sum = sum(st_uvs)
    gk_wuv = round(team_wuv * (pos_sums["GK"] / st_tot_sum), 2) if st_tot_sum > 0 else 1.0
    df_wuv = round(team_wuv * (pos_sums["DF"] / st_tot_sum), 2) if st_tot_sum > 0 else 4.0
    mf_wuv = round(team_wuv * (pos_sums["MF"] / st_tot_sum), 2) if st_tot_sum > 0 else 2.0
    fw_wuv = round(team_wuv * (pos_sums["FW"] / st_tot_sum), 2) if st_tot_sum > 0 else 2.0
    
    return {
        "team_wuv": team_wuv,
        "st_avg": round(st_avg, 3),
        "sub_avg": round(sub_avg, 3),
        "gk_wuv": gk_wuv,
        "df_wuv": df_wuv,
        "mf_wuv": mf_wuv,
        "fw_wuv": fw_wuv,
        "starters_detail": starters_detail
    }

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
    
    h_total = h_info["team_wuv"] + 0.25  # 홈 어드밴티지 +0.25 WUV
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
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_name TEXT NOT NULL,
        player_name TEXT NOT NULL,
        position TEXT NOT NULL,
        rating REAL NOT NULL,
        goals_per90 REAL NOT NULL,
        player_uv REAL NOT NULL,
        UNIQUE(team_name, player_name) ON CONFLICT REPLACE
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
        print(f"\n=== [{round_title}] 매치업 및 팀 11.0 WUV 상세 데이터 검증 ===", flush=True)
        
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
                
                ensure_team_roster(home_team)
                ensure_team_roster(away_team)
                
                pred = get_match_prediction(home_team, away_team)
                h_wuv = pred["home_wuv"]
                a_wuv = pred["away_wuv"]
                
                # [3. 데이터 검증 및 콘솔 로그 출력]
                print(f"\n⚽ [{home_team}] vs [{away_team}] 매치업 WUV 검증:", flush=True)
                print(f"   • [{home_team}] 팀 최종 11.0 WUV: {h_wuv['team_wuv']} WUV (선발 평균: {h_wuv['st_avg']} UV, 교체 평균: {h_wuv['sub_avg']} UV)", flush=True)
                print(f"     - 선발 11명 개인 UV: ", end="", flush=True)
                for p in h_wuv['starters_detail']:
                    print(f"{p['name']}({p['pos']}:{p['uv']}) ", end="", flush=True)
                print("", flush=True)
                
                print(f"   • [{away_team}] 팀 최종 11.0 WUV: {a_wuv['team_wuv']} WUV (선발 평균: {a_wuv['st_avg']} UV, 교체 평균: {a_wuv['sub_avg']} UV)", flush=True)
                print(f"     - 선발 11명 개인 UV: ", end="", flush=True)
                for p in a_wuv['starters_detail']:
                    print(f"{p['name']}({p['pos']}:{p['uv']}) ", end="", flush=True)
                print("", flush=True)
                
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
                print(f"  ✓ 예측 결과: {pred['winner']} ({status_disp})", flush=True)
                
            except Exception as ex:
                print(f"❌ 경기 동기화 실패: {ex}", flush=True)
                
    conn.commit()
    conn.close()
    print(f"\n🎉 성공적으로 EPL 공식 정규 시즌 {synced_count}개 경기를 epl_data.db에 적재하였습니다!", flush=True)

if __name__ == "__main__":
    print(f"🚀 EPL 정규 시즌 파이프라인 시작 (개인 UV 0.1~2.0 & 팀 11.0 WUV 합성 로직 적용)", flush=True)
    run_pipeline()
