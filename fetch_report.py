import urllib.request
import json
from datetime import datetime, timezone, timedelta

# ── Cities ──────────────────────────────────────────────────────────────────
CITIES = [
    {"name": "Kathmandu", "country": "Nepal",     "emoji": "🇳🇵", "lat": 27.7172,  "lon": 85.3240,  "tz": 5.75,  "tz_name": "NPT"},
    {"name": "New Delhi", "country": "India",     "emoji": "🇮🇳", "lat": 28.6139,  "lon": 77.2090,  "tz": 5.5,   "tz_name": "IST"},
    {"name": "New York",  "country": "USA",        "emoji": "🇺🇸", "lat": 40.7128,  "lon": -74.0060, "tz": -4.0,  "tz_name": "EDT"},
    {"name": "Sydney",    "country": "Australia",  "emoji": "🇦🇺", "lat": -33.8688, "lon": 151.2093, "tz": 10.0,  "tz_name": "AEST"},
    {"name": "Lagos",     "country": "Nigeria",    "emoji": "🇳🇬", "lat": 6.5244,   "lon": 3.3792,   "tz": 1.0,   "tz_name": "WAT"},
]

WMO_CODES = {
    0: "Clear Sky ☀️", 1: "Mainly Clear 🌤️", 2: "Partly Cloudy ⛅", 3: "Overcast ☁️",
    45: "Foggy 🌫️", 48: "Icy Fog 🌫️",
    51: "Light Drizzle 🌦️", 53: "Drizzle 🌦️", 55: "Heavy Drizzle 🌧️",
    61: "Light Rain 🌧️", 63: "Rain 🌧️", 65: "Heavy Rain 🌧️",
    71: "Light Snow 🌨️", 73: "Snow 🌨️", 75: "Heavy Snow ❄️",
    80: "Rain Showers 🌦️", 81: "Rain Showers 🌦️", 82: "Violent Showers ⛈️",
    95: "Thunderstorm ⛈️", 99: "Thunderstorm + Hail ⛈️",
}

def get_local_time(tz_offset):
    local = datetime.now(timezone.utc) + timedelta(hours=tz_offset)
    return local.strftime("%I:%M %p"), local.strftime("%A, %b %d %Y")

def fetch_weather(city):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={city['lat']}&longitude={city['lon']}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,"
        f"apparent_temperature,precipitation,weathercode"
        f"&wind_speed_unit=kmh&timezone=auto"
    )
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode())

def fetch_crypto():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode())
        btc = data.get("bitcoin", {})
        eth = data.get("ethereum", {})
        return {
            "btc_price": btc.get("usd", "N/A"),
            "btc_change": btc.get("usd_24h_change", 0),
            "eth_price": eth.get("usd", "N/A"),
            "eth_change": eth.get("usd_24h_change", 0),
        }
    except:
        return {"btc_price": "N/A", "btc_change": 0, "eth_price": "N/A", "eth_change": 0}

def fetch_stocks():
    try:
        symbols = {"SPY": "S&P 500", "QQQ": "NASDAQ", "GLD": "Gold", "USO": "Oil"}
        results = {}
        for sym, name in symbols.items():
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            meta = data["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice", "N/A")
            prev  = meta.get("chartPreviousClose", price)
            change = ((price - prev) / prev * 100) if prev and prev != 0 else 0
            results[name] = {"price": round(price, 2), "change": round(change, 2)}
        return results
    except:
        return {}

def arrow(change):
    if isinstance(change, (int, float)):
        return "📈" if change >= 0 else "📉"
    return "➡️"

def fmt_change(change):
    if isinstance(change, (int, float)):
        sign = "+" if change >= 0 else ""
        return f"{sign}{change:.2f}%"
    return "N/A"

def build_report():
    now_utc = datetime.now(timezone.utc)
    utc_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
    slot = "🌅 Morning" if now_utc.hour < 12 else "🌆 Evening"

    lines = []
    lines.append("# 🌍 Daily World Report\n")
    lines.append(f"> **{slot} Update** — {utc_str}")
    lines.append("> Auto-committed twice daily via GitHub Actions\n")
    lines.append("---\n")

    # ── Weather ──
    lines.append("## 🌦️ Live Weather\n")
    lines.append("| City | Country | 🕐 Local Time | 🌡️ Temp | 💧 Humidity | 💨 Wind | 🌤️ Condition |")
    lines.append("|------|---------|--------------|--------|------------|--------|-------------|")

    for city in CITIES:
        try:
            data  = fetch_weather(city)
            cur   = data["current"]
            temp  = cur["temperature_2m"]
            humid = cur["relative_humidity_2m"]
            wind  = cur["wind_speed_10m"]
            cond  = WMO_CODES.get(cur.get("weathercode", 0), "Unknown")
            unit  = data["current_units"]["temperature_2m"]
            t_time, _ = get_local_time(city["tz"])
            lines.append(f"| {city['emoji']} **{city['name']}** | {city['country']} | {t_time} {city['tz_name']} | {temp}{unit} | {humid}% | {wind} km/h | {cond} |")
        except Exception as e:
            lines.append(f"| {city['emoji']} **{city['name']}** | {city['country']} | — | — | — | — | ⚠️ Error |")

    lines.append("")
    lines.append("---\n")

    # ── Crypto ──
    lines.append("## 💹 Crypto Markets\n")
    crypto = fetch_crypto()
    lines.append("| Coin | Price (USD) | 24h Change |")
    lines.append("|------|------------|------------|")
    btc_arrow = arrow(crypto['btc_change'])
    eth_arrow = arrow(crypto['eth_change'])
    lines.append(f"| ₿ **Bitcoin** | ${crypto['btc_price']:,} | {btc_arrow} {fmt_change(crypto['btc_change'])} |")
    lines.append(f"| Ξ **Ethereum** | ${crypto['eth_price']:,} | {eth_arrow} {fmt_change(crypto['eth_change'])} |")
    lines.append("")
    lines.append("---\n")

    # ── Stocks ──
    lines.append("## 📈 Financial Markets\n")
    stocks = fetch_stocks()
    if stocks:
        lines.append("| Market | Price | 24h Change |")
        lines.append("|--------|-------|------------|")
        for name, data in stocks.items():
            a = arrow(data['change'])
            lines.append(f"| **{name}** | ${data['price']:,} | {a} {fmt_change(data['change'])} |")
    else:
        lines.append("> ⚠️ Market data temporarily unavailable (markets may be closed)")
    lines.append("")
    lines.append("---\n")

    lines.append(f"*⏱️ Next update in ~12 hours • Last run: {utc_str}*")
    lines.append("\n*Data: [Open-Meteo](https://open-meteo.com/) • [CoinGecko](https://coingecko.com/) • [Yahoo Finance](https://finance.yahoo.com/)*")

    return "\n".join(lines)

if __name__ == "__main__":
    print("⏳ Fetching world report...")
    report = build_report()
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("✅ Report written to REPORT.md")
    print(report)
