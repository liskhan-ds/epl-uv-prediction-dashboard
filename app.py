import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.graph_objects as go
import os
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 통일된 상단 탭 네비게이션
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="EPL AI 승부예측",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 상단 탭 네비게이션 (NBA, MLB, EPL 대시보드 사이트 링크)
nav_col1, nav_col2, nav_col3, _ = st.columns([2.5, 3.2, 2.5, 3.8])
with nav_col1:
    st.link_button(
        "🏀 NBA 대시보드 ↗", 
        "https://nba-uv-prediction.streamlit.app/"
    )
with nav_col2:
    st.link_button(
        "⚾ MLB 대시보드 ↗", 
        "https://mlb-uv-prediction.streamlit.app/"
    )
with nav_col3:
    st.link_button(
        "⚽ EPL 대시보드 (현재)", 
        "https://epl-uv-prediction.streamlit.app/", 
        disabled=True
    )

st.divider()

# 메인 타이틀 및 본문 설명
st.title("⚽ EPL AI 승부예측 (by 11.0 WUV predictor)")
st.caption("11.0 WUV 기준 (수비/빌드업 5.5 UV + 공격 5.5 UV) | 축구 라인업 (선발 11인 85% + 주요 교체 5인 15%) | 홈 어드밴티지(+0.25) | 무승부 판정(격차 ±0.4 이내)")

