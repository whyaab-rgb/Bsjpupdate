import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="BSJP Screener Premium",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# DEFAULT WATCHLIST
# =========================
DEFAULT_WATCHLIST = """
AALI.JK,ACES.JK,ADHI.JK,ADMR.JK,ADRO.JK,AKRA.JK,AMMN.JK,ANTM.JK,ARTO.JK,ASII.JK,
BBCA.JK,BBNI.JK,BBRI.JK,BBTN.JK,BBYB.JK,BMRI.JK,BRIS.JK,BRMS.JK,BRPT.JK,BSDE.JK,
BUKA.JK,BUMI.JK,CPIN.JK,CTRA.JK,DOID.JK,ELSA.JK,EMTK.JK,ERAA.JK,ESSA.JK,EXCL.JK,
GOTO.JK,HRUM.JK,ICBP.JK,INCO.JK,INDF.JK,INDY.JK,INKP.JK,INTP.JK,ISAT.JK,ITMG.JK,
JPFA.JK,JSMR.JK,KLBF.JK,MAPI.JK,MDKA.JK,MEDC.JK,MIKA.JK,MYOR.JK,NCKL.JK,PGAS.JK,
PTBA.JK,PTPP.JK,PWON.JK,RAJA.JK,SCMA.JK,SIDO.JK,SMDR.JK,SMGR.JK,SMRA.JK,TINS.JK,
TKIM.JK,TLKM.JK,TOBA.JK,TOWR.JK,UNTR.JK,UNVR.JK,WIKA.JK
"""

MIN_VALUE = 1_000_000_000
MIN_VOLUME = 500_000

