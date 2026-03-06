from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

# ── 監視銘柄リスト ──────────────────────────────────────
JP_TICKERS = [
    {"ticker": "7203.T", "name": "トヨタ自動車"},
    {"ticker": "6758.T", "name": "ソニーグループ"},
    {"ticker": "9984.T", "name": "ソフトバンクG"},
    {"ticker": "8306.T", "name": "三菱UFJ FG"},
    {"ticker": "6861.T", "name": "キーエンス"},
    {"ticker": "7974.T", "name": "任天堂"},
    {"ticker": "8035.T", "name": "東京エレクトロン"},
    {"ticker": "4063.T", "name": "信越化学工業"},
    {"ticker": "6367.T", "name": "ダイキン工業"},
    {"ticker": "9432.T", "name": "NTT"},
    {"ticker": "7267.T", "name": "本田技研工業"},
    {"ticker": "6902.T", "name": "デンソー"},
    {"ticker": "4502.T", "name": "武田薬品工業"},
    {"ticker": "9433.T", "name": "KDDI"},
    {"ticker": "8316.T", "name": "三井住友FG"},
    {"ticker": "6954.T", "name": "ファナック"},
    {"ticker": "9983.T", "name": "ファーストリテイリング"},
    {"ticker": "8411.T", "name": "みずほFG"},
    {"ticker": "4661.T", "name": "オリエンタルランド"},
    {"ticker": "6501.T", "name": "日立製作所"},
    {"ticker": "6702.T", "name": "富士通"},
    {"ticker": "4568.T", "name": "第一三共"},
    {"ticker": "8058.T", "name": "三菱商事"},
    {"ticker": "8031.T", "name": "三井物産"},
    {"ticker": "4543.T", "name": "テルモ"},
    {"ticker": "6594.T", "name": "ニデック"},
    {"ticker": "5401.T", "name": "日本製鉄"},
    {"ticker": "6098.T", "name": "リクルートHD"},
    {"ticker": "7751.T", "name": "キヤノン"},
    {"ticker": "2914.T", "name": "日本たばこ産業"},
    {"ticker": "4452.T", "name": "花王"},
    {"ticker": "6503.T", "name": "三菱電機"},
    {"ticker": "7270.T", "name": "SUBARU"},
    {"ticker": "7201.T", "name": "日産自動車"},
    {"ticker": "9020.T", "name": "東日本旅客鉄道"},
    {"ticker": "4519.T", "name": "中外製薬"},
    {"ticker": "8802.T", "name": "三菱地所"},
    {"ticker": "8801.T", "name": "三井不動産"},
    {"ticker": "4507.T", "name": "塩野義製薬"},
    {"ticker": "2802.T", "name": "味の素"},
    {"ticker": "6645.T", "name": "オムロン"},
    {"ticker": "7733.T", "name": "オリンパス"},
    {"ticker": "6479.T", "name": "ミネベアミツミ"},
    {"ticker": "3382.T", "name": "セブン&アイHD"},
    {"ticker": "4704.T", "name": "トレンドマイクロ"},
    {"ticker": "5108.T", "name": "ブリヂストン"},
    {"ticker": "6723.T", "name": "ルネサスエレクトロニクス"},
    {"ticker": "4578.T", "name": "大塚HD"},
    {"ticker": "9022.T", "name": "東海旅客鉄道"},
    {"ticker": "6471.T", "name": "日本精工"},
]