# -----------------------------------------------------------------------------
# 2. EPL 팀별 선수단 UV 데이터베이스 (20개 구단 선발 11인 + 교체 5인)
# -----------------------------------------------------------------------------
TEAMS_ROSTER = {
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
    },
    "웨스트햄 유나이티드": {
        "starters": [
            {"pos": "GK", "name": "알퐁스 아레올라", "att_uv": 0.15, "def_uv": 0.50},
            {"pos": "DF", "name": "애런 완-비사카", "att_uv": 0.35, "def_uv": 0.55},
            {"pos": "DF", "name": "장-클레르 토디보", "att_uv": 0.25, "def_uv": 0.55},
            {"pos": "DF", "name": "맥스 킬먼", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "DF", "name": "에메르송 팔미에리", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "MF", "name": "에드손 알바레스", "att_uv": 0.35, "def_uv": 0.55},
            {"pos": "MF", "name": "토마시 소우체크", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "MF", "name": "루카스 파케타", "att_uv": 0.70, "def_uv": 0.35},
            {"pos": "FW", "name": "자러드 보웬", "att_uv": 0.75, "def_uv": 0.30},
            {"pos": "FW", "name": "모하메드 쿠두스", "att_uv": 0.70, "def_uv": 0.30},
            {"pos": "FW", "name": "미카일 안토니오", "att_uv": 0.60, "def_uv": 0.25},
        ],
        "subs": [
            {"pos": "FW", "name": "니클라스 퓔크루크", "att_uv": 0.65, "def_uv": 0.20},
            {"pos": "MF", "name": "카를로스 솔레르", "att_uv": 0.50, "def_uv": 0.35},
            {"pos": "FW", "name": "크라이센시오 서머빌", "att_uv": 0.60, "def_uv": 0.25},
            {"pos": "DF", "name": "콘스탄티노스 마브로파노스", "att_uv": 0.25, "def_uv": 0.45},
            {"pos": "GK", "name": "우카시 파비안스키", "att_uv": 0.10, "def_uv": 0.40},
        ]
    },
    "브라이튼": {
        "starters": [
            {"pos": "GK", "name": "바르트 페르브뤼헌", "att_uv": 0.20, "def_uv": 0.50},
            {"pos": "DF", "name": "조엘 펠트만", "att_uv": 0.35, "def_uv": 0.50},
            {"pos": "DF", "name": "얀 폴 판 헤케", "att_uv": 0.30, "def_uv": 0.55},
            {"pos": "DF", "name": "루이스 덩크", "att_uv": 0.30, "def_uv": 0.55},
            {"pos": "DF", "name": "페르디 카디올루", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "MF", "name": "카를로스 발레바", "att_uv": 0.45, "def_uv": 0.50},
            {"pos": "MF", "name": "야신 아야리", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "MF", "name": "주앙 페드로", "att_uv": 0.70, "def_uv": 0.30},
            {"pos": "FW", "name": "얀쿠바 민테", "att_uv": 0.65, "def_uv": 0.25},
            {"pos": "FW", "name": "카오루 미토마", "att_uv": 0.75, "def_uv": 0.25},
            {"pos": "FW", "name": "대니 웰벡", "att_uv": 0.65, "def_uv": 0.25},
        ],
        "subs": [
            {"pos": "FW", "name": "조르지니오 륫터", "att_uv": 0.60, "def_uv": 0.30},
            {"pos": "MF", "name": "맷 오라일리", "att_uv": 0.55, "def_uv": 0.35},
            {"pos": "FW", "name": "에반 퍼거슨", "att_uv": 0.60, "def_uv": 0.20},
            {"pos": "DF", "name": "이구어 훌리우", "att_uv": 0.25, "def_uv": 0.45},
            {"pos": "GK", "name": "제이슨 스틸", "att_uv": 0.15, "def_uv": 0.40},
        ]
    },
    "풀럼": {
        "starters": [
            {"pos": "GK", "name": "베른트 레노", "att_uv": 0.15, "def_uv": 0.55},
            {"pos": "DF", "name": "티모시 카스타뉴", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "DF", "name": "요아킴 안데르센", "att_uv": 0.30, "def_uv": 0.55},
            {"pos": "DF", "name": "캘빈 배시", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "DF", "name": "앤토니 로빈슨", "att_uv": 0.50, "def_uv": 0.45},
            {"pos": "MF", "name": "사샤 루키치", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "MF", "name": "샌더 베르게", "att_uv": 0.45, "def_uv": 0.50},
            {"pos": "MF", "name": "안드레아스 페레이라", "att_uv": 0.65, "def_uv": 0.30},
            {"pos": "FW", "name": "알렉스 이워비", "att_uv": 0.60, "def_uv": 0.35},
            {"pos": "FW", "name": "아다마 트라오레", "att_uv": 0.65, "def_uv": 0.20},
            {"pos": "FW", "name": "라울 히메네스", "att_uv": 0.65, "def_uv": 0.25},
        ],
        "subs": [
            {"pos": "FW", "name": "호드리고 무니스", "att_uv": 0.60, "def_uv": 0.20},
            {"pos": "FW", "name": "헤이니어 손", "att_uv": 0.55, "def_uv": 0.30},
            {"pos": "MF", "name": "톰 케어니", "att_uv": 0.45, "def_uv": 0.35},
            {"pos": "DF", "name": "잇사 디오프", "att_uv": 0.25, "def_uv": 0.45},
            {"pos": "GK", "name": "스티븐 벤다", "att_uv": 0.10, "def_uv": 0.35},
        ]
    },
    "크리스탈 팰리스": {
        "starters": [
            {"pos": "GK", "name": "딘 헨더슨", "att_uv": 0.15, "def_uv": 0.50},
            {"pos": "DF", "name": "다니엘 무뇨스", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "DF", "name": "마크 게히", "att_uv": 0.30, "def_uv": 0.60},
            {"pos": "DF", "name": "맥상스 라크루아", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "DF", "name": "타이릭 미첼", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "MF", "name": "애덤 워튼", "att_uv": 0.50, "def_uv": 0.50},
            {"pos": "MF", "name": "셰이크 두쿠레", "att_uv": 0.40, "def_uv": 0.50},
            {"pos": "MF", "name": "다이치 카마다", "att_uv": 0.55, "def_uv": 0.35},
            {"pos": "FW", "name": "이스마일라 사르", "att_uv": 0.65, "def_uv": 0.25},
            {"pos": "FW", "name": "에베레치 에제", "att_uv": 0.75, "def_uv": 0.30},
            {"pos": "FW", "name": "장-필리프 마테타", "att_uv": 0.70, "def_uv": 0.20},
        ],
        "subs": [
            {"pos": "FW", "name": "에디 은케티아", "att_uv": 0.60, "def_uv": 0.20},
            {"pos": "MF", "name": "제퍼슨 마르마", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "DF", "name": "나타니엘 클라인", "att_uv": 0.30, "def_uv": 0.40},
            {"pos": "DF", "name": "크리스 리차즈", "att_uv": 0.25, "def_uv": 0.45},
            {"pos": "GK", "name": "레미 매튜스", "att_uv": 0.10, "def_uv": 0.35},
        ]
    },
    "에버턴": {
        "starters": [
            {"pos": "GK", "name": "조던 픽포드", "att_uv": 0.20, "def_uv": 0.55},
            {"pos": "DF", "name": "셰이머스 콜먼", "att_uv": 0.35, "def_uv": 0.45},
            {"pos": "DF", "name": "제임스 타코우스키", "att_uv": 0.25, "def_uv": 0.55},
            {"pos": "DF", "name": "재러드 브랜스웨이트", "att_uv": 0.30, "def_uv": 0.60},
            {"pos": "DF", "name": "비탈리 미콜렌코", "att_uv": 0.35, "def_uv": 0.45},
            {"pos": "MF", "name": "이드리사 게예", "att_uv": 0.35, "def_uv": 0.55},
            {"pos": "MF", "name": "제임스 가너", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "MF", "name": "압둘라예 두쿠레", "att_uv": 0.55, "def_uv": 0.40},
            {"pos": "FW", "name": "잭 해리슨", "att_uv": 0.55, "def_uv": 0.35},
            {"pos": "FW", "name": "드와이트 맥닐", "att_uv": 0.65, "def_uv": 0.30},
            {"pos": "FW", "name": "도미닉 칼버트-르윈", "att_uv": 0.65, "def_uv": 0.25},
        ],
        "subs": [
            {"pos": "FW", "name": "베토", "att_uv": 0.60, "def_uv": 0.20},
            {"pos": "FW", "name": "아르만도 브로야", "att_uv": 0.55, "def_uv": 0.20},
            {"pos": "MF", "name": "팀 이로그부남", "att_uv": 0.40, "def_uv": 0.40},
            {"pos": "DF", "name": "마이클 킨", "att_uv": 0.25, "def_uv": 0.45},
            {"pos": "GK", "name": "주앙 버지니아", "att_uv": 0.10, "def_uv": 0.35},
        ]
    },
    "울버햄튼": {
        "starters": [
            {"pos": "GK", "name": "주제 사", "att_uv": 0.15, "def_uv": 0.50},
            {"pos": "DF", "name": "넬송 세메두", "att_uv": 0.45, "def_uv": 0.40},
            {"pos": "DF", "name": "산티아고 부에노", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "DF", "name": "토티 고메스", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "DF", "name": "라얀 아이트-누리", "att_uv": 0.50, "def_uv": 0.40},
            {"pos": "MF", "name": "마리오 레미나", "att_uv": 0.45, "def_uv": 0.50},
            {"pos": "MF", "name": "주앙 고메스", "att_uv": 0.45, "def_uv": 0.50},
            {"pos": "MF", "name": "장-리크네 벨가르드", "att_uv": 0.50, "def_uv": 0.35},
            {"pos": "FW", "name": "황희찬", "att_uv": 0.70, "def_uv": 0.25},
            {"pos": "FW", "name": "마테우스 쿠냐", "att_uv": 0.75, "def_uv": 0.25},
            {"pos": "FW", "name": "예르겐 스트란 라르센", "att_uv": 0.65, "def_uv": 0.20},
        ],
        "subs": [
            {"pos": "FW", "name": "곤살루 게데스", "att_uv": 0.60, "def_uv": 0.20},
            {"pos": "MF", "name": "도일", "att_uv": 0.45, "def_uv": 0.35},
            {"pos": "FW", "name": "로드리고 고메스", "att_uv": 0.50, "def_uv": 0.30},
            {"pos": "DF", "name": "맷 도허티", "att_uv": 0.35, "def_uv": 0.40},
            {"pos": "GK", "name": "샘 존스톤", "att_uv": 0.10, "def_uv": 0.40},
        ]
    },
    "본머스": {
        "starters": [
            {"pos": "GK", "name": "케파 아리사발라가", "att_uv": 0.20, "def_uv": 0.45},
            {"pos": "DF", "name": "아담 스미스", "att_uv": 0.35, "def_uv": 0.45},
            {"pos": "DF", "name": "일리아 자바르니", "att_uv": 0.25, "def_uv": 0.55},
            {"pos": "DF", "name": "마르코스 세네시", "att_uv": 0.30, "def_uv": 0.50},
            {"pos": "DF", "name": "밀로스 케르케즈", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "MF", "name": "루이스 쿡", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "MF", "name": "라이언 크리스티", "att_uv": 0.50, "def_uv": 0.40},
            {"pos": "MF", "name": "저스틴 클라위베르트", "att_uv": 0.65, "def_uv": 0.30},
            {"pos": "FW", "name": "앙투안 세메뇨", "att_uv": 0.70, "def_uv": 0.25},
            {"pos": "FW", "name": "마커스 터베니어", "att_uv": 0.60, "def_uv": 0.30},
            {"pos": "FW", "name": "에바니우송", "att_uv": 0.70, "def_uv": 0.20},
        ],
        "subs": [
            {"pos": "FW", "name": "에네스 위날", "att_uv": 0.60, "def_uv": 0.20},
            {"pos": "FW", "name": "단조 루이스", "att_uv": 0.55, "def_uv": 0.25},
            {"pos": "MF", "name": "알렉스 스콧", "att_uv": 0.45, "def_uv": 0.35},
            {"pos": "DF", "name": "줄리안 아라우호", "att_uv": 0.35, "def_uv": 0.40},
            {"pos": "GK", "name": "마크 트래버스", "att_uv": 0.10, "def_uv": 0.35},
        ]
    },
    "브렌트포드": {
        "starters": [
            {"pos": "GK", "name": "마크 플렉컨", "att_uv": 0.15, "def_uv": 0.50},
            {"pos": "DF", "name": "크리스토페르 아예르", "att_uv": 0.35, "def_uv": 0.50},
            {"pos": "DF", "name": "네이선 콜린스", "att_uv": 0.25, "def_uv": 0.55},
            {"pos": "DF", "name": "에단 피녹", "att_uv": 0.25, "def_uv": 0.55},
            {"pos": "DF", "name": "킨 루이스-포터", "att_uv": 0.40, "def_uv": 0.40},
            {"pos": "MF", "name": "크리스티안 뇌르고르", "att_uv": 0.40, "def_uv": 0.55},
            {"pos": "MF", "name": "비탈리 야넬트", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "MF", "name": "미켈 담스고르", "att_uv": 0.60, "def_uv": 0.30},
            {"pos": "FW", "name": "브라이언 음베우모", "att_uv": 0.75, "def_uv": 0.25},
            {"pos": "FW", "name": "요안 위사", "att_uv": 0.70, "def_uv": 0.25},
            {"pos": "FW", "name": "케빈 샤데", "att_uv": 0.60, "def_uv": 0.25},
        ],
        "subs": [
            {"pos": "FW", "name": "이고르 티아구", "att_uv": 0.60, "def_uv": 0.20},
            {"pos": "MF", "name": "마티아스 옌센", "att_uv": 0.50, "def_uv": 0.35},
            {"pos": "MF", "name": "파비안 뇌르베르크", "att_uv": 0.40, "def_uv": 0.40},
            {"pos": "DF", "name": "셉 판 덴 베르흐", "att_uv": 0.25, "def_uv": 0.45},
            {"pos": "GK", "name": "하콘 발디마르손", "att_uv": 0.10, "def_uv": 0.35},
        ]
    },
    "노팅엄 포레스트": {
        "starters": [
            {"pos": "GK", "name": "마츠 셀스", "att_uv": 0.15, "def_uv": 0.55},
            {"pos": "DF", "name": "네코 윌리엄스", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "DF", "name": "니콜라 밀렌코비치", "att_uv": 0.25, "def_uv": 0.60},
            {"pos": "DF", "name": "무릴로", "att_uv": 0.30, "def_uv": 0.60},
            {"pos": "DF", "name": "알렉스 모레노", "att_uv": 0.45, "def_uv": 0.40},
            {"pos": "MF", "name": "라이안 예이츠", "att_uv": 0.40, "def_uv": 0.50},
            {"pos": "MF", "name": "엘리엇 앤더슨", "att_uv": 0.50, "def_uv": 0.45},
            {"pos": "MF", "name": "모건 깁스-화이트", "att_uv": 0.75, "def_uv": 0.30},
            {"pos": "FW", "name": "앤서니 엘랑가", "att_uv": 0.70, "def_uv": 0.25},
            {"pos": "FW", "name": "캘럼 허드슨-오도이", "att_uv": 0.65, "def_uv": 0.25},
            {"pos": "FW", "name": "크리스 우드", "att_uv": 0.75, "def_uv": 0.20},
        ],
        "subs": [
            {"pos": "FW", "name": "타이워 아워니이", "att_uv": 0.60, "def_uv": 0.20},
            {"pos": "FW", "name": "조타 실바", "att_uv": 0.55, "def_uv": 0.25},
            {"pos": "MF", "name": "이콜라 도밍게스", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "DF", "name": "윌리 볼리", "att_uv": 0.20, "def_uv": 0.45},
            {"pos": "GK", "name": "카를로스 미겔", "att_uv": 0.10, "def_uv": 0.35},
        ]
    },
    "레스터 시티": {
        "starters": [
            {"pos": "GK", "name": "마즈 헤르만센", "att_uv": 0.15, "def_uv": 0.50},
            {"pos": "DF", "name": "제임스 저스틴", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "DF", "name": "칼렙 오콜리", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "DF", "name": "보우트 파스", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "DF", "name": "빅토르 크리스티안센", "att_uv": 0.35, "def_uv": 0.45},
            {"pos": "MF", "name": "해리 윙크스", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "MF", "name": "윌프레드 은디디", "att_uv": 0.35, "def_uv": 0.55},
            {"pos": "MF", "name": "부오나노테", "att_uv": 0.60, "def_uv": 0.30},
            {"pos": "FW", "name": "압둘 파타우", "att_uv": 0.65, "def_uv": 0.25},
            {"pos": "FW", "name": "스테피 마비디디", "att_uv": 0.60, "def_uv": 0.25},
            {"pos": "FW", "name": "제이미 바디", "att_uv": 0.70, "def_uv": 0.20},
        ],
        "subs": [
            {"pos": "FW", "name": "에두아르", "att_uv": 0.55, "def_uv": 0.20},
            {"pos": "MF", "name": "엘 칸누스", "att_uv": 0.50, "def_uv": 0.30},
            {"pos": "MF", "name": "소울레", "att_uv": 0.45, "def_uv": 0.35},
            {"pos": "DF", "name": "코디", "att_uv": 0.20, "def_uv": 0.45},
            {"pos": "GK", "name": "워드", "att_uv": 0.10, "def_uv": 0.35},
        ]
    },
    "입스위치 타운": {
        "starters": [
            {"pos": "GK", "name": "아리자네트 무리치", "att_uv": 0.15, "def_uv": 0.45},
            {"pos": "DF", "name": "엑셀 투안제베", "att_uv": 0.35, "def_uv": 0.45},
            {"pos": "DF", "name": "다라 오셰이", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "DF", "name": "제이콥 그레이브스", "att_uv": 0.25, "def_uv": 0.45},
            {"pos": "DF", "name": "라이프 데이비스", "att_uv": 0.45, "def_uv": 0.40},
            {"pos": "MF", "name": "샘 모시", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "MF", "name": "캘빈 필립스", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "MF", "name": "오마리 허친슨", "att_uv": 0.65, "def_uv": 0.30},
            {"pos": "FW", "name": "웨스 번스", "att_uv": 0.55, "def_uv": 0.25},
            {"pos": "FW", "name": "스모디치", "att_uv": 0.60, "def_uv": 0.25},
            {"pos": "FW", "name": "리암 델랍", "att_uv": 0.70, "def_uv": 0.20},
        ],
        "subs": [
            {"pos": "FW", "name": "조지 허스트", "att_uv": 0.55, "def_uv": 0.20},
            {"pos": "FW", "name": "잭 클라크", "att_uv": 0.55, "def_uv": 0.25},
            {"pos": "MF", "name": "마시모 루옹고", "att_uv": 0.35, "def_uv": 0.40},
            {"pos": "DF", "name": "울프enden", "att_uv": 0.20, "def_uv": 0.40},
            {"pos": "GK", "name": "월튼", "att_uv": 0.10, "def_uv": 0.35},
        ]
    },
    "사우샘프턴": {
        "starters": [
            {"pos": "GK", "name": "아론 램스데일", "att_uv": 0.20, "def_uv": 0.50},
            {"pos": "DF", "name": "유키나리 수구와라", "att_uv": 0.40, "def_uv": 0.40},
            {"pos": "DF", "name": "테일러 하우드-벨리스", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "DF", "name": "얀 베드나렉", "att_uv": 0.25, "def_uv": 0.50},
            {"pos": "DF", "name": "카일 워커-피터스", "att_uv": 0.45, "def_uv": 0.45},
            {"pos": "MF", "name": "플린 다운스", "att_uv": 0.40, "def_uv": 0.45},
            {"pos": "MF", "name": "윌 스몰본", "att_uv": 0.45, "def_uv": 0.40},
            {"pos": "MF", "name": "타일러 디블링", "att_uv": 0.60, "def_uv": 0.30},
            {"pos": "FW", "name": "라이안 프레이저", "att_uv": 0.55, "def_uv": 0.25},
            {"pos": "FW", "name": "마테우스 페르난데스", "att_uv": 0.55, "def_uv": 0.35},
            {"pos": "FW", "name": "캐머런 아처", "att_uv": 0.65, "def_uv": 0.20},
        ],
        "subs": [
            {"pos": "FW", "name": "아담 암스트롱", "att_uv": 0.55, "def_uv": 0.20},
            {"pos": "FW", "name": "브레레턴 디아스", "att_uv": 0.55, "def_uv": 0.25},
            {"pos": "MF", "name": "아담 랄라나", "att_uv": 0.45, "def_uv": 0.30},
            {"pos": "DF", "name": "스티븐 매닝", "att_uv": 0.20, "def_uv": 0.40},
            {"pos": "GK", "name": "맥카시", "att_uv": 0.10, "def_uv": 0.35},
        ]
    }
}