# =========================
# CSS PREMIUM
# =========================
st.markdown("""
<style>
.stApp {
    background: #050d18;
    color: #e8eef7;
}

.block-container {
    max-width: 1550px;
    padding-top: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07111f 0%, #06101d 100%);
    border-right: 1px solid #112b47;
}

[data-testid="stSidebar"] * {
    color: #f2f7ff;
}

.sidebar-logo {
    padding: 18px 10px 14px 10px;
    border-bottom: 1px solid #15314f;
    margin-bottom: 12px;
}

.logo-title {
    font-size: 32px;
    font-weight: 900;
    letter-spacing: 1px;
    line-height: 1;
}

.logo-sub {
    color: #2bd4ff;
    font-weight: 900;
    letter-spacing: 4px;
    font-size: 14px;
}

.menu-item {
    padding: 11px 14px;
    border-radius: 10px;
    margin: 5px 0;
    font-size: 14px;
    color: #c8d6e8;
    background: transparent;
}

.menu-active {
    background: linear-gradient(90deg, #1557d6, #1767f2);
    color: white;
    font-weight: 800;
}

.side-card {
    background: #0b1d31;
    border: 1px solid #173a5b;
    border-radius: 14px;
    padding: 14px;
    margin-top: 14px;
}

/* HEADER */
.top-header {
    background: #07111f;
    border: 1px solid #112b47;
    border-radius: 16px;
    padding: 16px 18px;
}

.title-main {
    font-size: 25px;
    font-weight: 900;
    color: #f4f8ff;
}

.market-green {
    color: #22e57b;
    font-weight: 800;
}

.market-red {
    color: #ff5b5b;
    font-weight: 800;
}

/* CARDS */
.card {
    background: linear-gradient(145deg, #0b1d31, #081626);
    border: 1px solid #173a5b;
    border-radius: 16px;
    padding: 18px;
    min-height: 112px;
    box-shadow: 0 10px 24px rgba(0,0,0,.25);
}

.card-small {
    background: linear-gradient(145deg, #0b1d31, #081626);
    border: 1px solid #173a5b;
    border-radius: 16px;
    padding: 15px;
}

.metric-title {
    color: #a9b8cc;
    font-size: 13px;
    font-weight: 800;
}

.metric-value {
    font-size: 30px;
    font-weight: 900;
    margin-top: 6px;
}

.green { color: #22e57b; font-weight: 900; }
.blue { color: #2d95ff; font-weight: 900; }
.yellow { color: #ffc928; font-weight: 900; }
.red { color: #ff5050; font-weight: 900; }
.gray { color: #a9b8cc; }

/* FILTER BAR */
.filter-box {
    background: #0b1d31;
    border: 1px solid #173a5b;
    border-radius: 14px;
    padding: 14px;
}

/* BUTTON */
.stButton > button {
    width: 100%;
    border-radius: 10px;
    background: linear-gradient(90deg, #1557d6, #2d95ff);
    color: white;
    font-weight: 900;
    border: 0;
}

.stButton > button:hover {
    border: 0;
    background: linear-gradient(90deg, #2d95ff, #1557d6);
}

/* INPUT */
input, textarea, select {
    background-color: #ffffff !important;
    color: #111827 !important;
    border-radius: 10px !important;
}

/* TABLE */
thead tr th {
    background-color: #0e2238 !important;
    color: #ffffff !important;
    font-weight: 900 !important;
    border: 1px solid #1c3c5c !important;
}

tbody tr td {
    border: 1px solid #1c3c5c !important;
}

/* HIDE STREAMLIT FOOTER */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="logo-title">📈 BSJP</div>
        <div class="logo-sub">SCREENER</div>
    </div>
    """, unsafe_allow_html=True)

    menu_items = [
        "🏠 Dashboard",
        "🔍 Screener",
        "🎯 Kandidat Entry",
        "👁️ Saham Pantau",
        "🔔 Alert",
        "⭐ Watchlist",
        "📊 Top Volume",
        "🌐 Market Summary",
        "⚙️ Pengaturan",
        "📖 Panduan",
    ]

    for i, item in enumerate(menu_items):
        cls = "menu-item menu-active" if i == 0 else "menu-item"
        st.markdown(f"<div class='{cls}'>{item}</div>", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### ⚙️ Pengaturan")

    preset = st.selectbox("Preset Watchlist", ["IDX Pilihan", "Custom"], index=0)
    period = st.selectbox("Periode", ["3mo", "6mo", "1y"], index=1)
    interval = st.selectbox("Interval", ["1d", "1h", "30m", "15m"], index=0)

    auto_refresh = st.checkbox("Auto Refresh", value=False)
    refresh_seconds = st.selectbox("Refresh tiap", [30, 60, 120, 300], index=1)

    max_price = st.number_input(
        "Harga saham maksimal",
        min_value=50,
        max_value=100000,
        value=1000,
        step=50
    )

    max_result = st.number_input(
        "Hasil utama Top N",
        min_value=5,
        max_value=100,
        value=30,
        step=5
    )

    watchlist_input = st.text_area(
        "Daftar saham watchlist",
        value=DEFAULT_WATCHLIST.strip(),
        height=120
    )

    st.markdown("---")
    st.markdown("### 🤖 Telegram Bot")

    telegram_enabled = st.checkbox("Aktifkan notifikasi Telegram", value=False)
    bot_token = st.text_input("Bot Token", type="password")
    chat_id = st.text_input("Chat ID")
    telegram_top_n = st.number_input("Kirim Top N", min_value=1, max_value=30, value=5, step=1)
    send_only_strong = st.checkbox("Kirim hanya alert kuat", value=True)
    test_telegram = st.button("Tes Kirim Telegram", disabled=not telegram_enabled)

    st.markdown("---")
    st.markdown("### 🔎 Search Emiten Mandiri")

    manual_symbol = st.text_input("Masukkan emiten", placeholder="Contoh: BBCA atau GOTO")
    search_mode = st.radio(
        "Mode pencarian",
        ["Tambahkan ke watchlist", "Analisa emiten ini saja"],
        index=0
    )

    run_screener = st.button("Jalankan Screener")

    st.markdown("""
    <div class="side-card">
        <b>🔔 Alert Telegram</b><br>
        <span style="font-size:13px;color:#b7c6d8;">
        Dapatkan notifikasi sinyal BSJP KUAT langsung ke Telegram Anda.
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="side-card">
        <b>Auto Refresh</b><br><br>
        Interval: <b>{refresh_seconds} detik</b><br>
        Filter harga: <b>{max_price}</b><br>
        Limit hasil: <b>{max_result}</b>
    </div>
    """, unsafe_allow_html=True)

if auto_refresh:
    st.markdown(f"<meta http-equiv='refresh' content='{refresh_seconds}'>", unsafe_allow_html=True)

# =========================
# WATCHLIST LOGIC
# =========================
watchlist = [x.strip().upper() for x in watchlist_input.replace("\n", ",").split(",") if x.strip()]
watchlist = [x if x.endswith(".JK") else f"{x}.JK" for x in watchlist]

if manual_symbol:
    manual_symbol = manual_symbol.strip().upper()
    manual_symbol = manual_symbol if manual_symbol.endswith(".JK") else f"{manual_symbol}.JK"

    if search_mode == "Tambahkan ke watchlist":
        if manual_symbol not in watchlist:
            watchlist.append(manual_symbol)
    else:
        watchlist = [manual_symbol]

# =========================
# FUNCTIONS
# =========================
def send_telegram_message(token, chat, message):
    try:
        if not token or not chat:
            return False, "Bot Token atau Chat ID belum diisi."

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat, "text": message, "parse_mode": "HTML"}
        r = requests.post(url, data=payload, timeout=10)

        if r.status_code == 200:
            return True, "Telegram berhasil dikirim."
        return False, r.text
    except Exception as e:
        return False, str(e)

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def macd(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal
    return macd_line, signal, hist

def rupiah_short(x):
    if pd.isna(x):
        return "-"
    if x >= 1_000_000_000_000:
        return f"{x/1_000_000_000_000:.2f} T"
    if x >= 1_000_000_000:
        return f"{x/1_000_000_000:.2f} B"
    if x >= 1_000_000:
        return f"{x/1_000_000:.2f} M"
    return f"{x:,.0f}"

def calculate_bsjp(ticker, period="6mo", interval="1d"):
    try:
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False,
            threads=False
        )

        if df.empty or len(df) < 60:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna()

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        last_close = float(close.iloc[-1])
        prev_close = float(close.iloc[-2])
        change_pct = ((last_close - prev_close) / prev_close) * 100

        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()
        rsi_val = rsi(close)
        macd_line, macd_signal, macd_hist = macd(close)

        if pd.isna(ma20.iloc[-1]) or pd.isna(ma50.iloc[-1]) or pd.isna(rsi_val.iloc[-1]):
            return None

        avg_vol20 = volume.rolling(20).mean()
        rvol = float(volume.iloc[-1] / avg_vol20.iloc[-1]) if avg_vol20.iloc[-1] > 0 else 0
        value = last_close * float(volume.iloc[-1])

        support = float(low.tail(20).min())
        resistance = float(high.tail(20).max())
        breakout = resistance

        stop_loss = support * 0.985
        target1 = resistance
        target2 = resistance + (resistance - support)

        risk = max(last_close - stop_loss, 1)
        reward = max(target1 - last_close, 0)
        rr = reward / risk if risk > 0 else 0

        entry_low = support * 1.01
        entry_high = last_close

        latest_rsi = float(rsi_val.iloc[-1])
        prev_rsi = float(rsi_val.iloc[-2])
        latest_hist = float(macd_hist.iloc[-1])
        prev_hist = float(macd_hist.iloc[-2])

        score = 0
        reasons = []

        if last_close > ma20.iloc[-1] and last_close > ma50.iloc[-1]:
            score += 10
            reasons.append("Harga di atas MA20 & MA50")
        if ma20.iloc[-1] > ma50.iloc[-1]:
            score += 5
            reasons.append("MA20 di atas MA50")
        if low.iloc[-1] >= low.tail(10).min():
            score += 5
            reasons.append("Tidak membuat low baru")
        if resistance > 0 and 0 <= ((resistance - last_close) / last_close) <= 0.03:
            score += 5
            reasons.append("Dekat breakout")

        if rvol > 1.5:
            score += 8
            reasons.append("RVOL tinggi")
        if volume.iloc[-1] > avg_vol20.iloc[-1]:
            score += 6
            reasons.append("Volume di atas rata-rata")
        if value >= MIN_VALUE:
            score += 5
            reasons.append("Value likuid")
        if last_close > prev_close and volume.iloc[-1] > volume.iloc[-2]:
            score += 6
            reasons.append("Candle naik + volume naik")

        if 45 <= latest_rsi <= 68:
            score += 7
            reasons.append("RSI sehat")
        if latest_rsi > prev_rsi:
            score += 4
            reasons.append("RSI naik")
        if latest_hist > prev_hist:
            score += 5
            reasons.append("MACD histogram membaik")
        if macd_line.iloc[-1] > macd_signal.iloc[-1]:
            score += 4
            reasons.append("MACD bullish")

        if rr >= 2:
            score += 8
            reasons.append("RR minimal 1:2")
        if abs(last_close - support) / last_close <= 0.08:
            score += 4
            reasons.append("Support dekat")
        if abs(last_close - support) / last_close <= 0.10:
            score += 4
            reasons.append("Entry dekat support")
        if target1 > last_close:
            score += 4
            reasons.append("Target realistis")

        gain_3d = ((last_close - close.iloc[-4]) / close.iloc[-4]) * 100 if len(close) > 4 else 0

        if gain_3d <= 8:
            score += 4
            reasons.append("Tidak FOMO")
        if latest_rsi < 75:
            score += 3
            reasons.append("RSI tidak overbought")
        if abs(last_close - ma20.iloc[-1]) / last_close <= 0.08:
            score += 3
            reasons.append("Harga dekat MA20")

        score = min(score, 100)

        trend = "UP" if last_close > ma20.iloc[-1] > ma50.iloc[-1] else "SIDEWAYS" if last_close >= ma50.iloc[-1] else "DOWN"
        macd_status = "Bullish" if macd_line.iloc[-1] > macd_signal.iloc[-1] else "Bearish"

        if (
            score >= 80 and rvol >= 1.5 and 45 <= latest_rsi <= 68
            and latest_hist > prev_hist and last_close > ma20.iloc[-1]
            and rr >= 2 and latest_rsi < 75
        ):
            status = "BSJP KUAT"
        elif (
            score >= 70 and rvol >= 1.2 and 40 <= latest_rsi <= 70
            and trend in ["UP", "SIDEWAYS"] and rr >= 1.8
        ):
            status = "BSJP SIAP"
        elif score >= 60:
            status = "PANTAU"
        else:
            status = "TUNGGU"

        if latest_rsi > 75 or value < MIN_VALUE or volume.iloc[-1] < MIN_VOLUME or rr < 1.2 or gain_3d > 15:
            status = "TUNGGU"

        return {
            "Kode": ticker.replace(".JK", ""),
            "Harga": round(last_close, 0),
            "Chg %": round(change_pct, 2),
            "Volume": int(volume.iloc[-1]),
            "RVOL": round(rvol, 2),
            "Value": value,
            "RSI": round(latest_rsi, 1),
            "MACD": macd_status,
            "MA20 / MA50": "✅ / ✅" if last_close > ma20.iloc[-1] and last_close > ma50.iloc[-1] else "❌ / ❌",
            "Trend": trend,
            "Breakout": round(breakout, 0),
            "Support": round(support, 0),
            "Resistance": round(resistance, 0),
            "Score": int(score),
            "Status": status,
            "Entry Area": f"{entry_low:,.0f} - {entry_high:,.0f}",
            "SL": round(stop_loss, 0),
            "Target 1": round(target1, 0),
            "Target 2": round(target2, 0),
            "Risk/Reward": round(rr, 2),
            "Alasan Sinyal": ", ".join(reasons[:6])
        }

    except Exception:
        return None

