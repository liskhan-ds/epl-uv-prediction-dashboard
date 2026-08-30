import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.graph_objects as go
import sqlite3
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

# 상단 탭 네비게이션 (NBA, MLB, EPL, NHL 4대 종목 균등 와이드 배치)
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([2.5, 2.5, 2.5, 2.5])
with nav_col1:
    st.link_button(
        "🏀 NBA 대시보드 ↗", 
        "https://nba-uv-prediction-dashboard.streamlit.app/",
        use_container_width=True
    )
with nav_col2:
    st.link_button(
        "⚾ MLB 대시보드 ↗", 
        "https://mlb-uv-prediction-dashboard.streamlit.app/",
        use_container_width=True
    )
with nav_col3:
    st.button(
        "⚽ EPL 대시보드 (현재)", 
        disabled=True,
        use_container_width=True
    )
with nav_col4:
    st.link_button(
        "🏒 NHL 대시보드 ↗", 
        "https://nhl-uv-prediction-dashboard.streamlit.app/",
        use_container_width=True
    )

st.divider()

# 메인 타이틀 및 본문 설명
st.title("⚽ EPL AI 승부예측")

# -----------------------------------------------------------------------------
# 2. EPL 팀별 선수단 UV 데이터베이스 (20개 구단 선발 11인 + 교체 5인)
# -----------------------------------------------------------------------------
TEAMS_ROSTER = {
    "본머스": {
        "starters": [
            {
                "pos": "GK",
                "name": "Fraser Forster",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Adam Smith",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Max Aarons",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "James Hill",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Julián Araujo",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "David Brooks",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Ryan Christie",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Tyler Adams",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "Evanilson",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Justin Kluivert",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Amine Adli",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Michele Di Gregorio",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Bafodé Diakité",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Adrien Truffert",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Lewis Cook",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Marcus Tavernier",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    },
    "아스널": {
        "starters": [
            {
                "pos": "GK",
                "name": "케파 아리사발라가",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Ezri Konsa",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "가브리엘 마갈량이스",
                "att_uv": 0.45,
                "def_uv": 0.65
            },
            {
                "pos": "DF",
                "name": "벤 화이트",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "윌리엄 살리바",
                "att_uv": 0.45,
                "def_uv": 0.7
            },
            {
                "pos": "MF",
                "name": "Fabio Vieira",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "마르틴 외데고르",
                "att_uv": 0.8,
                "def_uv": 0.35
            },
            {
                "pos": "MF",
                "name": "미켈 메리노",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "가브리엘 제수스",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "카이 하베르츠",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "빅토르 예케레스",
                "att_uv": 0.85,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "다비드 라야",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "율리엔 팀버",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Piero Hincapié",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "브루노 기마랑이스",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "데클런 라이스",
                "att_uv": 0.55,
                "def_uv": 0.6
            }
        ]
    },
    "아스톤 빌라": {
        "starters": [
            {
                "pos": "GK",
                "name": "Marco Bizot",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Tyrone Mings",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Victor Lindelöf",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Matty Cash",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Aaron Wan-Bissaka",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Ross Barkley",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "John McGinn",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Leon Goretzka",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "Ollie Watkins",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Leon Bailey",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Tammy Abraham",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Emiliano Martínez",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Pau Torres",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Ian Maatsen",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Emiliano Buendía",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Boubacar Kamara",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    },
    "브렌트포드": {
        "starters": [
            {
                "pos": "GK",
                "name": "Ellery Balcombe",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Kristoffer Ajer",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Rico Henry",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Sepp van den Berg",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Nathan Collins",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Vitaly Janelt",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Mathias Jensen",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Mamadou Sangare",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "Callum Wilson",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Keane Lewis-Potter",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Igor Thiago",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Caoimhín Kelleher",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Aaron Hickey",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Jayden Meghoma",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Fábio Carvalho",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Josh Dasilva",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    },
    "브라이튼": {
        "starters": [
            {
                "pos": "GK",
                "name": "Jason Steele",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Lewis Dunk",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Olivier Boscagli",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Igor Julio",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Ferdi Kadioglu",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Pascal Gross",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Diego Gómez",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Matt O'Riley",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "Georginio Rutter",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Evan Ferguson",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Promise David",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Tom McGill",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Pascal Struijk",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Costinha",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Kaoru Mitoma",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Mats Wieffer",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    },
    "첼시": {
        "starters": [
            {
                "pos": "GK",
                "name": "로베르트 산체스",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "리스 제임스",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Tosin Adarabioyo",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Maxence Lacroix",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "웨슬리 포파나",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Jordan Henderson",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Morgan Rogers",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "엔초 페르난데스",
                "att_uv": 0.6,
                "def_uv": 0.5
            },
            {
                "pos": "FW",
                "name": "Danny Welbeck",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "페드로 네투",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "주앙 페드로",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Gaga Slonina",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "리바이 콜윌",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Pep Chavarría",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "모이세스 카이세도",
                "att_uv": 0.5,
                "def_uv": 0.6
            },
            {
                "pos": "MF",
                "name": "콜 파머",
                "att_uv": 0.9,
                "def_uv": 0.3
            }
        ]
    },
    "코번트리 시티": {
        "starters": [
            {
                "pos": "GK",
                "name": "Daniel Bentley",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "Jake Bidwell",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Jay Da Silva",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Ethan Pinnock",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Joel Latibeaudiere",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Matt Grimes",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Gustavo Hamer",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Ephron Mason-Clark",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "FW",
                "name": "Taiwo Awoniyi",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Haji Wright",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Brandon Thomas-Asante",
                "att_uv": 0.66,
                "def_uv": 0.24
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Ben Wilson",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "Luke Woolfenden",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Liam Kitching",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Victor Torp",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Frank Onyeka",
                "att_uv": 0.48,
                "def_uv": 0.42
            }
        ]
    },
    "크리스탈 팰리스": {
        "starters": [
            {
                "pos": "GK",
                "name": "Walter Benítez",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Daniel Muñoz",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Borna Sosa",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Axel Disasi",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Takehiro Tomiyasu",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Will Hughes",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Jefferson Lerma",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Daichi Kamada",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "Ismaïla Sarr",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Jean-Philippe Mateta",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Jørgen Strand Larsen",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Remi Matthews",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Chris Richards",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Óscar Mingueza",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Cheick Doucouré",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Justin Devenny",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    },
    "에버턴": {
        "starters": [
            {
                "pos": "GK",
                "name": "Mark Travers",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Michael Keane",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "James Tarkowski",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Vitaliy Mykolenko",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Nathan Patterson",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Christian Nørgaard",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Kiernan Dewsbury-Hall",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "James Garner",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "Iliman Ndiaye",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Beto",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Brennan Johnson",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Tom King",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Jake O'Brien",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Jarrad Branthwaite",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Hayden Hackney",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Charly Alcaraz",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    },
    "풀럼": {
        "starters": [
            {
                "pos": "GK",
                "name": "Benjamin Lecomte",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Kenny Tete",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Joachim Andersen",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Timothy Castagne",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Antonee Robinson",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "César Palacios",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Tom Cairney",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Harrison Reed",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "Gonzalo García",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Alex Iwobi",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Rodrigo Muniz",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Bernd Leno",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Jorge Cuenca",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Calvin Bassey",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Sander Berge",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Ryan Sessegnon",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    },
    "헐 시티": {
        "starters": [
            {
                "pos": "GK",
                "name": "Jack Butland",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "John Egan",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Semi Ajayi",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Matt Targett",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Paddy McNair",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Matt Crooks",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Kieran Dowell",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Abdülkadir Ömür",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "FW",
                "name": "Oliver McBurnie",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Babajide David",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Liam Millar",
                "att_uv": 0.66,
                "def_uv": 0.24
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Dillon Phillips",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "Lewie Coyle",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Ryan Giles",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Regan Slater",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Hidemasa Morita",
                "att_uv": 0.48,
                "def_uv": 0.42
            }
        ]
    },
    "입스위치 타운": {
        "starters": [
            {
                "pos": "GK",
                "name": "David Button",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "Darnell Furlong",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Issa Diop",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Dara O'Shea",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Cedric Kipre",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Julio Enciso",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Jack Taylor",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Cameron Humphreys",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "FW",
                "name": "Chuba Akpom",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Chiedozie Ogbene",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Jack Clarke",
                "att_uv": 0.66,
                "def_uv": 0.24
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Christian Walton",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "Leif Davis",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Jacob Greaves",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Sasa Lukic",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Exequiel Palacios",
                "att_uv": 0.48,
                "def_uv": 0.42
            }
        ]
    },
    "리즈 유나이티드": {
        "starters": [
            {
                "pos": "GK",
                "name": "Alex Cairns",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "Nico Elvedi",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "James Justin",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Joe Rodon",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Jayden Bogle",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Ilia Gruev",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Ethan Ampadu",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Sean Longstaff",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "FW",
                "name": "Harry Wilson",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Dominic Calvert-Lewin",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Daniel James",
                "att_uv": 0.66,
                "def_uv": 0.24
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Lucas Perri",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "Gabriel Gudmundsson",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Jaka Bijol",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Ao Tanaka",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Brenden Aaronson",
                "att_uv": 0.48,
                "def_uv": 0.42
            }
        ]
    },
    "리버풀": {
        "starters": [
            {
                "pos": "GK",
                "name": "알리송 베케르",
                "att_uv": 0.3,
                "def_uv": 0.65
            },
            {
                "pos": "DF",
                "name": "조 고메스",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "버질 반 다이크",
                "att_uv": 0.45,
                "def_uv": 0.7
            },
            {
                "pos": "DF",
                "name": "Kostas Tsimikas",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Conor Bradley",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Wataru Endo",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "알렉시스 맥 알리스터",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "도미니크 소보슬라이",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "페데리코 키에사",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "알렉산데르 이삭",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "코디 각포",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Freddie Woodman",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "로날드 아라우호",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "제레미 프림퐁",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "라이언 흐라번베르흐",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Harvey Elliott",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    },
    "맨체스터 시티": {
        "starters": [
            {
                "pos": "GK",
                "name": "헤로니모 룰리",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "후벵 디아스",
                "att_uv": 0.45,
                "def_uv": 0.65
            },
            {
                "pos": "DF",
                "name": "마크 게히",
                "att_uv": 0.4,
                "def_uv": 0.65
            },
            {
                "pos": "DF",
                "name": "라얀 아이트-누리",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "요슈코 그바르디올",
                "att_uv": 0.5,
                "def_uv": 0.6
            },
            {
                "pos": "MF",
                "name": "마테오 코바치치",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "잭 그릴리시",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Elliot Anderson",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "엘링 홀란드",
                "att_uv": 0.9,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "앙투안 세메뇨",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "제레미 도쿠",
                "att_uv": 0.75,
                "def_uv": 0.3
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Marcus Bettinelli",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Josh Wilson-Esbrand",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "리코 루이스",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "필 포든",
                "att_uv": 0.8,
                "def_uv": 0.35
            },
            {
                "pos": "MF",
                "name": "라얀 체르키",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    },
    "맨체스터 유나이티드": {
        "starters": [
            {
                "pos": "GK",
                "name": "Tom Heaton",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "해리 매과이어",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "루크 쇼",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "리산드로 마르티네스",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "디오구 달롯",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "브루노 페르난데스",
                "att_uv": 0.75,
                "def_uv": 0.4
            },
            {
                "pos": "MF",
                "name": "유리 틸레만스",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Jack Fletcher",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "마커스 래시포드",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "마테우스 쿠냐",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "브라이언 음베우모",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "칼 다를로우",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "마테이스 더 리흐트",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "누사이르 마즈라위",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "메이슨 마운트",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "마누엘 우가르테",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    },
    "뉴캐슬 유나이티드": {
        "starters": [
            {
                "pos": "GK",
                "name": "Mark Gillespie",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Lewis Hall",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Fabian Schär",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Dan Burn",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Sven Botman",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Jacob Murphy",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Joelinton",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Harvey Barnes",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "Yoane Wissa",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Anthony Elanga",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "Nick Woltemade",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Nick Pope",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "Tino Livramento",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Malick Thiaw",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "Joe Willock",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "Jacob Ramsey",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    },
    "노팅엄 포레스트": {
        "starters": [
            {
                "pos": "GK",
                "name": "Matz Sels",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "Morato",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Ola Aina",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Nikola Milenkovic",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Neco Williams",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Ibrahim Sangaré",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Xaver Schlager",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Ryan Yates",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "FW",
                "name": "Chris Wood",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Callum Hudson-Odoi",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Dan Ndoye",
                "att_uv": 0.66,
                "def_uv": 0.24
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "John Victor",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "Luca Netz",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Jair Paula",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Morgan Gibbs-White",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Nicolás Domínguez",
                "att_uv": 0.48,
                "def_uv": 0.42
            }
        ]
    },
    "선덜랜드": {
        "starters": [
            {
                "pos": "GK",
                "name": "Simon Moore",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "Thomas Meunier",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Nordi Mukiele",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Omar Alderete",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Reinildo Mandava",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Abdoullah Ba",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Granit Xhaka",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Luke O'Nien",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "FW",
                "name": "Wilson Isidor",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Brian Brobbey",
                "att_uv": 0.66,
                "def_uv": 0.24
            },
            {
                "pos": "FW",
                "name": "Simon Adingra",
                "att_uv": 0.66,
                "def_uv": 0.24
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Robin Roefs",
                "att_uv": 0.2,
                "def_uv": 0.55
            },
            {
                "pos": "DF",
                "name": "Ajibola Alese",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "DF",
                "name": "Danny Ballard",
                "att_uv": 0.4,
                "def_uv": 0.5
            },
            {
                "pos": "MF",
                "name": "Alan Browne",
                "att_uv": 0.48,
                "def_uv": 0.42
            },
            {
                "pos": "MF",
                "name": "Enzo Le Fée",
                "att_uv": 0.48,
                "def_uv": 0.42
            }
        ]
    },
    "토트넘 홋스퍼": {
        "starters": [
            {
                "pos": "GK",
                "name": "마르틴 두브라브카",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "벤 데이비스",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "앤디 로버트슨",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "마르코스 세네시",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Kevin Danso",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "제임스 매디슨",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "로드리고 벤탕쿠르",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "산드로 토날리",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "FW",
                "name": "히샤를리송",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "도미닉 솔랑케",
                "att_uv": 0.73,
                "def_uv": 0.25
            },
            {
                "pos": "FW",
                "name": "오마르 마르무시",
                "att_uv": 0.73,
                "def_uv": 0.25
            }
        ],
        "subs": [
            {
                "pos": "GK",
                "name": "Brandon Austin",
                "att_uv": 0.25,
                "def_uv": 0.6
            },
            {
                "pos": "DF",
                "name": "페드로 포로",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "DF",
                "name": "Jan Paul van Hecke",
                "att_uv": 0.44,
                "def_uv": 0.54
            },
            {
                "pos": "MF",
                "name": "모하메드 쿠두스",
                "att_uv": 0.54,
                "def_uv": 0.44
            },
            {
                "pos": "MF",
                "name": "코너 갤러거",
                "att_uv": 0.54,
                "def_uv": 0.44
            }
        ]
    }
}

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

def calculate_player_uv(player_data):
    p_name = player_data.get("name", "")
    rating = float(player_data.get("rating", 6.80) or 6.80)
    goals_per90 = float(player_data.get("goals_per90", 0.0) or 0.0)
    pos = str(player_data.get("pos", "MF") or "MF").upper()

    PLAYER_STATS_LOOKUP = {
        "Erling Haaland": {"rating": 7.85, "pos": "FW", "goals_per90": 0.95},
        "엘링 홀란드": {"rating": 7.85, "pos": "FW", "goals_per90": 0.95},
        "Phil Foden": {"rating": 7.65, "pos": "MF", "goals_per90": 0.55},
        "필 포든": {"rating": 7.65, "pos": "MF", "goals_per90": 0.55},
        "Bernardo Silva": {"rating": 7.45, "pos": "MF", "goals_per90": 0.20},
        "베르나르두 실바": {"rating": 7.45, "pos": "MF", "goals_per90": 0.20},
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
        "Cole Palmer": {"rating": 7.80, "pos": "FW", "goals_per90": 0.60},
        "콜 파머": {"rating": 7.80, "pos": "FW", "goals_per90": 0.60},
    }

    for name_key, info in PLAYER_STATS_LOOKUP.items():
        if name_key.lower() in p_name.lower() or p_name.lower() in name_key.lower():
            rating = info["rating"]
            goals_per90 = info.get("goals_per90", goals_per90)
            pos = info.get("pos", pos)
            break

    if pos in ["GK", "G"]:
        raw_uv = 1.0 + (rating - 6.8) * 1.2
    elif pos in ["DF", "D"]:
        raw_uv = 1.0 + (rating - 6.8) * 1.1
    elif pos in ["MF", "M"]:
        raw_uv = 1.0 + (rating - 6.8) * 1.0
    elif pos in ["FW", "F"]:
        raw_uv = 1.0 + (rating - 6.8) * 1.0 + (goals_per90 * 0.5)
    else:
        raw_uv = 1.0 + (rating - 6.8) * 1.0

    return round(min(max(raw_uv, 0.1), 3.0), 3)

def calculate_wuv(team_name):
    ensure_team_roster(team_name)
    team = TEAMS_ROSTER[team_name]
    
    starters = team.get("starters", [])[:11]
    subs = team.get("subs", [])[:5]
    
    st_list = []
    for p in starters:
        uv = calculate_player_uv(p)
        st_list.append({"name": p.get("name"), "pos": p.get("pos"), "att_uv": round(uv*0.6, 2), "def_uv": round(uv*0.4, 2), "uv": uv})
        
    sub_list = []
    for p in subs:
        uv = calculate_player_uv(p)
        sub_list.append({"name": p.get("name"), "pos": p.get("pos"), "att_uv": round(uv*0.6, 2), "def_uv": round(uv*0.4, 2), "uv": uv})
        
    st_avg = sum([p["uv"] for p in st_list]) / len(st_list) if st_list else 1.0
    sub_avg = sum([p["uv"] for p in sub_list]) / len(sub_list) if sub_list else 1.0
    
    team_wuv = 11.0 * (0.85 * st_avg + 0.15 * sub_avg)
    
    st_df = pd.DataFrame(st_list)
    sub_df = pd.DataFrame(sub_list)
    
    return {
        "st_att": round(st_avg * 11 * 0.6, 2),
        "st_def": round(st_avg * 11 * 0.4, 2),
        "st_total": round(st_avg * 11, 2),
        "sub_att_raw": round(sub_avg * 5 * 0.6, 2),
        "sub_def_raw": round(sub_avg * 5 * 0.4, 2),
        "sub_att_scaled": round(sub_avg * 11 * 0.6, 2),
        "sub_def_scaled": round(sub_avg * 11 * 0.4, 2),
        "sub_total_scaled": round(sub_avg * 11, 2),
        "wuv_att": round(team_wuv * 0.6, 2),
        "wuv_def": round(team_wuv * 0.4, 2),
        "wuv_total": round(team_wuv, 2),
        "team_wuv": round(team_wuv, 2),
        "st_avg": round(st_avg, 3),
        "sub_avg": round(sub_avg, 3),
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
    "Round 01 (2026-08-21 ~ 08-24)": [
        ("아스널", "코번트리 시티", "아스널", 1),
        ("헐 시티", "맨체스터 유나이티드", "헐 시티", 0),
        ("에버턴", "크리스탈 팰리스", "에버턴", 0),
        ("입스위치 타운", "선덜랜드", "입스위치 타운", 1),
        ("노팅엄 포레스트", "리즈 유나이티드", "리즈 유나이티드", 0),
        ("브렌트포드", "토트넘 홋스퍼", "브렌트포드", 0),
        ("브라이튼", "아스톤 빌라", "브라이튼", 0),
        ("맨체스터 시티", "본머스", "맨체스터 시티", 1),
        ("뉴캐슬 유나이티드", "리버풀", "무승부 (Draw)", 1),
        ("풀럼", "첼시", "첼시", 0),
    ],
    "Round 02 (2026-08-28 ~ 08-31)": [
        ("크리스탈 팰리스", "맨체스터 시티", "", None),
        ("리버풀", "노팅엄 포레스트", "", None),
        ("본머스", "에버턴", "", None),
        ("코번트리 시티", "헐 시티", "", None),
        ("토트넘 홋스퍼", "뉴캐슬 유나이티드", "", None),
        ("첼시", "브라이튼", "", None),
        ("리즈 유나이티드", "브렌트포드", "", None),
        ("선덜랜드", "풀럼", "", None),
        ("맨체스터 유나이티드", "입스위치 타운", "", None),
        ("아스톤 빌라", "아스널", "", None),
    ],
    "Round 03 (2026-09-04 ~ 09-06)": [
        ("입스위치 타운", "리버풀", "", None),
        ("뉴캐슬 유나이티드", "본머스", "", None),
        ("브렌트포드", "선덜랜드", "", None),
        ("브라이튼", "리즈 유나이티드", "", None),
        ("풀럼", "크리스탈 팰리스", "", None),
        ("맨체스터 시티", "코번트리 시티", "", None),
        ("노팅엄 포레스트", "토트넘 홋스퍼", "", None),
        ("헐 시티", "아스톤 빌라", "", None),
        ("에버턴", "맨체스터 유나이티드", "", None),
        ("아스널", "첼시", "", None),
    ]
}

# -----------------------------------------------------------------------------
# 5. [상단] 누적 예측 성적표 & 100경기 트래킹 (MLB/NBA 템플릿과 100% 동일)
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "epl_data.db")

def load_data():
    if not os.path.exists(DB_PATH):
        try:
            from run_epl import run_pipeline
            run_pipeline()
        except Exception:
            pass

    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            db_df = pd.read_sql("SELECT * FROM predictions ORDER BY date ASC, id ASC", conn)
            conn.close()
            if not db_df.empty:
                records = []
                for _, row in db_df.iterrows():
                    h_team = row["home_team"]
                    v_team = row["visit_team"]
                    p = get_match_prediction(h_team, v_team)
                    records.append({
                        "date": row["date"],
                        "uk_date": row["uk_date"] if ("uk_date" in db_df.columns and pd.notna(row["uk_date"])) else row["date"],
                        "kst_date": row["kst_date"] if ("kst_date" in db_df.columns and pd.notna(row["kst_date"])) else row["date"],
                        "round_name": row["round_name"] if ("round_name" in db_df.columns and pd.notna(row["round_name"])) else row["date"],
                        "home_team": h_team,
                        "visit_team": v_team,
                        "predicted_winner": row["predicted_winner"],
                        "predicted_gap": row["predicted_gap"],
                        "prob_home": row["prob_home"],
                        "prob_draw": row["prob_draw"],
                        "prob_away": row["prob_away"],
                        "actual_winner": row["actual_winner"] if row["actual_winner"] else "",
                        "is_correct": row["is_correct"] if pd.notna(row["is_correct"]) else None,
                        "home_uv": row["home_uv"],
                        "visit_uv": row["visit_uv"],
                        "res_obj": p
                    })
                return pd.DataFrame(records)
        except Exception:
            pass

    # DB 미존재 시 Fallback 데이터셋
    all_records = []
    for r_date, m_list in ROUNDS_MATCHES.items():
        for home, away, act_win, _ in m_list:
            p = get_match_prediction(home, away)
            is_corr = 1 if (p["winner"] == act_win) else (0 if act_win else None)
            all_records.append({
                "date": r_date,
                "uk_date": r_date,
                "kst_date": r_date,
                "round_name": r_date,
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
    return pd.DataFrame(all_records)

df = load_data()

df['total_no'] = range(1, len(df) + 1)
stats_df = df[df['actual_winner'].notna() & (df['actual_winner'] != '')].copy()

st.header("📊 누적 예측 성적표")
total_stats = len(stats_df)
correct_total = stats_df['is_correct'].sum() if total_stats > 0 else 0

col_acc, col_track = st.columns([2, 1])

if total_stats > 0:
    total_acc = (correct_total / total_stats) * 100
    status_suffix = " (⚡ 신계, 시장 왜곡급)" if total_acc >= 55 else ""
    
    with col_acc:
        st.subheader(f"전체 완료 경기 적중률: `{total_acc:.2f}%`{status_suffix}")
        st.markdown(f"**적중 경기 수:** {int(correct_total)} / **완료 경기 수:** {total_stats} (전체 예정: {len(df)}경기)")
    
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
# 6. [중단] 라운드별 예측 성적표 (6단계 등급 및 Altair 바 차트)
# -----------------------------------------------------------------------------
st.header("📈 라운드별 예측 성적표 (EPL Gameweek)")

if not stats_df.empty:
    group_col = 'round_name' if 'round_name' in stats_df.columns else 'date'
    round_stats = stats_df.groupby(group_col, sort=False).agg(
        total_games=('home_team', 'count'),
        correct_games=('is_correct', 'sum')
    ).reset_index()

    round_stats['accuracy'] = (round_stats['correct_games'] / round_stats['total_games']) * 100
    
    def get_bar_color(acc):
        if acc >= 55: return '#A020F0'      # 보라 (신계)
        elif acc >= 50: return '#FF0000'    # 빨강 (초고수/AI)
        elif acc >= 45: return '#FFA500'    # 주황 (프로/고수)
        elif acc >= 38: return '#1E90FF'    # 파랑 (노력하는 일반인)
        elif acc >= 30: return '#008000'    # 녹색 (지극히 정상인)
        else: return '#808080'             # 회색 (예측 금지)

    round_stats['bar_color'] = round_stats['accuracy'].apply(get_bar_color)
    round_stats['label_text'] = round_stats.apply(
        lambda x: f"{int(x['correct_games'])}/{int(x['total_games'])}", 
        axis=1
    )

    round_stats_7d = round_stats.tail(7)

    base = alt.Chart(round_stats_7d).encode(x=alt.X(group_col, title='EPL 라운드 (Gameweek)', sort=None))
    bars = base.mark_bar().encode(
        y=alt.Y('accuracy', title='적중률(%)', scale=alt.Scale(domain=[0, 110])),
        color=alt.Color('bar_color', scale=None),
        tooltip=[group_col, 'accuracy', 'total_games', 'correct_games']
    )
    text = base.mark_text(align='center', baseline='bottom', dy=-5, fontSize=14, fontWeight='bold').encode(
        y='accuracy', text='label_text'
    )
    st.altair_chart((bars + text).properties(height=320), use_container_width=True)
else:
    st.info("💡 예정 경기 예측 완료! (경기가 종료되는 대로 라운드별 실시간 적중률이 집계됩니다.)")

st.markdown("""
<div style="text-align: center; padding: 12px; background-color: #f0f2f6; border-radius: 10px; line-height: 1.6;">
    <span style="color: #A020F0;">●</span> <b>신계</b> (55%↑) &nbsp;&nbsp;
    <span style="color: #FF0000;">●</span> <b>초고수/AI</b> (50%~55%) &nbsp;&nbsp;
    <span style="color: #FFA500;">●</span> <b>프로/고수</b> (45%~50%) &nbsp;&nbsp;
    <span style="color: #1E90FF;">●</span> <b>노력하는 일반인</b> (38%~45%) &nbsp;&nbsp;
    <span style="color: #008000;">●</span> <b>지극히 정상인</b> (30%~38%) &nbsp;&nbsp;
    <span style="color: #808080;">●</span> <b>예측 금지</b> (30%↓)
    <br><small>* 3-Way(승/무/패) 특성상 평균 46%~48% 이상부터 통계적 손익분기점(Breakeven)을 달성합니다.</small>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. [하단] 라운드별 10개 매치업 목록 카드 & 상세 데이터프레임
# -----------------------------------------------------------------------------
st.header("📋 라운드별 경기 리포트 (10개 매치업 카드 리스트)")

def extract_round_num(text):
    import re
    m = re.search(r'Round\s*(\d+)', str(text))
    return int(m.group(1)) if m else 0

if 'round_name' in df.columns:
    unique_dates = sorted(df['round_name'].unique(), key=extract_round_num, reverse=True)
    
    # 디폴트 라운드 자동 지정: 가장 최근에 완료된 라운드 '다음' 진행 예정 라운드 자동 선택
    pending_df = df[df['actual_winner'].isna() | (df['actual_winner'] == '')]
    default_idx = 0
    if not pending_df.empty:
        pending_rounds = sorted(pending_df['round_name'].unique(), key=extract_round_num, reverse=False)
        target_round = pending_rounds[0]
        if target_round in unique_dates:
            default_idx = unique_dates.index(target_round)
            
    selected_date = st.selectbox("확인하고 싶은 라운드를 선택하세요:", unique_dates, index=default_idx)
    filtered_df = df[df['round_name'] == selected_date].copy().reset_index(drop=True)
else:
    unique_dates = sorted(df['date'].unique(), reverse=True)
    selected_date = st.selectbox("확인하고 싶은 라운드를 선택하세요:", unique_dates, index=0)
    filtered_df = df[df['date'] == selected_date].copy().reset_index(drop=True)

if not filtered_df.empty:
    filtered_df['day_no'] = range(1, len(filtered_df) + 1)
    
    completed_in_round = filtered_df[filtered_df['actual_winner'].notna() & (filtered_df['actual_winner'] != '')]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("해당 라운드 총 경기 수", f"{len(filtered_df)} 경기")
    col2.metric("경기 완료 수", f"{len(completed_in_round)} 경기")
    
    if not completed_in_round.empty:
        corr_cnt = int(completed_in_round['is_correct'].sum())
        acc = (corr_cnt / len(completed_in_round)) * 100
        col3.metric("라운드 적중률", f"{acc:.1f}% ({corr_cnt}/{len(completed_in_round)})")
    else:
        col3.metric("라운드 적중률", "⏳ 진행 예정")

    # 대시보드 리포트용 데이터프레임
    display_df = pd.DataFrame()
    display_df['No.'] = filtered_df['day_no']
    display_df['경기 일시 (영국 현지)'] = filtered_df['uk_date']
    display_df['한국 시각 (KST)'] = filtered_df['kst_date']
    display_df['홈 팀'] = filtered_df.apply(lambda r: f"{r['home_team']} ({r['home_uv']:.2f} WUV)" if pd.notna(r.get('home_uv')) else r['home_team'], axis=1)
    display_df['원정 팀'] = filtered_df.apply(lambda r: f"{r['visit_team']} ({r['visit_uv']:.2f} WUV)" if pd.notna(r.get('visit_uv')) else r['visit_team'], axis=1)
    display_df['예측 결과'] = filtered_df['predicted_winner']
    display_df['3-Way 확률 [홈%|무%|원정%]'] = filtered_df.apply(
        lambda r: f"[{r['prob_home']:.1f}% | {r['prob_draw']:.1f}% | {r['prob_away']:.1f}%]", axis=1
    )
    display_df['예상 격차(ΔUV)'] = filtered_df['predicted_gap'].apply(lambda x: f"{x:+.2f}")
    display_df['실제 결과'] = filtered_df['actual_winner'].apply(lambda x: x if (pd.notna(x) and x != '') else "대기중")
    
    def get_status_tag(r):
        act = r['actual_winner']
        if not act or pd.isna(act) or act == '':
            return "⏳ 경기 대기중"
        return "✅ 정답" if r['is_correct'] == 1 else "❌ 오답"
        
    display_df['적중 여부'] = filtered_df.apply(get_status_tag, axis=1)

    st.dataframe(display_df, hide_index=True, use_container_width=True)

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
