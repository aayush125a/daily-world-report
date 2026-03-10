import requests
import os
from datetime import datetime, timezone
import pytz

API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "demo")

# ─────────────────────────────────────────────
# ALL MAJOR + TRENDING CURRENCY PAIRS
# ─────────────────────────────────────────────
PAIRS = [
    # Majors
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
    "AUD/USD", "USD/CAD", "NZD/USD",
    # Crosses
    "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY",
    "EUR/AUD", "GBP/AUD", "EUR/CAD",
    # Exotics
    "USD/TRY", "USD/ZAR", "USD/MXN", "USD/SGD",
    "USD/HKD", "USD/NOK", "USD/SEK",
    # Commodities (treated as pairs)
    "XAU/USD",  # Gold
    "XAG/USD",  # Silver
]

# ─────────────────────────────────────────────
# MARKET SESSION TIMES (UTC)
# ─────────────────────────────────────────────
SESSIONS = {
    "🗼 Tokyo":   {"open": "00:00", "close": "09:00", "tz": "Asia/Tokyo"},
    "🇬🇧 London":  {"open": "08:00", "close": "17:00", "tz": "Europe/London"},
    "🇺🇸 New York": {"open": "13:00", "close": "22:00", "tz": "America/New_York"},
    "🇦🇺 Sydney":  {"open": "22:00", "close": "07:00", "tz": "Australia/Sydney"},
}

def get_session_status():
    utc_now = datetime.now(timezone.utc)
    current_hour = utc_now.hour + utc_now.minute / 60
    lines = []
    for name, info in SESSIONS.items():
        tz = pytz.timezone(info["tz"])
        local_time = utc_now.astimezone(tz).strftime("%I:%M %p")
        oh, om = map(int, info["open"].split(":"))
        ch, cm = map(int, info["close"].split(":"))
        open_dec = oh + om / 60
        close_dec = ch + cm / 60
        if close_dec < open_dec:  # crosses midnight
            is_open = current_hour >= open_dec or current_hour < close_dec
        else:
            is_open = open_dec <= current_hour < close_dec
        status = "🟢 **OPEN**" if is_open else "🔴 Closed"
        lines.append(f"| {name} | {info['open']} – {info['close']} UTC | {local_time} | {status} |")
    return lines

def fetch_quotes():
    symbols = ",".join(PAIRS)
    url = f"https://api.twelvedata.com/price?symbol={symbols}&apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        return data
    except Exception as e:
        return {}

def fetch_quote_details():
    """Fetch detailed quote with % change, high, low"""
    symbols = ",".join(PAIRS[:20])  # Twelve Data free tier limit per call
    url = f"https://api.twelvedata.com/quote?symbol={symbols}&apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=15)
        return r.json()
    except:
        return {}

def get_flag(pair):
    flags = {
        "EUR": "🇪🇺", "USD": "🇺🇸", "GBP": "🇬🇧", "JPY": "🇯🇵",
        "AUD": "🇦🇺", "CAD": "🇨🇦", "CHF": "🇨🇭", "NZD": "🇳🇿",
        "TRY": "🇹🇷", "ZAR": "🇿🇦", "MXN": "🇲🇽", "SGD": "🇸🇬",
        "HKD": "🇭🇰", "NOK": "🇳🇴", "SEK": "🇸🇪", "XAU": "🥇", "XAG": "🥈",
    }
    base = pair.split("/")[0]
    quote = pair.split("/")[1]
    return flags.get(base, "🌐") + flags.get(quote, "🌐")

