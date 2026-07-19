import base64
from pathlib import Path

import streamlit as st


def inject_styles() -> None:
    hero_path = Path(__file__).resolve().parents[2] / "assets" / "images" / "market-hero-3d.png"
    hero_image = ""
    if hero_path.exists():
        hero_image = base64.b64encode(hero_path.read_bytes()).decode("ascii")
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,700;9..144,800&display=swap');
    .stApp { background: #f7f8ff; color: #172b22; background-image: radial-gradient(circle at 7% 8%, #b7f3cf 0, transparent 25%), radial-gradient(circle at 89% 4%, #ffd4ad 0, transparent 22%), radial-gradient(circle at 60% 82%, #e0ccff 0, transparent 28%); }
    .block-container { max-width: 1180px; padding-top: 1.4rem; padding-bottom: 6rem; }
    #MainMenu, footer {visibility:hidden;} [data-testid="stSidebar"] { background: linear-gradient(180deg,#082b25,#0b4637); border-right:1px solid #ffffff14; } [data-testid="stSidebar"] * { color:#ecfff5!important; } [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color:#a9d4c0!important}
    h1,h2,h3 { font-family:Fraunces,serif !important; color:#173826 !important; } p,label,.stMarkdown { font-family:'DM Sans',sans-serif; color:#173826; } [data-testid="stCaptionContainer"] {color:#557063!important}
    .hero { position:relative; overflow:hidden; background-image:linear-gradient(90deg,rgba(15,67,49,.92) 0%,rgba(20,94,65,.74) 38%,rgba(14,73,50,.14) 72%),url("data:image/png;base64,__HERO_IMAGE__"); background-size:cover; background-position:center; border:1px solid #ffffffa0; border-radius:30px; padding:42px; color:#fff; box-shadow:0 28px 60px #1b432d45, inset 0 1px #fff8; margin-bottom:18px; min-height:390px; transform:perspective(900px) rotateX(1.4deg); }
    .hero:after { content:''; position:absolute; inset:auto 7% 7% auto; width:108px; height:108px; border-radius:50%; background:radial-gradient(circle at 35% 28%,#ffffffcc,#ffffff22 48%,#ffffff08 70%); border:1px solid #fff8; box-shadow:0 18px 36px #193c2b55; animation:float 4s ease-in-out infinite; } @keyframes float {50%{transform:translateY(-14px) rotate(7deg)}} .hero h1{position:relative;z-index:1;margin:12px 0;font-size:3.35rem !important;color:#fff!important;max-width:650px;line-height:1.03}.hero p{position:relative;z-index:1;max-width:550px;font-size:1.08rem;color:#fff!important}.hero .pill{position:relative;z-index:1}
    .pill,.mini-pill {display:inline-block;padding:6px 11px;border-radius:999px;font-weight:700;font-size:.78rem;background:#ffffff2b;border:1px solid #ffffff70;backdrop-filter:blur(8px)} .mini-pill{color:#0d4b38;background:#c9ffdd;border:0}
    .section-title {font:800 1.6rem Fraunces,serif;color:#173826;margin:25px 0 11px}.subtle{color:#557063}
    .glass-card,.product-card,.vendor-card,.stat-card,.login-card {background:linear-gradient(135deg,#ffffffef,#ffffffbb); color:#173826; border:1px solid #ffffff; border-radius:22px; padding:17px; box-shadow:0 15px 35px #26382c1c, inset 0 1px #fff; backdrop-filter:blur(18px); transition:transform .2s ease, border-color .2s ease;}
    .glass-card:hover,.product-card:hover,.vendor-card:hover {transform:translateY(-5px) rotateX(1deg); border-color:#72dba6;}.vendor-card{min-height:172px}.product-card{min-height:152px}.product-emoji{font-size:47px;filter:drop-shadow(0 9px 7px #0003)}.muted{color:#557063;font-size:.89rem}.price{color:#d85726;font-weight:800;font-size:1.24rem;margin-top:5px}.vendor-name{font-weight:800;font-size:1.05rem;color:#173826}.rating{color:#c47700;font-weight:800}.category{min-height:88px;text-align:center;padding:12px 6px;color:#173826;font-weight:700}.category span{font-size:29px;display:block}.order-box{background:#e6fff0;border:1px solid #83d9a7;padding:17px;border-radius:18px}.login-card{min-height:175px}.stat-card{min-height:105px}.stat-value{font:800 1.85rem Fraunces,serif;color:#d85726}
    .stButton>button,.stLinkButton>a{border-radius:12px!important;border:1px solid #159c6522!important;background:linear-gradient(135deg,#36c983,#159c65)!important;color:white!important;font-weight:800!important;transition:transform .15s!important}.stButton>button:hover,.stLinkButton>a:hover{transform:translateY(-2px)!important;filter:brightness(1.12)}.stTextInput input,.stNumberInput input{background:#fff!important;color:#173826!important;border-color:#9abaaa!important}.stSelectbox div[data-baseweb="select"]>div{background:#fff!important;color:#173826!important;border-color:#9abaaa!important}.stAlert{border-radius:16px}.stRadio label{color:#173826!important}
    .landing-stat {background:#ffffffb8;border:1px solid #fff;border-radius:18px;padding:15px;text-align:center;box-shadow:0 12px 26px #1a57301a}.landing-stat b{display:block;font:800 1.55rem Fraunces,serif;color:#126b43}.feature-card{background:#fff;border-radius:20px;padding:20px;min-height:150px;box-shadow:0 12px 28px #1a573018;border:1px solid #fff}.feature-card .icon{font-size:34px}.feature-card h3{margin:8px 0 4px;font-size:1.15rem!important}.feature-card p{margin:0;color:#557063}.social-proof{background:linear-gradient(120deg,#173826,#225a39);color:#fff!important;padding:20px 24px;border-radius:22px;box-shadow:0 18px 38px #123b2944}.social-proof *{color:#fff!important}
    </style>
    """.replace("__HERO_IMAGE__", hero_image), unsafe_allow_html=True)


def inr(value: float) -> str:
    return f"₹{value:,.0f}"