US_TICKERS = [
    {"ticker": "AAPL",  "name": "Apple"},
    {"ticker": "MSFT",  "name": "Microsoft"},
    {"ticker": "NVDA",  "name": "NVIDIA"},
    {"ticker": "GOOGL", "name": "Alphabet"},
    {"ticker": "AMZN",  "name": "Amazon"},
    {"ticker": "META",  "name": "Meta"},
    {"ticker": "TSLA",  "name": "Tesla"},
    {"ticker": "BRK-B", "name": "Berkshire Hathaway"},
    {"ticker": "LLY",   "name": "Eli Lilly"},
    {"ticker": "JPM",   "name": "JPMorgan Chase"},
    {"ticker": "V",     "name": "Visa"},
    {"ticker": "UNH",   "name": "UnitedHealth"},
    {"ticker": "XOM",   "name": "ExxonMobil"},
    {"ticker": "MA",    "name": "Mastercard"},
    {"ticker": "JNJ",   "name": "Johnson & Johnson"},
    {"ticker": "PG",    "name": "Procter & Gamble"},
    {"ticker": "HD",    "name": "Home Depot"},
    {"ticker": "MRK",   "name": "Merck"},
    {"ticker": "COST",  "name": "Costco"},
    {"ticker": "ABBV",  "name": "AbbVie"},
    {"ticker": "BAC",   "name": "Bank of America"},
    {"ticker": "CVX",   "name": "Chevron"},
    {"ticker": "NFLX",  "name": "Netflix"},
    {"ticker": "KO",    "name": "Coca-Cola"},
    {"ticker": "PEP",   "name": "PepsiCo"},
    {"ticker": "WMT",   "name": "Walmart"},
    {"ticker": "CRM",   "name": "Salesforce"},
    {"ticker": "MCD",   "name": "McDonald's"},
    {"ticker": "AMD",   "name": "AMD"},
    {"ticker": "INTC",  "name": "Intel"},
    {"ticker": "QCOM",  "name": "Qualcomm"},
    {"ticker": "ADBE",  "name": "Adobe"},
    {"ticker": "TXN",   "name": "Texas Instruments"},
    {"ticker": "CSCO",  "name": "Cisco"},
    {"ticker": "ORCL",  "name": "Oracle"},
    {"ticker": "IBM",   "name": "IBM"},
    {"ticker": "GE",    "name": "GE Aerospace"},
    {"ticker": "CAT",   "name": "Caterpillar"},
    {"ticker": "BA",    "name": "Boeing"},
    {"ticker": "UPS",   "name": "UPS"},
    {"ticker": "NEE",   "name": "NextEra Energy"},
    {"ticker": "TMO",   "name": "Thermo Fisher"},
    {"ticker": "DHR",   "name": "Danaher"},
    {"ticker": "NKE",   "name": "Nike"},
    {"ticker": "AMGN",  "name": "Amgen"},
    {"ticker": "PM",    "name": "Philip Morris"},
    {"ticker": "LIN",   "name": "Linde"},
    {"ticker": "ACN",   "name": "Accenture"},
    {"ticker": "SPGI",  "name": "S&P Global"},
    {"ticker": "NOW",   "name": "ServiceNow"},
]

# ── ランキングキャッシュ (5分) ──────────────────────────
_ranking_cache = {}
CACHE_TTL = 300


def _fetch_change(t):
    try:
        hist = yf.Ticker(t["ticker"]).history(period="5d")
        close = hist["Close"].dropna()
        if len(close) < 2:
            return None
        price = float(close.iloc[-1])
        change_pct = (close.iloc[-1] / close.iloc[-2] - 1) * 100
        change_amt = close.iloc[-1] - close.iloc[-2]
        return {
            "ticker": t["ticker"],
            "name": t["name"],
            "price": round(price, 2),
            "change_pct": round(float(change_pct), 2),
            "change_amt": round(float(change_amt), 2),
        }
    except Exception:
        return None

app = Flask(__name__)


def get_stock_data(ticker, period="6mo"):
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    info = stock.info
    return stock, hist, info


