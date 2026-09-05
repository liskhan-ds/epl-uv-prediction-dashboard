import os
import sqlite3
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "epl_data.db")

TEAM_NAME_MAP = {
    "Manchester United": "Manchester United", "Arsenal": "Arsenal", "Manchester City": "Manchester City",
    "Liverpool": "Liverpool", "Chelsea": "Chelsea", "Tottenham Hotspur": "Tottenham Hotspur", "Tottenham": "Tottenham Hotspur",
    "Newcastle United": "Newcastle United", "Newcastle": "Newcastle United", "Aston Villa": "Aston Villa",
    "West Ham United": "West Ham United", "West Ham": "West Ham United", "Brighton & Hove Albion": "Brighton & Hove Albion",
    "Brighton": "Brighton & Hove Albion", "Fulham": "Fulham", "Crystal Palace": "Crystal Palace", "Everton": "Everton",
    "Wolverhampton Wanderers": "Wolverhampton Wanderers", "Wolves": "Wolverhampton Wanderers", "AFC Bournemouth": "AFC Bournemouth",
    "Bournemouth": "AFC Bournemouth", "Brentford": "Brentford", "Nottingham Forest": "Nottingham Forest",
    "Leicester City": "Leicester City", "Ipswich Town": "Ipswich Town", "Southampton": "Southampton",
    "Sunderland": "Sunderland", "Burnley": "Burnley", "Leeds United": "Leeds United", "Leeds": "Leeds United",
    "Coventry City": "Coventry City", "Coventry": "Coventry City", "Hull City": "Hull City", "Hull": "Hull City"
}

def normalize_team_name(raw_name):
    for key, val in TEAM_NAME_MAP.items():
        if key.lower() in raw_name.lower() or raw_name.lower() in key.lower():
            return val
    return raw_name

def parse_espn_date(date_str):
    if not date_str:
        return "", ""
    try:
        dt_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        # UK Time: BST in summer (UTC+1), GMT in winter (UTC+0)
        dt_uk = dt_utc.astimezone(timezone(timedelta(hours=1)))
        # KST Time: UTC+9
        dt_kst = dt_utc.astimezone(timezone(timedelta(hours=9)))
        return dt_uk.strftime("%Y-%m-%d"), dt_kst.strftime("%Y-%m-%d")
    except Exception:
        return date_str[:10], date_str[:10]

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
    "Liverpool": ["Jeremie Frimpong"],
    "Manchester City": ["Kevin De Bruyne"],
    "Manchester United": ["Matthijs de Ligt"],
    "Newcastle United": ["Sven Botman"],
    "Tottenham Hotspur": ["Destiny Udogie"],
    "Aston Villa": ["Boubacar Kamara"],
    "Brighton & Hove Albion": ["Solly March"],
}

def load_rosters_from_json():
    json_path = os.path.join(BASE_DIR, "rosters_2026.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load rosters_2026.json: {e}")
    return {}

TEAMS_ROSTER = load_rosters_from_json()

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

def get_team_roster(team_name, absentees=None):
    ensure_team_roster(team_name)
    roster = TEAMS_ROSTER.get(team_name, {"starters": [], "subs": []})
    starters = list(roster.get("starters", []))
    subs = list(roster.get("subs", []))
    
    if absentees:
        active_starters = [p for p in starters if p.get("name") not in absentees]
        missing_count = len(starters) - len(active_starters)
        
        if missing_count > 0:
            available_subs = [p for p in subs if p.get("name") not in absentees]
            substitutes = available_subs[:missing_count]
            starters = active_starters + substitutes
            
    return {"starters": starters, "subs": subs}

def calculate_player_uv(player_data, team_name=""):
    p_name = player_data.get("name", "")
    p_pos = player_data.get("pos", "MF")
    
    if p_name in OFFICIAL_STATS:
        rating, xg_90 = OFFICIAL_STATS[p_name]
    else:
        rating = 6.80
        xg_90 = 0.10
        
    conceded_per_game = TEAM_CONCEDED_PER_GAME.get(team_name, 1.40)
    def_uv = max(0.1, round(0.50 * (rating / 7.0) * (1.20 / max(0.5, conceded_per_game)), 2))
    
    goals_per_game = TEAM_GOALS_PER_GAME.get(team_name, 1.30)
    
    if p_pos in ["FW", "ST", "LW", "RW"]:
        base_att = 0.65 * (rating / 7.0) * (1.0 + xg_90)
    elif p_pos in ["MF", "CAM", "CM"]:
        base_att = 0.45 * (rating / 7.0) * (1.0 + (xg_90 * 0.5))
    elif p_pos in ["DF", "CB", "LB", "RB"]:
        base_att = 0.30 * (rating / 7.0)
    else:
        base_att = 0.15 * (rating / 7.0)
        
    att_uv = max(0.1, round(base_att * (goals_per_game / 1.30), 2))
    
    att_uv = min(2.0, max(0.1, att_uv))
    def_uv = min(2.0, max(0.1, def_uv))
    
    return {"att_uv": att_uv, "def_uv": def_uv, "total_uv": att_uv + def_uv}

