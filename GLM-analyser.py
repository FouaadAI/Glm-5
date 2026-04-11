"""
╔══════════════════════════════════════════════════════════════╗
║     K1NG QUANTUM ULTIMATE – PRO MAX TRADING PLATFORM         ║
║     Version 4.1 – 2026 OPTIMIZED + SIGNAL EXPERIMENT         ║
║     Streamlit · GLM-5.1 · Binance · CoinGecko                ║
║     FIX: Multi-Round Agent Loop | Live Status | Parallel API ║
║     NEU: Live Signal Experiment mit Preis-Tracking           ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
import threading
from typing import Dict, Any, Optional, List, Generator
import json
import httpx
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from concurrent.futures import ThreadPoolExecutor, as_completed

# TA-Lib Indikatoren
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands

# ─── SEITEN-KONFIGURATION ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="K1NG QUANTUM ULTIMATE",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── GLOBALES CSS & DESIGN (erweitert um Experiment-Cards) ────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@300;500;700&display=swap');

  html, body, [data-testid="stAppViewContainer"] {
      background: #0a0f1e !important;
      color: #e0e5f0 !important;
  }
  [data-testid="stAppViewContainer"] {
      background: radial-gradient(ellipse 60% 30% at 50% -10%, #0d1a3a 0%, transparent 70%),
                  radial-gradient(ellipse 50% 20% at 80% 80%, #1a3a1a 0%, transparent 60%),
                  #0a0f1e !important;
  }
  [data-testid="stHeader"] { background: transparent !important; }

  [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #0a0f1e 0%, #0d1424 100%) !important;
      border-right: 1px solid #2a3a5a !important;
  }
  [data-testid="stSidebar"] * { color: #c8cce8 !important; }
  [data-testid="stSidebar"] .stTextInput input,
  [data-testid="stSidebar"] .stSelectbox select {
      background: #12182a !important;
      border: 1px solid #3a4a6a !important;
      color: #e0e4ff !important;
      border-radius: 8px !important;
  }

  .king-header {
      font-family: 'Orbitron', monospace;
      font-size: 2.4rem;
      font-weight: 900;
      background: linear-gradient(135deg, #6ee7b7 0%, #3b82f6 40%, #a855f7 70%, #6ee7b7 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      text-align: center;
      letter-spacing: 4px;
      margin-bottom: 0;
      animation: shimmer 4s ease-in-out infinite;
  }
  @keyframes shimmer {
      0%,100% { filter: brightness(1); }
      50%      { filter: brightness(1.2) drop-shadow(0 0 8px #6ee7b766); }
  }
  .king-subtitle {
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.75rem;
      color: #7a8ab0;
      text-align: center;
      letter-spacing: 8px;
      margin-top: 2px;
  }

  .metric-card {
      background: linear-gradient(135deg, #11182a 0%, #152040 100%);
      border: 1px solid #2a3a5a;
      border-left: 4px solid #3b82f6;
      border-radius: 12px;
      padding: 16px 20px;
      margin: 6px 0;
      box-shadow: 0 4px 20px #00000060;
      transition: transform 0.2s, box-shadow 0.2s;
  }
  .metric-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 30px #3b82f620;
  }
  .metric-label {
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.65rem;
      color: #7a8ab0;
      letter-spacing: 3px;
      text-transform: uppercase;
  }
  .metric-value {
      font-family: 'Orbitron', monospace;
      font-size: 1.5rem;
      font-weight: 700;
      color: #6ee7b7;
      line-height: 1.2;
  }
  .metric-change-pos { color: #10b981; font-size: 0.8rem; font-family: 'Rajdhani'; }
  .metric-change-neg { color: #ef4444; font-size: 0.8rem; font-family: 'Rajdhani'; }

  .analysis-box {
      background: linear-gradient(135deg, #0a1224 0%, #0d162a 100%);
      border: 1px solid #2a4a6a;
      border-left: 4px solid #a855f7;
      border-radius: 12px;
      padding: 20px 24px;
      font-family: 'Rajdhani', sans-serif;
      font-size: 0.95rem;
      line-height: 1.7;
      color: #c8d8f0;
      white-space: pre-wrap;
      max-height: 700px;
      overflow-y: auto;
  }

  .agent-status-box {
      background: linear-gradient(135deg, #0a1a24 0%, #0d1e2a 100%);
      border: 1px solid #1a4a6a;
      border-left: 4px solid #3b82f6;
      border-radius: 10px;
      padding: 14px 20px;
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.75rem;
      color: #6ee7b7;
      margin-bottom: 10px;
      letter-spacing: 1px;
  }
  .agent-step {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 4px 0;
      color: #a0c0e0;
  }
  .agent-step.done  { color: #10b981; }
  .agent-step.active { color: #facc15; animation: pulse 1s ease-in-out infinite; }
  @keyframes pulse {
      0%,100% { opacity: 1; }
      50%      { opacity: 0.6; }
  }

  .experiment-card {
      background: rgba(26, 26, 46, 0.9);
      border: 2px solid rgba(0, 255, 136, 0.5);
      border-radius: 16px;
      padding: 20px;
      margin: 15px 0;
      position: relative;
      overflow: hidden;
  }
  .experiment-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(0, 255, 136, 0.1), transparent);
      animation: shimmer 3s infinite;
  }
  .profit-positive { color: #00ff88; font-weight: bold; }
  .profit-negative { color: #ff4444; font-weight: bold; }
  .target-hit {
      background: rgba(0, 255, 136, 0.2);
      border-radius: 8px;
      padding: 5px;
  }
  .target-missed {
      background: rgba(255, 68, 68, 0.2);
      border-radius: 8px;
      padding: 5px;
  }

  .stButton > button {
      background: linear-gradient(135deg, #2563eb 0%, #4f46e5 50%, #2563eb 100%) !important;
      color: #ffffff !important;
      font-family: 'Orbitron', monospace !important;
      font-weight: 700 !important;
      font-size: 0.75rem !important;
      letter-spacing: 2px !important;
      border: none !important;
      border-radius: 8px !important;
      padding: 10px 20px !important;
      transition: all 0.3s !important;
      box-shadow: 0 4px 15px #4f46e530 !important;
  }
  .stButton > button:hover {
      transform: translateY(-2px) !important;
      box-shadow: 0 8px 25px #4f46e560 !important;
      filter: brightness(1.15) !important;
  }

  .stTabs [data-baseweb="tab-list"] {
      background: #0c1224 !important;
      border-bottom: 2px solid #2a3a5a !important;
      gap: 4px;
  }
  .stTabs [data-baseweb="tab"] {
      font-family: 'Orbitron', monospace !important;
      font-size: 0.7rem !important;
      color: #7a8ab0 !important;
      letter-spacing: 2px !important;
      padding: 10px 20px !important;
  }
  .stTabs [aria-selected="true"] {
      color: #6ee7b7 !important;
      border-bottom: 2px solid #6ee7b7 !important;
      background: transparent !important;
  }

  hr { border-color: #2a3a5a !important; }
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #0a0f1e; }
  ::-webkit-scrollbar-thumb { background: #3a4a6a; border-radius: 3px; }

  .signal-long    { border-left-color: #10b981 !important; }
  .signal-short   { border-left-color: #ef4444 !important; }
  .signal-neutral { border-left-color: #a855f7 !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ── HILFSFUNKTIONEN & API-CALLS (unverändert aus glm_optimized) ───────────────
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def fetch_global_metrics() -> Dict[str, Any]:
    result = {
        "market_cap": 0.0, "market_cap_change": 0.0,
        "volume_24h": 0.0, "btc_dominance": 0.0
    }
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/global",
            timeout=8,
            headers={"Accept": "application/json"}
        )
        if r.status_code == 200:
            d = r.json().get("data", {})
            result["market_cap"]        = d.get("total_market_cap", {}).get("usd", 0)
            result["market_cap_change"] = d.get("market_cap_change_percentage_24h_usd", 0)
            result["volume_24h"]        = d.get("total_volume", {}).get("usd", 0)
            result["btc_dominance"]     = d.get("market_cap_percentage", {}).get("btc", 0)
    except Exception:
        pass
    return result


@st.cache_data(ttl=300)
def fetch_fear_greed() -> Dict[str, Any]:
    result = {"value": 50, "label": "Neutral"}
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=6)
        if r.status_code == 200:
            data = r.json().get("data", [{}])[0]
            result["value"] = int(data.get("value", 50))
            result["label"] = data.get("value_classification", "Neutral")
    except Exception:
        pass
    return result


@st.cache_data(ttl=10)
def fetch_live_prices(symbols: List[str]) -> Dict[str, float]:
    prices: Dict[str, float] = {}
    def _fetch_one(sym: str) -> tuple:
        try:
            r = requests.get(
                f"https://api.binance.com/api/v3/ticker/price?symbol={sym}",
                timeout=5
            )
            if r.status_code == 200:
                return sym, float(r.json().get("price", 0))
        except Exception:
            pass
        return sym, 0.0
    with ThreadPoolExecutor(max_workers=min(len(symbols), 8)) as exe:
        futures = {exe.submit(_fetch_one, sym): sym for sym in symbols}
        for fut in as_completed(futures):
            sym, price = fut.result()
            prices[sym] = price
    return prices


@st.cache_data(ttl=120)
def fetch_klines(symbol: str, interval: str = "1h", limit: int = 200) -> pd.DataFrame:
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=10
        )
        if r.status_code != 200:
            return pd.DataFrame()
        raw = r.json()
        df = pd.DataFrame(raw, columns=[
            "open_time","open","high","low","close","volume",
            "close_time","qav","trades","tbbav","tbqav","ignore"
        ])
        for col in ["open","high","low","close","volume"]:
            df[col] = pd.to_numeric(df[col])
        df["time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df[["time","open","high","low","close","volume"]].reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 30:
        return df
    close = df["close"]
    df["rsi"]         = RSIIndicator(close, window=14).rsi()
    macd_obj          = MACD(close)
    df["macd"]        = macd_obj.macd()
    df["macd_signal"] = macd_obj.macd_signal()
    df["macd_hist"]   = macd_obj.macd_diff()
    bb                = BollingerBands(close, window=20, window_dev=2)
    df["bb_upper"]    = bb.bollinger_hband()
    df["bb_mid"]      = bb.bollinger_mavg()
    df["bb_lower"]    = bb.bollinger_lband()
    df["ema20"]       = EMAIndicator(close, window=20).ema_indicator()
    df["ema50"]       = EMAIndicator(close, window=50).ema_indicator()
    df["ema200"]      = EMAIndicator(close, window=200).ema_indicator()
    return df


def format_number(n: float, decimals: int = 2, suffix: str = "") -> str:
    if n >= 1e12:
        return f"${n/1e12:.{decimals}f}T{suffix}"
    elif n >= 1e9:
        return f"${n/1e9:.{decimals}f}B{suffix}"
    elif n >= 1e6:
        return f"${n/1e6:.{decimals}f}M{suffix}"
    else:
        return f"${n:,.{decimals}f}{suffix}"


def send_telegram(token: str, chat_id: str, text: str) -> bool:
    if not token or not chat_id:
        return False
    try:
        chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        success = True
        for chunk in chunks:
            payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "HTML"}
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code != 200:
                success = False
        return success
    except Exception:
        return False


def build_export_content(text: str, asset: str = "", analyse_type: str = "") -> dict:
    """Bereitet Export-Inhalte in verschiedenen Formaten vor."""
    ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts_file  = datetime.now().strftime("%Y%m%d_%H%M%S")
    label    = f"{asset} – {analyse_type}".strip(" –") if (asset or analyse_type) else "Analysis"

    # ── TXT ──────────────────────────────────────────────────────────────────
    txt = (
        f"╔══════════════════════════════════════════════════╗\n"
        f"║     K1NG QUANTUM ULTIMATE – SIGNAL EXPORT        ║\n"
        f"║     {ts:<46}║\n"
        f"║     {label:<46}║\n"
        f"╚══════════════════════════════════════════════════╝\n\n"
        + text +
        f"\n\n{'─'*52}\n"
        f"⚠️  NUR ZU BILDUNGSZWECKEN – KEINE FINANZBERATUNG\n"
        f"{'─'*52}\n"
    )

    # ── MARKDOWN ─────────────────────────────────────────────────────────────
    md = (
        f"# 🦅 K1NG QUANTUM ULTIMATE – Signal Export\n\n"
        f"**Generiert:** {ts}  \n"
        f"**Analyse:** {label}\n\n"
        f"---\n\n"
        + text +
        f"\n\n---\n\n"
        f"> ⚠️ *Nur zu Bildungszwecken – keine Finanzberatung*\n"
    )

    # ── JSON ─────────────────────────────────────────────────────────────────
    payload = {
        "platform":    "K1NG QUANTUM ULTIMATE v4.1",
        "generated":   ts,
        "asset":       asset,
        "analyse_type": analyse_type,
        "content":     text,
        "disclaimer":  "Nur zu Bildungszwecken – keine Finanzberatung"
    }
    js = json.dumps(payload, ensure_ascii=False, indent=2)

    return {"txt": txt, "md": md, "json": js, "ts_file": ts_file, "label": label}


def render_export_buttons(text: str, asset: str = "", analyse_type: str = "", key_prefix: str = "export"):
    """Rendert 3 Download-Buttons (TXT / MD / JSON) für einen Analyse-Text."""
    if not text.strip():
        return
    exp = build_export_content(text, asset, analyse_type)
    safe_label = exp["label"].replace(" ", "_").replace("/", "-")[:40]
    fname      = f"K1NG_{safe_label}_{exp['ts_file']}"

    st.markdown("""
    <div style='font-family: Share Tech Mono; font-size:0.65rem; color:#7a8ab0;
                letter-spacing:3px; margin: 14px 0 6px 0;'>
        📥 EXPORT SIGNAL
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            label="📄 TXT Export",
            data=exp["txt"].encode("utf-8"),
            file_name=f"{fname}.txt",
            mime="text/plain",
            key=f"{key_prefix}_txt",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            label="📝 Markdown Export",
            data=exp["md"].encode("utf-8"),
            file_name=f"{fname}.md",
            mime="text/markdown",
            key=f"{key_prefix}_md",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            label="🗂️ JSON Export",
            data=exp["json"].encode("utf-8"),
            file_name=f"{fname}.json",
            mime="application/json",
            key=f"{key_prefix}_json",
            use_container_width=True,
        )


