import yfinance as yf
import pandas as pd
import streamlit as st

# 1. إعدادات الصفحة
st.set_page_config(page_title="The Deep Lab | PMP", page_icon="🧠", layout="centered")

# 2. الهوية البصرية (Theme) المستوحاة من اللوغو
st.markdown("""
    <style>
    /* لون الخلفية (أسود عميق) */
    .stApp {
        background-color: #000000;
    }
    
    /* العناوين (الأزرق السماوي المستوحى من كلمة DEEP LAB) */
    h1, h2, h3 {
        color: #00D4FF !important;
        font-family: 'Arial', sans-serif;
    }
    
    /* النصوص العادية */
    p, .stMarkdown {
        color: #FFFFFF;
    }
    
    /* لون أرقام النتائج PMP (الأخضر النيون المستوحى من الشموع اليابانية) */
    [data-testid="stMetricValue"] {
        color: #5DE23C !important;
    }
    
    /* تصميم الزر */
    .stButton>button {
        background-color: #000000;
        color: #00D4FF;
        border: 2px solid #00D4FF;
        border-radius: 8px;
        width: 100%;
        font-size: 18px;
        font-weight: bold;
        transition: 0.3s;
    }
    
    /* تأثير الزر عند تمرير الفأرة (Hover) */
    .stButton>button:hover {
        background-color: #00D4FF;
        color: #000000;
        border: 2px solid #00D4FF;
    }
    
    /* تصميم رسائل النجاح والخطأ */
    .stAlert {
        background-color: #0A0A0A;
        border: 1px solid #5DE23C;
        color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

# 3. العناوين (مطابقة للوغو)
st.title("🧠 THE DEEP LAB")
st.subheader("Market Research & Trading | PMP Concept")
st.markdown("استخراج مستويات السيولة (Liquidity Levels) لمعامل الربط بين NQ و QQQ")
st.divider()

# 4. وظيفة الحساب
def calculate_pmp():
    try:
        qqq = yf.Ticker("QQQ").history(period="5d", interval="5m", prepost=True)
        nq = yf.Ticker("NQ=F").history(period="5d", interval="5m", prepost=True)

        if qqq.empty or nq.empty:
            return None, "Error: Could not retrieve data from Yahoo Finance."

        for df in [qqq, nq]:
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
            else:
                df.index = df.index.tz_convert('America/New_York')

        last_date = qqq.index[-1].date()
        qqq_today = qqq[qqq.index.date == last_date]
        nq_today = nq[nq.index.date == last_date]

        session_qqq = qqq_today.between_time('04:00', '07:59')
        if session_qqq.empty:
            return None, f"No Pre-market data (04:00-07:59) found for QQQ on {last_date}."
        
        qqq_high = session_qqq['High'].max()
        qqq_low = session_qqq['Low'].min()

        qqq_9am = qqq_today.at_time('09:00')
        nq_9am = nq_today.at_time('09:00')

        if qqq_9am.empty or nq_9am.empty:
            return None, f"شمعة 09:00 صباحاً لم تتشكل بعد لتاريخ اليوم ({last_date}). يرجى المحاولة بعد الافتتاح."

        qqq9amopen = qqq_9am['Open'].iloc[0]
        nq9amopen = nq_9am['Open'].iloc[0]

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
        return None, f"حدث خطأ أثناء جلب البيانات: {e}"

# 5. واجهة التشغيل وعرض النتائج
if st.button("Calculate PMP Levels"):
    with st.spinner('جاري جلب الأسعار من السوق...'):
        data, error = calculate_pmp()
        
        if error:
            st.error(error)
        else:
            st.success(f"✅ تم التحديث بنجاح! بيانات يوم: {data['Date']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="📈 PMP High (Target)", value=f"{data['PMP_High']:.2f}")
            with col2:
                st.metric(label="📉 PMP Low (Target)", value=f"{data['PMP_Low']:.2f}")
            
            st.divider()
            st.markdown("<p style='color:#00D4FF; font-weight:bold;'>📊 تفاصيل الحساب:</p>", unsafe_allow_html=True)
            st.write(f"- **QQQ 09:00 AM Open:** {data['QQQ_9AM_Open']:.2f}")
            st.write(f"- **NQ 09:00 AM Open:** {data['NQ_9AM_Open']:.2f}")
            st.write(f"- **Multiplier (K):** {data['K']:.6f}")
