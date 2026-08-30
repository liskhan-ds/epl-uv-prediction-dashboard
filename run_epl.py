

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


OFFICIAL_STATS = {
    "Bukayo Saka": (7.75, 0.48), "Martin Ødegaard": (7.65, 0.35), "Declan Rice": (7.55, 0.20),
    "William Saliba": (7.50, 0.05), "Gabriel Magalhães": (7.45, 0.10), "Viktor Gyökeres": (7.70, 0.65),
    "Ben White": (7.30, 0.05), "David Raya": (7.25, 0.0), "Kai Havertz": (7.35, 0.38),
    "Gabriel Martinelli": (7.30, 0.30), "Leandro Trossard": (7.25, 0.32), "Kepa Arrizabalaga": (7.10, 0.0),
    "Erling Haaland": (7.85, 0.95), "Phil Foden": (7.65, 0.55), "Bernardo Silva": (7.45, 0.20),
    "Rúben Dias": (7.45, 0.05), "Josko Gvardiol": (7.40, 0.12), "Kevin De Bruyne": (7.75, 0.40),
    "Rodri": (7.60, 0.15), "Ederson": (7.25, 0.0), "Jérémy Doku": (7.30, 0.25), "Marc Guéhi": (7.35, 0.05),
    "Rayan Aït-Nouri": (7.25, 0.08), "Gerónimo Rulli": (7.15, 0.0),
    "Mohamed Salah": (7.80, 0.75), "Virgil van Dijk": (7.55, 0.08), "Trent Alexander-Arnold": (7.50, 0.12),
    "Florian Wirtz": (7.70, 0.45), "Alexis Mac Allister": (7.35, 0.18), "Dominik Szoboszlai": (7.30, 0.22),
    "Alisson Becker": (7.40, 0.0), "Luis Díaz": (7.35, 0.35), "Cody Gakpo": (7.25, 0.30),
    "Cole Palmer": (7.80, 0.60), "Moisés Caicedo": (7.40, 0.05), "Enzo Fernández": (7.30, 0.15),
    "Nicolas Jackson": (7.25, 0.40), "Pedro Neto": (7.20, 0.25), "Robert Sánchez": (7.15, 0.0),
    "Bruno Fernandes": (7.55, 0.30), "Marcus Rashford": (7.25, 0.32), "Alejandro Garnacho": (7.20, 0.28),
    "Kobbie Mainoo": (7.30, 0.15), "Matthijs de Ligt": (7.25, 0.08), "André Onana": (7.15, 0.0),
    "Son Heung-Min": (7.60, 0.50), "James Maddison": (7.30, 0.28), "Dominic Solanke": (7.20, 0.40),
    "Cristian Romero": (7.35, 0.10), "Micky van de Ven": (7.30, 0.08), "Guglielmo Vicario": (7.20, 0.0),
    "Ollie Watkins": (7.35, 0.45), "John McGinn": (7.15, 0.15), "Emiliano Martínez": (7.35, 0.0),
    "Alexander Isak": (7.45, 0.55), "Anthony Gordon": (7.25, 0.35), "Bruno Guimarães": (7.40, 0.15),
    "Kaoru Mitoma": (7.15, 0.25), "Evan Ferguson": (7.05, 0.30), "Bart Verbruggen": (7.10, 0.0),
    "Evanilson": (7.05, 0.35), "Justin Kluivert": (7.00, 0.25), "Fraser Forster": (7.00, 0.0),
    "Yoane Wissa": (7.05, 0.38), "Bryan Mbeumo": (7.30, 0.42), "Caoimhín Kelleher": (7.10, 0.0),
    "Jean-Philippe Mateta": (7.10, 0.42), "Eberechi Eze": (7.30, 0.30), "Dean Henderson": (7.10, 0.0),
    "Jordan Pickford": (7.20, 0.0), "Dwight McNeil": (6.95, 0.15), "Jarrad Branthwaite": (7.20, 0.05),
    "Bernd Leno": (7.15, 0.0), "Alex Iwobi": (7.00, 0.18), "Emile Smith Rowe": (7.10, 0.22),
    "Chris Wood": (6.75, 0.32), "Morgan Gibbs-White": (7.15, 0.20), "Matz Sels": (7.00, 0.0),
    "Liam Delap": (6.45, 0.10), "Arijanet Muric": (6.50, 0.0),
    "Illan Meslier": (6.40, 0.0), "Daniel James": (6.45, 0.12),
    "Haji Wright": (6.40, 0.10), "Oliver Dovin": (6.45, 0.0),
    "Oscar Estupiñan": (6.35, 0.08), "Ivor Pandur": (6.40, 0.0),
    "Wilson Isidor": (6.35, 0.08), "Anthony Patterson": (6.40, 0.0),
}