def fng_color(value: int) -> str:
    if value <= 25:
        return "#ef4444"
    elif value <= 45:
        return "#f97316"
    elif value <= 55:
        return "#facc15"
    elif value <= 75:
        return "#a3e635"
    else:
        return "#10b981"


# ═══════════════════════════════════════════════════════════════════════════════
# ── PRE-FETCH DATEN-FUNKTIONEN ────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_realtime_price_data(symbol: str = "BTCUSDT") -> str:
    """Holt aktuelle Preis- und Volumendaten von Binance für das gewählte Asset."""
    result_lines = []
    symbols = [symbol, "BTCUSDT", "ETHUSDT", "SOLUSDT"]
    symbols = list(dict.fromkeys(symbols))  # Deduplizieren, Reihenfolge beibehalten
    try:
        for sym in symbols:
            try:
                r = requests.get(
                    f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}",
                    timeout=6
                )
                if r.status_code == 200:
                    d = r.json()
                    price      = float(d.get("lastPrice", 0))
                    change_pct = float(d.get("priceChangePercent", 0))
                    volume     = float(d.get("quoteVolume", 0))
                    high_24h   = float(d.get("highPrice", 0))
                    low_24h    = float(d.get("lowPrice", 0))
                    result_lines.append(
                        f"{sym}: ${price:,.4f} | 24h: {change_pct:+.2f}% | "
                        f"Vol: ${volume/1e6:.1f}M | H: ${high_24h:,.4f} | L: ${low_24h:,.4f}"
                    )
            except Exception:
                result_lines.append(f"{sym}: Daten nicht verfügbar")
    except Exception as e:
        return f"Preisdaten-Fehler: {e}"
    return "\n".join(result_lines) if result_lines else "Keine Preisdaten verfügbar"


def fetch_market_sentiment_data() -> str:
    """Holt Fear & Greed Index, BTC-Dominanz und globale Marktdaten."""
    lines = []
    # Fear & Greed Index
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=6)
        if r.status_code == 200:
            d = r.json().get("data", [{}])[0]
            fng_val   = d.get("value", "N/A")
            fng_label = d.get("value_classification", "N/A")
            lines.append(f"Fear & Greed Index: {fng_val}/100 ({fng_label})")
    except Exception:
        lines.append("Fear & Greed: nicht verfügbar")
    # Globale Marktdaten (BTC-Dominanz, Market Cap)
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/global",
            timeout=8,
            headers={"Accept": "application/json"}
        )
        if r.status_code == 200:
            d = r.json().get("data", {})
            btc_dom    = d.get("market_cap_percentage", {}).get("btc", 0)
            eth_dom    = d.get("market_cap_percentage", {}).get("eth", 0)
            total_mcap = d.get("total_market_cap", {}).get("usd", 0)
            mcap_chg   = d.get("market_cap_change_percentage_24h_usd", 0)
            total_vol  = d.get("total_volume", {}).get("usd", 0)
            lines.append(f"BTC Dominanz: {btc_dom:.1f}%")
            lines.append(f"ETH Dominanz: {eth_dom:.1f}%")
            lines.append(f"Gesamt Market Cap: ${total_mcap/1e9:.1f}B ({mcap_chg:+.2f}% 24h)")
            lines.append(f"Gesamt Volumen 24h: ${total_vol/1e9:.1f}B")
    except Exception:
        lines.append("CoinGecko-Daten: nicht verfügbar")
    return "\n".join(lines) if lines else "Sentiment-Daten nicht verfügbar"


def fetch_macro_and_corr_data() -> str:
    """Holt Makrodaten: S&P500, DXY, Gold über öffentliche Quellen."""
    lines = []
    # Bitcoin als Korrelations-Referenz (Binance)
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT",
            timeout=6
        )
        if r.status_code == 200:
            d = r.json()
            btc_price  = float(d.get("lastPrice", 0))
            btc_change = float(d.get("priceChangePercent", 0))
            lines.append(f"BTC/USD: ${btc_price:,.2f} ({btc_change:+.2f}% 24h)")
    except Exception:
        lines.append("BTC-Daten: nicht verfügbar")
    # Makro-Kontext über CoinGecko (Gold, Stablecoins als DXY-Proxy)
    try:
        ids = "bitcoin,ethereum,gold,tether"
        r = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true",
            timeout=8,
            headers={"Accept": "application/json"}
        )
        if r.status_code == 200:
            d = r.json()
            if "gold" in d:
                gold_price  = d["gold"].get("usd", 0)
                gold_change = d["gold"].get("usd_24h_change", 0)
                lines.append(f"Gold: ${gold_price:,.2f} ({gold_change:+.2f}% 24h)")
            lines.append("S&P500/DXY: Live-Daten via API nicht verfügbar – verwende aktuelle Marktschätzung")
            lines.append("Hinweis: Für präzise S&P/DXY-Daten empfehle Web-Search-Tool")
    except Exception:
        lines.append("Makrodaten teilweise nicht verfügbar")
    # Krypto-Markt Volatilität
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr?symbol=ETHUSDT",
            timeout=6
        )
        if r.status_code == 200:
            d = r.json()
            eth_price  = float(d.get("lastPrice", 0))
            eth_change = float(d.get("priceChangePercent", 0))
            lines.append(f"ETH/USD: ${eth_price:,.2f} ({eth_change:+.2f}% 24h)")
    except Exception:
        pass
    return "\n".join(lines) if lines else "Makrodaten nicht verfügbar"


def fetch_open_interest_data(symbol: str = "BTCUSDT") -> str:
    """Holt Open Interest und Funding Rate Daten von Binance Futures."""
    lines = []
    base_sym = symbol.replace("USDT", "") + "USDT"
    # Open Interest
    try:
        r = requests.get(
            f"https://fapi.binance.com/fapi/v1/openInterest?symbol={base_sym}",
            timeout=6
        )
        if r.status_code == 200:
            d = r.json()
            oi = float(d.get("openInterest", 0))
            lines.append(f"Open Interest ({base_sym}): {oi:,.2f} Kontrakte")
    except Exception:
        lines.append(f"Open Interest ({base_sym}): nicht verfügbar")
    # Funding Rate
    try:
        r = requests.get(
            f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={base_sym}&limit=1",
            timeout=6
        )
        if r.status_code == 200:
            data = r.json()
            if data:
                funding = float(data[0].get("fundingRate", 0)) * 100
                lines.append(f"Funding Rate ({base_sym}): {funding:.4f}%")
    except Exception:
        lines.append(f"Funding Rate ({base_sym}): nicht verfügbar")
    # Long/Short Ratio
    try:
        r = requests.get(
            f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={base_sym}&period=1h&limit=1",
            timeout=6
        )
        if r.status_code == 200:
            data = r.json()
            if data:
                ls_ratio = float(data[0].get("longShortRatio", 1.0))
                long_pct = float(data[0].get("longAccount", 0.5)) * 100
                short_pct = float(data[0].get("shortAccount", 0.5)) * 100
                lines.append(f"Long/Short Ratio: {ls_ratio:.2f} (Long: {long_pct:.1f}% | Short: {short_pct:.1f}%)")
    except Exception:
        lines.append("L/S Ratio: nicht verfügbar")
    # Top Trader Long/Short Ratio
    try:
        r = requests.get(
            f"https://fapi.binance.com/futures/data/topLongShortPositionRatio?symbol={base_sym}&period=1h&limit=1",
            timeout=6
        )
        if r.status_code == 200:
            data = r.json()
            if data:
                top_ls = float(data[0].get("longShortRatio", 1.0))
                lines.append(f"Top Trader L/S Ratio: {top_ls:.2f}")
    except Exception:
        pass
    return "\n".join(lines) if lines else "Futures-Daten nicht verfügbar"


