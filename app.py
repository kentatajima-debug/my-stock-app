import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. ページの設定とタイトル
st.set_page_config(page_title="日経225総合投資判断アプリ", layout="wide")
st.title("📊 日経225 テクニカル分析＆一括抽出アプリ")

# 2. タブによる機能の切り替え
tab1, tab2 = st.tabs(["🔍 日経225一括抽出 (スクリーニング)", "📈 個別銘柄の詳細分析"])

# 日経225の全225銘柄リスト（2026年最新版対応）
NIKKEI_225_SAMPLES = [
    "1332.T", "1605.T", "1721.T", "1801.T", "1802.T", "1803.T", "1812.T", "1925.T", "1928.T", "1963.T",
    "2002.T", "2269.T", "2282.T", "2413.T", "2502.T", "2503.T", "2531.T", "2768.T", "2801.T", "2802.T",
    "2871.T", "2914.T", "3086.T", "3092.T", "3101.T", "3289.T", "3382.T", "3401.T", "3402.T", "3405.T",
    "3407.T", "3436.T", "3659.T", "3861.T", "3863.T", "4004.T", "4005.T", "4021.T", "4042.T", "4043.T",
    "4061.T", "4063.T", "4151.T", "4183.T", "4188.T", "4208.T", "4324.T", "4452.T", "4502.T", "4503.T",
    "4506.T", "4507.T", "4519.T", "4523.T", "4543.T", "4568.T", "4578.T", "4661.T", "4689.T", "4704.T",
    "4755.T", "4901.T", "4911.T", "5019.T", "5020.T", "5101.T", "5108.T", "5201.T", "5202.T", "5214.T",
    "5301.T", "5332.T", "5333.T", "5401.T", "5406.T", "5411.T", "5541.T", "5631.T", "5703.T", "5706.T",
    "5711.T", "5713.T", "5714.T", "5802.T", "5803.T", "6098.T", "6103.T", "6113.T", "6178.T", "6301.T",
    "6302.T", "6305.T", "6326.T", "6367.T", "6471.T", "6472.T", "6473.T", "6501.T", "6503.T", "6504.T",
    "6506.T", "6645.T", "6701.T", "6702.T", "6703.T", "6723.T", "6724.T", "6752.T", "6753.T", "6758.T",
    "6762.T", "6770.T", "6841.T", "6857.T", "6902.T", "6920.T", "6952.T", "6954.T", "6971.T", "6976.T",
    "6981.T", "7003.T", "7004.T", "7011.T", "7012.T", "7013.T", "7186.T", "7201.T", "7202.T", "7203.T",
    "7205.T", "7211.T", "7261.T", "7267.T", "7269.T", "7270.T", "7731.T", "7733.T", "7735.T", "7751.T",
    "7752.T", "7832.T", "7911.T", "7912.T", "7951.T", "7974.T", "8001.T", "8002.T", "8015.T", "8031.T",
    "8035.T", "8053.T", "8058.T", "8233.T", "8252.T", "8267.T", "8304.T", "8306.T", "8308.T", "8309.T",
    "8316.T", "8331.T", "8354.T", "8411.T", "8601.T", "8604.T", "8628.T", "8630.T", "8725.T", "8750.T",
    "8766.T", "8795.T", "8801.T", "8802.T", "8804.T", "8830.T", "9001.T", "9005.T", "9007.T", "9008.T",
    "9009.T", "9020.T", "9021.T", "9022.T", "9041.T", "9042.T", "9062.T", "9064.T", "9101.T", "9104.T",
    "9107.T", "9201.T", "9202.T", "9301.T", "9432.T", "9433.T", "9434.T", "9501.T", "9502.T", "9503.T",
    "9531.T", "9532.T", "9602.T", "9613.T", "9735.T", "9766.T", "9843.T", "9983.T", "9984.T"
]

# テクニカル指標を手動計算する共通関数
def calculate_indicators(df):
    if df.empty or len(df) < 5:
        return df
    
    sma_short = 5 if len(df) >= 5 else len(df)
    sma_long = 25 if len(df) >= 25 else len(df)
    rsi_period = 14 if len(df) >= 14 else len(df) - 1

    df["SMA5"] = df["Close"].rolling(window=sma_short).mean()
    df["SMA25"] = df["Close"].rolling(window=sma_long).mean()
    
    if rsi_period > 0:
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=rsi_period).mean()
        avg_loss = loss.rolling(window=rsi_period).mean()
        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))
    else:
        df["RSI"] = 50.0
    return df

