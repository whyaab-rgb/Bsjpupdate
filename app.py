# app.py
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Dashboard BSJP Screener",
    page_icon="📈",
    layout="wide"
)

# =========================
# CONFIG
# =========================
IDX_TICKERS = [
    "AALI.JK","ACES.JK","ADHI.JK","ADMR.JK","ADRO.JK","AKRA.JK","AMMN.JK","ANTM.JK",
    "ARTO.JK","ASII.JK","BBCA.JK","BBNI.JK","BBRI.JK","BBTN.JK","BMRI.JK","BRIS.JK",
    "BRPT.JK","BUKA.JK","CPIN.JK","CTRA.JK","ESSA.JK","EXCL.JK","GOTO.JK","HRUM.JK",
    "ICBP.JK","INCO.JK","INDF.JK","INKP.JK","INTP.JK","ISAT.JK","ITMG.JK","JPFA.JK",
    "JSMR.JK","KLBF.JK","MDKA.JK","MEDC.JK","PGAS.JK","PTBA.JK","SMGR.JK","TLKM.JK",
    "TOWR.JK","UNTR.JK","UNVR.JK"
]

MIN_VALUE = 1_000_000_000
MIN_VOLUME = 500_000

# =========================
# CSS
# =========================
st.markdown("""
<style>
.stApp {
    background: #07111f;
    color: #e8eef7;
}
[data-testid="stSidebar"] {
    display: none;
}
.block-container {
    padding-top: 1.2rem;
    max-width: 1500px;
}
.card {
    background: linear-gradient(145deg, #0d1b2e, #0a1626);
    border: 1px solid #1c3554;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 8px 24px rgba(0,0,0,.25);
}
.big-title {
    font-size: 28px;
    font-weight: 800;
    color: #f4f8ff;
}
.green { color: #20e37a; font-weight: 700; }
.blue { color: #2196ff; font-weight: 700; }
.yellow { color: #ffc928; font-weight: 700; }
.red { color: #ff4b4b; font-weight: 700; }
.metric-title {
    font-size: 13px;
    color: #a9b8cc;
}
.metric-value {
    font-size: 30px;
    font-weight: 800;
}
hr {
    border: 1px solid #152840;
}
</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR TELEGRAM
# =========================
with st.sidebar:
    st.markdown("## 🤖 Bot Telegram")
    st.caption("Kirim alert BSJP KUAT / BSJP SIAP ke Telegram.")

    telegram_enabled = st.toggle("Aktifkan Telegram", value=False)

    bot_token = st.text_input(
        "Bot Token",
        type="password",
        placeholder="Contoh: 123456:ABC..."
    )

    chat_id = st.text_input(
        "Chat ID",
        placeholder="Contoh: 123456789"
    )

    send_only_strong = st.checkbox(
        "Kirim hanya BSJP KUAT",
        value=True
    )

    test_telegram = st.button("Test Kirim Telegram")
  
# =========================
# INDICATORS
# =========================
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

def calculate_bsjp(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=False)

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

        score = 0
        reasons = []

        # A. Trend & Struktur Harga — 25
        if last_close > ma20.iloc[-1] and last_close > ma50.iloc[-1]:
            score += 10
            reasons.append("harga di atas MA20 & MA50")
        if ma20.iloc[-1] > ma50.iloc[-1]:
            score += 5
            reasons.append("MA20 di atas MA50")
        if low.iloc[-1] >= low.tail(10).min():
            score += 5
            reasons.append("tidak membuat low baru")
        if resistance > 0 and 0 <= ((resistance - last_close) / last_close) <= 0.03:
            score += 5
            reasons.append("dekat breakout")

        # B. Volume & Akumulasi — 25
        if rvol > 1.5:
            score += 8
            reasons.append("RVOL tinggi")
        if volume.iloc[-1] > avg_vol20.iloc[-1]:
            score += 6
            reasons.append("volume di atas rata-rata")
        if value >= MIN_VALUE:
            score += 5
            reasons.append("value likuid")
        if last_close > prev_close and volume.iloc[-1] > volume.iloc[-2]:
            score += 6
            reasons.append("candle naik + volume naik")

        # C. Momentum — 20
        latest_rsi = float(rsi_val.iloc[-1])
        prev_rsi = float(rsi_val.iloc[-2])
        latest_hist = float(macd_hist.iloc[-1])
        prev_hist = float(macd_hist.iloc[-2])

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

        # D. Risk Reward — 20
        if rr >= 2:
            score += 8
            reasons.append("RR minimal 1:2")
        if abs(last_close - support) / last_close <= 0.08:
            score += 4
            reasons.append("support dekat")
        if abs(last_close - support) / last_close <= 0.10:
            score += 4
            reasons.append("entry tidak jauh dari support")
        if target1 > last_close:
            score += 4
            reasons.append("target realistis")

        # E. Anti-FOMO — 10
        gain_3d = ((last_close - close.iloc[-4]) / close.iloc[-4]) * 100 if len(close) > 4 else 0
        if gain_3d <= 8:
            score += 4
            reasons.append("tidak FOMO")
        if latest_rsi < 75:
            score += 3
            reasons.append("RSI tidak overbought")
        if abs(last_close - ma20.iloc[-1]) / last_close <= 0.08:
            score += 3
            reasons.append("harga tidak jauh dari MA20")

        score = min(score, 100)

        trend = "UP" if last_close > ma20.iloc[-1] > ma50.iloc[-1] else "SIDEWAYS" if last_close >= ma50.iloc[-1] else "DOWN"
        macd_status = "Bullish" if macd_line.iloc[-1] > macd_signal.iloc[-1] else "Bearish"

        # Hard filter status
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
            "Change %": round(change_pct, 2),
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
            "Score BSJP": int(score),
            "Status": status,
            "Entry Area": f"{entry_low:,.0f} - {entry_high:,.0f}",
            "Stop Loss": round(stop_loss, 0),
            "Target 1": round(target1, 0),
            "Target 2": round(target2, 0),
            "Risk Reward": round(rr, 2),
            "Alasan Sinyal": ", ".join(reasons[:5])
        }

    except Exception:
        return None

@st.cache_data(ttl=300)
def scan_market(tickers):
    rows = []
    for ticker in tickers:
        result = calculate_bsjp(ticker)
        if result:
            rows.append(result)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values("Score BSJP", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", df.index + 1)
    return df
  
# =========================
# TELEGRAM
# =========================
def send_telegram_message(bot_token, chat_id, message):
    try:
        if not bot_token or not chat_id:
            return False, "Bot token / chat ID belum diisi."

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, data=payload, timeout=10)

        if response.status_code == 200:
            return True, "Berhasil kirim Telegram."
        return False, response.text

    except Exception as e:
        return False, str(e)

# =========================
# HEADER
# =========================
now = datetime.now(ZoneInfo("Asia/Jakarta"))
market_open = time(9, 0) <= now.time() <= time(16, 15) and now.weekday() < 5
market_status = "Market Open" if market_open else "Market Closed"

st.markdown(f"""
<div class="card">
    <div class="big-title">DASHBOARD BSJP SCREENER</div>
    <div style="margin-top:8px;">
        Status: <span class="{'green' if market_open else 'red'}">{market_status}</span>
        &nbsp; | &nbsp; Update: {now.strftime('%d %B %Y %H:%M:%S')} WIB
    </div>
</div>
""", unsafe_allow_html=True)

st.write("")

# =========================
# FILTER
# =========================
with st.container():
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.5, 1])

    with c1:
        max_price = st.number_input("Harga Maksimal", min_value=50, value=1000, step=50)

    with c2:
        status_filter = st.selectbox(
            "Status BSJP",
            ["SEMUA", "BSJP KUAT", "BSJP SIAP", "PANTAU", "TUNGGU"]
        )

    with c3:
        only_best = st.toggle("Hanya Kandidat Terbaik", value=False)

    with c4:
        search = st.text_input("Cari kode emiten", placeholder="Contoh: BBRI, TLKM, ANTM")

    with c5:
        refresh = st.button("Refresh Data")

# =========================
# DATA
# =========================
with st.spinner("Sedang scan saham IDX..."):
    df = scan_market(IDX_TICKERS)

if df.empty:
    st.error("Data belum tersedia. Coba refresh beberapa saat lagi.")
    st.stop()

filtered = df.copy()
filtered = filtered[filtered["Harga"] <= max_price]

if status_filter != "SEMUA":
    filtered = filtered[filtered["Status"] == status_filter]

if only_best:
    filtered = filtered[filtered["Status"].isin(["BSJP KUAT", "BSJP SIAP"])]

if search:
    filtered = filtered[filtered["Kode"].str.contains(search.upper(), na=False)]

# =========================
# TELEGRAM
# =========================
def send_telegram_message(bot_token, chat_id, message):
    try:
        if not bot_token or not chat_id:
            return False, "Bot token / chat ID belum diisi."

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, data=payload, timeout=10)

        if response.status_code == 200:
            return True, "Berhasil kirim Telegram."
        return False, response.text

    except Exception as e:
        return False, str(e)

# =========================
# MARKET MOOD
# =========================
strong_count = int((filtered["Status"] == "BSJP KUAT").sum())
ready_count = int((filtered["Status"] == "BSJP SIAP").sum())
watch_count = int((filtered["Status"] == "PANTAU").sum())

if strong_count >= 5:
    mood = "BULLISH"
    mood_class = "green"
elif strong_count + ready_count >= 5:
    mood = "NETRAL POSITIF"
    mood_class = "yellow"
else:
    mood = "SELEKTIF"
    mood_class = "blue"

# =========================
# SUMMARY CARDS
# =========================
m1, m2, m3, m4, m5 = st.columns(5)

cards = [
    ("Total Saham Discan", len(df), "blue"),
    ("BSJP Kuat", strong_count, "green"),
    ("Kandidat Entry", strong_count + ready_count, "blue"),
    ("Saham Pantau", watch_count, "yellow"),
    ("Market Mood", mood, mood_class),
]

for col, item in zip([m1, m2, m3, m4, m5], cards):
    title, value, color = item
    with col:
        st.markdown(f"""
        <div class="card">
            <div class="metric-title">{title}</div>
            <div class="metric-value {color}">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# =========================
# TABLE STYLE
# =========================
def color_status(v):
    if v == "BSJP KUAT":
        return "color:#20e37a;font-weight:800;"
    if v == "BSJP SIAP":
        return "color:#2196ff;font-weight:800;"
    if v == "PANTAU":
        return "color:#ffc928;font-weight:800;"
    if v == "TUNGGU":
        return "color:#ff4b4b;font-weight:800;"
    return ""

def color_change(v):
    return "color:#20e37a;font-weight:700;" if v > 0 else "color:#ff4b4b;font-weight:700;"

def color_score(v):
    if v >= 80:
        return "color:#20e37a;font-weight:800;"
    if v >= 70:
        return "color:#2196ff;font-weight:800;"
    if v >= 60:
        return "color:#ffc928;font-weight:800;"
    return "color:#ff4b4b;font-weight:800;"

def color_macd(v):
    return "color:#20e37a;font-weight:700;" if v == "Bullish" else "color:#ff4b4b;font-weight:700;"

def style_table(data):
    display = data.copy()
    display["Volume"] = display["Volume"].apply(lambda x: f"{x:,.0f}")
    display["Value"] = display["Value"].apply(rupiah_short)
    display["Harga"] = display["Harga"].apply(lambda x: f"{x:,.0f}")
    display["Breakout"] = display["Breakout"].apply(lambda x: f"{x:,.0f}")
    display["Support"] = display["Support"].apply(lambda x: f"{x:,.0f}")
    display["Resistance"] = display["Resistance"].apply(lambda x: f"{x:,.0f}")
    display["Stop Loss"] = display["Stop Loss"].apply(lambda x: f"{x:,.0f}")
    display["Target 1"] = display["Target 1"].apply(lambda x: f"{x:,.0f}")
    display["Target 2"] = display["Target 2"].apply(lambda x: f"{x:,.0f}")
    display["Risk Reward"] = display["Risk Reward"].apply(lambda x: f"1 : {x:.2f}")

    return (
        display.style
        .map(color_status, subset=["Status"])
        .map(color_change, subset=["Change %"])
        .map(color_score, subset=["Score BSJP"])
        .map(color_macd, subset=["MACD"])
        .set_properties(**{
            "background-color": "#0b1728",
            "color": "#dce7f7",
            "border-color": "#223a5a",
            "font-size": "13px"
        })
        .set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#101f34"),
                ("color", "#ffffff"),
                ("font-weight", "800"),
                ("border", "1px solid #223a5a")
            ]},
            {"selector": "td", "props": [
                ("border", "1px solid #223a5a")
            ]}
        ])
    )