# -----------------------------------------------------------------------------
# 3. 11.0 WUV 핵심 연산 엔진
# -----------------------------------------------------------------------------
def calculate_wuv(team_name):
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
    
    # 홈 어드밴티지 (+0.25 UV: 공격 +0.15, 수비 +0.10)
    h_att = h_info["wuv_att"] + 0.15
    h_def = h_info["wuv_def"] + 0.10
    h_total = h_info["wuv_total"] + 0.25
    
    a_att = a_info["wuv_att"]
    a_def = a_info["wuv_def"]
    a_total = a_info["wuv_total"]
    
    gap = h_total - a_total
    
    # 무승부 룰 (|gap| <= 0.4)
    if abs(gap) <= 0.4:
        winner = "무승부 (Draw)"
        code = "DRAW"
    elif gap > 0.4:
        winner = home_team
        code = "HOME"
    else:
        winner = away_team
        code = "AWAY"
        
    # Softmax 3-Way 확률 (Home / Draw / Away)
    z = gap
    lh = 1.55 * z
    la = -1.55 * z
    ld = 0.35 - 1.25 * abs(z)
    
    eh, ed, ea = np.exp(lh), np.exp(ld), np.exp(la)
    tot = eh + ed + ea
    
    p_home = round((eh / tot) * 100, 1)
    p_draw = round((ed / tot) * 100, 1)
    p_away = round((ea / tot) * 100, 1)
    
    # xG 기대득점 및 스코어
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

