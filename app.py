import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 상단 네비게이션
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="EPL AI 승부예측",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 상단 탭 네비게이션 (NBA/MLB 대시보드 템플릿과 동일 구조)
nav_col1, nav_col2, nav_col3, _ = st.columns([2.5, 2.5, 2.5, 4.5])
with nav_col1:
    st.button("⚽ EPL 대시보드 (현재)", disabled=True)
with nav_col2:
    st.link_button(
        "🏀 NBA 대시보드 바로가기 ↗", 
        "https://nba-uv-prediction.streamlit.app/"
    )
with nav_col3:
    st.link_button(
        "⚾ MLB 대시보드 바로가기 ↗", 
        "https://mlb-uv-prediction.streamlit.app/"
    )

st.divider()

# 메인 타이틀
st.title("⚽ EPL AI 승부예측 (by 11.0 WUV predictor)")
st.caption("11.0 WUV 기준 (공격 5.5 UV + 수비/빌드업 5.5 UV) | 선발 11인(85%) + 주요 교체 5인(15%) | 홈 어드밴티지(+0.25 UV) | 무승부 판정(격차 ±0.4 이내)")

# -----------------------------------------------------------------------------
# 2. EPL 구단별 라인업 및 UV 혜택 데이터 정의 (샘플 데이터베이스)
# -----------------------------------------------------------------------------
TEAMS_DATA = {
    "맨체스터 유나이티드": {
        "starters": [
            {"pos": "GK", "name": "안드레 오나나", "att_uv": 0.20, "def_uv": 0.50},
            {"pos": "DF", "name": "디오구 달롯", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "DF", "name": "마테이스 더 리흐트", "att_uv": 0.25, "def_uv": 0.55},
            {"pos": "DF", "name": "리산드로 마르티네스", "att_uv": 0.30, "def_uv": 0.55},
            {"pos": "DF", "name": "누사이르 마즈라위", "att_uv": 0.35, "def_uv": 0.45},
            {"pos": "MF", "name": "카세미루", "att_uv": 0.35, "def_uv": 0.55},
            {"pos": "MF", "name": "코비 메이누", "att_uv": 0.45, "def_uv": 0.50},
            {"pos": "MF", "name": "브루노 페르난데스", "att_uv": 0.70, "def_uv": 0.35},
            {"pos": "FW", "name": "알레한드로 가르나초", "att_uv": 0.60, "def_uv": 0.30},
            {"pos": "FW", "name": "마커스 래시포드", "att_uv": 0.65, "def_uv": 0.25},
            {"pos": "FW", "name": "라스무스 호일룬", "att_uv": 0.60, "def_uv": 0.25},
        ],
        "subs": [
            {"pos": "FW", "name": "조슈아 지르크지", "att_uv": 0.50, "def_uv": 0.25},
            {"pos": "MF", "name": "크리스티안 에릭센", "att_uv": 0.45, "def_uv": 0.30},
            {"pos": "MF", "name": "마누엘 우가르테", "att_uv": 0.30, "def_uv": 0.50},
            {"pos": "DF", "name": "해리 매과이어", "att_uv": 0.25, "def_uv": 0.45},
            {"pos": "GK", "name": "알타이 바인디르", "att_uv": 0.10, "def_uv": 0.40},
        ]
    },
    "아스널": {
        "starters": [
            {"pos": "GK", "name": "다비드 라야", "att_uv": 0.25, "def_uv": 0.55},
            {"pos": "DF", "name": "벤 화이트", "att_uv": 0.45, "def_uv": 0.50},
            {"pos": "DF", "name": "윌리엄 살리바", "att_uv": 0.30, "def_uv": 0.65},
            {"pos": "DF", "name": "가브리엘 마갈량이스", "att_uv": 0.35, "def_uv": 0.60},
            {"pos": "DF", "name": "율리엔 팀버", "att_uv": 0.40, "def_uv": 0.50},
            {"pos": "MF", "name": "데클런 라이스", "att_uv": 0.50, "def_uv": 0.60},
            {"pos": "MF", "name": "토마스 파티", "att_uv": 0.40, "def_uv": 0.50},
            {"pos": "MF", "name": "마르틴 외데고르", "att_uv": 0.75, "def_uv": 0.35},
            {"pos": "FW", "name": "부카요 사카", "att_uv": 0.80, "def_uv": 0.35},
            {"pos": "FW", "name": "가브리엘 마르티넬리", "att_uv": 0.65, "def_uv": 0.30},
            {"pos": "FW", "name": "가브리엘 제수스", "att_uv": 0.60, "def_uv": 0.35},
        ],
        "subs": [
            {"pos": "FW", "name": "레안드로 트로사르", "att_uv": 0.60, "def_uv": 0.25},
            {"pos": "MF", "name": "미켈 메리노", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "DF", "name": "리카르도 칼라피오리", "att_uv": 0.35, "def_uv": 0.50},
            {"pos": "FW", "name": "카이 하베르츠", "att_uv": 0.60, "def_uv": 0.35},
            {"pos": "GK", "name": "네투", "att_uv": 0.10, "def_uv": 0.40},
        ]
    },
    "맨체스터 시티": {
        "starters": [
            {"pos": "GK", "name": "에데르송", "att_uv": 0.30, "def_uv": 0.50},
            {"pos": "DF", "name": "카일 워커", "att_uv": 0.40, "def_uv": 0.55},
            {"pos": "DF", "name": "후벵 디아스", "att_uv": 0.30, "def_uv": 0.65},
            {"pos": "DF", "name": "마누엘 아칸지", "att_uv": 0.35, "def_uv": 0.55},
            {"pos": "DF", "name": "요슈코 그바르디올", "att_uv": 0.45, "def_uv": 0.55},
            {"pos": "MF", "name": "로드리", "att_uv": 0.55, "def_uv": 0.65},
            {"pos": "MF", "name": "케빈 더 브라위너", "att_uv": 0.85, "def_uv": 0.30},
            {"pos": "MF", "name": "베르나르두 실바", "att_uv": 0.65, "def_uv": 0.45},
            {"pos": "FW", "name": "필 포든", "att_uv": 0.75, "def_uv": 0.35},
            {"pos": "FW", "name": "사비뉴", "att_uv": 0.65, "def_uv": 0.30},
            {"pos": "FW", "name": "엘링 홀란드", "att_uv": 0.90, "def_uv": 0.20},
        ],
        "subs": [
            {"pos": "MF", "name": "일카이 귄도안", "att_uv": 0.55, "def_uv": 0.40},
            {"pos": "FW", "name": "잭 그릴리시", "att_uv": 0.60, "def_uv": 0.30},
            {"pos": "MF", "name": "마테오 코바치치", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "DF", "name": "존 스톤스", "att_uv": 0.35, "def_uv": 0.55},
            {"pos": "GK", "name": "스테판 오르테가", "att_uv": 0.15, "def_uv": 0.45},
        ]
    },
    "리버풀": {
        "starters": [
            {"pos": "GK", "name": "알리송 베케르", "att_uv": 0.25, "def_uv": 0.60},
            {"pos": "DF", "name": "트렌트 알렉산더-아놀드", "att_uv": 0.65, "def_uv": 0.40},
            {"pos": "DF", "name": "버질 반 다이크", "att_uv": 0.35, "def_uv": 0.65},
            {"pos": "DF", "name": "이브라히마 코나테", "att_uv": 0.25, "def_uv": 0.60},
            {"pos": "DF", "name": "앤디 로버트슨", "att_uv": 0.45, "def_uv": 0.50},
            {"pos": "MF", "name": "라이언 흐라번베르흐", "att_uv": 0.50, "def_uv": 0.50},
            {"pos": "MF", "name": "알렉시스 맥 알리스터", "att_uv": 0.55, "def_uv": 0.45},
            {"pos": "MF", "name": "도미니크 소보슬라이", "att_uv": 0.60, "def_uv": 0.40},
            {"pos": "FW", "name": "모하메드 살라", "att_uv": 0.85, "def_uv": 0.25},
            {"pos": "FW", "name": "루이스 디아스", "att_uv": 0.70, "def_uv": 0.30},
            {"pos": "FW", "name": "다윈 누녜스", "att_uv": 0.65, "def_uv": 0.25},
        ],
        "subs": [
            {"pos": "FW", "name": "디오구 조타", "att_uv": 0.65, "def_uv": 0.25},
            {"pos": "FW", "name": "코디 각포", "att_uv": 0.60, "def_uv": 0.30},
            {"pos": "MF", "name": "커티스 존스", "att_uv": 0.45, "def_uv": 0.40},
            {"pos": "DF", "name": "코스타스 치미카스", "att_uv": 0.35, "def_uv": 0.45},
            {"pos": "GK", "name": "퀴빈 켈러허", "att_uv": 0.10, "def_uv": 0.45},
        ]
    },
    "첼시": {
        "starters": [
            {"pos": "GK", "name": "로베르트 산체스", "att_uv": 0.20, "def_uv": 0.45},
            {"pos": "DF", "name": "말로 쥐스토", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "DF", "name": "웨슬리 포파나", "att_uv": 0.25, "def_uv": 0.55},
            {"pos": "DF", "name": "리바이 콜윌", "att_uv": 0.30, "def_uv": 0.55},
            {"pos": "DF", "name": "마르크 쿠쿠렐라", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "MF", "name": "모이세스 카이세도", "att_uv": 0.40, "def_uv": 0.60},
            {"pos": "MF", "name": "엔초 페르난데스", "att_uv": 0.55, "def_uv": 0.45},
            {"pos": "MF", "name": "콜 파머", "att_uv": 0.85, "def_uv": 0.30},
            {"pos": "FW", "name": "노니 마두에케", "att_uv": 0.65, "def_uv": 0.25},
            {"pos": "FW", "name": "페드로 네투", "att_uv": 0.65, "def_uv": 0.30},
            {"pos": "FW", "name": "니콜라 잭슨", "att_uv": 0.65, "def_uv": 0.25},
        ],
        "subs": [
            {"pos": "FW", "name": "크리스토퍼 은쿤쿠", "att_uv": 0.65, "def_uv": 0.25},
            {"pos": "MF", "name": "로메오 라비아", "att_uv": 0.35, "def_uv": 0.45},
            {"pos": "FW", "name": "제이든 산초", "att_uv": 0.55, "def_uv": 0.25},
            {"pos": "DF", "name": "악셀 디사시", "att_uv": 0.25, "def_uv": 0.45},
            {"pos": "GK", "name": "필립 요르겐센", "att_uv": 0.10, "def_uv": 0.40},
        ]
    },
    "토트넘 홋스퍼": {
        "starters": [
            {"pos": "GK", "name": "굴리엘모 비카리오", "att_uv": 0.20, "def_uv": 0.55},
            {"pos": "DF", "name": "페드로 포로", "att_uv": 0.55, "def_uv": 0.40},
            {"pos": "DF", "name": "크리스티안 로메로", "att_uv": 0.35, "def_uv": 0.60},
            {"pos": "DF", "name": "미키 판 더 펜", "att_uv": 0.35, "def_uv": 0.60},
            {"pos": "DF", "name": "데스티니 우도기", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "MF", "name": "이브 비수마", "att_uv": 0.35, "def_uv": 0.50},
            {"pos": "MF", "name": "파페 사르", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "MF", "name": "제임스 매디슨", "att_uv": 0.70, "def_uv": 0.30},
            {"pos": "FW", "name": "브레넌 존슨", "att_uv": 0.65, "def_uv": 0.25},
            {"pos": "FW", "name": "손흥민", "att_uv": 0.80, "def_uv": 0.30},
            {"pos": "FW", "name": "도미닉 솔랑케", "att_uv": 0.65, "def_uv": 0.25},
        ],
        "subs": [
            {"pos": "FW", "name": "데얀 쿨루셰프스키", "att_uv": 0.65, "def_uv": 0.35},
            {"pos": "FW", "name": "히샤를리송", "att_uv": 0.60, "def_uv": 0.25},
            {"pos": "MF", "name": "로드리고 벤탕쿠르", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "DF", "name": "라두 드라구신", "att_uv": 0.20, "def_uv": 0.50},
            {"pos": "GK", "name": "프레이저 포스터", "att_uv": 0.10, "def_uv": 0.35},
        ]
    },
    "뉴캐슬 유나이티드": {
        "starters": [
            {"pos": "GK", "name": "닉 포프", "att_uv": 0.15, "def_uv": 0.55},
            {"pos": "DF", "name": "키에런 트리피어", "att_uv": 0.55, "def_uv": 0.45},
            {"pos": "DF", "name": "파비안 셰어", "att_uv": 0.35, "def_uv": 0.55},
            {"pos": "DF", "name": "댄 번", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "DF", "name": "티노 리브라멘토", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "MF", "name": "브루노 기마랑이스", "att_uv": 0.55, "def_uv": 0.55},
            {"pos": "MF", "name": "산드로 토날리", "att_uv": 0.50, "def_uv": 0.50},
            {"pos": "MF", "name": "조엘린톤", "att_uv": 0.45, "def_uv": 0.50},
            {"pos": "FW", "name": "앤서니 고든", "att_uv": 0.70, "def_uv": 0.30},
            {"pos": "FW", "name": "제이콥 머피", "att_uv": 0.55, "def_uv": 0.30},
            {"pos": "FW", "name": "알렉산데르 이삭", "att_uv": 0.80, "def_uv": 0.20},
        ],
        "subs": [
            {"pos": "FW", "name": "하비 반스", "att_uv": 0.60, "def_uv": 0.25},
            {"pos": "MF", "name": "조 윌록", "att_uv": 0.45, "def_uv": 0.35},
            {"pos": "MF", "name": "숀롱스태프", "att_uv": 0.35, "def_uv": 0.40},
            {"pos": "DF", "name": "스벤 보트만", "att_uv": 0.25, "def_uv": 0.55},
            {"pos": "GK", "name": "마틴 두브라브카", "att_uv": 0.10, "def_uv": 0.40},
        ]
    },
    "아스톤 빌라": {
        "starters": [
            {"pos": "GK", "name": "에밀리아노 마르티네스", "att_uv": 0.20, "def_uv": 0.60},
            {"pos": "DF", "name": "매티 캐시", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "DF", "name": "에즈리 콘사", "att_uv": 0.30, "def_uv": 0.55},
            {"pos": "DF", "name": "파우 토레스", "att_uv": 0.35, "def_uv": 0.55},
            {"pos": "DF", "name": "루카 디뉴", "att_uv": 0.45, "def_uv": 0.40},
            {"pos": "MF", "name": "아마두 오나나", "att_uv": 0.40, "def_uv": 0.55},
            {"pos": "MF", "name": "유리 틸레만스", "att_uv": 0.55, "def_uv": 0.45},
            {"pos": "MF", "name": "존 맥긴", "att_uv": 0.50, "def_uv": 0.45},
            {"pos": "FW", "name": "레온 베일리", "att_uv": 0.70, "def_uv": 0.25},
            {"pos": "FW", "name": "모건 로저스", "att_uv": 0.60, "def_uv": 0.30},
            {"pos": "FW", "name": "올리 왓킨스", "att_uv": 0.80, "def_uv": 0.25},
        ],
        "subs": [
            {"pos": "FW", "name": "존 두란", "att_uv": 0.65, "def_uv": 0.20},
            {"pos": "MF", "name": "로스 바클리", "att_uv": 0.45, "def_uv": 0.35},
            {"pos": "MF", "name": "제이콥 램지", "att_uv": 0.50, "def_uv": 0.30},
            {"pos": "DF", "name": "디에고 카를로스", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "GK", "name": "조 로빈 오센", "att_uv": 0.10, "def_uv": 0.35},
        ]
    }
}