TEAM_CONCEDED_PER_GAME = {
    "Arsenal": 0.8, "Manchester City": 0.9, "Liverpool": 1.0, "Chelsea": 1.2,
    "Manchester United": 1.3, "Tottenham Hotspur": 1.35, "Aston Villa": 1.3,
    "Newcastle United": 1.35, "Brighton & Hove Albion": 1.4, "AFC Bournemouth": 1.45,
    "Brentford": 1.50, "Crystal Palace": 1.50, "Fulham": 1.55, "Everton": 1.60,
    "Nottingham Forest": 1.65, "Ipswich Town": 1.75, "Leeds United": 1.80,
    "Coventry City": 1.85, "Sunderland": 1.90, "Hull City": 1.95,
}

TEAM_GOALS_PER_GAME = {
    "Arsenal": 2.2, "Manchester City": 2.3, "Liverpool": 2.1, "Chelsea": 1.8,
    "Manchester United": 1.6, "Tottenham Hotspur": 1.7, "Aston Villa": 1.6,
    "Newcastle United": 1.5, "Brighton & Hove Albion": 1.4, "AFC Bournemouth": 1.3,
    "Brentford": 1.2, "Crystal Palace": 1.1, "Fulham": 1.15, "Everton": 1.0,
    "Nottingham Forest": 1.05, "Ipswich Town": 0.95, "Leeds United": 0.90,
    "Coventry City": 0.85, "Sunderland": 0.80, "Hull City": 0.75,
}

LOW_POSSESSION_TEAMS = ["Everton", "Nottingham Forest", "Ipswich Town", "Leeds United", "Coventry City", "Sunderland", "Hull City"]

MATCHWEEK_1_ABSENCES = {
    "Arsenal": ["William Saliba", "Jurriën Timber"],
    "Chelsea": ["Wesley Fofana"],
    "Fulham": ["Joachim Andersen"],
    "Manchester United": ["Rasmus Højlund", "Tyrell Malacia"],
    "Tottenham Hotspur": ["Richarlison"],
    "Liverpool": ["Stefan Bajcetic"],
    "Newcastle United": ["Sven Botman"],
    "Aston Villa": ["Boubacar Kamara"],
}

def get_team_roster(team_name, absentees=None):
    if not os.path.exists("rosters_2026.json"):
        return {"starters": [], "subs": []}
    with open("rosters_2026.json", "r", encoding="utf-8") as f:
        rosters = json.load(f)
        
    normalized_map = {normalize_team_name(k): v for k, v in rosters.items()}
    norm_tname = normalize_team_name(team_name)
    plist = normalized_map.get(norm_tname, [])
    
    if absentees is None:
        absentees = MATCHWEEK_1_ABSENCES.get(team_name, [])
        
    available = [p for p in plist if p.get("name") not in absentees]
    
    for p in available:
        p["calc_uv"] = calculate_player_uv(p, team_name)
        
    gks = sorted([p for p in available if p.get("pos") in ["G", "GK"]], key=lambda x: x["calc_uv"], reverse=True)
    dfs = sorted([p for p in available if p.get("pos") in ["D", "DF"]], key=lambda x: x["calc_uv"], reverse=True)
    mfs = sorted([p for p in available if p.get("pos") in ["M", "MF"]], key=lambda x: x["calc_uv"], reverse=True)
    fws = sorted([p for p in available if p.get("pos") in ["F", "FW"]], key=lambda x: x["calc_uv"], reverse=True)
    
    starters = gks[:1] + dfs[:4] + mfs[:3] + fws[:3]
    subs = (gks[1:2] + dfs[4:6] + mfs[3:5] + fws[3:5])[:5]
    return {"starters": starters, "subs": subs}