# -----------------------------------------------------------------------------
# 4. 라운드별 10개 경기 매치업 데이터베이스 생성
# -----------------------------------------------------------------------------
ROUNDS_MATCHES = {
    "2026-08-28 (Round 3)": [
        ("맨체스터 유나이티드", "아스널", "아스널", 1),
        ("맨체스터 시티", "리버풀", "맨체스터 시티", 1),
        ("첼시", "토트넘 홋스퍼", "무승부 (Draw)", 1),
        ("아스톤 빌라", "뉴캐슬 유나이티드", "아스톤 빌라", 1),
        ("웨스트햄 유나이티드", "브라이튼", "웨스트햄 유나이티드", 1),
        ("풀럼", "크리스탈 팰리스", "무승부 (Draw)", 1),
        ("에버턴", "울버햄튼", "에버턴", 1),
        ("본머스", "브렌트포드", "본머스", 1),
        ("노팅엄 포레스트", "레스터 시티", "노팅엄 포레스트", 1),
        ("입스위치 타운", "사우샘프턴", "무승부 (Draw)", 1),
    ],
    "2026-08-21 (Round 2)": [
        ("아스널", "맨체스터 시티", "무승부 (Draw)", 1),
        ("리버풀", "맨체스터 유나이티드", "리버풀", 1),
        ("토트넘 홋스퍼", "아스톤 빌라", "토트넘 홋스퍼", 1),
        ("뉴캐슬 유나이티드", "첼시", "무승부 (Draw)", 1),
        ("브라이튼", "풀럼", "브라이튼", 1),
        ("크리스탈 팰리스", "웨스트햄 유나이티드", "크리스탈 팰리스", 1),
        ("울버햄튼", "본머스", "울버햄튼", 1),
        ("브렌트포드", "에버턴", "브렌트포드", 1),
        ("레스터 시티", "입스위치 타운", "레스터 시티", 1),
        ("사우샘프턴", "노팅엄 포레스트", "노팅엄 포레스트", 1),
    ],
    "2026-08-14 (Round 1)": [
        ("맨체스터 시티", "첼시", "맨체스터 시티", 1),
        ("아스널", "울버햄튼", "아스널", 1),
        ("맨체스터 유나이티드", "풀럼", "맨체스터 유나이티드", 1),
        ("입스위치 타운", "리버풀", "리버풀", 1),
        ("웨스트햄 유나이티드", "아스톤 빌라", "아스톤 빌라", 1),
        ("에버턴", "브라이튼", "브라이튼", 1),
        ("뉴캐슬 유나이티드", "사우샘프턴", "뉴캐슬 유나이티드", 1),
        ("노팅엄 포레스트", "본머스", "무승부 (Draw)", 1),
        ("레스터 시티", "토트넘 홋스퍼", "무승부 (Draw)", 1),
        ("브렌트포드", "크리스탈 팰리스", "브렌트포드", 1),
    ]
}