# -----------------------------------------------------------------------------
# 3. 11.0 WUV 예측 로직 계산 함수
# -----------------------------------------------------------------------------
def calculate_team_wuv(team_name):
    team = TEAMS_DATA[team_name]
    
    # 1) 선발 11인 합산 (Att, Def)
    starter_df = pd.DataFrame(team["starters"])
    starter_att = starter_df["att_uv"].sum()
    starter_def = starter_df["def_uv"].sum()
    starter_total = starter_att + starter_def
    
    # 2) 교체 5인 합산 및 피치 스케일링 (11/5)
    sub_df = pd.DataFrame(team["subs"])
    sub_att_raw = sub_df["att_uv"].sum()
    sub_def_raw = sub_df["def_uv"].sum()
    
    sub_att_scaled = sub_att_raw * (11.0 / 5.0)
    sub_def_scaled = sub_def_raw * (11.0 / 5.0)
    sub_total_scaled = sub_att_scaled + sub_def_scaled
    
    # 3) 가중치 적용 (선발 85% + 교체 15%)
    wuv_att = 0.85 * starter_att + 0.15 * sub_att_scaled
    wuv_def = 0.85 * starter_def + 0.15 * sub_def_scaled
    wuv_total = wuv_att + wuv_def
    
    return {
        "starter_att": starter_att,
        "starter_def": starter_def,
        "starter_total": starter_total,
        "sub_att_raw": sub_att_raw,
        "sub_def_raw": sub_def_raw,
        "sub_att_scaled": sub_att_scaled,
        "sub_def_scaled": sub_def_scaled,
        "sub_total_scaled": sub_total_scaled,
        "wuv_att": wuv_att,
        "wuv_def": wuv_def,
        "wuv_total": wuv_total,
        "starter_df": starter_df,
        "sub_df": sub_df
    }