@st.cache_data(ttl=300)
def scan_market(tickers, period, interval):
    rows = []
    for ticker in tickers:
        result = calculate_bsjp(ticker, period, interval)
        if result:
            rows.append(result)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values("Score", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", df.index + 1)
    return df

def color_status(v):
    if v == "BSJP KUAT":
        return "color:#22e57b;font-weight:900;"
    if v == "BSJP SIAP":
        return "color:#2d95ff;font-weight:900;"
    if v == "PANTAU":
        return "color:#ffc928;font-weight:900;"
    if v == "TUNGGU":
        return "color:#ff5050;font-weight:900;"
    return ""

def color_change(v):
    return "color:#22e57b;font-weight:900;" if float(v) > 0 else "color:#ff5050;font-weight:900;"

def color_score(v):
    if v >= 80:
        return "color:#22e57b;font-weight:900;"
    if v >= 70:
        return "color:#2d95ff;font-weight:900;"
    if v >= 60:
        return "color:#ffc928;font-weight:900;"
    return "color:#ff5050;font-weight:900;"

def color_macd(v):
    return "color:#22e57b;font-weight:900;" if v == "Bullish" else "color:#ff5050;font-weight:900;"

def style_table(data):
    display = data.copy()

    for c in ["Harga", "Breakout", "Support", "Resistance", "SL", "Target 1", "Target 2"]:
        display[c] = display[c].apply(lambda x: f"{x:,.0f}")

    display["Volume"] = display["Volume"].apply(lambda x: f"{x:,.0f}")
    display["Value"] = display["Value"].apply(rupiah_short)
    display["Risk/Reward"] = display["Risk/Reward"].apply(lambda x: f"1 : {x:.2f}")

    return (
        display.style
        .map(color_status, subset=["Status"])
        .map(color_change, subset=["Chg %"])
        .map(color_score, subset=["Score"])
        .map(color_macd, subset=["MACD"])
        .set_properties(**{
            "background-color": "#081626",
            "color": "#dce7f7",
            "border-color": "#1c3c5c",
            "font-size": "13px"
        })
        .set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#0e2238"),
                ("color", "#ffffff"),
                ("font-weight", "900"),
                ("border", "1px solid #1c3c5c")
            ]},
            {"selector": "td", "props": [
                ("border", "1px solid #1c3c5c")
            ]}
        ])
    )