def calculate_wuv(team_name, absentees=None):
    roster_info = get_team_roster(team_name, absentees)
    starters = roster_info["starters"]
    
    att_list = []
    def_list = []
    
    for p in starters:
        uv_res = calculate_player_uv(p, team_name)
        att_list.append(uv_res["att_uv"])
        def_list.append(uv_res["def_uv"])
        
    raw_team_att = sum(att_list) if att_list else 5.5
    raw_team_def = sum(def_list) if def_list else 5.5
    raw_team_uv = raw_team_att + raw_team_def
    
    goals_pg = TEAM_GOALS_PER_GAME.get(team_name, 1.30)
    conc_pg = TEAM_CONCEDED_PER_GAME.get(team_name, 1.40)
    
    off_factor = goals_pg / 1.40
    def_factor = 1.30 / conc_pg
    
    if team_name in LOW_POSSESSION_TEAMS:
        tactical_mod = 0.95
    else:
        tactical_mod = 1.05
        
    scaled_team_uv = 11.0 * (raw_team_uv / 11.0) * (0.4 * off_factor + 0.4 * def_factor + 0.2 * tactical_mod)
    scaled_team_uv = max(8.5, min(14.5, round(scaled_team_uv, 2)))
    
    return {
        "team_name": team_name,
        "raw_team_uv": round(raw_team_uv, 2),
        "team_wuv": scaled_team_uv,
        "starters_count": len(starters)
    }

def get_match_prediction(home_team, away_team):
    h_info = calculate_wuv(home_team)
    a_info = calculate_wuv(away_team)
    
    h_total = h_info["team_wuv"] + 0.25
    a_total = a_info["team_wuv"]
    
    gap = h_total - a_total
    
    if abs(gap) <= 0.40:
        winner = "Draw"
        code = "DRAW"
    elif gap > 0.40:
        winner = f"{home_team} Win"
        code = "HOME"
    else:
        winner = f"{away_team} Win"
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
    
    if code == "DRAW":
        sc_h = sc_a = int(round((sc_h + sc_a) / 2.0))
    elif code == "HOME" and sc_h <= sc_a:
        sc_h = sc_a + 1
    elif code == "AWAY" and sc_a <= sc_h:
        sc_a = sc_h + 1
        
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