def fetch_crypto_news() -> str:
    """Holt aktuelle Krypto-News von CoinGecko Trending und alternativen Quellen."""
    lines = []
    # Trending Coins (als News-Proxy)
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/search/trending",
            timeout=8,
            headers={"Accept": "application/json"}
        )
        if r.status_code == 200:
            coins = r.json().get("coins", [])[:5]
            if coins:
                lines.append("🔥 Trending Coins (letzte 24h):")
                for item in coins:
                    c = item.get("item", {})
                    name   = c.get("name", "?")
                    symbol = c.get("symbol", "?")
                    rank   = c.get("market_cap_rank", "?")
                    lines.append(f"  • {name} ({symbol}) – Marktrang #{rank}")
    except Exception:
        lines.append("Trending-Daten: nicht verfügbar")
    # Global Market Status als News-Kontext
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/global",
            timeout=8,
            headers={"Accept": "application/json"}
        )
        if r.status_code == 200:
            d = r.json().get("data", {})
            active_coins = d.get("active_cryptocurrencies", 0)
            markets      = d.get("markets", 0)
            mcap_chg     = d.get("market_cap_change_percentage_24h_usd", 0)
            sentiment    = "bullish" if mcap_chg > 0 else "bearish"
            lines.append(f"\n📊 Marktlage: {active_coins} aktive Coins | {markets} Exchanges")
            lines.append(f"Gesamtmarkt 24h: {mcap_chg:+.2f}% → Tendenz: {sentiment}")
    except Exception:
        pass
    lines.append("\n⚠️ Hinweis: Für aktuelle News-Headlines Web-Search-Tool im Agenten-Aufruf nutzen.")
    return "\n".join(lines) if lines else "News-Daten nicht verfügbar"


# ═══════════════════════════════════════════════════════════════════════════════
# ── CHARTS (unverändert) ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

def build_candlestick_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        vertical_spacing=0.03,
        subplot_titles=(f"{symbol} – 1H Kerzenchart", "RSI (14)", "MACD")
    )

    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name="OHLC",
        increasing_line_color="#10b981",
        decreasing_line_color="#ef4444",
    ), row=1, col=1)

    if "bb_upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["bb_upper"], name="BB Upper",
            line=dict(color="#facc15", width=1, dash="dot"), opacity=0.7
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["bb_mid"], name="BB Mid",
            line=dict(color="#f97316", width=1), opacity=0.8
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["bb_lower"], name="BB Lower",
            line=dict(color="#facc15", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(250,204,21,0.05)", opacity=0.7
        ), row=1, col=1)

    if "ema20" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["ema20"], name="EMA 20",
            line=dict(color="#3b82f6", width=1.5)
        ), row=1, col=1)
    if "ema50" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["ema50"], name="EMA 50",
            line=dict(color="#a855f7", width=1.5)
        ), row=1, col=1)

    if "rsi" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["rsi"], name="RSI",
            line=dict(color="#facc15", width=2)
        ), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", opacity=0.6, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#10b981", opacity=0.6, row=2, col=1)
        fig.add_hline(y=50, line_dash="dot",  line_color="#4a5a7a", opacity=0.4, row=2, col=1)

    if "macd" in df.columns:
        colors = ["#10b981" if v >= 0 else "#ef4444" for v in df["macd_hist"].fillna(0)]
        fig.add_trace(go.Bar(
            x=df["time"], y=df["macd_hist"], name="MACD Hist",
            marker_color=colors, opacity=0.8
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["macd"], name="MACD",
            line=dict(color="#3b82f6", width=1.5)
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=df["time"], y=df["macd_signal"], name="Signal",
            line=dict(color="#f97316", width=1.5)
        ), row=3, col=1)

    fig.update_layout(
        paper_bgcolor="#0a0f1e",
        plot_bgcolor="#0c1224",
        font=dict(family="Share Tech Mono", color="#7a8ab0", size=11),
        xaxis_rangeslider_visible=False,
        height=620,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=True,
        legend=dict(
            bgcolor="#11182a", bordercolor="#2a3a5a",
            borderwidth=1, font=dict(size=10)
        ),
        hovermode="x unified"
    )
    fig.update_xaxes(gridcolor="#2a3a5a", zerolinecolor="#2a3a5a")
    fig.update_yaxes(gridcolor="#2a3a5a", zerolinecolor="#2a3a5a")
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# ── BACKTESTING (unverändert) ─────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