def build_chart(hist, ticker):
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("株価チャート", "MACD", "RSI")
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist["Open"],
        high=hist["High"],
        low=hist["Low"],
        close=hist["Close"],
        name="株価",
        increasing_line_color="#16a34a",
        decreasing_line_color="#dc2626"
    ), row=1, col=1)

    # Moving averages
    ma25 = hist["Close"].rolling(25).mean()
    ma75 = hist["Close"].rolling(75).mean()
    fig.add_trace(go.Scatter(x=hist.index, y=ma25, name="MA25",
                             line=dict(color="#f59e0b", width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=ma75, name="MA75",
                             line=dict(color="#2563eb", width=1.5)), row=1, col=1)

    # Volume
    colors = ["#16a34a" if c >= o else "#dc2626"
              for c, o in zip(hist["Close"], hist["Open"])]
    fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="出来高",
                         marker_color=colors, opacity=0.4), row=1, col=1)

    # MACD
    macd = ta.trend.MACD(hist["Close"])
    macd_line = macd.macd()
    signal_line = macd.macd_signal()
    macd_hist = macd.macd_diff()
    fig.add_trace(go.Scatter(x=hist.index, y=macd_line, name="MACD",
                             line=dict(color="#2563eb", width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=signal_line, name="Signal",
                             line=dict(color="#f59e0b", width=1.5)), row=2, col=1)
    hist_colors = ["#16a34a" if v >= 0 else "#dc2626" for v in macd_hist.fillna(0)]
    fig.add_trace(go.Bar(x=hist.index, y=macd_hist, name="Histogram",
                         marker_color=hist_colors), row=2, col=1)

    # RSI
    rsi = ta.momentum.RSIIndicator(hist["Close"]).rsi()
    fig.add_trace(go.Scatter(x=hist.index, y=rsi, name="RSI",
                             line=dict(color="#7c3aed", width=1.5)), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#dc2626", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#16a34a", row=3, col=1)

    fig.update_layout(
        height=700,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#1a202c"),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, bgcolor="rgba(255,255,255,0)"),
        margin=dict(l=50, r=20, t=60, b=20)
    )
    for i in range(1, 4):
        fig.update_xaxes(gridcolor="#e2e8f0", row=i, col=1)
        fig.update_yaxes(gridcolor="#e2e8f0", row=i, col=1)

    return json.loads(fig.to_json())


def extract_metrics(info):
    def fmt(val, suffix="", divisor=1, decimals=2):
        if val is None or val == "N/A":
            return "N/A"
        try:
            v = float(val) / divisor
            if divisor >= 1e9:
                return f"{v:.2f}兆円" if divisor == 1e12 else f"{v:.2f}十億"
            return f"{v:,.{decimals}f}{suffix}"
        except Exception:
            return str(val)

    currency = info.get("currency", "")
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
    change = None
    change_pct = None
    if price and prev_close:
        change = price - prev_close
        change_pct = (change / prev_close) * 100

    return {
        "name": info.get("longName") or info.get("shortName", ""),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "currency": currency,
        "price": fmt(price, f" {currency}", decimals=2),
        "change": fmt(change, f" {currency}", decimals=2) if change is not None else "N/A",
        "change_pct": fmt(change_pct, "%", decimals=2) if change_pct is not None else "N/A",
        "change_positive": (change >= 0) if change is not None else None,
        "market_cap": fmt(info.get("marketCap"), "", 1e9, 2) + "B" if info.get("marketCap") else "N/A",
        "pe_ratio": fmt(info.get("trailingPE")),
        "forward_pe": fmt(info.get("forwardPE")),
        "eps": fmt(info.get("trailingEps"), f" {currency}"),
        "dividend_yield": fmt(info.get("dividendYield"), "%", 0.01),
        "week_52_high": fmt(info.get("fiftyTwoWeekHigh"), f" {currency}"),
        "week_52_low": fmt(info.get("fiftyTwoWeekLow"), f" {currency}"),
        "avg_volume": fmt(info.get("averageVolume"), "", 1e6, 2) + "M" if info.get("averageVolume") else "N/A",
        "beta": fmt(info.get("beta")),
        "roe": fmt(info.get("returnOnEquity"), "%", 0.01) if info.get("returnOnEquity") else "N/A",
        "debt_to_equity": fmt(info.get("debtToEquity")),
        "profit_margin": fmt(info.get("profitMargins"), "%", 0.01) if info.get("profitMargins") else "N/A",
        "revenue": fmt(info.get("totalRevenue"), "", 1e9, 2) + "B" if info.get("totalRevenue") else "N/A",
        "summary": info.get("longBusinessSummary", ""),
    }


def build_intraday_chart(hist):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.75, 0.25],
        subplot_titles=("5分足チャート", "出来高")
    )

    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist["Open"],
        high=hist["High"],
        low=hist["Low"],
        close=hist["Close"],
        name="株価",
        increasing_line_color="#16a34a",
        decreasing_line_color="#dc2626"
    ), row=1, col=1)

    # 移動平均 (25本・75本)
    ma25 = hist["Close"].rolling(25).mean()
    ma75 = hist["Close"].rolling(75).mean()
    fig.add_trace(go.Scatter(x=hist.index, y=ma25, name="MA25",
                             line=dict(color="#f59e0b", width=1.2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=ma75, name="MA75",
                             line=dict(color="#2563eb", width=1.2)), row=1, col=1)

    colors = ["#16a34a" if c >= o else "#dc2626"
              for c, o in zip(hist["Close"], hist["Open"])]
    fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="出来高",
                         marker_color=colors, opacity=0.5), row=2, col=1)

    fig.update_layout(
        height=520,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#1a202c"),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, bgcolor="rgba(255,255,255,0)"),
        margin=dict(l=50, r=20, t=60, b=20)
    )
    for i in range(1, 3):
        fig.update_xaxes(gridcolor="#e2e8f0", row=i, col=1)
        fig.update_yaxes(gridcolor="#e2e8f0", row=i, col=1)

    return json.loads(fig.to_json())


