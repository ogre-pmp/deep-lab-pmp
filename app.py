import yfinance as yf
import pandas as pd
import streamlit as st

# إعدادات واجهة الموقع
st.set_page_config(page_title="PMP Levels | The Deep Lab", page_icon="🎯", layout="centered")

st.title("🎯 PMP Concept Levels")
st.markdown("**The Deep Lab | Strategy Playbook**")
st.write("Calculating Liquidity Levels for NQ/QQQ Correlation")

def calculate_pmp():
    try:
        # جلب البيانات
        qqq = yf.Ticker("QQQ").history(period="5d", interval="5m", prepost=True)
        nq = yf.Ticker("NQ=F").history(period="5d", interval="5m", prepost=True)

        if qqq.empty or nq.empty:
            return None, "Error: Could not retrieve data from Yahoo Finance."

        # تعديل المنطقة الزمنية لنيويورك
        for df in [qqq, nq]:
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
            else:
                df.index = df.index.tz_convert('America/New_York')

        last_date = qqq.index[-1].date()
        qqq_today = qqq[qqq.index.date == last_date]
        nq_today = nq[nq.index.date == last_date]

        # استخراج مستويات QQQ من 4 إلى 7:59
        session_qqq = qqq_today.between_time('04:00', '07:59')
        if session_qqq.empty:
            return None, f"No Pre-market data (04:00-07:59) found for QQQ on {last_date}."
        
        qqq_high = session_qqq['High'].max()
        qqq_low = session_qqq['Low'].min()

        # استخراج افتتاح 9:00
        qqq_9am = qqq_today.at_time('09:00')
        nq_9am = nq_today.at_time('09:00')

        if qqq_9am.empty or nq_9am.empty:
            return None, f"Notice: The 09:00 AM candle has not formed yet for today ({last_date}). Please run after 09:00 AM NY time."

        qqq9amopen = qqq_9am['Open'].iloc[0]
        nq9amopen = nq_9am['Open'].iloc[0]

        # حساب المعامل K والمستويات النهائية
        K = nq9amopen / qqq9amopen
        pmp_high = K * qqq_high
        pmp_low = K * qqq_low

        return {
            "Date": last_date,
            "QQQ_9AM_Open": qqq9amopen,
            "NQ_9AM_Open": nq9amopen,
            "K": K,
            "PMP_High": pmp_high,
            "PMP_Low": pmp_low
        }, None

    except Exception as e:
        return None, f"An error occurred: {e}"

# واجهة المستخدم (الزر والنتائج)
if st.button("Calculate PMP Levels Now", type="primary"):
    with st.spinner('Fetching prices and calculating levels...'):
        data, error = calculate_pmp()
        
        if error:
            st.error(error)
        else:
            st.success(f"✅ Successfully updated! Data for: {data['Date']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="📈 PMP High", value=f"{data['PMP_High']:.2f}")
            with col2:
                st.metric(label="📉 PMP Low", value=f"{data['PMP_Low']:.2f}")
            
            st.divider()
            st.write("### 📊 Calculation Details:")
            st.write(f"- **QQQ 09:00 Open:** {data['QQQ_9AM_Open']:.2f}")
            st.write(f"- **NQ 09:00 Open:** {data['NQ_9AM_Open']:.2f}")
            st.write(f"- **Multiplier (K):** {data['K']:.6f}")
