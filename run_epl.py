
PLAYER_NAME_MAP = {
    '엘링 홀란드': 'Erling Haaland', '필 포든': 'Phil Foden', '베르나르두 실바': 'Bernardo Silva',
    '후벵 디아스': 'Rúben Dias', '요슈코 그바르디올': 'Josko Gvardiol', '잔루이지 돈나룸마': 'Gianluigi Donnarumma',
    '헤로니모 룰리': 'Geronimo Rulli', '부카요 사카': 'Bukayo Saka', '마르틴 외데고르': 'Martin Ødegaard',
    '데클런 라이스': 'Declan Rice', '윌리엄 살리바': 'William Saliba', '가브리엘 마갈량이스': 'Gabriel Magalhães',
    '빅토르 예케레스': 'Viktor Gyökeres', '벤 화이트': 'Ben White', '다비드 라야': 'David Raya',
    '버질 반 다이크': 'Virgil van Dijk', '트렌트 알렉산더-아놀드': 'Trent Alexander-Arnold',
    '플로리안 비르츠': 'Florian Wirtz', '알리송 베케르': 'Alisson Becker', '콜 파머': 'Cole Palmer',
    '모이세스 카이세도': 'Moisés Caicedo', '브루노 페르난데스': 'Bruno Fernandes', '올리 와트킨스': 'Ollie Watkins',
    '알렉산데르 이삭': 'Alexander Isak', '제임스 매디슨': 'James Maddison', '도미닉 솔랑케': 'Dominic Solanke',
    '가브리엘 제수스': 'Gabriel Jesus', '카이 하베르츠': 'Kai Havertz', '미켈 메리노': 'Mikel Merino',
    '마커스 래시포드': 'Marcus Rashford', '마테우스 쿠냐': 'Matheus Cunha', '브라이언 음베우모': 'Bryan Mbeumo',
    '해리 매과이어': 'Harry Maguire', '루크 쇼': 'Luke Shaw', '리산드로 마르티네스': 'Lisandro Martínez',
    '디오구 달롯': 'Diogo Dalot', '유리 틸레만스': 'Youri Tielemans', '엔초 페르난데스': 'Enzo Fernández',
    '페드로 네투': 'Pedro Neto', '주앙 페드로': 'João Pedro', '리스 제임스': 'Reece James',
    '웨슬리 포파나': 'Wesley Fofana', '로베르트 산체스': 'Robert Sánchez', '산드로 토날리': 'Sandro Tonali',
    '로드리고 벤탕쿠르': 'Rodrigo Bentancur', '히샤를리송': 'Richarlison', '앤디 로버트슨': 'Andrew Robertson',
    '벤 데이비스': 'Ben Davies', '마르틴 두브라브카': 'Martin Dúbravka', '존 맥긴': 'John McGinn',
}

def normalize_player_name(p_name):
    return PLAYER_NAME_MAP.get(p_name.strip(), p_name.strip())

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