@app.route("/api/intraday")
def intraday():
    ticker = request.args.get("ticker", "").strip().upper()
    period = request.args.get("period", "1d")
    if not ticker:
        return jsonify({"error": "ティッカーシンボルを入力してください"}), 400

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval="5m")
        if hist.empty:
            return jsonify({"error": f"'{ticker}' の5分足データが取得できませんでした"}), 404

        chart = build_intraday_chart(hist)
        return jsonify({"chart": chart})
    except Exception as e:
        return jsonify({"error": f"データ取得エラー: {str(e)}"}), 500


def build_prediction(hist, days=30):
    close = hist["Close"].dropna()
    if len(close) < 30:
        return None

    # x: 日数インデックス
    x = np.arange(len(close)).reshape(-1, 1)
    y = close.values

    # 多項式回帰 (degree=2) でトレンドフィット
    model = make_pipeline(PolynomialFeatures(degree=2), LinearRegression())
    model.fit(x, y)

    # 残差の標準偏差（信頼区間の幅に使用）
    residuals = y - model.predict(x)
    residual_std = np.std(residuals)

    # 将来の日付生成（営業日ベース）
    last_date = close.index[-1]
    future_dates = pd.bdate_range(start=last_date, periods=days + 1, freq="B")[1:]
    x_future = np.arange(len(close), len(close) + days).reshape(-1, 1)

    pred = model.predict(x_future)

    # 不確実性は時間とともに拡大（sqrt スケール）
    uncertainty = residual_std * 1.96 * np.sqrt(np.arange(1, days + 1) / len(close) * len(close))
    upper = pred + uncertainty
    lower = pred - uncertainty

    # 直近実績との接続用に最終実績点を先頭に追加
    connect_date = [last_date]
    connect_price = [float(close.iloc[-1])]

    all_dates = connect_date + list(future_dates)
    all_pred = connect_price + list(pred)
    all_upper = connect_price + list(upper)
    all_lower = connect_price + list(lower)

    # 予測サマリー
    last_price = float(close.iloc[-1])
    pred_end = float(pred[-1])
    change_pct = (pred_end - last_price) / last_price * 100

    return {
        "dates": [str(d.date()) for d in pd.DatetimeIndex(all_dates)],
        "pred": [round(v, 4) for v in all_pred],
        "upper": [round(v, 4) for v in all_upper],
        "lower": [round(v, 4) for v in all_lower],
        "last_price": round(last_price, 4),
        "pred_price": round(pred_end, 4),
        "change_pct": round(change_pct, 2),
        "days": days,
    }