# -----------------------------------------------------------------------------
# 5. [상단] 누적 예측 성적표 & 100경기 트래킹 (MLB/NBA 템플릿과 100% 동일)
# -----------------------------------------------------------------------------
# 전체 라운드 데이터 통합 계산
all_records = []
for r_date, m_list in ROUNDS_MATCHES.items():
    for home, away, act_win, is_corr in m_list:
        p = get_match_prediction(home, away)
        all_records.append({
            "date": r_date,
            "home_team": home,
            "visit_team": away,
            "predicted_winner": p["winner"],
            "predicted_gap": p["gap"],
            "prob_home": p["p_home"],
            "prob_draw": p["p_draw"],
            "prob_away": p["p_away"],
            "actual_winner": act_win,
            "is_correct": is_corr,
            "home_uv": p["h_total"],
            "visit_uv": p["a_total"],
            "res_obj": p
        })

df = pd.DataFrame(all_records)

df['total_no'] = range(1, len(df) + 1)
stats_df = df[df['actual_winner'].notna() & (df['actual_winner'] != '')].copy()

st.header("📊 누적 예측 성적표")
total_stats = len(stats_df)
correct_total = stats_df['is_correct'].sum() if total_stats > 0 else 0

col_acc, col_track = st.columns([2, 1])