PLAYER_STATS_LOOKUP = {
    # 1. 아스널 (Arsenal)
    "Bukayo Saka": {"rating": 7.75, "pos": "FW", "goals_per90": 0.48},
    "부카요 사카": {"rating": 7.75, "pos": "FW", "goals_per90": 0.48},
    "Martin Ødegaard": {"rating": 7.65, "pos": "MF", "goals_per90": 0.35},
    "마르틴 외데고르": {"rating": 7.65, "pos": "MF", "goals_per90": 0.35},
    "Declan Rice": {"rating": 7.55, "pos": "MF", "goals_per90": 0.20},
    "데클런 라이스": {"rating": 7.55, "pos": "MF", "goals_per90": 0.20},
    "William Saliba": {"rating": 7.50, "pos": "DF", "goals_per90": 0.05},
    "윌리엄 살리바": {"rating": 7.50, "pos": "DF", "goals_per90": 0.05},
    "Gabriel Magalhães": {"rating": 7.45, "pos": "DF", "goals_per90": 0.10},
    "가브리엘 마갈량이스": {"rating": 7.45, "pos": "DF", "goals_per90": 0.10},
    "Viktor Gyökeres": {"rating": 7.70, "pos": "FW", "goals_per90": 0.65},
    "빅토르 예케레스": {"rating": 7.70, "pos": "FW", "goals_per90": 0.65},

    # 2. 맨체스터 시티 (Man City)
    "Erling Haaland": {"rating": 7.85, "pos": "FW", "goals_per90": 0.95},
    "엘링 홀란드": {"rating": 7.85, "pos": "FW", "goals_per90": 0.95},
    "Phil Foden": {"rating": 7.65, "pos": "MF", "goals_per90": 0.55},
    "필 포든": {"rating": 7.65, "pos": "MF", "goals_per90": 0.55},
    "Bernardo Silva": {"rating": 7.45, "pos": "MF", "goals_per90": 0.20},
    "베르나르두 실바": {"rating": 7.45, "pos": "MF", "goals_per90": 0.20},
    "Rúben Dias": {"rating": 7.45, "pos": "DF", "goals_per90": 0.05},
    "후벵 디아스": {"rating": 7.45, "pos": "DF", "goals_per90": 0.05},

    # 3. 리버풀 (Liverpool)
    "Virgil van Dijk": {"rating": 7.55, "pos": "DF", "goals_per90": 0.08},
    "버질 반 다이크": {"rating": 7.55, "pos": "DF", "goals_per90": 0.08},
    "Trent Alexander-Arnold": {"rating": 7.50, "pos": "DF", "goals_per90": 0.12},
    "트렌트 알렉산더-아놀드": {"rating": 7.50, "pos": "DF", "goals_per90": 0.12},
    "Florian Wirtz": {"rating": 7.70, "pos": "MF", "goals_per90": 0.45},
    "플로리안 비르츠": {"rating": 7.70, "pos": "MF", "goals_per90": 0.45},

    # 4. 첼시 (Chelsea)
    "Cole Palmer": {"rating": 7.80, "pos": "FW", "goals_per90": 0.60},
    "콜 파머": {"rating": 7.80, "pos": "FW", "goals_per90": 0.60},

    # 5. 맨체스터 유나이티드 (Man Utd)
    "Bruno Fernandes": {"rating": 7.55, "pos": "MF", "goals_per90": 0.30},
    "브루노 페르난데스": {"rating": 7.55, "pos": "MF", "goals_per90": 0.30},

    # 6. 아스톤 빌라 (Aston Villa)
    "Ollie Watkins": {"rating": 7.35, "pos": "FW", "goals_per90": 0.45},
    "올리 와트킨스": {"rating": 7.35, "pos": "FW", "goals_per90": 0.45},
    "John McGinn": {"rating": 7.15, "pos": "MF", "goals_per90": 0.15},
    "존 맥긴": {"rating": 7.15, "pos": "MF", "goals_per90": 0.15},

    # 7. 뉴캐슬 유나이티드 (Newcastle)
    "Alexander Isak": {"rating": 7.45, "pos": "FW", "goals_per90": 0.55},
    "알렉산데르 이삭": {"rating": 7.45, "pos": "FW", "goals_per90": 0.55},
    "Anthony Gordon": {"rating": 7.25, "pos": "FW", "goals_per90": 0.35},
    "앤서니 고든": {"rating": 7.25, "pos": "FW", "goals_per90": 0.35},

    # 8. 토트넘 홋스퍼 (Tottenham)
    "James Maddison": {"rating": 7.30, "pos": "MF", "goals_per90": 0.28},
    "제임스 매디슨": {"rating": 7.30, "pos": "MF", "goals_per90": 0.28},
    "Dominic Solanke": {"rating": 7.20, "pos": "FW", "goals_per90": 0.40},
    "도미닉 솔랑케": {"rating": 7.20, "pos": "FW", "goals_per90": 0.40},

    # 9. 브라이튼 (Brighton)
    "Kaoru Mitoma": {"rating": 7.15, "pos": "FW", "goals_per90": 0.25},
    "미토마 카오루": {"rating": 7.15, "pos": "FW", "goals_per90": 0.25},
    "Evan Ferguson": {"rating": 7.05, "pos": "FW", "goals_per90": 0.30},

    # 10. 본머스 (Bournemouth)
    "Evanilson": {"rating": 7.05, "pos": "FW", "goals_per90": 0.35},
    "에바닐송": {"rating": 7.05, "pos": "FW", "goals_per90": 0.35},

    # 11. 브렌트포드 (Brentford)
    "Yoane Wissa": {"rating": 7.05, "pos": "FW", "goals_per90": 0.38},
    "요안 위사": {"rating": 7.05, "pos": "FW", "goals_per90": 0.38},

    # 12. 풀럼 (Fulham)
    "Alex Iwobi": {"rating": 7.00, "pos": "MF", "goals_per90": 0.18},
    "알렉스 이워비": {"rating": 7.00, "pos": "MF", "goals_per90": 0.18},

    # 13. 크리스탈 팰리스 (Crystal Palace)
    "Jean-Philippe Mateta": {"rating": 7.10, "pos": "FW", "goals_per90": 0.42},
    "장필리프 마테타": {"rating": 7.10, "pos": "FW", "goals_per90": 0.42},

    # 14. 에버턴 (Everton)
    "Dwight McNeil": {"rating": 6.95, "pos": "MF", "goals_per90": 0.15},
    "드와이트 맥닐": {"rating": 6.95, "pos": "MF", "goals_per90": 0.15},

    # 15. 노팅엄 포레스트 (Nottingham Forest)
    "Chris Wood": {"rating": 6.65, "pos": "FW", "goals_per90": 0.30},
    "크리스 우드": {"rating": 6.65, "pos": "FW", "goals_per90": 0.30},

    # 16. 입스위치 타운 (Ipswich Town)
    "Liam Delap": {"rating": 6.55, "pos": "FW", "goals_per90": 0.25},
    "리암 들랍": {"rating": 6.55, "pos": "FW", "goals_per90": 0.25},

    # 17. 코번트리 시티 (Coventry City)
    "Haji Wright": {"rating": 6.45, "pos": "FW", "goals_per90": 0.22},
    "하지 라이트": {"rating": 6.45, "pos": "FW", "goals_per90": 0.22},

    # 18. 헐 시티 (Hull City)
    "Oscar Estupiñan": {"rating": 6.40, "pos": "FW", "goals_per90": 0.20},
    "오스카르 에스투피냔": {"rating": 6.40, "pos": "FW", "goals_per90": 0.20},

    # 19. 선덜랜드 (Sunderland)
    "Wilson Isidor": {"rating": 6.35, "pos": "FW", "goals_per90": 0.18},
    "윌슨 이시도르": {"rating": 6.35, "pos": "FW", "goals_per90": 0.18},

    # 20. 리즈 유나이티드 (Leeds United)
    "Daniel James": {"rating": 6.50, "pos": "FW", "goals_per90": 0.20},
    "다니엘 제임스": {"rating": 6.50, "pos": "FW", "goals_per90": 0.20},
}