# =========================
# HEADER
# =========================
now = datetime.now(ZoneInfo("Asia/Jakarta"))
market_open = time(9, 0) <= now.time() <= time(16, 15) and now.weekday() < 5
market_text = "Market Open" if market_open else "Market Closed"

st.markdown(f"""
<div class="top-header">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
            <span class="title-main">DASHBOARD BSJP SCREENER</span>
            &nbsp;&nbsp;
            <span class="{'market-green' if market_open else 'market-red'}">● {market_text}</span>
        </div>
        <div class="gray">
            📅 {now.strftime('%A, %d %B %Y')} &nbsp; | &nbsp; {now.strftime('%H:%M')} WIB
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.write("")

# =========================
# TELEGRAM TEST
# =========================
if test_telegram:
    ok, msg = send_telegram_message(
        bot_token,
        chat_id,
        "✅ <b>Test Telegram Berhasil</b>\n\nBot BSJP Screener sudah terhubung."
    )
    if ok:
        st.sidebar.success(msg)
    else:
        st.sidebar.error(msg)

# =========================
# SCAN DATA
# =========================
with st.spinner("Sedang scan saham IDX..."):
    df = scan_market(watchlist, period, interval)

if df.empty:
    st.error("Data belum tersedia. Coba refresh atau kurangi watchlist.")
    st.stop()

filtered = df.copy()
filtered = filtered[filtered["Harga"] <= max_price]

strong_count_all = int((filtered["Status"] == "BSJP KUAT").sum())
ready_count_all = int((filtered["Status"] == "BSJP SIAP").sum())
watch_count_all = int((filtered["Status"] == "PANTAU").sum())

if strong_count_all >= 5:
    mood = "BULLISH"
    mood_class = "green"
elif strong_count_all + ready_count_all >= 5:
    mood = "NETRAL"
    mood_class = "yellow"
else:
    mood = "SELEKTIF"
    mood_class = "blue"

# =========================
# SUMMARY CARDS
# =========================
c1, c2, c3, c4, c5 = st.columns(5)

cards = [
    ("TOTAL SAHAM DISCAN", len(df), "📈", "blue"),
    ("BSJP KUAT", strong_count_all, "🎯", "green"),
    ("KANDIDAT ENTRY", strong_count_all + ready_count_all, "🚀", "blue"),
    ("SAHAM PANTAU", watch_count_all, "👁️", "yellow"),
    ("MARKET MOOD", mood, "🐂", mood_class),
]

for col, (title, value, icon, color) in zip([c1, c2, c3, c4, c5], cards):
    with col:
        st.markdown(f"""
        <div class="card">
            <div style="display:flex;justify-content:space-between;">
                <div>
                    <div class="metric-title">{title}</div>
                    <div class="metric-value {color}">{value}</div>
                </div>
                <div style="font-size:34px;">{icon}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# =========================
# FILTER BAR
# =========================
st.markdown('<div class="filter-box">', unsafe_allow_html=True)
f1, f2, f3, f4, f5, f6 = st.columns([1, 1, 1, 1, 2, 1])

with f1:
    price_filter = st.selectbox("Filter Harga", ["Semua Harga", "< 1000", "< 500"])
with f2:
    max_price_top = st.number_input("Harga Maksimal", value=int(max_price), step=50)
with f3:
    status_filter = st.selectbox("Tampilkan", ["Semua", "BSJP KUAT", "BSJP SIAP", "PANTAU", "TUNGGU"])
with f4:
    only_best = st.toggle("Kandidat Terbaik", value=False)
with f5:
    search = st.text_input("Cari kode / nama emiten...", placeholder="Contoh: BBCA / GOTO")
with f6:
    reset_filter = st.button("Reset Filter")

st.markdown('</div>', unsafe_allow_html=True)

if price_filter == "< 1000":
    filtered = filtered[filtered["Harga"] < 1000]
elif price_filter == "< 500":
    filtered = filtered[filtered["Harga"] < 500]

filtered = filtered[filtered["Harga"] <= max_price_top]

if status_filter != "Semua":
    filtered = filtered[filtered["Status"] == status_filter]

if only_best:
    filtered = filtered[filtered["Status"].isin(["BSJP KUAT", "BSJP SIAP"])]

if search:
    filtered = filtered[filtered["Kode"].str.contains(search.upper(), na=False)]

filtered = filtered.head(int(max_result))

st.write("")

# =========================
# TABLE
# =========================
st.markdown("### 🏆 RANKING BSJP")

if filtered.empty:
    st.warning("Tidak ada saham yang lolos filter.")
    st.stop()

st.dataframe(
    style_table(filtered),
    use_container_width=True,
    height=520
)

st.caption(f"Menampilkan 1 - {len(filtered)} dari {len(df)} saham")

# =========================
# TELEGRAM ALERT
# =========================
st.markdown("### 📲 Alert Telegram")

if telegram_enabled:
    if st.button("Kirim Alert Kandidat BSJP"):
        if send_only_strong:
            alert_df = filtered[filtered["Status"] == "BSJP KUAT"]
        else:
            alert_df = filtered[filtered["Status"].isin(["BSJP KUAT", "BSJP SIAP"])]

        alert_df = alert_df.head(int(telegram_top_n))

        if alert_df.empty:
            st.warning("Tidak ada kandidat yang layak dikirim.")
        else:
            lines = [
                "🚀 <b>ALERT BSJP SCREENER</b>",
                f"Update: {now.strftime('%d/%m/%Y %H:%M:%S')} WIB",
                ""
            ]

            for _, r in alert_df.iterrows():
                lines.append(
                    f"📌 <b>{r['Kode']}</b> | {r['Status']}\n"
                    f"Harga: {r['Harga']:,.0f}\n"
                    f"Score: {r['Score']}/100\n"
                    f"RSI: {r['RSI']} | RVOL: {r['RVOL']}\n"
                    f"Entry: {r['Entry Area']}\n"
                    f"SL: {r['SL']:,.0f}\n"
                    f"TP1: {r['Target 1']:,.0f} | TP2: {r['Target 2']:,.0f}\n"
                    f"RR: 1 : {r['Risk/Reward']:.2f}\n"
                    f"Alasan: {r['Alasan Sinyal']}\n"
                )

            ok, msg = send_telegram_message(bot_token, chat_id, "\n".join(lines))
            if ok:
                st.success("Alert berhasil dikirim ke Telegram.")
            else:
                st.error(f"Gagal kirim alert: {msg}")
else:
    st.info("Aktifkan Telegram dari sidebar untuk mengirim alert.")

# =========================
# DETAIL PANEL
# =========================
st.markdown("---")
st.markdown("### 🔎 DETAIL SAHAM TERPILIH")

selected_code = st.selectbox("Pilih saham", filtered["Kode"].tolist())
row = filtered[filtered["Kode"] == selected_code].iloc[0]

status_class = (
    "green" if row["Status"] == "BSJP KUAT"
    else "blue" if row["Status"] == "BSJP SIAP"
    else "yellow" if row["Status"] == "PANTAU"
    else "red"
)

left, mid, right = st.columns([1.1, 2.2, 1.3])

with left:
    st.markdown(f"""
    <div class="card-small">
        <h2>{row['Kode']} ⭐</h2>
        <h1>{row['Harga']:,.0f}</h1>
        <p class="{status_class}">{row['Status']}</p>
        <hr>
        <p>Value: <b>{rupiah_short(row['Value'])}</b></p>
        <p>Volume: <b>{row['Volume']:,.0f}</b></p>
        <p>RVOL: <b>{row['RVOL']}</b></p>
        <p>RSI: <b>{row['RSI']}</b></p>
        <p>Trend: <b>{row['Trend']}</b></p>
    </div>
    """, unsafe_allow_html=True)

with mid:
    st.markdown(f"""
    <div class="card-small">
        <h3>📊 ANALISA TEKNIKAL</h3>
        <p><b>Alasan Sinyal:</b></p>
        <p>{row['Alasan Sinyal']}</p>
        <hr>
        <p>MACD: <b>{row['MACD']}</b></p>
        <p>MA20 / MA50: <b>{row['MA20 / MA50']}</b></p>
        <p>Breakout: <b>{row['Breakout']:,.0f}</b></p>
        <p>Support: <b>{row['Support']:,.0f}</b></p>
        <p>Resistance: <b>{row['Resistance']:,.0f}</b></p>
        <p class="gray">Catatan: gunakan chart broker/TradingView untuk konfirmasi candle real-time sebelum entry.</p>
    </div>
    """, unsafe_allow_html=True)

success_rate = min(max(int(row["Score"]), 35), 90)

with right:
    st.markdown(f"""
    <div class="card-small">
        <h3>🎯 STRATEGI</h3>
        <p>Entry Area: <b>{row['Entry Area']}</b></p>
        <p>Stop Loss: <b>{row['SL']:,.0f}</b></p>
        <p>Target 1: <b>{row['Target 1']:,.0f}</b></p>
        <p>Target 2: <b>{row['Target 2']:,.0f}</b></p>
        <p>Risk / Reward: <b class="green">1 : {row['Risk/Reward']:.2f}</b></p>
        <hr>
        <h1 class="green">{success_rate}%</h1>
        <p>Peluang sukses estimasi</p>
    </div>
    """, unsafe_allow_html=True)

st.caption("Disclaimer: Screener ini hanya alat bantu analisa, bukan ajakan beli/jual.")