def build_readme(prices, details):
    utc_now = datetime.now(timezone.utc)
    timestamp = utc_now.strftime("%Y-%m-%d %H:%M UTC")
    ist = pytz.timezone("Asia/Kolkata")
    ist_time = utc_now.astimezone(ist).strftime("%Y-%m-%d %I:%M %p IST")

    session_rows = get_session_status()
    session_table = "\n".join(session_rows)

    # Build pairs table
    pair_rows = []
    for pair in PAIRS:
        flag = get_flag(pair)
        price = "—"
        change = "—"
        high = "—"
        low = "—"
        sentiment = "—"

        key = pair.replace("/", "")
        detail = details.get(pair, details.get(key, {}))

        if isinstance(detail, dict) and "close" in detail:
            try:
                price = float(detail.get("close", 0))
                open_p = float(detail.get("open", price))
                high = float(detail.get("high", price))
                low = float(detail.get("low", price))
                pct = ((price - open_p) / open_p) * 100 if open_p else 0
                arrow = "📈" if pct >= 0 else "📉"
                change = f"{arrow} {pct:+.2f}%"
                sentiment = "🟢 Bullish" if pct > 0.1 else ("🔴 Bearish" if pct < -0.1 else "⚪ Neutral")
                price = f"`{price:.5f}`" if price < 10 else f"`{price:.2f}`"
                high = f"{high:.5f}" if high < 10 else f"{high:.2f}"
                low = f"{low:.5f}" if low < 10 else f"{low:.2f}"
            except:
                pass
        elif isinstance(prices.get(pair), dict) and "price" in prices[pair]:
            try:
                p = float(prices[pair]["price"])
                price = f"`{p:.5f}`" if p < 10 else f"`{p:.2f}`"
            except:
                pass

        pair_rows.append(f"| {flag} {pair} | {price} | {high} | {low} | {change} | {sentiment} |")

    pairs_table = "\n".join(pair_rows)

    # Key tips section
    tips = """
## 📚 Forex Trader's Daily Checklist

| # | Task | Why It Matters |
|---|------|----------------|
| 1 | ✅ Check economic calendar (Forex Factory) | High-impact news = big moves |
| 2 | ✅ Identify session overlaps (London + NY) | Highest liquidity & volatility |
| 3 | ✅ Mark daily S/R levels on your chart | Price respects key levels |
| 4 | ✅ Check COT (Commitment of Traders) report | Know what big players are doing |
| 5 | ✅ Review DXY (Dollar Index) trend | USD drives 80% of pairs |
| 6 | ✅ Check VIX (Fear Index) | High VIX = risk-off = USD/JPY/CHF up |
| 7 | ✅ Note any central bank statements | Fed/ECB/BOJ move markets massively |
| 8 | ✅ Set alerts at key price levels | Never miss a breakout |
| 9 | ✅ Review your open trades & SL/TP | Risk management first |
| 10 | ✅ Journal your trades | The edge is in the data |
"""

    key_levels = """
## ⚡ Key Market Concepts to Monitor

| Concept | Description | Where to Find |
|---------|-------------|---------------|
| 📅 High-Impact News | NFP, CPI, Rate Decisions | [Forex Factory](https://forexfactory.com) |
| 📊 DXY (Dollar Index) | Strength of USD vs basket | [TradingView](https://tradingview.com/symbols/TVC-DXY/) |
| 😨 VIX Fear Index | Market fear = safe haven demand | [CBOE](https://cboe.com/vix) |
| 🏦 COT Report | Institutional positioning (released Fridays) | [CFTC.gov](https://cftc.gov/MarketReports/CommitmentsofTraders) |
| 🏛️ Central Banks | Fed, ECB, BOJ, BOE policy | [FedWatch Tool](https://cmegroup.com/trading/interest-rates/countdown-to-fomc.html) |
| 📈 Retail Sentiment | Contrarian indicator | [Myfxbook](https://myfxbook.com/forex-market/sentiment) |
| 🕯️ Key S/R Levels | Weekly/Monthly highs & lows | TradingView Charts |
| 💧 Liquidity Zones | Where stops are hiding | ICT / Smart Money concepts |
"""

    session_overlap = """
## 🔥 Best Times to Trade (Session Overlaps)

| Overlap | UTC Time | Why It's the Best |
|---------|----------|-------------------|
| 🇬🇧🇺🇸 London + New York | 13:00 – 17:00 | Highest volume, biggest moves |
| 🗼🇬🇧 Tokyo + London | 07:00 – 09:00 | GBP/JPY, EUR/JPY active |
| 🇦🇺🗼 Sydney + Tokyo | 00:00 – 02:00 | AUD/JPY, NZD pairs move |
"""

    readme = f"""# 📊 Live Forex Dashboard — Auto-Updated 2x Daily

> 🤖 Auto-committed by GitHub Actions • Last updated: **{timestamp}** ({ist_time})
> 
> *"Markets are never wrong — opinions often are."* — Jesse Livermore

---

## 🕐 Market Sessions Status

| Session | Hours (UTC) | Local Time | Status |
|---------|-------------|------------|--------|
{session_table}

{session_overlap}

---

## 💱 Live Currency Prices — All Major, Cross & Exotic Pairs

| Pair | Price | Day High | Day Low | Change | Sentiment |
|------|-------|----------|---------|--------|-----------|
{pairs_table}

> 📡 Data sourced from [Twelve Data](https://twelvedata.com) • Prices update 2x daily at 08:00 & 20:00 UTC

---

{key_levels}

---

{tips}

---

## 📰 Resources Every Forex Trader Needs Bookmarked

| Tool | Purpose | Link |
|------|---------|------|
| 📅 Forex Factory | Economic Calendar | [forexfactory.com](https://forexfactory.com) |
| 📊 TradingView | Charting Platform | [tradingview.com](https://tradingview.com) |
| 🏦 Investing.com | News + Data | [investing.com](https://investing.com) |
| 📈 Myfxbook | Sentiment + Stats | [myfxbook.com](https://myfxbook.com) |
| 🔢 Pip Calculator | Risk Calculator | [babypips.com/tools/pip-value-calculator](https://babypips.com/tools/pip-value-calculator) |
| 😨 VIX Index | Fear Gauge | [cboe.com/vix](https://cboe.com/vix) |
| 🏛️ CFTC COT Report | Institutional Positioning | [cftc.gov](https://cftc.gov/MarketReports/CommitmentsofTraders) |
| 🧠 BabyPips | Learning Hub | [babypips.com](https://babypips.com) |
| 📻 FXStreet | Live News | [fxstreet.com](https://fxstreet.com) |

---

## 🧠 Quick Forex Wisdom

```
📌 Risk no more than 1-2% per trade
📌 The trend is your friend — until it ends
📌 Cut losses short, let winners run
📌 Trade the setup, not the excitement
📌 London & NY overlap = peak opportunity
📌 Always check the news before entering
📌 DXY up → USD pairs shift accordingly
📌 High VIX → JPY and CHF strengthen (safe havens)
📌 NFP (First Friday of month) = highest volatility
📌 Never average down on a losing trade
```

---

<div align="center">

⭐ **Star this repo** if it helps your trading journey!

*Built with 🔥 passion for markets • Auto-updated by GitHub Actions*

</div>
"""
    return readme

if __name__ == "__main__":
    print("📡 Fetching forex data...")
    prices = fetch_quotes()
    details = fetch_quote_details()
    readme_content = build_readme(prices, details)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("✅ README.md updated successfully!")