# =====================================================================
# タブ1: 一括抽出 (スクリーニング) 機能
# =====================================================================
with tab1:
    st.header("日経225全銘柄「買い推奨」シグナル一括抽出")
    
    period_tab1 = st.selectbox(
        "データ期間（抽出用）", 
        options=["1d", "5d", "1mo", "3mo", "6mo", "1y"], 
        index=3, 
        key="p_tab1"
    )
    
    if st.button("日経225（全219銘柄）から買い銘柄を抽出する"):
        st.info(f"期間【{period_tab1}】で日経平均構成銘柄をフルスキャン中...（約30秒〜1分かかります）")
        
        buy_signals = []
        progress_bar = st.progress(0)
        
        for i, ticker in enumerate(NIKKEI_225_SAMPLES):
            try:
                interval = "1m" if period_tab1 in ["1d", "5d"] else "1d"
                df = yf.download(ticker, period=period_tab1, interval=interval, multi_level_index=False, progress=False)
                df = calculate_indicators(df)
                
                if df.empty or "SMA5" not in df.columns or df["SMA5"].isna().iloc[-1]:
                    continue
                
                today = df.iloc[-1]
                yesterday = df.iloc[-2] if len(df) > 1 else today
                
                # シグナル判定
                is_golden_cross = (yesterday["SMA5"] <= df["SMA25"].iloc[-2]) and (today["SMA5"] > today["SMA25"]) if len(df) > 1 else False
                is_oversold = today["RSI"] < 30
                
                if is_golden_cross or is_oversold:
                    reason = "ゴールデンクロス発生" if is_golden_cross else "RSI30以下（売られすぎ）"
                    buy_signals.append({
                        "銘柄コード": ticker,
                        "最新の株価": f"{float(today['Close']):,.1f}円",
                        "最新のRSI": f"{float(today['RSI']):,.1f}",
                        "抽出理由": reason
                    })
            except:
                continue
            progress_bar.progress((i + 1) / len(NIKKEI_225_SAMPLES))
            
        st.success("フルスキャンが完了しました！")
        
        if len(buy_signals) > 0:
            result_df = pd.DataFrame(buy_signals)
            st.subheader(f"🎯 抽出結果一覧 （該当: {len(buy_signals)}件）")
            st.dataframe(result_df, use_container_width=True)
            
            # 【新機能】結果のCSVダウンロードボタン
            csv = result_df.to_csv(index=False).encode('utf-8-sig') # 日本語文字化け対策のbom付き
            st.download_button(
                label="📥 抽出結果をCSVファイルとして保存",
                data=csv,
                file_name=f"nikkei225_buy_signals_{period_tab1}.csv",
                mime="text/csv"
            )
        else:
            st.warning(f"現在、期間【{period_tab1}】で『買いシグナル』に該当する銘柄はありませんでした。")

# =====================================================================
# タブ2: 個別銘柄の詳細分析 機能
# =====================================================================
with tab2:
    st.header("銘柄別 テクニカルチャート＆詳細投資判断")
    col1, col2 = st.columns(2)
    with col1:
        ticker_tab2 = st.text_input("銘柄コードを入力（日本株は末尾に .T）", value="7203.T", key="t_tab2")
    with col2:
        period_tab2 = st.selectbox(
            "データ期間（詳細分析用）", 
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y"], 
            index=3, 
            key="p_tab2"
        )
        
    interval_tab2 = "1m" if period_tab2 in ["1d", "5d"] else "1d"
    df_ind = yf.download(ticker_tab2, period=period_tab2, interval=interval_tab2, multi_level_index=False, progress=False)
    df_ind = calculate_indicators(df_ind)

    if df_ind.empty or "SMA5" not in df_ind.columns or df_ind["SMA5"].isna().iloc[-1]:
        st.error("データの取得に失敗したか、十分なデータがありません。")
    else:
        today = df_ind.iloc[-1]
        yesterday = df_ind.iloc[-2] if len(df_ind) > 1 else today
        
        decision = "様子見"
        reason = "明確な売買シグナルは出ていません。"
        bg_color = "#f0f2f6"

        is_golden_cross = (yesterday["SMA5"] <= df_ind["SMA25"].iloc[-2]) and (today["SMA5"] > today["SMA25"]) if len(df_ind) > 1 else False
        is_dead_cross = (yesterday["SMA5"] >= df_ind["SMA25"].iloc[-2]) and (today["SMA5"] < today["SMA25"]) if len(df_ind) > 1 else False

        if is_golden_cross:
            decision = "買いシグナル"
            reason = f"【{period_tab2}】チャートにおいて、短期線が長期線を上抜ける「ゴールデンクロス」が発生しました。"
            bg_color = "#d4edda"
        elif is_dead_cross:
            decision = "売りシグナル"
            reason = f"【{period_tab2}】チャートにおいて、短期線が長期線を下抜ける「デッドクロス」が発生しました。"
            bg_color = "#f8d7da"
        elif today["RSI"] < 30:
            decision = "買い（売られすぎ）"
            reason = f"RSIが{float(today['RSI']):.1f}となっており、短期的な売られすぎシグナルを示しています。"
            bg_color = "#d4edda"
        elif today["RSI"] > 70:
            decision = "売り（買われすぎ）"
            reason = f"RSIが{float(today['RSI']):.1f}となっており、短期的な買われすぎシグナルを示しています。"
            bg_color = "#f8d7da"

        st.html(
            f"""
            <div style="background-color:{bg_color}; padding:20px; border-radius:10px; border:1px solid #ccc; margin-bottom:20px;">
                <h2 style="margin:0; color:black;">【判断】 {decision}</h2>
                <p style="margin:10px 0 0 0; color:#333; font-size:16px;">理由: {reason}</p>
                <p style="margin:5px 0 0 0; color:#666; font-size:14px;">（現在の価格: {float(today['Close']):,.1f}円 / RSI: {float(today['RSI']):,.1f}）</p>
            </div>
            """
        )

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df_ind.index, open=df_ind['Open'], high=df_ind['High'], low=df_ind['Low'], close=df_ind['Close'], name="ローソク足"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_ind.index, y=df_ind['SMA5'], name="短期移動平均線", line=dict(color='orange', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_ind.index, y=df_ind['SMA25'], name="長期移動平均線", line=dict(color='blue', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_ind.index, y=df_ind['RSI'], name="RSI", line=dict(color='purple', width=1.5)), row=2, col=1)
        fig.add_shape(type="line", x0=df_ind.index, y0=30, x1=df_ind.index[-1], y1=30, line=dict(color="gray", dash="dash"), row=2, col=1)
        fig.add_shape(type="line", x0=df_ind.index, y0=70, x1=df_ind.index[-1], y1=70, line=dict(color="gray", dash="dash"), row=2, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False, height=550, margin=dict(l=50, r=50, b=50, t=20))
        st.plotly_chart(fig, use_container_width=True)