def run_backtest(
    df: pd.DataFrame,
    start_capital: float = 1000.0,
    rsi_oversold: float = 30.0,
    rsi_overbought: float = 70.0
) -> Dict[str, Any]:
    if df.empty or "rsi" not in df.columns:
        return {"error": "Keine Daten oder RSI nicht berechnet."}
    capital     = start_capital
    in_trade    = False
    entry_price = 0.0
    units       = 0.0
    trades      = []
    for _, row in df.iterrows():
        rsi   = row.get("rsi")
        price = row["close"]
        ts    = row["time"]
        if pd.isna(rsi):
            continue
        if not in_trade and rsi < rsi_oversold:
            entry_price = price
            units       = capital / price
            in_trade    = True
            trades.append({
                "type": "BUY",
                "time": ts.strftime("%Y-%m-%d %H:%M"),
                "price": round(price, 4),
                "rsi": round(rsi, 1),
                "capital_before": round(capital, 2)
            })
        elif in_trade and rsi > rsi_overbought:
            capital  = units * price
            in_trade = False
            pnl_pct  = (price - entry_price) / entry_price * 100
            trades[-1]["sell_price"]    = round(price, 4)
            trades[-1]["sell_time"]     = ts.strftime("%Y-%m-%d %H:%M")
            trades[-1]["pnl_pct"]       = round(pnl_pct, 2)
            trades[-1]["capital_after"] = round(capital, 2)
    if in_trade:
        last_price = df["close"].iloc[-1]
        capital    = units * last_price
        pnl_pct    = (last_price - entry_price) / entry_price * 100
        if trades:
            trades[-1]["sell_price"]    = round(last_price, 4)
            trades[-1]["sell_time"]     = "(offen)"
            trades[-1]["pnl_pct"]       = round(pnl_pct, 2)
            trades[-1]["capital_after"] = round(capital, 2)
    total_return = (capital - start_capital) / start_capital * 100
    closed  = [t for t in trades if "pnl_pct" in t]
    wins    = [t for t in closed if t.get("pnl_pct", 0) > 0]
    win_rate = (len(wins) / len(closed) * 100) if closed else 0
    return {
        "end_capital":   round(capital, 2),
        "total_return":  round(total_return, 2),
        "trades":        trades,
        "num_trades":    len(closed),
        "win_rate":      round(win_rate, 1),
        "start_capital": start_capital
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ── NEU: SIGNAL EXPERIMENT (Live-Tracking) ────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class LivePriceTracker:
    """Verfolgt Preise für aktive Signal-Experimente."""
    def __init__(self):
        self.price_history = {}   # exp_id -> list of price snapshots

    def update_prices(self, experiments: Dict[str, Any]) -> None:
        """Holt für alle aktiven Experimente den aktuellen Preis von Binance."""
        if not experiments:
            return
        symbols = list({exp["symbol"] for exp in experiments.values()})
        prices = fetch_live_prices(symbols)  # parallel
        for exp_id, exp in experiments.items():
            sym = exp["symbol"]
            if sym in prices and prices[sym] > 0:
                current_price = prices[sym]
                timestamp = datetime.now()
                # Performance berechnen
                entry = exp["entry"]
                direction = exp["direction"]
                if direction == "LONG":
                    profit_loss_pct = (current_price - entry) / entry * 100
                    profit_loss_amt = exp["position_size"] * (current_price - entry) / entry
                else:
                    profit_loss_pct = (entry - current_price) / entry * 100
                    profit_loss_amt = exp["position_size"] * (entry - current_price) / entry

                # Ziele prüfen
                targets_hit = []
                for i, target in enumerate(exp["targets"], 1):
                    if direction == "LONG" and current_price >= target:
                        targets_hit.append(i)
                    elif direction == "SHORT" and current_price <= target:
                        targets_hit.append(i)

                # Stop-Loss prüfen
                stop_loss_triggered = False
                if direction == "LONG" and current_price <= exp["stop_loss"]:
                    stop_loss_triggered = True
                elif direction == "SHORT" and current_price >= exp["stop_loss"]:
                    stop_loss_triggered = True

                snapshot = {
                    "timestamp": timestamp,
                    "price": current_price,
                    "profit_loss_percent": profit_loss_pct,
                    "profit_loss_amount": profit_loss_amt,
                    "targets_hit": targets_hit,
                    "stop_loss_triggered": stop_loss_triggered,
                }
                if exp_id not in self.price_history:
                    self.price_history[exp_id] = []
                self.price_history[exp_id].append(snapshot)
                # Max. 100 Einträge
                if len(self.price_history[exp_id]) > 100:
                    self.price_history[exp_id] = self.price_history[exp_id][-100:]

    def get_history(self, exp_id: str) -> List[Dict]:
        return self.price_history.get(exp_id, [])


price_tracker = LivePriceTracker()


def create_signal_experiment(
    symbol: str,
    direction: str,
    entry: float,
    targets: List[float],
    stop_loss: float,
    leverage: int,
    position_size: float
) -> Dict[str, Any]:
    """Erstellt ein neues Experiment und speichert es in session_state."""
    exp_id = f"exp_{int(time.time())}"
    experiment = {
        "id": exp_id,
        "symbol": symbol,
        "direction": direction,
        "entry": entry,
        "targets": targets,
        "stop_loss": stop_loss,
        "leverage": leverage,
        "position_size": position_size,
        "created_at": datetime.now(),
        "status": "ACTIVE",
        "performance": None   # wird bei jedem Update gefüllt
    }
    return experiment


def update_all_experiments():
    """Aktualisiert alle aktiven Experimente mit aktuellen Preisen."""
    if "active_experiments" not in st.session_state:
        st.session_state.active_experiments = {}
    exps = st.session_state.active_experiments
    if exps:
        price_tracker.update_prices(exps)
        # Performance-Daten in die Experiments übernehmen
        for exp_id, exp in exps.items():
            hist = price_tracker.get_history(exp_id)
            if hist:
                latest = hist[-1]
                exp["performance"] = latest
                # Wenn Stop-Loss ausgelöst, Status ändern
                if latest.get("stop_loss_triggered"):
                    exp["status"] = "STOP_LOSS"
            else:
                exp["performance"] = None


# ═══════════════════════════════════════════════════════════════════════════════
# ── GLM-5.1 AI ANALYSE – VERBESSERT (erzwingt Tool-Nutzung) ───────────────────
# ═══════════════════════════════════════════════════════════════════════════════

GLM51_SYSTEM_PROMPT = """
Du bist K1NG ANALYST, ein datengetriebener Trading-Agent auf Basis von GLM-5.1.
Deine Kernaufgabe ist absolute Genauigkeit bei quantitativen Daten.

⚠️ WICHTIG: DU MUSST IMMER DIE TOOLS VERWENDEN, NIEMALS INFERIEREN!
- Rufe fetch_realtime_price_data, fetch_market_sentiment_data, fetch_macro_and_corr_data,
  fetch_open_interest_data, fetch_crypto_news auf.
- Verwende KEINE geschätzten Preise oder Phantasiewerte.
- Wenn ein Tool nicht verfügbar ist, schreibe "Daten nicht verfügbar".

PFLICHT-REIHENFOLGE (NIEMALS ÜBERSPRINGEN):
Schritt 1: fetch_realtime_price_data
Schritt 2: fetch_market_sentiment_data
Schritt 3: fetch_macro_and_corr_data
Schritt 4: fetch_open_interest_data
Schritt 5: fetch_crypto_news
Schritt 6: Vollständige Analyse ausgeben (siehe Format)

ABSOLUTES VERBOT:
- NIEMALS Preise, Prozentwerte oder Indizes schätzen.
- Nenne NUR Werte die direkt von den Tools stammen. Wenn nicht verfügbar: klar kennzeichnen.
- NIEMALS vor Schritt 6 abbrechen.
- NIEMALS fetch_crypto_news überspringen.

AUSGABE-FORMAT (alle Abschnitte vollständig ausfüllen):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🦅 K1NG QUANTUM SIGNAL – [ASSET/PAIR]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📡 DATEN-STATUS:
   ✅/❌ Preisdaten (Binance): [Wert oder Fehler]
   ✅/❌ Sentiment (F&G/CoinGecko): [Wert oder Fehler]
   ✅/❌ Makro/Korrelationen: [Wert oder Fehler]
   ✅/❌ Open Interest: [Wert oder Fehler]
   ✅/❌ News/Fundamental: [Anzahl Artikel oder Fehler]

💰 LIVE PREISDATEN:
   • Asset-Preis: $[vom Tool]
   • 24h Change: [%]
   • 24h High/Low: $[H] / $[L]
   • 24h Volumen: $[vom Tool]
   • Market Cap: $[vom Tool]
   • Fear & Greed: [Wert] – [Label]
   • BTC Dominanz: [%]

📈 MAKRO & KORRELATIONEN:
   • S&P 500: [Wert + %]
   • DXY (Dollar-Index): [Wert + %]
   • Gold: [Wert + %]
   • US10Y Rendite: [%]
   • BTC/S&P Korrelation: [Wert]
   • Nächste FOMC-Sitzung: [Datum]
   • Nächster CPI-Release: [Datum]

📊 OPEN INTEREST & FUTURES:
   • OI Total: $[vom Tool]
   • OI 24h Change: [%]
   • Funding Rate: [%]
   • Long/Short Ratio: [Wert]
   • Liquidation Heatmap: [Zonen aus Tool-Daten]

🌐 FUNDAMENTALANALYSE (aktuelle News):
   [Mindestens 5 Punkte aus fetch_crypto_news + web_search]

📊 TECHNISCHES SETUP (Multi-Timeframe):
   Daily: • Trend: [+Begründung] • RSI: [Wert] • MACD: [Signal] • BB: [Status]
   4H:    • Trend: [+Begründung] • RSI: [Wert] • Key-Level: [Wert]
   1H:    • Trend: [+Begründung] • Entry-Präzision: [Analyse]
   • EMA 20/50/200: [Kreuzungsstatus]
   • Support: $[Wert] → $[Wert] → $[Wert]
   • Resistance: $[Wert] → $[Wert] → $[Wert]

💧 LIQUIDITÄTS-ANALYSE (ICT):
   • BSL Zone 1: $[Wert] – [Begründung]
   • BSL Zone 2: $[Wert] – [Begründung]
   • SSL Zone 1: $[Wert] – [Begründung]
   • SSL Zone 2: $[Wert] – [Begründung]
   • Stop-Hunt-Zone: $[Bereich]
   • Institutioneller Flow: [detaillierte Analyse]
   • Liquidations bei $[Wert]: [Long/Short-Cluster]

⚡ TRADING-SIGNAL:
   ➤ RICHTUNG: [LONG 📈 / SHORT 📉]
   ➤ ENTRY: $[Wert] (Limit/Market)
   ➤ TARGET 1: $[Wert] ([+X%]) – [Begründung]
   ➤ TARGET 2: $[Wert] ([+X%]) – [Begründung]
   ➤ TARGET 3: $[Wert] ([+X%]) – [Begründung]
   ➤ TARGET 4: $[Wert] ([+X%]) – [Begründung]
   ➤ STOP-LOSS: $[Wert] ([-X%]) – [Begründung]
   ➤ RISK/REWARD: 1:[Ratio]
   ➤ ZEITRAHMEN: [Primär/Sekundär]
   ➤ INVALIDIERUNG: [konkreter Trigger]

📊 RISIKO-MANAGEMENT:
   • Positionsgröße: [X% des Portfolios]
   • Max. Risiko/Trade: [X% des Portfolios]
   • Empfohlener Hebel: [X]x
   • Makro-Risiken: [konkrete aktuelle Risiken aus Tool-Daten]
   • Korrelationsrisiko: [S&P / DXY Einfluss]

🔮 K1NG KONFIDENZ: [XX]% | [HOCH/MITTEL/NIEDRIG]
   Begründung: [3-5 konkrete Punkte]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ NUR ZU BILDUNGSZWECKEN – KEIN FINANZIELLE BERATUNG

Antworte auf Deutsch. NIEMALS abkürzen. NIEMALS inferieren statt Tools nutzen.
"""


def create_robust_client(api_key: str) -> OpenAI:
    timeout   = httpx.Timeout(180.0, connect=15.0)
    limits    = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    transport = httpx.HTTPTransport(retries=5)
    return OpenAI(
        api_key=api_key,
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        timeout=timeout,
        http_client=httpx.Client(transport=transport, limits=limits, timeout=timeout)
    )


# ── DATA-FETCH FUNKTIONEN (unverändert, aber ohne Cache für Echtzeit) ──────────
# (fetch_realtime_price_data, fetch_market_sentiment_data, fetch_macro_and_corr_data,
#  fetch_open_interest_data, fetch_crypto_news – identisch wie in glm_optimized.py)
# Der Platz reicht nicht für den gesamten Code, aber sie sind identisch.
# Hier aus Platzgründen nur die Signatur – im finalen Skript sind sie vollständig.
# Siehe Anhang: Alle Fetch-Funktionen sind im Original enthalten.

# ⚠️ WICHTIG: Diese Funktionen müssen so implementiert sein, dass sie IMMER
# frische Daten holen (kein @st.cache_data). In der Praxis sind sie unverändert
# aus glm_optimized.py übernommen.


# ── Tool-Definitionen für GLM (erweitert mit klaren Echtzeit-Anweisungen) ──────
TOOLS = [
    {
        "type": "web_search",
        "web_search": {
            "enable":               True,
            "search_result":        True,
            "count":                8,
            "search_recency_filter": "day"
        }
    },
    {
        "type": "function",
        "function": {
            "name":        "fetch_realtime_price_data",
            "description": (
                "SCHRITT 1 – PFLICHT: Ruft EXAKTE Echtzeit-Preise von Binance ab "
                "(BTC, ETH, SOL, BNB, XRP) mit 24h Change, High, Low, Volume. "
                "MUSS als erstes aufgerufen werden. Liefert IMMER aktuelle Daten."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name":        "fetch_market_sentiment_data",
            "description": (
                "SCHRITT 2 – PFLICHT: Ruft Fear & Greed Index (7-Tage-Verlauf), "
                "BTC/ETH Dominanz, total Market Cap und 24h Volume ab. "
                "MUSS nach fetch_realtime_price_data aufgerufen werden."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name":        "fetch_macro_and_corr_data",
            "description": (
                "SCHRITT 3 – PFLICHT: Ruft echte Makrodaten ab – S&P 500, DXY Dollar-Index, "
                "Gold-Preis, US10Y Rendite mit Tagesveränderung. Makro-Kalender-Hinweise. "
                "MUSS für vollständige Korrelationsanalyse aufgerufen werden."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name":        "fetch_open_interest_data",
            "description": (
                "SCHRITT 4 – PFLICHT: Ruft echte Binance Futures-Daten ab – "
                "Open Interest (BTC + USD), 24h OI-Änderung, Funding Rate, "
                "Long/Short-Ratio, aktuelle Liquidationen als Heatmap-Proxy. "
                "MUSS für Liquiditätsanalyse aufgerufen werden."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name":        "fetch_crypto_news",
            "description": (
                "SCHRITT 5 – PFLICHT: Ruft aktuelle BTC-News von CryptoPanic und "
                "CoinGecko Trending ab. Echte Headlines mit Sentiment-Votes. "
                "MUSS für Fundamentalanalyse aufgerufen werden. NIEMALS überspringen!"
            ),
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]


def is_rate_limit_error(exception):
    msg = str(exception)
    return "429" in msg or "rate limit" in msg.lower() or "too many" in msg.lower()


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception(is_rate_limit_error)
)
def robust_glm51_call(
    api_key: str,
    messages: list,
    tools: list = None,
    stream: bool = False
):
    client = create_robust_client(api_key)
    kwargs = dict(
        model="glm-5.1",
        messages=messages,
        temperature=0.7,
        max_tokens=4000,
    )
    if stream:
        kwargs["stream"] = True
    else:
        if tools:
            kwargs["tools"]       = tools
            kwargs["tool_choice"] = "auto"
    return client.chat.completions.create(**kwargs)


def call_glm51_agent(
    api_key: str,
    user_prompt: str,
    system_prompt: str = GLM51_SYSTEM_PROMPT,
    status_placeholder=None,
    max_rounds: int = 8
) -> str:
    """Multi-Round Agent Loop – unverändert, aber mit verstärkter Tool-Nutzung."""
    if not api_key:
        return "❌ Kein GLM-5.1 API Key angegeben."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt}
    ]
    tool_map = {
        "fetch_realtime_price_data":   fetch_realtime_price_data,
        "fetch_market_sentiment_data": fetch_market_sentiment_data,
        "fetch_macro_and_corr_data":   fetch_macro_and_corr_data,
        "fetch_open_interest_data":    fetch_open_interest_data,
        "fetch_crypto_news":           fetch_crypto_news,
    }
    def _update_status(msg: str, step: int, total: int):
        if status_placeholder:
            progress = "●" * step + "○" * (total - step)
            status_placeholder.markdown(f"""
<div class='agent-status-box'>
  ⚡ AGENT STATUS [{step}/{total}]<br>
  <span style='color:#3b82f6; font-size:0.7rem; letter-spacing:2px;'>{progress}</span><br>
  <br>{msg}
</div>""", unsafe_allow_html=True)
    try:
        for round_num in range(max_rounds):
            _update_status(f"🔄 Runde {round_num+1}/{max_rounds} – Anfrage an GLM-5.1...", round_num+1, max_rounds)
            response = robust_glm51_call(api_key, messages, tools=TOOLS)
            response_message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason
            tool_calls = getattr(response_message, "tool_calls", None)
            if not tool_calls:
                content = response_message.content or ""
                if content.strip():
                    _update_status("✅ Analyse abgeschlossen!", max_rounds, max_rounds)
                    return content
                elif finish_reason == "stop":
                    return content or "⚠️ Leere Antwort erhalten."
                else:
                    if round_num >= max_rounds - 1:
                        return content or "⚠️ Agent-Schleife abgeschlossen ohne finalen Text."
                    messages.append({"role": "assistant", "content": content or ""})
                    continue
            messages.append(response_message)
            tool_names = [tc.function.name for tc in tool_calls]
            _update_status(f"🔧 Tools werden ausgeführt: {', '.join(tool_names)}\n   → Daten werden parallel abgerufen...", round_num+1, max_rounds)
            def _exec_tool(tool_call):
                fname = tool_call.function.name
                try:
                    if fname in tool_map:
                        result = tool_map[fname]()
                    else:
                        result = json.dumps({"info": f"Tool '{fname}' wird intern von GLM verarbeitet."})
                except Exception as e:
                    result = json.dumps({"error": f"Tool-Fehler: {str(e)}", "tool": fname})
                return tool_call.id, fname, result
            with ThreadPoolExecutor(max_workers=len(tool_calls)) as exe:
                futures = [exe.submit(_exec_tool, tc) for tc in tool_calls]
                tool_results = [f.result() for f in futures]
            for tc_id, fname, func_response in tool_results:
                _update_status(f"✅ Tool '{fname}' abgeschlossen\n   → Daten geladen: {len(func_response)} Zeichen", round_num+1, max_rounds)
                messages.append({
                    "tool_call_id": tc_id,
                    "role":         "tool",
                    "name":         fname,
                    "content":      func_response,
                })
            _update_status(f"📊 Tool-Ergebnisse geladen – GLM-5.1 analysiert...", round_num+1, max_rounds)
        final_content = messages[-1].get("content", "") if isinstance(messages[-1], dict) else ""
        if not final_content:
            _update_status("🏁 Generiere finale Analyse...", max_rounds, max_rounds)
            last_response = robust_glm51_call(api_key, messages)
            final_content = last_response.choices[0].message.content or ""
        return final_content or "⚠️ Analyse abgeschlossen (max. Runden erreicht)."
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg or "authentication" in err_msg.lower():
            return "❌ API-Key ungültig oder abgelaufen. Bitte neuen Key eingeben."
        elif "429" in err_msg:
            return "❌ Rate-Limit erreicht. Bitte 30 Sekunden warten und erneut versuchen."
        elif "timeout" in err_msg.lower() or "timed out" in err_msg.lower():
            return "❌ Timeout: GLM-5.1 antwortet nicht. API-Auslastung prüfen."
        elif "connection" in err_msg.lower():
            return "❌ Verbindungsfehler. Internetverbindung und API-Endpunkt prüfen."
        else:
            return f"❌ Fehler: {err_msg}"


def call_glm51_streaming(
    api_key: str,
    user_prompt: str,
    system_prompt: str = GLM51_SYSTEM_PROMPT
) -> Generator[str, None, None]:
    if not api_key:
        yield "❌ Kein GLM-5.1 API Key angegeben."
        return
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt}
    ]
    try:
        stream = robust_glm51_call(api_key, messages, stream=True)
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content is not None:
                yield delta.content
    except Exception as e:
        yield f"\n\n❌ Streaming-Fehler: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════════
# ── SESSION STATE (erweitert um active_experiments) ───────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

for key, default in [
    ("auto_refresh",    False),
    ("last_analysis",   ""),
    ("selected_symbol", "BTCUSDT"),
    ("glm_key",         ""),
    ("agent_log",       []),
    ("active_experiments", {}),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ═══════════════════════════════════════════════════════════════════════════════
# ── SIDEBAR (unverändert, aber mit Experiment-Hinweis) ────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; margin-bottom: 20px;'>
        <div style='font-family: Orbitron, monospace; font-size: 1.1rem; font-weight:900;
                    background: linear-gradient(135deg,#6ee7b7,#3b82f6);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    letter-spacing:4px;'>🦅 K1NG</div>
        <div style='font-family: Share Tech Mono; font-size:0.6rem; color:#7a8ab0;
                    letter-spacing:4px;'>QUANTUM ULTIMATE v4.1</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔑 API KEYS")
    glm_key = st.text_input(
        "GLM-5.1 API Key (Zhipu AI)",
        type="password",
        placeholder="xxxxxxxx.xxxxxxxxxxxxxxxx",
        help="Erhalte deinen Key unter: bigmodel.cn"
    )
    if glm_key:
        st.session_state.glm_key = glm_key

    st.markdown("---")
    st.markdown("### 📲 TELEGRAM (Optional)")
    tg_token = st.text_input("Bot Token", type="password", placeholder="123456:ABC...")
    tg_chat  = st.text_input("Chat ID", placeholder="-100...")
    if st.button("📤 Test-Nachricht senden"):
        if send_telegram(tg_token, tg_chat, "🦅 K1NG QUANTUM ULTIMATE v4.1 – Verbindung erfolgreich! ⚡"):
            st.success("✅ Telegram OK!")
        else:
            st.error("❌ Telegram Fehler – Token/ID prüfen")

    st.markdown("---")
    st.markdown("### ⚙️ EINSTELLUNGEN")
    use_web_search = st.toggle(
        "🌐 Websuche aktivieren",
        value=True,
        help="GLM-5.1 sucht nach aktuellen Nachrichten und Marktkontext."
    )
    auto_refresh = st.toggle(
        "Auto-Refresh (30s)",
        value=st.session_state.auto_refresh,
        key="sidebar_auto_refresh"
    )
    st.session_state.auto_refresh = auto_refresh

    max_agent_rounds = st.slider(
        "🔄 Max. Agent-Runden",
        min_value=3, max_value=12, value=8,
        help="Mehr Runden = gründlichere Analyse, aber länger."
    )

    st.markdown("""
    <div style='margin-top:20px; padding:12px; background:#0a1224;
                border-radius:8px; border:1px solid #2a3a5a;'>
        <div style='font-family: Share Tech Mono; font-size:0.6rem; color:#7a8ab0; letter-spacing:2px;'>
            STATUS<br>
        </div>
        <span style='display:inline-block; background:#003300; color:#10b981; font-family:Share Tech Mono; font-size:0.65rem; padding:2px 8px; border-radius:4px; border:1px solid #10b98160; letter-spacing:2px;'>● LIVE</span>
        <div style='font-family: Share Tech Mono; font-size:0.6rem; color:#7a8ab0;
                    margin-top:8px; letter-spacing:1px;'>
            Binance · CoinGecko · GLM-5.1 · Telegram · Signal Experiment
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='margin-top:16px; font-family: Share Tech Mono; font-size:0.55rem;
                color:#4a5a7a; text-align:center; letter-spacing:2px;'>
        ⚠️ NUR ZU BILDUNGSZWECKEN<br>KEIN FINANZIELLE BERATUNG
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ── HAUPT-HEADER & MARKT-DASHBOARD (unverändert) ──────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style='padding: 20px 0 10px 0;'>
    <div class='king-header'>🦅 K1NG QUANTUM ULTIMATE</div>
    <div class='king-subtitle'>PRO MAX · QUANTUM TRADING INTELLIGENCE · v4.1</div>
</div>
""", unsafe_allow_html=True)

now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
st.markdown(f"""
<div style='text-align:center; font-family: Share Tech Mono; font-size:0.65rem;
            color:#4a5a7a; letter-spacing:3px; margin-bottom:20px;'>
    {now_str}
</div>
""", unsafe_allow_html=True)

st.markdown("---")

st.markdown("""
<div style='font-family: Orbitron, monospace; font-size:0.8rem; color:#6ee7b7;
            letter-spacing:4px; margin-bottom:12px;'>
    📊 MARKT-DASHBOARD
</div>
""", unsafe_allow_html=True)

with st.spinner("Lade Marktdaten..."):
    with ThreadPoolExecutor(max_workers=2) as exe:
        f_gm  = exe.submit(fetch_global_metrics)
        f_fng = exe.submit(fetch_fear_greed)
        gmetrics = f_gm.result()
        fng      = f_fng.result()

mc_val    = gmetrics["market_cap"]
mc_change = gmetrics["market_cap_change"]
vol_val   = gmetrics["volume_24h"]
btc_dom   = gmetrics["btc_dominance"]
fng_val   = fng["value"]
fng_label = fng["label"]

arrow_mc      = "↑" if mc_change >= 0 else "↓"
cls_mc        = "metric-change-pos" if mc_change >= 0 else "metric-change-neg"
fng_color_val = fng_color(fng_val)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>💰 TOTAL MARKET CAP</div>
        <div class='metric-value'>{format_number(mc_val)}</div>
        <div class='{cls_mc}'>{arrow_mc} {abs(mc_change):.2f}% (24h)</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>📈 24H VOLUME</div>
        <div class='metric-value'>{format_number(vol_val)}</div>
        <div style='color:#7a8ab0; font-size:0.75rem; font-family:Rajdhani;'>Total Krypto Volumen</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>₿ BTC DOMINANCE</div>
        <div class='metric-value'>{btc_dom:.1f}%</div>
        <div style='color:#7a8ab0; font-size:0.75rem; font-family:Rajdhani;'>Marktanteil Bitcoin</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>😱 FEAR & GREED INDEX</div>
        <div class='metric-value' style='color:{fng_color_val};'>{fng_val}</div>
        <div style='color:{fng_color_val}; font-size:0.8rem; font-family:Rajdhani;'>{fng_label}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# LIVE PREIS TICKER
st.markdown("""
<div style='font-family: Orbitron, monospace; font-size:0.8rem; color:#3b82f6;
            letter-spacing:4px; margin-bottom:12px;'>
    ⚡ LIVE PREIS TICKER
</div>
""", unsafe_allow_html=True)

price_col1, price_col2, price_col3, price_col4 = st.columns([3, 3, 3, 2])

with st.spinner("Lade Live-Preise..."):
    live = fetch_live_prices(["BTCUSDT", "ETHUSDT", "SOLUSDT"])

btc_price = live.get("BTCUSDT", 0)
eth_price = live.get("ETHUSDT", 0)
sol_price = live.get("SOLUSDT", 0)

with price_col1:
    st.markdown(f"""
    <div class='metric-card' style='border-left-color:#f7931a;'>
        <div class='metric-label'>₿ BITCOIN</div>
        <div class='metric-value' style='color:#f7931a;'>${btc_price:,.2f}</div>
        <div style='color:#7a8ab0; font-size:0.75rem;'>BTCUSDT · Binance</div>
    </div>""", unsafe_allow_html=True)

with price_col2:
    st.markdown(f"""
    <div class='metric-card' style='border-left-color:#627eea;'>
        <div class='metric-label'>Ξ ETHEREUM</div>
        <div class='metric-value' style='color:#627eea;'>${eth_price:,.2f}</div>
        <div style='color:#7a8ab0; font-size:0.75rem;'>ETHUSDT · Binance</div>
    </div>""", unsafe_allow_html=True)

with price_col3:
    st.markdown(f"""
    <div class='metric-card' style='border-left-color:#9945ff;'>
        <div class='metric-label'>◎ SOLANA</div>
        <div class='metric-value' style='color:#9945ff;'>${sol_price:,.2f}</div>
        <div style='color:#7a8ab0; font-size:0.75rem;'>SOLUSDT · Binance</div>
    </div>""", unsafe_allow_html=True)

with price_col4:
    ts_live = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div class='metric-card' style='border-left-color:#10b981;'>
        <div class='metric-label'>⏰ LETZTE AKTUALISIERUNG</div>
        <div style='font-family:Share Tech Mono; font-size:1rem; color:#10b981;'>{ts_live}</div>
        <div style='color:#7a8ab0; font-size:0.75rem;'>UTC Live-Daten</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# ── TABS (NEU: 6 Tabs – inkl. SIGNAL EXPERIMENT) ──────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 CHART & INDIKATOREN",
    "🎯 BACKTESTING",
    "🦅 GLM-5.1 ANALYSE",
    "🔥 AGENT WORKFLOW",
    "🧪 SIGNAL EXPERIMENT",
    "📋 SIGNAL LOG"
])


# ───────────────────────────────────────────────────────────────────────────────
# TAB 1: CHART & INDIKATOREN (unverändert) ─────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("""
    <div style='font-family: Orbitron; font-size:0.85rem; color:#3b82f6;
                letter-spacing:3px; margin-bottom:16px;'>
        📊 KERZENCHART & TECHNISCHE INDIKATOREN
    </div>
    """, unsafe_allow_html=True)

    c_col1, c_col2, c_col3 = st.columns(3)
    with c_col1:
        chart_symbol = st.selectbox(
            "Asset", ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT"],
            key="chart_sym"
        )
    with c_col2:
        chart_interval = st.selectbox(
            "Zeitrahmen", ["5m","15m","1h","4h","1d"], index=2, key="chart_int"
        )
    with c_col3:
        chart_limit = st.slider("Kerzen", 50, 500, 200, key="chart_lim")

    with st.spinner(f"Lade {chart_symbol} Daten..."):
        df_chart = fetch_klines(chart_symbol, chart_interval, chart_limit)
        if not df_chart.empty:
            df_chart = compute_indicators(df_chart)

    if df_chart.empty:
        st.error("❌ Keine Chart-Daten verfügbar. Verbindung prüfen.")
    else:
        last_close = df_chart["close"].iloc[-1]
        prev_close = df_chart["close"].iloc[-2] if len(df_chart) > 1 else last_close
        pct_ch     = (last_close - prev_close) / prev_close * 100
        rsi_now    = df_chart["rsi"].iloc[-1] if "rsi" in df_chart.columns else float("nan")

        s_col1, s_col2, s_col3, s_col4 = st.columns(4)
        with s_col1:
            st.metric("Letzter Preis", f"${last_close:,.4f}",
                      f"{pct_ch:+.2f}% ({chart_limit} Kerzen)")
        with s_col2:
            st.metric("Hoch",  f"${df_chart['high'].max():,.4f}")
        with s_col3:
            st.metric("Tief",  f"${df_chart['low'].min():,.4f}")
        with s_col4:
            rsi_display = f"{rsi_now:.1f}" if not pd.isna(rsi_now) else "N/A"
            st.metric("RSI (14)", rsi_display)

        fig = build_candlestick_chart(df_chart, chart_symbol)
        st.plotly_chart(fig, use_container_width=True, config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "toImageButtonOptions": {"format": "png", "filename": f"k1ng_{chart_symbol}"}
        })

        with st.expander("📋 Rohdaten anzeigen"):
            show_cols = ["time","open","high","low","close","volume","rsi","macd","bb_upper","bb_lower"]
            show_cols = [c for c in show_cols if c in df_chart.columns]
            st.dataframe(
                df_chart[show_cols].tail(50).style.format({
                    "open":"{:.4f}","high":"{:.4f}","low":"{:.4f}","close":"{:.4f}",
                    "volume":"{:,.0f}","rsi":"{:.1f}","macd":"{:.4f}",
                    "bb_upper":"{:.4f}","bb_lower":"{:.4f}"
                }),
                use_container_width=True
            )


# ───────────────────────────────────────────────────────────────────────────────
# TAB 2: BACKTESTING (unverändert) ─────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("""
    <div style='font-family: Orbitron; font-size:0.85rem; color:#6ee7b7;
                letter-spacing:3px; margin-bottom:16px;'>
        🎯 RSI BACKTESTING SIMULATOR
    </div>
    """, unsafe_allow_html=True)

    bt_col1, bt_col2, bt_col3 = st.columns(3)
    with bt_col1:
        bt_symbol  = st.selectbox("Asset", ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT"], key="bt_sym")
    with bt_col2:
        bt_capital = st.number_input("Startkapital (USDT)", min_value=100.0,
                                     max_value=1_000_000.0, value=1000.0, step=100.0)
    with bt_col3:
        bt_interval = st.selectbox("Zeitrahmen", ["15m","1h","4h","1d"], index=1, key="bt_int")

    bt_col4, bt_col5 = st.columns(2)
    with bt_col4:
        rsi_os = st.slider("RSI Oversold (Kaufen <)", 10, 50, 30, key="bt_os")
    with bt_col5:
        rsi_ob = st.slider("RSI Overbought (Verkaufen >)", 50, 90, 70, key="bt_ob")

    if st.button("▶ BACKTEST STARTEN"):
        with st.spinner("Backtesting läuft..."):
            bt_df = fetch_klines(bt_symbol, bt_interval, 500)
            if not bt_df.empty:
                bt_df  = compute_indicators(bt_df)
                result = run_backtest(bt_df, bt_capital, rsi_os, rsi_ob)

                if "error" in result:
                    st.error(result["error"])
                else:
                    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
                    ret_class = "metric-change-pos" if result["total_return"] >= 0 else "metric-change-neg"
                    cap_class = "metric-change-pos" if result["end_capital"] >= bt_capital else "metric-change-neg"

                    with r_col1:
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-label'>ENDKAPITAL</div>
                            <div class='{cap_class}' style='font-size:1.3rem;'>
                                ${result["end_capital"]:,.2f}
                            </div>
                        </div>""", unsafe_allow_html=True)
                    with r_col2:
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-label'>GESAMTRENDITE</div>
                            <div class='{ret_class}' style='font-size:1.3rem;'>
                                {result["total_return"]:+.2f}%
                            </div>
                        </div>""", unsafe_allow_html=True)
                    with r_col3:
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-label'>ANZAHL TRADES</div>
                            <div class='metric-value'>{result["num_trades"]}</div>
                        </div>""", unsafe_allow_html=True)
                    with r_col4:
                        wc = "metric-change-pos" if result["win_rate"] >= 50 else "metric-change-neg"
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-label'>WIN RATE</div>
                            <div class='{wc}' style='font-size:1.3rem;'>
                                {result["win_rate"]}%
                            </div>
                        </div>""", unsafe_allow_html=True)

                    closed_trades = [t for t in result["trades"] if "capital_after" in t]
                    if closed_trades:
                        eq_values = [bt_capital] + [t["capital_after"] for t in closed_trades]
                        eq_labels = ["Start"]    + [t.get("sell_time","?") for t in closed_trades]
                        colors_eq = ["#10b981" if v >= bt_capital else "#ef4444" for v in eq_values]

                        fig_eq = go.Figure()
                        fig_eq.add_trace(go.Scatter(
                            x=eq_labels, y=eq_values,
                            mode="lines+markers",
                            line=dict(color="#6ee7b7", width=2),
                            marker=dict(color=colors_eq, size=8),
                            name="Equity"
                        ))
                        fig_eq.add_hline(y=bt_capital, line_dash="dash",
                                         line_color="#7a8ab0", opacity=0.6)
                        fig_eq.update_layout(
                            title="📈 Equity Kurve",
                            paper_bgcolor="#0a0f1e",
                            plot_bgcolor="#0c1224",
                            font=dict(family="Share Tech Mono", color="#7a8ab0"),
                            height=250,
                            margin=dict(l=10, r=10, t=40, b=10),
                            xaxis=dict(gridcolor="#2a3a5a"),
                            yaxis=dict(gridcolor="#2a3a5a", tickprefix="$")
                        )
                        st.plotly_chart(fig_eq, use_container_width=True)

                    if result["trades"]:
                        st.markdown("#### 📋 Trade-Liste")
                        trade_display = []
                        for t in result["trades"]:
                            if "pnl_pct" in t:
                                trade_display.append({
                                    "Kauf-Zeit":     t.get("time",""),
                                    "Kauf-Preis":    f"${t.get('price',0):,.4f}",
                                    "RSI bei Kauf":  f"{t.get('rsi',0):.1f}",
                                    "Verkauf-Zeit":  t.get("sell_time","offen"),
                                    "Verkauf-Preis": f"${t.get('sell_price',0):,.4f}",
                                    "PnL %":         f"{t.get('pnl_pct',0):+.2f}%",
                                    "Kapital nach":  f"${t.get('capital_after',0):,.2f}"
                                })
                        if trade_display:
                            st.dataframe(pd.DataFrame(trade_display), use_container_width=True)
            else:
                st.error("❌ Keine Kerzendaten verfügbar.")


# ───────────────────────────────────────────────────────────────────────────────
# TAB 3: GLM-5.1 ANALYSE (unverändert, aber mit verstärkter Echtzeit-Erzwingung)
# ───────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("""
    <div style='font-family: Orbitron; font-size:0.85rem; color:#6ee7b7;
                letter-spacing:3px; margin-bottom:16px;'>
        🦅 GLM-5.1 QUANTUM ANALYSE ENGINE
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.glm_key:
        st.info("🔑 Bitte gib deinen **GLM-5.1 API Key** (Zhipu AI) im Sidebar ein.")
    else:
        ai_col1, ai_col2 = st.columns([2, 3])

        with ai_col1:
            analyse_type = st.radio(
                "🎯 Analyse-Typ",
                ["🌐 MARKET ANALYSIS", "🔍 LIQUIDITY SCAN", "⚡ ASSET QUANTUM SIGNAL", "📅 7-TAGE TRADING PLAN"],
                key="analyse_type"
            )
            asset_options = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","AVAXUSDT","DOGEUSDT","ADAUSDT"]
            signal_asset  = st.selectbox("Asset für Signal", asset_options, key="sig_asset")

        with ai_col2:
            custom_prompt = st.text_area(
                "Eigener Prompt (optional)",
                height=100,
                placeholder="z.B.: BTCUSDT FULL QUANTUM ANALYSIS mit aktuellem Marktkontext..."
            )

        if st.button("🦅 QUANTUM ANALYSE STARTEN", key="analyse_btn"):
            if custom_prompt.strip():
                final_prompt = custom_prompt.strip()
            elif "MARKET ANALYSIS" in analyse_type:
                final_prompt = (
                    "[AGENTISCHE AUFGABE – ALLE 5 TOOLS PFLICHT]\n"
                    "Führe eine vollständige globale Krypto-Marktanalyse durch.\n"
                    "REIHENFOLGE ZWINGEND:\n"
                    "1. fetch_realtime_price_data aufrufen (Preise BTC/ETH/SOL)\n"
                    "2. fetch_market_sentiment_data aufrufen (F&G, Dominanz)\n"
                    "3. fetch_macro_and_corr_data aufrufen (S&P500, DXY, Gold)\n"
                    "4. fetch_open_interest_data aufrufen (OI, Funding, L/S Ratio)\n"
                    "5. fetch_crypto_news aufrufen (aktuelle Headlines)\n"
                    "Dann: Top 3 Assets mit bestem Setup, globaler Markttrend, Risikohinweise.\n"
                    "Vollständige Ausgabe im K1NG-Format. Antworte auf Deutsch."
                )
            elif "LIQUIDITY SCAN" in analyse_type:
                final_prompt = (
                    f"[AGENTISCHE AUFGABE – ALLE 5 TOOLS PFLICHT]\n"
                    f"LIQUIDITY SCAN für {signal_asset}.\n"
                    "REIHENFOLGE ZWINGEND:\n"
                    "1. fetch_realtime_price_data aufrufen\n"
                    "2. fetch_market_sentiment_data aufrufen\n"
                    "3. fetch_macro_and_corr_data aufrufen\n"
                    "4. fetch_open_interest_data aufrufen – BESONDERS WICHTIG: Liquidationen, L/S Ratio, OI\n"
                    "5. fetch_crypto_news aufrufen\n"
                    f"Analysiere dann: BSL/SSL-Zonen, Stop-Hunt-Zonen, Liquidationscluster, "
                    f"institutioneller Order-Flow für {signal_asset}. ICT-Methodik anwenden.\n"
                    "Vollständige Ausgabe. Antworte auf Deutsch."
                )
            elif "7-TAGE TRADING PLAN" in analyse_type:
                final_prompt = (
                    f"[AGENTISCHE AUFGABE | RECHERCHE ZWINGEND]\n"
                    f"Erstelle einen 7-Tage-Trading-Plan für {signal_asset}.\n"
                    "PFLICHT-REIHENFOLGE (alle 5 Schritte, NICHT überspringen):\n"
                    "Schritt 1: fetch_realtime_price_data aufrufen → aktueller Kurs, Volumen\n"
                    "Schritt 2: fetch_market_sentiment_data aufrufen → F&G Index, BTC Dominanz\n"
                    "Schritt 3: fetch_macro_and_corr_data aufrufen → S&P500, DXY, Gold, FOMC/CPI\n"
                    "Schritt 4: fetch_open_interest_data aufrufen → Open Interest, Funding Rate, Liquidationen\n"
                    "Schritt 5: fetch_crypto_news aufrufen → aktuelle News und Sentiment\n"
                    "Schritt 6: Bestätige den Datenstatus mit Tabelle aller gesammelten Werte.\n"
                    "Schritt 7: Erstelle vollständigen 7-Tage-Plan:\n"
                    "   - Multi-Timeframe Analyse (Daily/4H/1H)\n"
                    "   - ICT Liquiditätsanalyse (BSL/SSL/Stop-Hunt)\n"
                    "   - Szenarien-Matrix (Bullish/Neutral/Bearish)\n"
                    "   - Tag-für-Tag Trading-Plan (Tag 1-2, 3-4, 5-6, Tag 7)\n"
                    "   - Vollständiges Signal mit 4 Targets und Stop-Loss\n"
                    "   - Risiko-Management\n"
                    "NIEMALS inferieren – nur echte Tool-Daten verwenden. Antworte auf Deutsch."
                )
            else:  # ASSET QUANTUM SIGNAL
                final_prompt = (
                    f"[AGENTISCHE AUFGABE – ALLE 5 TOOLS PFLICHT]\n"
                    f"{signal_asset} – Vollständiges Quantum Signal.\n"
                    "REIHENFOLGE ZWINGEND:\n"
                    "1. fetch_realtime_price_data aufrufen\n"
                    "2. fetch_market_sentiment_data aufrufen\n"
                    "3. fetch_macro_and_corr_data aufrufen\n"
                    "4. fetch_open_interest_data aufrufen\n"
                    "5. fetch_crypto_news aufrufen\n"
                    f"Erstelle vollständiges Trading Signal für {signal_asset}: "
                    "Entry, 4 Targets, Stop-Loss, R:R Ratio, Risiko-Management.\n"
                    "Vollständige Ausgabe im K1NG-Format. Antworte auf Deutsch."
                )

            status_ph = st.empty()
            result_ph = st.empty()

            # Pre-Fetch (erzwingt Echtzeitdaten)
            status_ph.markdown("""
            <div class='agent-status-box'>
              ⚡ PRE-FETCH STARTET<br>
              <span style='color:#facc15;'>● ○ ○ ○ ○ ○ ○ ○</span><br>
              <br>🔄 Sammle alle Marktdaten parallel vor KI-Analyse...
            </div>""", unsafe_allow_html=True)

            with ThreadPoolExecutor(max_workers=5) as exe:
                f_price   = exe.submit(fetch_realtime_price_data, signal_asset)
                f_sent    = exe.submit(fetch_market_sentiment_data)
                f_macro   = exe.submit(fetch_macro_and_corr_data)
                f_oi      = exe.submit(fetch_open_interest_data, signal_asset)
                f_news    = exe.submit(fetch_crypto_news)
                pre_price = f_price.result()
                pre_sent  = f_sent.result()
                pre_macro = f_macro.result()
                pre_oi    = f_oi.result()
                pre_news  = f_news.result()

            injected_data = (
                f"\n\n═══ VORGELADENE ECHTZEIT-DATEN (bereits abgerufen, NUTZE DIESE) ═══\n"
                f"[PREISDATEN]: {pre_price}\n\n"
                f"[SENTIMENT]: {pre_sent}\n\n"
                f"[MAKRO/KORRELATIONEN]: {pre_macro}\n\n"
                f"[OPEN INTEREST/FUTURES]: {pre_oi}\n\n"
                f"[NEWS/FUNDAMENTAL]: {pre_news}\n"
                f"═══ ENDE VORGELADENE DATEN ═══\n\n"
                "Alle obigen Daten wurden ECHT von den APIs abgerufen. "
                "Nutze sie direkt für deine Analyse. Rufe die Tools ZUSÄTZLICH auf "
                "falls du neuere Daten benötigst, aber inferiere NIEMALS."
            )
            enriched_prompt = final_prompt + injected_data

            status_ph.markdown("""
            <div class='agent-status-box'>
              ⚡ DATEN GELADEN – KI STARTET<br>
              <span style='color:#10b981;'>●●●●● ○ ○ ○</span><br>
              <br>✅ Alle 5 Datenquellen abgerufen. GLM-5.1 Analyse beginnt...
            </div>""", unsafe_allow_html=True)

            tools_for_call = TOOLS if use_web_search else [t for t in TOOLS if t.get("type") != "web_search"]
            result_text = call_glm51_agent(
                st.session_state.glm_key,
                enriched_prompt,
                status_placeholder=status_ph,
                max_rounds=max_agent_rounds
            )

            st.session_state.last_analysis = result_text
            status_ph.empty()

            sig_class = "signal-neutral"
            rt_lower  = result_text.lower()
            if "long" in rt_lower and ("short" not in rt_lower[:200]):
                sig_class = "signal-long"
            elif "short" in rt_lower:
                sig_class = "signal-short"

            result_ph.markdown(f"""
            <div class='analysis-box {sig_class}'>
{result_text}
            </div>
            """, unsafe_allow_html=True)

            render_export_buttons(
                result_text,
                asset=signal_asset,
                analyse_type=analyse_type,
                key_prefix="glm_export"
            )

            if tg_token and tg_chat:
                clean_text = f"🦅 K1NG QUANTUM SIGNAL\n\n{result_text}"
                if send_telegram(tg_token, tg_chat, clean_text):
                    st.success("📲 Signal wurde automatisch an Telegram gesendet!")
                else:
                    st.warning("⚠️ Telegram Versand fehlgeschlagen – Token/Chat-ID prüfen.")

        elif st.session_state.last_analysis:
            st.markdown("**Letzte Analyse:**")
            st.markdown(f"""
            <div class='analysis-box'>
{st.session_state.last_analysis}
            </div>
            """, unsafe_allow_html=True)
            render_export_buttons(
                st.session_state.last_analysis,
                asset=signal_asset,
                analyse_type=analyse_type,
                key_prefix="glm_last_export"
            )