from app import TEAMS_ROSTER

def normalize_team_name(raw_name):
    for key, val in TEAM_NAME_MAP.items():
        if key.lower() in raw_name.lower() or raw_name.lower() in key.lower():
            return val
    return raw_name

def calculate_player_uv(player_data):
    """
    [1. 개인별 UV 산출 함수 (0.1 ~ 3.0 Scale)]
    기준점: 리그 평균 선수 평점(6.80) = 1.0 UV
    공식:
      - GK: min(max(1.0 + (rating - 6.8) * 1.2, 0.1), 3.0)
      - DF: min(max(1.0 + (rating - 6.8) * 1.1, 0.1), 3.0)
      - MF: min(max(1.0 + (rating - 6.8) * 1.0, 0.1), 3.0)
      - FW: min(max(1.0 + (rating - 6.8) * 1.0 + (goals_per90 * 0.5), 0.1), 3.0)
    """
    p_name_raw = player_data.get("name", "")
    p_name = normalize_player_name(p_name_raw)
    pos = str(player_data.get("pos", "MF") or "MF").upper()
    pos_clean = "GK" if pos in ["GK", "G"] else ("DF" if pos in ["DF", "D"] else ("MF" if pos in ["MF", "M"] else "FW"))
    
    rating = float(player_data.get("rating", 6.80) or 6.80)
    goals_per90 = float(player_data.get("goals_per90", 0.0) or 0.0)

    # 1. DB player_stats 테이블 직접 조회
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT rating, goals_per90, position FROM player_stats WHERE player_name LIKE ? OR player_name = ?", (f"%{p_name}%", p_name))
        row = cursor.fetchone()
        conn.close()
        if row:
            rating = float(row[0])
            goals_per90 = float(row[1])
            pos_clean = str(row[2])
    except Exception:
        pass

    if pos_clean in ["GK", "G"]:
        raw_uv = 1.0 + (rating - 6.8) * 1.2
    elif pos_clean in ["DF", "D"]:
        raw_uv = 1.0 + (rating - 6.8) * 1.1
    elif pos_clean in ["MF", "M"]:
        raw_uv = 1.0 + (rating - 6.8) * 1.0
    elif pos_clean in ["FW", "F"]:
        raw_uv = 1.0 + (rating - 6.8) * 1.0 + (goals_per90 * 0.5)
    else:
        raw_uv = 1.0 + (rating - 6.8) * 1.0

    return round(min(max(raw_uv, 0.1), 3.0), 3)