def run_pipeline():
    url_mw1 = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates=20260820-20260826"
    url_mw2 = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates=20260828-20260901"
    
    try:
        resp_mw1 = requests.get(url_mw1, timeout=10).json()
        resp_mw2 = requests.get(url_mw2, timeout=10).json()
    except Exception as e:
        print(f"Error fetching ESPN API: {e}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT UNIQUE,
        round_name TEXT NOT NULL,
        home_team TEXT NOT NULL,
        away_team TEXT NOT NULL,
        match_date TEXT NOT NULL,
        uk_date TEXT,
        kst_date TEXT,
        home_wuv REAL NOT NULL,
        away_wuv REAL NOT NULL,
        home_total_wuv REAL NOT NULL,
        away_total_wuv REAL NOT NULL,
        gap REAL NOT NULL,
        predicted_winner TEXT NOT NULL,
        prob_home REAL NOT NULL,
        prob_draw REAL NOT NULL,
        prob_away REAL NOT NULL,
        score_home INTEGER NOT NULL,
        score_away INTEGER NOT NULL,
        actual_score_home INTEGER,
        actual_score_away INTEGER,
        actual_winner TEXT,
        is_correct INTEGER
    )
    """)
    
    cursor.execute("PRAGMA table_info(predictions)")
    cols = [r[1] for r in cursor.fetchall()]
    if "uk_date" not in cols:
        cursor.execute("ALTER TABLE predictions ADD COLUMN uk_date TEXT")
    if "kst_date" not in cols:
        cursor.execute("ALTER TABLE predictions ADD COLUMN kst_date TEXT")

    def process_espn_events(events, round_label, mw_prefix):
        for idx, e in enumerate(events, 1):
            comp = e.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
                
            home_comp = competitors[0] if competitors[0].get("homeAway") == "home" else competitors[1]
            away_comp = competitors[1] if competitors[0].get("homeAway") == "home" else competitors[0]
            
            h_team_raw = home_comp.get("team", {}).get("displayName", "")
            a_team_raw = away_comp.get("team", {}).get("displayName", "")
            
            h_team = normalize_team_name(h_team_raw)
            a_team = normalize_team_name(a_team_raw)
            
            date_raw = e.get("date", "")
            uk_d, kst_d = parse_espn_date(date_raw)
            
            status_type = e.get("status", {}).get("type", {}).get("name", "")
            is_completed = (status_type == "STATUS_FULL_TIME")
            is_cancelled = status_type in ["STATUS_POSTPONED", "STATUS_CANCELED", "STATUS_SUSPENDED", "STATUS_ABANDONED"]
            
            act_sc_h = int(home_comp.get("score")) if (is_completed and home_comp.get("score") is not None) else None
            act_sc_a = int(away_comp.get("score")) if (is_completed and away_comp.get("score") is not None) else None
            
            if is_completed and act_sc_h is not None and act_sc_a is not None:
                if act_sc_h > act_sc_a:
                    act_winner = f"{h_team} Win"
                elif act_sc_a > act_sc_h:
                    act_winner = f"{a_team} Win"
                else:
                    act_winner = "Draw"
            elif is_cancelled:
                act_winner = "Postponed"
            else:
                act_winner = None
                
            mid = f"2026_{mw_prefix}_{idx}"
            
            cursor.execute("SELECT predicted_winner FROM predictions WHERE match_id = ?", (mid,))
            existing = cursor.fetchone()
            
            if existing:
                pred_winner = existing[0]
                if is_completed and act_winner is not None:
                    if (act_winner == pred_winner) or (h_team in act_winner and h_team in pred_winner) or (a_team in act_winner and a_team in pred_winner):
                        is_corr = 1
                    else:
                        is_corr = 0
                else:
                    is_corr = None
                    
                cursor.execute("""
                UPDATE predictions SET
                    uk_date = ?,
                    kst_date = ?,
                    actual_score_home = ?,
                    actual_score_away = ?,
                    actual_winner = ?,
                    is_correct = ?
                WHERE match_id = ?
                """, (uk_d, kst_d, act_sc_h, act_sc_a, act_winner, is_corr, mid))
            else:
                pred = get_match_prediction(h_team, a_team)
                pred_winner = pred["winner"]
                
                if is_completed and act_winner is not None:
                    if (act_winner == pred_winner) or (h_team in act_winner and h_team in pred_winner) or (a_team in act_winner and a_team in pred_winner):
                        is_corr = 1
                    else:
                        is_corr = 0
                else:
                    is_corr = None
                    
                cursor.execute("""
                INSERT INTO predictions (
                    match_id, round_name, home_team, away_team, match_date, uk_date, kst_date,
                    home_wuv, away_wuv, home_total_wuv, away_total_wuv,
                    gap, predicted_winner, prob_home, prob_draw, prob_away,
                    score_home, score_away,
                    actual_score_home, actual_score_away, actual_winner, is_correct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    mid, round_label, h_team, a_team, date_raw[:10], uk_d, kst_d,
                    pred["home_wuv"]["team_wuv"], pred["away_wuv"]["team_wuv"], pred["h_total"], pred["a_total"],
                    pred["gap"], pred_winner, pred["p_home"], pred["p_draw"], pred["p_away"],
                    pred["sc_h"], pred["sc_a"],
                    act_sc_h, act_sc_a, act_winner, is_corr
                ))

    process_espn_events(resp_mw1.get("events", []), "Round 1 (Gameweek 1)", "MW1")
    process_espn_events(resp_mw2.get("events", []), "Round 2 (Gameweek 2)", "MW2")

    conn.commit()
    conn.close()
    print("✅ Pipeline run complete! epl_data.db successfully updated.")

if __name__ == "__main__":
    print(f"🚀 EPL 정규 시즌 파이프라인 시작 (개인 UV 0.1~2.0 & 팀 11.0 WUV 합성 로직 적용)", flush=True)
    run_pipeline()
