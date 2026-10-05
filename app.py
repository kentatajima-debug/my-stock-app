import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. ページの設定とタイトル
st.set_page_config(page_title="日経225総合投資判断アプリ", layout="wide")
st.title("📊 日経225 テクニカル分析＆一括抽出アプリ")

# 2. タブによる機能の切り替え（ここが合体のポイントです！）
tab1, tab2 = st.tabs(["🔍 日経225一括抽出 (スクリーニング)", "📈 個別銘柄の詳細分析"])

# 日経225の主要な銘柄リスト（テスト用）
NIKKEI_225_SAMPLES = [
    "1605.T", "1925.T", "2502.T", "2802.T", "2914.T", "3402.T", "4063.T", "4502.T", 
    "4503.T", "4519.T", "4568.T", "4901.T", "6367.T", "6501.T", "6503.T", "6752.T", 
    "6758.T", "6857.T", "6954.T", "6971.T", "7201.T", "7203.T", "7267.T", "7751.T", 
    "7974.T", "8001.T", "8031.T", "8035.T", "8058.T", "8306.T", "8316.T", "8411.T", 
    "8604.T", "8766.T", "9432.T", "9433.T", "9983.T", "9984.T"
]

# =====================================================================
# タブ1: 一括抽出 (スクリーニング) 機能
# =====================================================================
with tab1:
    st.header("日経225「買い推奨」シグナル一括抽出")
    
    # 抽出用の設定
    period_tab1 = st.selectbox("データ期間（抽出用）", options=["3mo", "6mo", "1y"], index=1, key="p_tab1")
    
    if st.button("日経225から買い銘柄を抽出する"):
        st.info(f"データ期間: 【{period_tab1}】 でスキャン中...（しばらくお待ちください）")
        
        buy_signals = []
        progress_bar = st.progress(0)
        
        for i, ticker in enumerate(NIKKEI_225_SAMPLES):
            try:
                df = yf.download(ticker, period=period_tab1, multi_level_index=False, progress=False)
                if df.empty or len(df) < 26:
                    continue
                    
                df["SMA5"] = ta.sma(df["Close"], length=5)
                df["SMA25"] = ta.sma(df["Close"], length=25)
                df["RSI"] = ta.rsi(df["Close"], length=14)
                
                today = df.iloc[-1]
                yesterday = df.iloc[-2]
                
                is_golden_cross = (yesterday["SMA5"] <= yesterday["SMA25"]) and (today["SMA5"] > today["SMA25"])
                is_oversold = today["RSI"] < 30
                
                if is_golden_cross or is_oversold:
                    reason = "ゴールデンクロス" if is_golden_cross else "RSI30以下（売られすぎ）"
                    buy_signals.append({
                        "銘柄コード": ticker,
                        "現在の株価": f"{float(today['Close']):,.1f}円",
                        "RSI(14)": f"{float(today['RSI']):,.1f}",
                        "抽出理由": reason
                    })
            except:
                continue
            progress_bar.progress((i + 1) / len(NIKKEI_225_SAMPLES))
            
        st.success("スキャンが完了しました！")
        
        if len(buy_signals) > 0:
            result_df = pd.DataFrame(buy_signals)
            st.dataframe(result_df, use_container_width=True)
        else:
            st.warning("該当する銘柄はありませんでした。")

# =====================================================================
# タブ2: 個別銘柄の詳細分析 機能（以前の機能）
# =====================================================================
with tab2:
    st.header("銘柄別 テクニカルチャート＆詳細投資判断")
    
    # 個別分析用の設定（画面上部にすっきり配置）
    col1, col2 = st.columns(2)
    with col1:
        ticker_tab2 = st.text_input("銘柄コードを入力（日本株は末尾に .T）", value="7203.T", key="t_tab2")
    with col2:
        period_tab2 = st.selectbox("データ期間（詳細分析用）", options=["3mo", "6mo", "1y"], index=1, key="p_tab2")
        
    # データ読み込み用関数
    def load_individual_data(symbol, p):
        df = yf.download(symbol, period=p, multi_level_index=False, progress=False)
        if not df.empty:
            df["SMA5"] = ta.sma(df["Close"], length=5)
            df["SMA25"] = ta.sma(df["Close"], length=25)
            df["RSI"] = ta.rsi(df["Close"], length=14)
        return df

    df_ind = load_individual_data(ticker_tab2, period_tab2)

    if df_ind.empty:
        st.error("データの取得に失敗しました。銘柄コードを確認してください。")
    else:
        today = df_ind.iloc[-1]
        yesterday = df_ind.iloc[-2]
        
        decision = "様子見"
        reason = "明確な売買シグナルは出ていません。"
        bg_color = "#f0f2f6"

        is_golden_cross = (yesterday["SMA5"] <= yesterday["SMA25"]) and (today["SMA5"] > today["SMA25"])
        is_dead_cross = (yesterday["SMA5"] >= yesterday["SMA25"]) and (today["SMA5"] < today["SMA25"])

        if is_golden_cross:
            decision = "買いシグナル"
            reason = "5日移動平均線が25日移動平均線を上抜ける「ゴールデンクロス」が発生しました。"
            bg_color = "#d4edda"
        elif is_dead_cross:
            decision = "売りシグナル"
            reason = "5日移動平均線が25日移動平均線を下抜ける「デッドクロス」が発生しました。"
            bg_color = "#f8d7da"
        elif today["RSI"] < 30:
            decision = "買い（売られすぎ）"
            reason = "RSIが30以下となっており、相場が売られすぎのシグナルを示しています。"
            bg_color = "#d4edda"
        elif today["RSI"] > 70:
            decision = "売り（買われすぎ）"
            reason = "RSIが70以上となっており、相場が買われすぎのシグナルを示しています。"
            bg_color = "#f8d7da"

        # 投資判断の画面表示
        st.html(
            f"""
            <div style="background-color:{bg_color}; padding:20px; border-radius:10px; border:1px solid #ccc; margin-bottom:20px;">
                <h2 style="margin:0; color:black;">【判断】 {decision}</h2>
                <p style="margin:10px 0 0 0; color:#333; font-size:16px;">理由: {reason}</p>
                <p style="margin:5px 0 0 0; color:#666; font-size:14px;">（現在の終値: {float(today['Close']):,.1f}円 / RSI: {float(today['RSI']):,.1f}）</p>
            </div>
            """
        )

        # チャートの描画
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df_ind.index, open=df_ind['Open'], high=df_ind['High'], low=df_ind['Low'], close=df_ind['Close'], name="ローソク足"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_ind.index, y=df_ind['SMA5'], name="5日移動平均線", line=dict(color='orange', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_ind.index, y=df_ind['SMA25'], name="25日移動平均線", line=dict(color='blue', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_ind.index, y=df_ind['RSI'], name="RSI(14)", line=dict(color='purple', width=1.5)), row=2, col=1)
        fig.add_shape(type="line", x0=df_ind.index[0], y0=30, x1=df_ind.index[-1], y1=30, line=dict(color="gray", dash="dash"), row=2, col=1)
        fig.add_shape(type="line", x0=df_ind.index[0], y0=70, x1=df_ind.index[-1], y1=70, line=dict(color="gray", dash="dash"), row=2, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False, height=550, margin=dict(l=50, r=50, b=50, t=20))
        st.plotly_chart(fig, use_container_width=True)