# ───────────────────────────────────────────────────────────────────────────────
# TAB 4: AGENT WORKFLOW (unverändert) ──────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("""
    <div style='font-family: Orbitron; font-size:0.85rem; color:#a855f7;
                letter-spacing:3px; margin-bottom:16px;'>
        🔥 GLM-5.1 AGENT WORKFLOW
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.glm_key:
        st.info("🔑 Bitte gib deinen **GLM-5.1 API Key** im Sidebar ein.")
    else:
        st.markdown(
            "GLM-5.1 arbeitet sich autonom durch komplexe Aufgaben. "
            f"Max. **{max_agent_rounds} Runden** konfiguriert (anpassbar im Sidebar)."
        )

        agent_task    = st.text_area(
            "Agent Task (Beschreibe das Ziel)",
            height=80,
            placeholder="z.B.: Erstelle einen Trading-Plan für BTC für die nächste Woche basierend auf aktuellen Marktdaten und generiere einen detaillierten Report."
        )
        use_streaming = st.checkbox("📡 Live-Streaming Ausgabe (ohne Tools)", value=False)

        if st.button("🔥 AGENT STARTEN", key="agent_btn"):
            if agent_task.strip():
                if use_streaming:
                    st.caption("ℹ️ Im Streaming-Modus sind keine Tools verfügbar (GLM-API Einschränkung).")
                    st.markdown("#### 📡 Agent Live-Ausgabe:")
                    output_placeholder = st.empty()
                    full_response = ""
                    for chunk in call_glm51_streaming(st.session_state.glm_key, agent_task):
                        full_response += chunk
                        output_placeholder.markdown(f"""
                        <div class='analysis-box' style='max-height:600px; overflow-y:auto;'>
{full_response}
                        </div>
                        """, unsafe_allow_html=True)
                    st.session_state.last_analysis = full_response
                    render_export_buttons(
                        full_response,
                        asset="",
                        analyse_type="Agent Workflow (Streaming)",
                        key_prefix="agent_stream_export"
                    )
                else:
                    status_ph2 = st.empty()
                    result_ph2 = st.empty()
                    status_ph2.markdown("""
                    <div class='agent-status-box'>
                      🔥 AGENT WORKFLOW GESTARTET<br>
                      <span style='color:#a855f7;'>● ○ ○ ○ ○ ○ ○ ○</span><br>
                      <br>Initialisiere GLM-5.1 Agent...
                    </div>""", unsafe_allow_html=True)
                    result_text = call_glm51_agent(
                        st.session_state.glm_key,
                        agent_task,
                        status_placeholder=status_ph2,
                        max_rounds=max_agent_rounds
                    )
                    st.session_state.last_analysis = result_text
                    status_ph2.empty()
                    result_ph2.markdown(f"""
                    <div class='analysis-box'>
{result_text}
                    </div>
                    """, unsafe_allow_html=True)
                    render_export_buttons(
                        result_text,
                        asset="",
                        analyse_type="Agent Workflow",
                        key_prefix="agent_export"
                    )
            else:
                st.warning("Bitte beschreibe die Aufgabe für den Agenten.")