@app.route("/api/predict")
def predict():
    ticker = request.args.get("ticker", "").strip().upper()
    days = int(request.args.get("days", 30))
    period = request.args.get("period", "1y")
    if not ticker:
        return jsonify({"error": "ティッカーシンボルを入力してください"}), 400

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return jsonify({"error": f"'{ticker}' のデータが見つかりません"}), 404

        result = build_prediction(hist, days=days)
        if result is None:
            return jsonify({"error": "データが不足しています（最低30日分必要）"}), 400
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"予測エラー: {str(e)}"}), 500


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze")
def analyze():
    ticker = request.args.get("ticker", "").strip().upper()
    period = request.args.get("period", "6mo")
    if not ticker:
        return jsonify({"error": "ティッカーシンボルを入力してください"}), 400

    try:
        stock, hist, info = get_stock_data(ticker, period)
        if hist.empty:
            return jsonify({"error": f"'{ticker}' のデータが見つかりません"}), 404

        chart = build_chart(hist, ticker)
        metrics = extract_metrics(info)
        return jsonify({"chart": chart, "metrics": metrics})
    except Exception as e:
        return jsonify({"error": f"データ取得エラー: {str(e)}"}), 500


@app.route("/api/compare")
def compare():
    tickers_raw = request.args.get("tickers", "")
    period = request.args.get("period", "1y")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    if len(tickers) < 2:
        return jsonify({"error": "2つ以上のティッカーを入力してください"}), 400
    if len(tickers) > 5:
        return jsonify({"error": "比較は最大5銘柄までです"}), 400

    COLORS = ["#2563eb", "#dc2626", "#16a34a", "#f59e0b", "#7c3aed"]

    stocks_data = []
    close_frames = {}
    fig = go.Figure()

    for i, ticker in enumerate(tickers):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            info = stock.info
            if hist.empty:
                continue

            close = hist["Close"].dropna()
            normalized = (close / close.iloc[0] * 100).round(3)
            close_frames[ticker] = close

            color = COLORS[i % len(COLORS)]
            period_return = round((close.iloc[-1] / close.iloc[0] - 1) * 100, 2)

            fig.add_trace(go.Scatter(
                x=normalized.index,
                y=normalized.values,
                name=ticker,
                line=dict(color=color, width=2),
                hovertemplate=f"<b>{ticker}</b>: %{{y:.2f}}<extra></extra>"
            ))

            metrics = extract_metrics(info)
            metrics["ticker"] = ticker
            metrics["color"] = color
            metrics["period_return"] = period_return
            stocks_data.append(metrics)
        except Exception:
            continue

    if len(stocks_data) < 2:
        return jsonify({"error": "データを取得できた銘柄が1つ以下です"}), 400

    fig.add_hline(y=100, line_dash="dot", line_color="#94a3b8", line_width=1,
                  annotation_text="基準", annotation_position="left")
    fig.update_layout(
        height=420,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#1a202c"),
        legend=dict(orientation="h", y=1.06, bgcolor="rgba(255,255,255,0)"),
        margin=dict(l=50, r=20, t=40, b=40),
        yaxis_title="基準化 (開始=100)",
        hovermode="x unified"
    )
    fig.update_xaxes(gridcolor="#e2e8f0")
    fig.update_yaxes(gridcolor="#e2e8f0")

    # 相関係数
    corr_data = None
    if len(close_frames) >= 2:
        df = pd.DataFrame(close_frames).dropna()
        if len(df) > 10:
            corr = df.pct_change().dropna().corr().round(3)
            corr_data = {
                "tickers": list(corr.columns),
                "matrix": corr.values.tolist()
            }

    return jsonify({
        "chart": json.loads(fig.to_json()),
        "stocks": stocks_data,
        "correlation": corr_data,
    })


@app.route("/api/ranking")
def ranking():
    market = request.args.get("market", "jp")
    force = request.args.get("force", "0") == "1"

    now = time.time()
    if not force and market in _ranking_cache:
        cached_time, cached_data = _ranking_cache[market]
        if now - cached_time < CACHE_TTL:
            return jsonify(cached_data)

    tickers = JP_TICKERS if market == "jp" else US_TICKERS

    results = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(_fetch_change, t): t for t in tickers}
        for future in as_completed(futures):
            r = future.result()
            if r:
                results.append(r)

    results.sort(key=lambda x: x["change_pct"], reverse=True)

    data = {
        "gainers": results[:10],
        "losers": list(reversed(results[-10:])),
        "updated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(results),
    }
    _ranking_cache[market] = (now, data)
    return jsonify(data)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", debug=False, port=port)