def predict_match(home_team_name, away_team_name):
    home_wuv = calculate_team_wuv(home_team_name)
    away_wuv = calculate_team_wuv(away_team_name)
    
    # 홈 어드밴티지 적용 (+0.25 UV: 공격 +0.15, 수비 +0.10)
    HOME_ADVANTAGE_ATT = 0.15
    HOME_ADVANTAGE_DEF = 0.10
    HOME_ADVANTAGE_TOTAL = 0.25
    
    final_home_att = home_wuv["wuv_att"] + HOME_ADVANTAGE_ATT
    final_home_def = home_wuv["wuv_def"] + HOME_ADVANTAGE_DEF
    final_home_total = home_wuv["wuv_total"] + HOME_ADVANTAGE_TOTAL
    
    final_away_att = away_wuv["wuv_att"]
    final_away_def = away_wuv["wuv_def"]
    final_away_total = away_wuv["wuv_total"]
    
    uv_gap = final_home_total - final_away_total
    
    # 무승부 판정 룰 (|uv_gap| <= 0.4)
    DRAW_THRESHOLD = 0.4
    
    if abs(uv_gap) <= DRAW_THRESHOLD:
        prediction_result = "무승부 (Draw)"
        result_code = "DRAW"
    elif uv_gap > DRAW_THRESHOLD:
        prediction_result = f"{home_team_name} 승리"
        result_code = "HOME_WIN"
    else:
        prediction_result = f"{away_team_name} 승리"
        result_code = "AWAY_WIN"
        
    # 확률 모델 (Softmax Distribution)
    z = uv_gap
    logit_home = 1.55 * z
    logit_away = -1.55 * z
    logit_draw = 0.35 - 1.25 * abs(z)
    
    exp_h = np.exp(logit_home)
    exp_d = np.exp(logit_draw)
    exp_a = np.exp(logit_away)
    total_exp = exp_h + exp_d + exp_a
    
    prob_home = (exp_h / total_exp) * 100
    prob_draw = (exp_d / total_exp) * 100
    prob_away = (exp_a / total_exp) * 100
    
    # 예상 스코어 모델 (xG)
    BASE_GOALS = 1.35
    xg_home = BASE_GOALS * (final_home_att / 5.5) * (5.5 / final_away_def)
    xg_away = BASE_GOALS * (final_away_att / 5.5) * (5.5 / final_home_def)
    
    # 정수 스코어 변환
    score_home = int(round(xg_home))
    score_away = int(round(xg_away))
    
    # 무승부 판정 시 스코어가 같지 않다면 조정 (xG 차이가 적을 때)
    if result_code == "DRAW" and score_home != score_away:
        avg_score = int(round((xg_home + xg_away) / 2.0))
        score_home = avg_score
        score_away = avg_score

    return {
        "home_wuv": home_wuv,
        "away_wuv": away_wuv,
        "final_home_att": final_home_att,
        "final_home_def": final_home_def,
        "final_home_total": final_home_total,
        "final_away_att": final_away_att,
        "final_away_def": final_away_def,
        "final_away_total": final_away_total,
        "uv_gap": uv_gap,
        "prediction_result": prediction_result,
        "result_code": result_code,
        "prob_home": prob_home,
        "prob_draw": prob_draw,
        "prob_away": prob_away,
        "xg_home": xg_home,
        "xg_away": xg_away,
        "score_home": score_home,
        "score_away": score_away,
    }