st.markdown("### 🏆 Ranking BSJP Screener")

if filtered.empty:
    st.warning("Tidak ada saham yang lolos filter.")
    st.stop()

st.dataframe(
    style_table(filtered),
    use_container_width=True,
    height=560
)

# =========================
# DETAIL SAHAM
# =========================
st.markdown("---")
st.markdown("### 🔎 Detail Saham Terpilih")

selected_code = st.selectbox(
    "Pilih saham untuk detail",
    filtered["Kode"].tolist()
)

row = filtered[filtered["Kode"] == selected_code].iloc[0]

d1, d2, d3 = st.columns([1, 1, 1])

with d1:
    st.markdown(f"""
    <div class="card">
        <h3>{row['Kode']}</h3>
        <h2>{row['Harga']:,.0f}</h2>
        <p>Status: <span class="{ 'green' if row['Status']=='BSJP KUAT' else 'blue' if row['Status']=='BSJP SIAP' else 'yellow' if row['Status']=='PANTAU' else 'red'}">{row['Status']}</span></p>
        <p>Score BSJP: <b>{row['Score BSJP']}/100</b></p>
        <p>Trend: <b>{row['Trend']}</b></p>
        <p>MACD: <b>{row['MACD']}</b></p>
        <p>RSI: <b>{row['RSI']}</b></p>
    </div>
    """, unsafe_allow_html=True)