def calculate_wuv(team_name):
    """
    [2. 팀 11.0 WUV 합성 로직 구현]
    Starters_Avg_UV = sum(선발 11명 UV) / 11
    Subs_Avg_UV = sum(교체 5명 UV) / 5
    Team_WUV = 11.0 * (0.85 * Starters_Avg_UV + 0.15 * Subs_Avg_UV)
    """
    ensure_team_roster(team_name)
    team = TEAMS_ROSTER[team_name]
    
    starters = team.get("starters", [])[:11]
    subs = team.get("subs", [])[:5]
    
    st_list = []
    for p in starters:
        uv = calculate_player_uv(p)
        st_list.append({"name": p.get("name"), "pos": p.get("pos"), "uv": uv})
        
    sub_list = []
    for p in subs:
        uv = calculate_player_uv(p)
        sub_list.append({"name": p.get("name"), "pos": p.get("pos"), "uv": uv})
        
    st_avg = sum([p["uv"] for p in st_list]) / len(st_list) if st_list else 1.0
    sub_avg = sum([p["uv"] for p in sub_list]) / len(sub_list) if sub_list else 1.0
    
    team_wuv = 11.0 * (0.85 * st_avg + 0.15 * sub_avg)
    
    st_df = pd.DataFrame(st_list)
    sub_df = pd.DataFrame(sub_list)
    
    return {
        "team_wuv": round(team_wuv, 2),
        "st_avg": round(st_avg, 3),
        "sub_avg": round(sub_avg, 3),
        "starters_detail": st_list,
        "subs_detail": sub_list,
        "wuv_att": round(team_wuv * 0.6, 2),
        "wuv_def": round(team_wuv * 0.4, 2),
        "wuv_total": round(team_wuv, 2),
        "st_df": st_df,
        "sub_df": sub_df
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
    print(f"🚀 EPL 정규 시즌 파이프라인 시작 (개인 UV 0.1~3.0 & 팀 11.0 WUV 합성 로직 적용)", flush=True)
    run_pipeline()