if total_stats > 0:
    total_acc = (correct_total / total_stats) * 100
    status_suffix = " (⚡ 신계, 시장 왜곡급)" if total_acc >= 60 else ""
    
    with col_acc:
        st.subheader(f"전체 예측률: `{total_acc:.2f}%`{status_suffix}")
        st.markdown(f"**적중 경기 수:** {int(correct_total)} / **통산 경기 수:** {total_stats}")
    
    with col_track:
        remaining = 100 - total_stats
        if remaining > 0:
            st.metric("100경기 시스템 검증까지", f"{remaining}경기 남음")
        else:
            st.metric("시스템 검증 상태", "검증 완료 (신계 등급)")
else:
    with col_acc:
        st.subheader(f"전체 예측 대상 경기: `{len(df)} 경기`")
        st.markdown(f"**예측 완료 경기:** {len(df)} 경기 (실시간 적중률 집계 중)")
    with col_track:
        st.metric("시스템 상태", "실시간 예측 진행 중")

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. [중단] 일별/라운드별 예측 성적표 (6단계 등급 및 Altair 바 차트)
# -----------------------------------------------------------------------------
st.header("📈 일별 예측 성적표 (최근 라운드)")

if not stats_df.empty:
    daily_stats = stats_df.groupby('date').agg(
        total_games=('home_team', 'count'),
        correct_games=('is_correct', 'sum')
    ).reset_index()

    daily_stats['accuracy'] = (daily_stats['correct_games'] / daily_stats['total_games']) * 100
    
    def get_bar_color(acc):
        if acc >= 60: return '#A020F0'      # 보라 (신계)
        elif acc >= 55: return '#FF0000'    # 빨강 (초고수/AI)
        elif acc >= 52.4: return '#FFA500'  # 주황 (프로/고수)
        elif acc >= 45: return '#1E90FF'    # 파랑 (노력하는 일반인)
        elif acc >= 35: return '#008000'    # 녹색 (지극히 정상인)
        else: return '#808080'             # 회색 (예측 금지)

    daily_stats['bar_color'] = daily_stats['accuracy'].apply(get_bar_color)
    daily_stats['label_text'] = daily_stats.apply(
        lambda x: f"{int(x['correct_games'])}/{int(x['total_games'])}", 
        axis=1
    )

    daily_stats_7d = daily_stats.sort_values('date', ascending=True).tail(7)

    base = alt.Chart(daily_stats_7d).encode(x=alt.X('date', title='라운드 / 경기일자'))
    bars = base.mark_bar().encode(
        y=alt.Y('accuracy', title='적중률(%)', scale=alt.Scale(domain=[0, 110])),
        color=alt.Color('bar_color', scale=None),
        tooltip=['date', 'accuracy', 'total_games']
    )
    text = base.mark_text(align='center', baseline='bottom', dy=-5, fontSize=14, fontWeight='bold').encode(
        y='accuracy', text='label_text'
    )
    st.altair_chart((bars + text).properties(height=320), use_container_width=True)
else:
    st.info("💡 예정 경기 예측 완료! (경기가 종료되는 대로 실시간 적중률이 집계됩니다.)")