with d2:
    st.markdown(f"""
    <div class="card">
        <h3>Entry Plan</h3>
        <p>Entry Area: <b>{row['Entry Area']}</b></p>
        <p>Stop Loss: <b>{row['Stop Loss']:,.0f}</b></p>
        <p>Target 1: <b>{row['Target 1']:,.0f}</b></p>
        <p>Target 2: <b>{row['Target 2']:,.0f}</b></p>
        <p>Risk Reward: <b>1 : {row['Risk Reward']:.2f}</b></p>
    </div>
    """, unsafe_allow_html=True)

success_rate = min(max(row["Score BSJP"], 35), 90)

with d3:
    st.markdown(f"""
    <div class="card">
        <h3>Ringkasan Analisa</h3>
        <p>{row['Alasan Sinyal']}</p>
        <p>Support: <b>{row['Support']:,.0f}</b></p>
        <p>Resistance: <b>{row['Resistance']:,.0f}</b></p>
        <p>Peluang Sukses Estimasi: <b class="green">{success_rate}%</b></p>
        <p class="yellow">Catatan: tetap tunggu konfirmasi candle dan volume sebelum entry.</p>
    </div>
    """, unsafe_allow_html=True)
    
# =========================
# KIRIM ALERT TELEGRAM
# =========================
st.markdown("### 📲 Kirim Alert Telegram")