def calculate_player_uv(player_data, team_name=""):
    p_name_raw = player_data.get("name", "")
    p_name = normalize_team_name(p_name_raw) if "normalize_team_name" in globals() else p_name_raw.strip()
    
    rating = None
    goals_per90 = 0.0
    position = player_data.get("pos", "M")
    
    matched = False
    for off_name, (off_r, off_g90) in OFFICIAL_STATS.items():
        if off_name.lower() in p_name_raw.lower() or p_name_raw.lower() in off_name.lower():
            rating = off_r
            goals_per90 = off_g90
            matched = True
            break
            
    if not matched and os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT rating, goals_per90, position FROM player_stats WHERE player_name = ? OR player_name LIKE ?", (p_name_raw, f"%{p_name_raw}%"))
            row = cursor.fetchone()
            if row:
                rating = row[0]
                goals_per90 = row[1]
                position = row[2]
            conn.close()
        except Exception:
            pass
            
    pos_clean = "GK" if position in ["G", "GK"] else ("DF" if position in ["D", "DF"] else ("MF" if position in ["M", "MF"] else "FW"))
    
    tgoals = TEAM_GOALS_PER_GAME.get(team_name, 1.30)
    is_low_poss = team_name in LOW_POSSESSION_TEAMS
    
    if rating is None:
        if pos_clean == "GK":
            raw_uv = 0.95
        elif pos_clean == "DF":
            raw_uv = 0.90
        elif pos_clean == "MF":
            raw_uv = 0.82 if is_low_poss else 0.88
        else: # FW
            raw_uv = 0.78 if tgoals < 1.1 else 0.85
    elif rating >= 6.65:
        if pos_clean == "GK":
            raw_uv = 1.0 + (rating - 6.65) * 0.45
        elif pos_clean == "DF":
            raw_uv = 1.0 + (rating - 6.65) * 0.40
        elif pos_clean == "MF":
            raw_uv = 1.0 + (rating - 6.65) * 0.35
            if is_low_poss:
                raw_uv -= 0.08
        else: # FW
            raw_uv = 1.0 + (rating - 6.65) * 0.35 + (goals_per90 * 0.20)
            if goals_per90 < 0.15 or tgoals < 1.1:
                fw_penalty = min(0.15, round(0.10 + (0.15 - max(goals_per90, 0.0)) * 0.33, 3))
                raw_uv -= fw_penalty
    else:
        # rating < 6.65 penalty: MF slope 0.80
        slope = 0.80 if pos_clean == "MF" else 0.65
        raw_uv = 1.0 + (rating - 6.65) * slope + (goals_per90 * 0.20 if pos_clean == "FW" else 0.0)
        if pos_clean == "MF" and is_low_poss:
            raw_uv -= 0.08
        elif pos_clean == "FW" and (goals_per90 < 0.15 or tgoals < 1.1):
            fw_penalty = min(0.15, round(0.10 + (0.15 - max(goals_per90, 0.0)) * 0.33, 3))
            raw_uv -= fw_penalty
        
    # Defense/GK conceded penalty if team conceded > 1.4 per game
    conc = TEAM_CONCEDED_PER_GAME.get(team_name, 1.30)
    if pos_clean in ["GK", "DF"] and conc > 1.4:
        def_penalty = min(0.12, round(0.04 + (conc - 1.4) * 0.10, 3))
        raw_uv -= def_penalty
        
    return round(min(max(raw_uv, 0.4), 2.0), 3)

def calculate_wuv(team_name, absentees=None):
    roster = get_team_roster(team_name, absentees=absentees)
    starters = roster.get("starters", [])
    subs = roster.get("subs", [])
    
    st_uvs = [calculate_player_uv(p, team_name) for p in starters]
    sub_uvs = [calculate_player_uv(p, team_name) for p in subs]
    
    st_avg = sum(st_uvs) / len(st_uvs) if st_uvs else 0.95
    sub_avg = sum(sub_uvs) / len(sub_uvs) if sub_uvs else 0.85
    
    raw_wuv = (0.85 * st_avg + 0.15 * sub_avg)
    team_wuv = round(11.0 + 10.5 * (raw_wuv - 0.835), 2)
    
    # Position detail breakdown
    pos_sums = {"GK": 0.0, "DF": 0.0, "MF": 0.0, "FW": 0.0}
    starters_detail = []
    for p in starters:
        uv = calculate_player_uv(p, team_name)
        pos = p.get("pos", "M")
        pos_clean = "GK" if pos in ["G","GK"] else ("DF" if pos in ["D","DF"] else ("MF" if pos in ["M","MF"] else "FW"))
        pos_sums[pos_clean] += uv
        starters_detail.append({"name": p.get("name"), "pos": pos_clean, "uv": uv})
        
    st_tot_sum = sum(st_uvs)
    gk_wuv = round(team_wuv * (pos_sums["GK"] / st_tot_sum), 2) if st_tot_sum > 0 else 1.0
    df_wuv = round(team_wuv * (pos_sums["DF"] / st_tot_sum), 2) if st_tot_sum > 0 else 4.0
    mf_wuv = round(team_wuv * (pos_sums["MF"] / st_tot_sum), 2) if st_tot_sum > 0 else 3.0
    fw_wuv = round(team_wuv * (pos_sums["FW"] / st_tot_sum), 2) if st_tot_sum > 0 else 3.0
    
    return {
        "team_wuv": team_wuv,
        "st_avg": round(st_avg, 3),
        "sub_avg": round(sub_avg, 3),
        "st_sum": round(st_tot_sum, 3),
        "sub_sum": round(sum(sub_uvs), 3),
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
    
    h_total = h_info["team_wuv"] + 0.25
    a_total = a_info["team_wuv"]
    
    gap = h_total - a_total
    
    home_kr = TEAM_NAME_MAP.get(home_team, home_team)
    away_kr = TEAM_NAME_MAP.get(away_team, away_team)
    
    if abs(gap) <= 0.40:
        winner = "무승부"
        code = "DRAW"
    elif gap > 0.40:
        winner = f"{home_kr} 승"
        code = "HOME"
    else:
        winner = f"{away_kr} 승"
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