# -----------------------------------------------------------------------------
# 4. 드롭다운 및 매치업 선택 UI
# -----------------------------------------------------------------------------
st.subheader("📌 경기 매치업 선택")

preset_matches = [
    "맨체스터 유나이티드 vs 아스널",
    "맨체스터 시티 vs 리버풀",
    "첼시 vs 토트넘",
    "아스톤 빌라 vs 뉴캐슬",
    "아스널 vs 맨체스터 시티",
    "리버풀 vs 맨체스터 유나이티드",
    "직접 선택 (Custom Matchup)"
]

selected_preset = st.selectbox("빅매치 추천 프리셋 선택", preset_matches, index=0)

all_teams = list(TEAMS_DATA.keys())

if selected_preset != "직접 선택 (Custom Matchup)":
    parts = selected_preset.split(" vs ")
    default_home = parts[0]
    default_away = parts[1]
else:
    default_home = "맨체스터 유나이티드"
    default_away = "아스널"

col_home_sel, col_away_sel = st.columns(2)
with col_home_sel:
    home_team = st.selectbox("🏠 홈 팀 (Home)", all_teams, index=all_teams.index(default_home))
with col_away_sel:
    away_options = [t for t in all_teams if t != home_team]
    away_index = away_options.index(default_away) if default_away in away_options else 0
    away_team = st.selectbox("✈️ 어웨이 팀 (Away)", away_options, index=away_index)