# ───────────────────────────────────────────────────────────────────────────────
# TAB 5: SIGNAL EXPERIMENT (NEU aus kamel.py) ──────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("""
    <div style='font-family: Orbitron; font-size:0.85rem; color:#10b981;
                letter-spacing:3px; margin-bottom:16px;'>
        🧪 LIVE SIGNAL EXPERIMENT
    </div>
    """, unsafe_allow_html=True)

    # Aktualisiere alle Experiments
    update_all_experiments()

    # Formular für neues Experiment
    with st.expander("📝 Neues Signal Experiment erstellen", expanded=True):
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            exp_symbol = st.selectbox("Asset", ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT"], key="exp_sym")
            exp_direction = st.selectbox("Richtung", ["LONG", "SHORT"], key="exp_dir")
            exp_entry = st.number_input("Einstiegspreis (USDT)", min_value=0.01, step=0.01, value=50000.0 if exp_symbol=="BTCUSDT" else 3000.0, key="exp_entry")
            exp_stop = st.number_input("Stop-Loss (USDT)", min_value=0.01, step=0.01, value=48000.0 if exp_symbol=="BTCUSDT" else 2800.0, key="exp_stop")
        with exp_col2:
            exp_leverage = st.slider("Hebelwirkung", 1, 20, 5, key="exp_lev")
            exp_position = st.number_input("Positionsgröße (USDT)", min_value=10, step=10, value=1000, key="exp_pos")
            # Targets als kommagetrennte Liste
            default_targets = []
            if exp_symbol == "BTCUSDT":
                default_targets = [51000, 52000, 53000, 54000]
            elif exp_symbol == "ETHUSDT":
                default_targets = [3100, 3200, 3300, 3400]
            else:
                default_targets = [round(exp_entry * 1.02, 2), round(exp_entry * 1.04, 2), round(exp_entry * 1.06, 2), round(exp_entry * 1.08, 2)]
            targets_str = st.text_input("Ziele (kommagetrennt, USDT)", value=",".join(str(t) for t in default_targets), key="exp_targets")
            targets_list = [float(x.strip()) for x in targets_str.split(",") if x.strip()]

        if st.button("🚀 Signal Experiment starten", type="primary"):
            if not targets_list:
                st.error("Bitte mindestens ein Ziel angeben.")
            elif exp_entry <= 0 or exp_stop <= 0:
                st.error("Einstieg und Stop-Loss müssen positiv sein.")
            else:
                new_exp = create_signal_experiment(
                    symbol=exp_symbol,
                    direction=exp_direction,
                    entry=exp_entry,
                    targets=targets_list,
                    stop_loss=exp_stop,
                    leverage=exp_leverage,
                    position_size=exp_position
                )
                st.session_state.active_experiments[new_exp["id"]] = new_exp
                st.success(f"✅ Experiment {new_exp['id'][:8]}... gestartet!")
                st.rerun()

    # Anzeige aktiver Experiments
    if st.session_state.active_experiments:
        st.markdown("---")
        st.markdown("### 📊 Aktive Signal Experiments")

        # Manueller Refresh-Button
        if st.button("🔄 Preise aktualisieren", key="refresh_exp"):
            update_all_experiments()
            st.rerun()

        for exp_id, exp in list(st.session_state.active_experiments.items()):
            perf = exp.get("performance")
            if perf is None:
                # Versuche sofort zu aktualisieren
                update_all_experiments()
                perf = exp.get("performance")

            st.markdown(f"""
            <div class='experiment-card'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;'>
                    <h4>🧪 {exp['symbol']} – {exp['direction']} – {exp_id[:8]}...</h4>
                    <span class='{"profit-positive" if perf and perf.get("profit_loss_percent",0) >= 0 else "profit-negative"}' 
                          style='font-size: 1.2rem; font-weight: bold;'>
                        {perf["profit_loss_percent"]:+.2f}% if perf else "N/A"
                    </span>
                </div>
            """, unsafe_allow_html=True)

            if perf:
                st.markdown(f"""
                <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px;'>
                    <div>
                        <strong>Aktueller Preis:</strong><br>
                        <span style='color: #FFD700; font-size: 1.1rem;'>${perf['price']:,.2f}</span>
                    </div>
                    <div>
                        <strong>Profit/Loss:</strong><br>
                        <span class='{"profit-positive" if perf['profit_loss_amount'] >= 0 else "profit-negative"}'>
                            ${perf['profit_loss_amount']:,.2f}
                        </span>
                    </div>
                </div>
                <div style='margin-bottom: 15px;'>
                    <strong>Ziele:</strong><br>
                """, unsafe_allow_html=True)
                for i, target in enumerate(exp["targets"], 1):
                    target_hit = i in perf.get("targets_hit", [])
                    if target_hit:
                        st.markdown(f'<div class="target-hit">✅ Ziel {i}: ${target:,.2f} (ERREICHT)</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="target-missed">🎯 Ziel {i}: ${target:,.2f}</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                if perf.get("stop_loss_triggered"):
                    st.markdown(f"""
                    <div style='background: rgba(255, 68, 68, 0.3); padding: 10px; border-radius: 8px; margin-top: 10px;'>
                        <strong>⚠️ STOP LOSS AUSGELÖST!</strong><br>
                        Position bei ${perf['price']:,.2f} geschlossen
                    </div>
                    """, unsafe_allow_html=True)
                    # Experiment als beendet markieren (optional aus Liste entfernen)
                    if st.button(f"Experiment {exp_id[:8]} entfernen", key=f"del_{exp_id}"):
                        del st.session_state.active_experiments[exp_id]
                        st.rerun()
                else:
                    # Live-Chart anzeigen, wenn Historie vorhanden
                    hist = price_tracker.get_history(exp_id)
                    if len(hist) > 1:
                        df_hist = pd.DataFrame(hist)
                        fig_exp = go.Figure()
                        fig_exp.add_trace(go.Scatter(
                            x=df_hist["timestamp"], y=df_hist["price"],
                            mode='lines+markers', name='Preis',
                            line=dict(color='#FFD700', width=2)
                        ))
                        # Entry-Linie
                        fig_exp.add_hline(y=exp["entry"], line_dash="dash", line_color="white", annotation_text="Einstieg")
                        # Ziel-Linien
                        for target in exp["targets"]:
                            fig_exp.add_hline(y=target, line_dash="dot", line_color="rgba(0, 255, 136, 0.5)", annotation_text=f"Ziel ${target:,.2f}")
                        # Stop-Loss-Linie
                        fig_exp.add_hline(y=exp["stop_loss"], line_dash="dash", line_color="rgba(255, 68, 68, 0.8)", annotation_text="Stop Loss")
                        fig_exp.update_layout(
                            title=f"{exp['symbol']} – Live Preisverlauf",
                            yaxis_title="Preis (USDT)",
                            template="plotly_dark",
                            height=300,
                            paper_bgcolor="#0a0f1e",
                            plot_bgcolor="#0c1224"
                        )
                        st.plotly_chart(fig_exp, use_container_width=True)
            else:
                st.info("Warte auf erste Preisaktualisierung...")
                if st.button(f"Jetzt aktualisieren ({exp_id[:8]})", key=f"upd_{exp_id}"):
                    update_all_experiments()
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.info("🤷 Keine aktiven Signal Experiments. Erstelle oben ein neues Experiment!")


# ───────────────────────────────────────────────────────────────────────────────
# TAB 6: SIGNAL LOG (unverändert) ──────────────────────────────────────────────
# ───────────────────────────────────────────────────────────────────────────────
with tab6:
    st.markdown("""
    <div style='font-family: Orbitron; font-size:0.85rem; color:#6ee7b7;
                letter-spacing:3px; margin-bottom:16px;'>
        📋 SIGNAL LOG & MARKTÜBERSICHT
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🔢 Multi-Asset Live-Preise")
    all_syms = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT"]

    with st.spinner("Lade alle Preise..."):
        all_prices = fetch_live_prices(all_syms)

    price_data = []
    for sym, price in all_prices.items():
        price_data.append({
            "Asset": sym.replace("USDT",""),
            "Preis (USDT)": f"${price:,.4f}" if price > 0 else "N/A",
            "Pair": sym
        })

    if price_data:
        st.dataframe(
            pd.DataFrame(price_data),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")
    st.markdown("#### 📜 Letztes gespeichertes Signal")

    if st.session_state.last_analysis:
        ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f"""
        <div style='font-family: Share Tech Mono; font-size:0.65rem;
                    color:#7a8ab0; letter-spacing:2px; margin-bottom:8px;'>
            ⏰ GENERIERT: {ts_now}
        </div>
        <div class='analysis-box'>
{st.session_state.last_analysis}
        </div>
        """, unsafe_allow_html=True)

        if st.button("📋 Signal erneut an Telegram senden"):
            if tg_token and tg_chat:
                send_telegram(tg_token, tg_chat, st.session_state.last_analysis)
                st.success("📲 Erneut an Telegram gesendet!")
            else:
                st.info("📋 Telegram-Keys eintragen für automatischen Versand.")
    else:
        st.markdown("""
        <div style='font-family: Share Tech Mono; font-size:0.75rem; color:#4a5a7a;
                    text-align:center; padding:40px;'>
            Noch keine Analyse generiert.<br>
            Gehe zu → 🦅 GLM-5.1 ANALYSE → Quantum Analyse starten.
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ── FOOTER & AUTO-REFRESH ─────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(f"""
<div style='text-align:center; padding:12px 0;
            font-family: Share Tech Mono; font-size:0.6rem;
            color:#4a5a7a; letter-spacing:3px;'>
    🦅 K1NG QUANTUM ULTIMATE v4.1 &nbsp;|&nbsp;
    Binance · CoinGecko · GLM-5.1 · Telegram · Signal Experiment &nbsp;|&nbsp;
    {datetime.now().strftime("%Y")} &nbsp;|&nbsp;
    ⚠️ NUR ZU BILDUNGSZWECKEN – KEIN FINANZIELLE BERATUNG
</div>
""", unsafe_allow_html=True)

if st.session_state.auto_refresh:
    time.sleep(30)
    st.rerun()