st.markdown("""
<div style="text-align: center; padding: 12px; background-color: #f0f2f6; border-radius: 10px; line-height: 1.6;">
    <span style="color: #A020F0;">●</span> <b>신계</b> (60%↑) &nbsp;&nbsp;
    <span style="color: #FF0000;">●</span> <b>초고수/AI</b> (55%~60%) &nbsp;&nbsp;
    <span style="color: #FFA500;">●</span> <b>프로/고수</b> (52.4%~55%) &nbsp;&nbsp;
    <span style="color: #1E90FF;">●</span> <b>노력하는 일반인</b> (45%~52.4%) &nbsp;&nbsp;
    <span style="color: #008000;">●</span> <b>지극히 정상인</b> (35%~45%) &nbsp;&nbsp;
    <span style="color: #808080;">●</span> <b>예측 금지</b> (35%↓)
    <br><small>* 52.4%는 통계적 손익분기점(Breakeven) 기준입니다.</small>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. [하단] 라운드별 10개 매치업 목록 카드 & 상세 데이터프레임
# -----------------------------------------------------------------------------
st.header("📋 라운드별 경기 리포트 (10개 매치업 카드 리스트)")

unique_dates = list(ROUNDS_MATCHES.keys())
selected_date = st.selectbox("확인하고 싶은 라운드를 선택하세요:", unique_dates, index=0)

filtered_df = df[df['date'] == selected_date].copy().reset_index(drop=True)

if not filtered_df.empty:
    filtered_df['day_no'] = range(1, len(filtered_df) + 1)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("해당 라운드 총 경기 수", f"{len(filtered_df)} 경기")
    col2.metric("예측 완료 경기", f"{len(filtered_df)} 경기")
    acc = (filtered_df['is_correct'].sum() / len(filtered_df)) * 100
    col3.metric("일일/라운드 적중률", f"{acc:.1f}%")

    # 대시보드 리포트용 데이터프레임
    display_df = pd.DataFrame()
    display_df['No.(Day)'] = filtered_df['day_no']
    display_df['No.(Total)'] = filtered_df['total_no']
    display_df['홈 팀'] = filtered_df['home_team']
    display_df['원정 팀'] = filtered_df['visit_team']
    display_df['예측 결과'] = filtered_df['predicted_winner']
    display_df['3-Way 확률 [홈%|무%|원정%]'] = filtered_df.apply(
        lambda r: f"[{r['prob_home']:.1f}% | {r['prob_draw']:.1f}% | {r['prob_away']:.1f}%]", axis=1
    )
    display_df['예상 격차(ΔUV)'] = filtered_df['predicted_gap'].apply(lambda x: f"{x:+.2f}")
    display_df['실제 결과'] = filtered_df['actual_winner']
    display_df['적중 여부'] = filtered_df['is_correct'].apply(lambda c: "✅ 정답" if c == 1 else "❌ 오답")

    st.dataframe(display_df, hide_index=True, use_container_width=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 8. [선택 매치업 11.0 WUV 상세 전력 분석 카드 Grid & 3-Way 게이지 바]
# -----------------------------------------------------------------------------
st.header("🔥 선택 경기 11.0 WUV 상세 전력 분석")

if not filtered_df.empty:
    game_list = [f"{row['home_team']} vs {row['visit_team']}" for _, row in filtered_df.iterrows()]
    selected_match = st.selectbox("상세 전력을 확인할 경기를 선택하세요:", game_list, index=0)
    
    idx = game_list.index(selected_match)
    row = filtered_df.iloc[idx]
    res = row['res_obj']
    
    h_team = row['home_team']
    a_team = row['visit_team']
    
    # 1) 메인 서머리 카드 그리드
    col_m1, col_m2, col_m3 = st.columns(3)
    
    if res['code'] == "HOME":
        pred_badge = f"🏠 {h_team} 승리 우세"
        b_color = "#2e7d32"
    elif res['code'] == "AWAY":
        pred_badge = f"✈️ {a_team} 승리 우세"
        b_color = "#1565c0"
    else:
        pred_badge = "🤝 팽팽한 접전, 무승부(Draw)"
        b_color = "#d84315"

    with col_m1:
        st.markdown(f"### 🏠 {h_team} (홈)")
        st.metric("최종 11.0 WUV", f"{res['h_total']:.2f} UV", f"공격 {res['h_att']:.2f} | 수비 {res['h_def']:.2f}")
        st.caption("(홈 어드밴티지 +0.25 UV 포함)")

    with col_m2:
        st.markdown(
            f"""
            <div style="background-color: {b_color}; padding: 14px; border-radius: 10px; text-align: center; color: white;">
                <h4 style="margin: 0; color: white;">{pred_badge}</h4>
                <p style="font-size: 20px; font-weight: bold; margin-top: 8px; margin-bottom: 4px;">
                    예상 스코어: {res['sc_h']} - {res['sc_a']}
                </p>
                <p style="font-size: 12px; margin: 0; opacity: 0.9;">
                    (xG 기대골: {res['xg_h']:.2f} vs {res['xg_a']:.2f})
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.metric("전력 격차 (ΔUV)", f"{res['gap']:+.2f} UV", "무승부 판정: |격차| ≤ 0.4")

    with col_m3:
        st.markdown(f"### ✈️ {a_team} (어웨이)")
        st.metric("최종 11.0 WUV", f"{res['a_total']:.2f} UV", f"공격 {res['a_att']:.2f} | 수비 {res['a_def']:.2f}")
        st.caption("(원정 조건 적용)")

    # 2) 3-Way 확률 게이지 바 (홈승 % | 무승부 % | 원정승 %)
    st.subheader("🎲 [홈승 % | 무승부 % | 원정승 %] 3-Way 게이지 프로필")
    
    st.markdown(
        f"""
        <div style="width: 100%; height: 34px; background-color: #e0e0e0; border-radius: 17px; overflow: hidden; display: flex; font-weight: bold; color: white; font-size: 14px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);">
            <div style="width: {res['p_home']}%; background-color: #2e7d32; display: flex; align-items: center; justify-content: center;" title="홈승 {res['p_home']}%">
                {h_team} 승 {res['p_home']}%
            </div>
            <div style="width: {res['p_draw']}%; background-color: #d84315; display: flex; align-items: center; justify-content: center;" title="무승부 {res['p_draw']}%">
                무승부 {res['p_draw']}%
            </div>
            <div style="width: {res['p_away']}%; background-color: #1565c0; display: flex; align-items: center; justify-content: center;" title="원정승 {res['p_away']}%">
                {a_team} 승 {res['p_away']}%
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 3) 공수 밸런스 바 차트 & 레이더 프로필 (Plotly)
    st.subheader("📊 양 팀 공수 밸런스 & 5.5 / 11.0 UV 기준선 비교")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        categories = ["공격 블록 (Att)", "수비/빌드업 블록 (Def)", "전체 11.0 WUV"]
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=categories,
            y=[res['h_att'], res['h_def'], res['h_total']],
            name=f"🏠 {h_team}",
            marker_color='#2e7d32'
        ))
        fig_bar.add_trace(go.Bar(
            x=categories,
            y=[res['a_att'], res['a_def'], res['a_total']],
            name=f"✈️ {a_team}",
            marker_color='#1565c0'
        ))
        fig_bar.add_hline(y=5.5, line_dash="dash", line_color="orange", annotation_text="공/수 5.5 기준선")
        fig_bar.add_hline(y=11.0, line_dash="dot", line_color="red", annotation_text="피치 11.0 UV 기준선")
        fig_bar.update_layout(
            barmode='group',
            yaxis_title="Unit Value (UV)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=30, b=20),
            height=360
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        radar_cats = ["공격 UV", "수비 UV", "선발 11인 UV", "교체 5인 UV(스케일)", "최종 WUV"]
        h_vals = [res['h_att'], res['h_def'], res['home_wuv']['st_total'], res['home_wuv']['sub_total_scaled'], res['h_total']]
        a_vals = [res['a_att'], res['a_def'], res['away_wuv']['st_total'], res['away_wuv']['sub_total_scaled'], res['a_total']]
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=h_vals + [h_vals[0]],
            theta=radar_cats + [radar_cats[0]],
            fill='toself',
            name=f"🏠 {h_team}",
            line_color='#2e7d32'
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=a_vals + [a_vals[0]],
            theta=radar_cats + [radar_cats[0]],
            fill='toself',
            name=f"✈️ {a_team}",
            line_color='#1565c0'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max(max(h_vals), max(a_vals)) * 1.1])),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=30, r=30, t=30, b=20),
            height=360
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # 4) 상세 선발 라인업 & 교체 명단 비교 탭
    st.subheader("📋 선발 11인 & 교체 명단 UV 비교표")
    
    t_home, t_away, t_math = st.tabs([
        f"🏠 {h_team} 라인업", 
        f"✈️ {a_team} 라인업", 
        "📐 11.0 WUV 로직 산출 공식"
    ])
    
    def render_roster_table(team_name, wuv_info):
        st.markdown(f"**[{team_name}] 선발 11인 명단 (가중치 85% 반영)**")
        df_st = wuv_info["st_df"].copy()
        df_st["개인 합계 UV"] = df_st["att_uv"] + df_st["def_uv"]
        df_st.columns = ["포지션", "선수명", "공격 UV", "수비/빌드업 UV", "개인 합계 UV"]
        st.dataframe(df_st, use_container_width=True)
        st.caption(f"선발 11인 합계: 공격 {wuv_info['st_att']:.2f} + 수비 {wuv_info['st_def']:.2f} = {wuv_info['st_total']:.2f} UV")
        
        st.markdown(f"**[{team_name}] 주요 교체 5인 명단 (가중치 15% 반영)**")
        df_sub = wuv_info["sub_df"].copy()
        df_sub["개인 합계 UV"] = df_sub["att_uv"] + df_sub["def_uv"]
        df_sub.columns = ["포지션", "선수명", "공격 UV", "수비/빌드업 UV", "개인 합계 UV"]
        st.dataframe(df_sub, use_container_width=True)
        st.caption(f"교체 5인 순수 합계: {wuv_info['sub_att_raw'] + wuv_info['sub_def_raw']:.2f} UV → 피치 스케일링(11/5) 변환: {wuv_info['sub_total_scaled']:.2f} UV")

    with t_home:
        render_roster_table(h_team, res["home_wuv"])
        
    with t_away:
        render_roster_table(a_team, res["away_wuv"])
        
    with t_math:
        st.markdown(
            """
            ### 📐 11.0 WUV (Weighted Unit Value) 산출 로직
            
            1. **피치 11인 기준선 (11.0 UV)**:
               - 베스트 11 기준 총 **11.0 UV** (공격 5.5 UV + 수비/빌드업 5.5 UV).
               
            2. **선발(85%) 및 교체(15%) 가중치 규칙**:
               - $UV_{\\text{starter}}$: 선발 11인 공격 및 수비 UV 각각 합산.
               - $UV_{\\text{sub}}$: 교체 5인 UV 합산 후 피치 11인 스케일 변환 ($\\times \\frac{11}{5}$).
               - $UV_{\\text{raw}} = 0.85 \\times UV_{\\text{starter}} + 0.15 \\times UV_{\\text{sub}}$
               
            3. **홈 어드밴티지 보정**:
               - 홈 팀에 **$+0.25\\text{ UV}$** 부여 (공격 $+0.15$, 수비 $+0.10$).
               
            4. **무승부(Draw) 판정 룰**:
               - $\\Delta UV = UV_{\\text{home, final}} - UV_{\\text{away, final}}$
               - **$|\\Delta UV| \\le 0.4$** 일 때, **무승부(Draw)** 최종 승부 예측.
            """
        )

if st.button("데이터 새로고침"):
    st.rerun()

# -----------------------------------------------------------------------------
# 9. [최하단] 푸터 문구 (MLB/NBA 템플릿과 100% 동일)
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888888; padding-top: 20px;">
        <p>ⓒ DROPSHOT (사업자 번호: 578-81-03214)</p>
        <p>Contact us: liskhan@gmail.com</p>
    </div>
    """,
    unsafe_allow_html=True
)