if telegram_enabled:
    if st.button("Kirim Alert Kandidat BSJP"):
        if send_only_strong:
            alert_df = filtered[filtered["Status"] == "BSJP KUAT"]
        else:
            alert_df = filtered[filtered["Status"].isin(["BSJP KUAT", "BSJP SIAP"])]

        if alert_df.empty:
            st.warning("Tidak ada kandidat yang layak dikirim.")
        else:
            lines = [
                "🚀 <b>ALERT BSJP SCREENER</b>",
                f"Update: {now.strftime('%d/%m/%Y %H:%M:%S')} WIB",
                ""
            ]

            for _, r in alert_df.head(10).iterrows():
                lines.append(
                    f"📌 <b>{r['Kode']}</b> | {r['Status']}\n"
                    f"Harga: {r['Harga']:,.0f}\n"
                    f"Score: {r['Score BSJP']}/100\n"
                    f"RSI: {r['RSI']} | RVOL: {r['RVOL']}\n"
                    f"Entry: {r['Entry Area']}\n"
                    f"SL: {r['Stop Loss']:,.0f}\n"
                    f"TP1: {r['Target 1']:,.0f} | TP2: {r['Target 2']:,.0f}\n"
                    f"RR: 1 : {r['Risk Reward']:.2f}\n"
                    f"Alasan: {r['Alasan Sinyal']}\n"
                )

            message = "\n".join(lines)

            ok, msg = send_telegram_message(bot_token, chat_id, message)

            if ok:
                st.success("Alert berhasil dikirim ke Telegram.")
            else:
                st.error(f"Gagal kirim alert: {msg}")
else:
    st.info("Aktifkan Telegram dari sidebar untuk mengirim alert.")
    
st.caption("Disclaimer: Screener ini hanya alat bantu analisa, bukan ajakan beli/jual, tetap sabar dan selalu dyor di situasi gonjang ganjing market.")