res = predict_match(home_team, away_team)

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. 최종 예측 결과 카드 & 승/무/패 확률
# -----------------------------------------------------------------------------
st.header(f"⚔️ {home_team} vs {away_team} 승부예측 리포트")

# 메인 예측 결과 배너 카드
card_bg = "#f0f2f6"
if res["result_code"] == "HOME_WIN":
    badge_color = "#2e7d32"
    badge_text = f"🏠 {home_team} 우세 승리 예상"
elif res["result_code"] == "AWAY_WIN":
    badge_color = "#1565c0"
    badge_text = f"✈️ {away_team} 우세 승리 예상"
else:
    badge_color = "#d84315"
    badge_text = "🤝 팽팽한 접전, 무승부(Draw) 예상"

m_col1, m_col2, m_col3 = st.columns([3.5, 3, 3.5])

with m_col1:
    st.markdown(f"### 🏠 {home_team}")
    st.metric("최종 11.0 WUV", f"{res['final_home_total']:.2f} UV", f"공격 {res['final_home_att']:.2f} | 수비 {res['final_home_def']:.2f}")
    st.caption("(홈 어드밴티지 +0.25 UV 포함)")

with m_col2:
    st.markdown(
        f"""
        <div style="background-color: {badge_color}; padding: 15px; border-radius: 10px; text-align: center; color: white;">
            <h3 style="margin: 0; color: white;">{badge_text}</h3>
            <p style="font-size: 22px; font-weight: bold; margin-top: 10px; margin-bottom: 5px;">
                예상 스코어: {res['score_home']} - {res['score_away']}
            </p>
            <p style="font-size: 13px; margin: 0; opacity: 0.9;">
                (xG 예상골: {res['xg_home']:.2f} vs {res['xg_away']:.2f})
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric("최종 UV 격차 (Home - Away)", f"{res['uv_gap']:+.2f} UV", "무승부 룰: |격차| ≤ 0.4")

with m_col3:
    st.markdown(f"### ✈️ {away_team}")
    st.metric("최종 11.0 WUV", f"{res['final_away_total']:.2f} UV", f"공격 {res['final_away_att']:.2f} | 수비 {res['final_away_def']:.2f}")
    st.caption("(어웨이 원정 조건 적용)")

# 승/무/패 확률 프로그레스 게이지
st.subheader("🎲 승 / 무 / 패 확률 분포")
p_col1, p_col2, p_col3 = st.columns(3)
with p_col1:
    st.metric(f"🏠 {home_team} 승리 확률", f"{res['prob_home']:.1f}%")
    st.progress(int(res['prob_home']))
with p_col2:
    st.metric("🤝 무승부(Draw) 확률", f"{res['prob_draw']:.1f}%")
    st.progress(int(res['prob_draw']))
with p_col3:
    st.metric(f"✈️ {away_team} 승리 확률", f"{res['prob_away']:.1f}%")
    st.progress(int(res['prob_away']))

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. 공수 밸런스 비교 차트 (Plotly)
# -----------------------------------------------------------------------------
st.header("📊 양 팀 공수 밸런스 & 피치 11.0 UV 기준선 비교")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("🎯 공수 블록별 UV 수치 비교 (기준선 5.5 UV)")
    
    categories = ["공격 블록 (Att)", "수비/빌드업 블록 (Def)", "전체 11.0 WUV"]
    
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=categories,
        y=[res['final_home_att'], res['final_home_def'], res['final_home_total']],
        name=f"🏠 {home_team}",
        marker_color='#2e7d32'
    ))
    fig_bar.add_trace(go.Bar(
        x=categories,
        y=[res['final_away_att'], res['final_away_def'], res['final_away_total']],
        name=f"✈️ {away_team}",
        marker_color='#1565c0'
    ))
    
    # 기준선 5.5 & 11.0 표시
    fig_bar.add_hline(y=5.5, line_dash="dash", line_color="orange", annotation_text="공/수 5.5 기준선")
    fig_bar.add_hline(y=11.0, line_dash="dot", line_color="red", annotation_text="피치 11.0 UV 기준선")
    
    fig_bar.update_layout(
        barmode='group',
        yaxis_title="Unit Value (UV)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20),
        height=380
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with chart_col2:
    st.subheader("🕸️ 공수 레이더 밸런스 프로필")
    
    radar_categories = ["공격 UV", "수비 UV", "선발 11인 UV", "교체 5인 UV(스케일)", "최종 WUV"]
    
    home_radar_vals = [
        res['final_home_att'],
        res['final_home_def'],
        res['home_wuv']['starter_total'],
        res['home_wuv']['sub_total_scaled'],
        res['final_home_total']
    ]
    
    away_radar_vals = [
        res['final_away_att'],
        res['final_away_def'],
        res['away_wuv']['starter_total'],
        res['away_wuv']['sub_total_scaled'],
        res['final_away_total']
    ]
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=home_radar_vals + [home_radar_vals[0]],
        theta=radar_categories + [radar_categories[0]],
        fill='toself',
        name=f"🏠 {home_team}",
        line_color='#2e7d32'
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=away_radar_vals + [away_radar_vals[0]],
        theta=radar_categories + [radar_categories[0]],
        fill='toself',
        name=f"✈️ {away_team}",
        line_color='#1565c0'
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max(max(home_radar_vals), max(away_radar_vals)) * 1.1])
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=30, b=20),
        height=380
    )
    st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. 선발 라인업 UV 비교표 및 가중치 세부 내역
# -----------------------------------------------------------------------------
st.header("📋 선발 라인업 & 교체 명단 UV 비교표")

tab_home, tab_away, tab_math = st.tabs([
    f"🏠 {home_team} 라인업 명단", 
    f"✈️ {away_team} 라인업 명단", 
    "📐 11.0 WUV 산출 로직 공식"
])

def render_team_tables(team_name, wuv_info):
    st.subheader(f"[{team_name}] 선발 11인 명단 (가중치 85% 반영)")
    df_st = wuv_info["starter_df"].copy()
    df_st["합계 UV"] = df_st["att_uv"] + df_st["def_uv"]
    df_st.columns = ["포지션", "선수명", "공격 UV", "수비/빌드업 UV", "개인 합계 UV"]
    st.dataframe(df_st, use_container_width=True)
    
    st.markdown(
        f"**선발 11인 합계**: 공격 `{wuv_info['starter_att']:.2f}` + 수비 `{wuv_info['starter_def']:.2f}` = **`{wuv_info['starter_total']:.2f} UV`**"
    )
    
    st.subheader(f"[{team_name}] 주요 교체 5인 명단 (가중치 15% 반영)")
    df_sub = wuv_info["sub_df"].copy()
    df_sub["합계 UV"] = df_sub["att_uv"] + df_sub["def_uv"]
    df_sub.columns = ["포지션", "선수명", "공격 UV", "수비/빌드업 UV", "개인 합계 UV"]
    st.dataframe(df_sub, use_container_width=True)
    
    st.markdown(
        f"**교체 5인 순수 합계**: `{wuv_info['sub_att_raw'] + wuv_info['sub_def_raw']:.2f} UV` | **11인 피치 스케일링 변환**: **`{wuv_info['sub_total_scaled']:.2f} UV`**"
    )

with tab_home:
    render_team_tables(home_team, res["home_wuv"])

with tab_away:
    render_team_tables(away_team, res["away_wuv"])

with tab_math:
    st.markdown(
        """
        ### 📐 11.0 WUV (Weighted Unit Value) 산출 로직
        
        1. **피치 11인 기준선 (11.0 UV)**:
           - 축구 베스트 11 피치 기준선은 총 **11.0 UV**로 설정 (공격 블록 5.5 UV + 수비/빌드업 블록 5.5 UV).
           
        2. **선발(85%) 및 교체(15%) 가중치 규칙**:
           - **$UV_{\\text{starter}}$**: 선발 11명의 공격 UV 및 수비 UV 각각 합산.
           - **$UV_{\\text{sub}}$**: 교체 5명의 UV 합산 후 피치 11인 스케일로 변환 ($$\\times \\frac{11}{5}$$).
           - **$UV_{\\text{raw}} = 0.85 \\times UV_{\\text{starter}} + 0.15 \\times UV_{\\text{sub}}$**
           
        3. **홈 어드밴티지 보정**:
           - 홈 팀에 **$+0.25\\text{ UV}$** 부여 (공격 $+0.15$, 수비 $+0.10$).
           
        4. **무승부(Draw) 판정 룰**:
           - 최종 UV 격차 $$\\Delta UV = UV_{\\text{home, final}} - UV_{\\text{away, final}}$$
           - **$$|\\Delta UV| \\le 0.4$$** 범위 내인 경우, 두 팀 간 전력 차이가 팽팽한 것으로 판단하여 **무승부(Draw)**로 최종 예측합니다.
        """
    )

st.markdown("---")
st.caption("EPL AI Win/Draw/Loss Prediction Dashboard | Powered by 11.0 WUV Predictor Engine")
