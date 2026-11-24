"""
از بابامنیر چه خبر
داشبورد گزارش روزانه کشاورزی بابامنیر
نسخه با بخش «از من بپرس»

اجرا:
    streamlit run babamenir_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import jdatetime
    HAS_JDATETIME = True
except ImportError:
    HAS_JDATETIME = False

st.set_page_config(
    page_title="از بابامنیر چه خبر",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: Tahoma, "Segoe UI", Arial, sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    .stMetric { direction: rtl; text-align: center; }
    .stMetric label { direction: rtl; text-align: center; display: block; }
    div[data-testid="stMetricValue"] { direction: ltr; text-align: center; }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a3c34 0%, #2d5a4c 100%);
    }
    section[data-testid="stSidebar"] * { color: #f8f9fa !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label { color: #e9ecef !important; }
    .news-card {
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        background: #f8f9fa;
    }
    .tag {
        display: inline-block;
        background: #e9ecef;
        color: #495057;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        margin-left: 4px;
    }
    .ask-box {
        background: #e8f5e9;
        border-right: 5px solid #2e7d32;
        padding: 16px;
        border-radius: 10px;
        margin: 12px 0;
    }
    h1, h2, h3 { font-family: Tahoma, "Segoe UI", Arial, sans-serif !important; }
</style>
""", unsafe_allow_html=True)

LOCATIONS = {
    "بابامنیر": {"lat": 30.07, "lon": 51.52, "name": "بابامنیر", "elev": 950},
    "نورآباد ممسنی": {"lat": 30.11, "lon": 51.52, "name": "نورآباد ممسنی", "elev": 920},
    "ماهور میلاتی": {"lat": 29.95, "lon": 51.45, "name": "ماهور میلاتی", "elev": 1100},
    "کازرون": {"lat": 29.62, "lon": 51.65, "name": "کازرون", "elev": 860},
    "شیراز": {"lat": 29.59, "lon": 52.58, "name": "شیراز", "elev": 1500},
    "مرودشت": {"lat": 29.87, "lon": 52.80, "name": "مرودشت", "elev": 1600},
    "سپیدان": {"lat": 30.26, "lon": 51.98, "name": "سپیدان", "elev": 2100},
    "فیروزآباد": {"lat": 28.84, "lon": 52.57, "name": "فیروزآباد", "elev": 1350},
}

SAMPLE_NEWS = [
    {"title": "شروع کشت گندم در شهرستان‌های شمالی فارس", "summary": "عملیات کشت گندم آبی و دیم از اقلید و آباده آغاز شده. هدف استان حدود ۴۷۰ هزار هکتار است.", "tags": ["#کشت", "#گندم", "#فارس"], "source": "جهاد کشاورزی فارس", "time": "۲ ساعت پیش", "priority": 5},
    {"title": "نوسان قیمت کود اوره و تغییر سازوکار بورس کالا", "summary": "آخرین معاملات اوره گرانول حدود ۶۲۸ هزار ریال به ازای هر کیلوگرم. استعلام محلی ضروری است.", "tags": ["#کود", "#اوره", "#بورس", "#نهاده"], "source": "بورس کالای ایران", "time": "۵ ساعت پیش", "priority": 5},
    {"title": "شرایط جوی مناسب برای ادامه کشت پاییزه در ممسنی", "summary": "بارش قابل توجهی در چند روز آینده پیش‌بینی نمی‌شود. دمای شبانه خنک اما بدون یخبندان شدید.", "tags": ["#هواشناسی", "#کشت", "#ممسنی"], "source": "Open-Meteo", "time": "۱ ساعت پیش", "priority": 4},
    {"title": "رتبه نخست فارس در تولید محصولات باغی", "summary": "فارس با تولید حدود ۳٫۶ تا ۳٫۷ میلیون تن محصولات باغی صدرنشین کشور است.", "tags": ["#باغبانی", "#فارس", "#تولید"], "source": "ایسنا", "time": "امروز", "priority": 3},
    {"title": "تأثیر قیمت سوخت بر هزینه حمل نهاده‌ها", "summary": "هرگونه تغییر نرخ سوخت مستقیماً روی هزینه حمل کود و بذر اثر می‌گذارد.", "tags": ["#سوخت", "#حمل", "#نهاده", "#هزینه"], "source": "تحلیل کارشناسی", "time": "دیروز", "priority": 4},
    {"title": "توصیه: استفاده از بذر گواهی‌شده در کشت دیم", "summary": "استفاده از بذر گواهی‌شده و ضدعفونی‌شده برای گندم و جو دیم اولویت دارد.", "tags": ["#بذر", "#توصیه", "#دیم"], "source": "دفتر فنی بابامنیر", "time": "امروز", "priority": 4},
]

FAQ_ANSWERS = {
    "هوا": "برای وضعیت هوا و پیش‌بینی، به بخش «خلاصه روز» یا «هواشناسی زنده» بروید. داده هر ۱۵ دقیقه به‌روز می‌شود.",
    "هواشناسی": "برای وضعیت هوا و پیش‌بینی، به بخش «خلاصه روز» یا «هواشناسی زنده» بروید. داده هر ۱۵ دقیقه به‌روز می‌شود.",
    "باران": "احتمال و مقدار بارش را در بخش هواشناسی و جدول ۷ روزه ببینید.",
    "کود": "قیمت کود (مخصوصاً اوره) نوسان شدید دارد. آخرین اطلاعات تقریبی در بخش «قیمت نهاده‌ها» است. حتماً استعلام محلی بگیرید.",
    "اوره": "قیمت کود اوره بر اساس معاملات بورس کالا متغیر است. جزئیات در بخش قیمت نهاده‌ها آمده. استعلام محلی ضروری است.",
    "بذر": "توصیه می‌شود از بذر گواهی‌شده و ضدعفونی‌شده استفاده کنید.",
    "کشت": "شرایط فعلی برای ادامه کشت گندم و جو دیم مناسب است. از بخش توصیه‌های فنی استفاده کنید.",
    "گندم": "کشت گندم در فارس در حال انجام است. توصیه‌های فنی و وضعیت هوا را در بخش‌های مربوطه ببینید.",
    "سوخت": "تغییر قیمت سوخت روی هزینه حمل نهاده اثر مستقیم دارد. اخبار مرتبط را با هشتگ #سوخت فیلتر کنید.",
    "تماس": "واتساپ: ۰۹۱۷۶۸۰۸۷۵۵ | ایتا و روبیکا: @a.d3469",
    "واتساپ": "شماره واتساپ دفتر فنی: ۰۹۱۷۶۸۰۸۷۵۵",
    "قیمت": "قیمت‌های تقریبی نهاده‌ها در بخش «قیمت نهاده‌ها» آمده است. استعلام محلی بگیرید.",
}

def weather_code_to_text(code: int) -> str:
    mapping = {0: "صاف و آفتابی", 1: "عمدتاً صاف", 2: "نیمه‌ابری", 3: "ابری", 45: "مه", 48: "مه یخ‌زده",
               51: "باران ریز", 61: "باران سبک", 63: "باران متوسط", 65: "باران شدید",
               71: "برف سبک", 80: "رگبار", 95: "رعد و برق", 96: "رعد و برق + تگرگ", 99: "رعد و برق شدید"}
    return mapping.get(int(code) if code is not None else -1, "نامشخص")

def wind_direction_to_text(degrees: Optional[float]) -> str:
    if degrees is None: return "نامشخص"
    directions = ["شمال", "شمال‌شرقی", "شرق", "جنوب‌شرقی", "جنوب", "جنوب‌غربی", "غرب", "شمال‌غربی"]
    return directions[int((degrees + 22.5) % 360 // 45)]

def get_shamsi_date() -> str:
    if HAS_JDATETIME:
        now = jdatetime.datetime.now()
        days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
        return f"{days[now.weekday()]} {now.day} {now.j_months_fa[now.month-1]} {now.year}"
    return datetime.now().strftime("%Y-%m-%d")

def get_current_time_str() -> str:
    if HAS_JDATETIME:
        return jdatetime.datetime.now().strftime("%H:%M")
    return datetime.now().strftime("%H:%M")

@st.cache_data(ttl=900, show_spinner=False)
def get_weather(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m", "weather_code", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "apparent_temperature"],
        "hourly": ["temperature_2m", "precipitation_probability", "precipitation", "weather_code", "wind_speed_10m", "et0_fao_evapotranspiration"],
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "precipitation_sum", "weather_code", "wind_speed_10m_max", "et0_fao_evapotranspiration", "uv_index_max", "sunrise", "sunset"],
        "timezone": "Asia/Tehran", "forecast_days": 7
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
        data["_fetched_at"] = datetime.now().isoformat()
        return data
    except Exception:
        return None

@st.cache_data(ttl=900, show_spinner=False)
def get_multiple_weather(names: List[str]) -> Dict[str, Optional[Dict]]:
    results = {}
    def fetch(n):
        info = LOCATIONS[n]
        return n, get_weather(info["lat"], info["lon"])
    with ThreadPoolExecutor(max_workers=4) as ex:
        for f in as_completed([ex.submit(fetch, n) for n in names]):
            name, data = f.result()
            results[name] = data
    return results

def generate_recommendations(weather: Dict[str, Any], location: str) -> List[str]:
    if not weather: return ["داده هواشناسی در دسترس نیست."]
    current = weather.get("current", {})
    daily = weather.get("daily", {})
    temp = current.get("temperature_2m", 20)
    humidity = current.get("relative_humidity_2m", 50)
    wind = current.get("wind_speed_10m", 0)
    precip_prob = daily.get("precipitation_probability_max", [0])[0] if daily else 0
    precip_sum = daily.get("precipitation_sum", [0])[0] if daily else 0
    et0 = daily.get("et0_fao_evapotranspiration", [0])[0] if daily else 0
    code = current.get("weather_code", 0)
    recs = []
    if 8 <= temp <= 22 and precip_prob < 60:
        recs.append(f"**کشت غلات:** شرایط دمایی ({temp:.0f}°C) مناسب کشت گندم و جو دیم است. از بذر گواهی‌شده استفاده کنید.")
    elif temp < 5:
        recs.append("**هشدار سرما:** دمای پایین. از کاشت جدید خودداری کنید.")
    else:
        recs.append(f"**کشت:** دمای فعلی {temp:.0f}°C. با پیش‌بینی ۷ روزه تنظیم کنید.")
    if et0 > 4:
        recs.append(f"**آبیاری:** ET₀ حدود {et0:.1f} mm. نیاز آبی را جدی بگیرید.")
    elif precip_sum > 5:
        recs.append(f"**بارش:** حدود {precip_sum:.1f} mm پیش‌بینی شده. از آبیاری اضافی خودداری کنید.")
    if wind > 15:
        recs.append(f"**سم‌پاشی:** باد {wind:.0f} km/h. از سم‌پاشی خودداری کنید.")
    elif humidity > 80 and precip_prob > 40:
        recs.append("**بیماری قارچی:** رطوبت بالا خطر بیماری برگی را افزایش می‌دهد.")
    else:
        recs.append("**سم‌پاشی:** شرایط نسبتاً مناسب است.")
    recs.append("**کود:** قیمت اوره نوسان دارد. بر اساس آزمون خاک و استعلام محلی مصرف کنید.")
    if code >= 61:
        recs.append("**عملیات مزرعه:** از ورود ماشین‌آلات به مزارع خیس خودداری کنید.")
    return recs

def answer_question(question: str) -> str:
    q = question.strip().lower()
    if not q:
        return "لطفاً سوال خود را بنویسید."
    for key, ans in FAQ_ANSWERS.items():
        if key in q:
            return ans
    return (
        "سوال شما دریافت شد. برای پاسخ دقیق‌تر و مشاوره فنی مستقیم با دفتر فنی در ارتباط باشید:\n\n"
        "📱 واتساپ: ۰۹۱۷۶۸۰۸۷۵۵\n"
        "📲 ایتا و روبیکا: @a.d3469\n\n"
        "همچنین از بخش‌های هواشناسی، قیمت نهاده‌ها و توصیه‌های فنی استفاده کنید."
    )

with st.sidebar:
    st.markdown("### 🌾 از بابامنیر چه خبر")
    st.markdown("---")
    selected_location = st.selectbox("📍 انتخاب منطقه", list(LOCATIONS.keys()), index=0)
    st.markdown("---")
    page = st.radio("بخش‌های داشبورد", [
        "🏠 خلاصه روز",
        "🌤️ هواشناسی زنده",
        "📊 مقایسه مناطق",
        "📰 اخبار و هشتگ‌ها",
        "💬 از من بپرس",
        "💰 قیمت نهاده‌ها",
        "🚜 توصیه‌های فنی",
        "⚙️ تنظیمات و نوتیفیکیشن"
    ], index=0)
    st.markdown("---")
    st.caption(f"🕐 ساعت: {get_current_time_str()}")
    st.caption(f"📅 {get_shamsi_date()}")
    st.caption("واتساپ: ۰۹۱۷۶۸۰۸۷۵۵")
    st.caption("ایتا و روبیکا: @a.d3469")

loc = LOCATIONS[selected_location]
if page in ["🏠 خلاصه روز", "🌤️ هواشناسی زنده", "🚜 توصیه‌های فنی"]:
    with st.spinner("دریافت آخرین داده هواشناسی..."):
        weather = get_weather(loc["lat"], loc["lon"])
else:
    weather = None

if page == "🏠 خلاصه روز":
    st.title("🌾 از بابامنیر چه خبر")
    st.markdown(f"**منطقه:** {selected_location} | **تاریخ:** {get_shamsi_date()} | **ساعت:** {get_current_time_str()}")
    st.markdown("---")
    if weather:
        current = weather["current"]
        daily = weather["daily"]
        hourly = weather.get("hourly", {})
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.metric("دمای فعلی", f"{current['temperature_2m']:.1f}°C", delta=f"احساس {current.get('apparent_temperature', current['temperature_2m']):.1f}°C")
        with c2: st.metric("حداقل / حداکثر", f"{daily['temperature_2m_min'][0]:.0f} / {daily['temperature_2m_max'][0]:.0f}°C")
        with c3: st.metric("رطوبت", f"{current['relative_humidity_2m']}%")
        with c4: st.metric("احتمال بارش", f"{daily['precipitation_probability_max'][0]}%")
        with c5: st.metric("ET₀ امروز", f"{daily.get('et0_fao_evapotranspiration', [0])[0]:.1f} mm")
        st.info(f"**وضعیت فعلی ({get_current_time_str()}):** {weather_code_to_text(current['weather_code'])} | باد: {current['wind_speed_10m']:.0f} km/h از {wind_direction_to_text(current.get('wind_direction_10m'))}")
        st.markdown("### 📈 پیش‌بینی دمای ۷ روزه")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily["time"], y=daily["temperature_2m_max"], mode="lines+markers", name="حداکثر", line=dict(color="#e74c3c", width=2)))
        fig.add_trace(go.Scatter(x=daily["time"], y=daily["temperature_2m_min"], mode="lines+markers", name="حداقل", line=dict(color="#3498db", width=2), fill="tonexty", fillcolor="rgba(52,152,219,0.12)"))
        fig.update_layout(height=340, hovermode="x unified", margin=dict(l=10,r=10,t=30,b=10), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        if hourly and "time" in hourly:
            st.markdown("### 🕐 وضعیت ساعتی (۲۴ ساعت آینده)")
            times = [t[11:16] for t in hourly["time"][:24]]
            fig_h = go.Figure()
            fig_h.add_trace(go.Scatter(x=times, y=hourly["temperature_2m"][:24], mode="lines+markers", name="دما", line=dict(color="#e74c3c")))
            fig_h.add_trace(go.Bar(x=times, y=hourly.get("precipitation", [0]*24)[:24], name="بارش", marker_color="#3498db", opacity=0.5, yaxis="y2"))
            fig_h.update_layout(height=300, yaxis=dict(title="دما"), yaxis2=dict(title="بارش", overlaying="y", side="left", showgrid=False), margin=dict(l=10,r=10,t=20,b=10), legend=dict(orientation="h", y=1.15), hovermode="x unified")
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})
        st.markdown("### ⚡ نکات سریع")
        for r in generate_recommendations(weather, selected_location)[:3]:
            st.markdown(f"- {r}")
    else:
        st.error("دریافت داده هواشناسی با مشکل مواجه شد.")

elif page == "🌤️ هواشناسی زنده":
    st.title(f"🌤️ هواشناسی زنده — {selected_location}")
    st.caption(f"ساعت: {get_current_time_str()} | کش ۱۵ دقیقه")
    if weather:
        current = weather["current"]
        daily = weather["daily"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("شرایط فعلی")
            st.markdown(f"- **دما:** {current['temperature_2m']:.1f}°C\n- **احساس:** {current.get('apparent_temperature', current['temperature_2m']):.1f}°C\n- **رطوبت:** {current['relative_humidity_2m']}%\n- **باد:** {current['wind_speed_10m']:.0f} km/h ({wind_direction_to_text(current.get('wind_direction_10m'))})\n- **وضعیت:** {weather_code_to_text(current['weather_code'])}")
        with col2:
            st.subheader("امروز")
            st.markdown(f"- **حداقل/حداکثر:** {daily['temperature_2m_min'][0]:.0f}/{daily['temperature_2m_max'][0]:.0f}°C\n- **احتمال بارش:** {daily['precipitation_probability_max'][0]}%\n- **بارش:** {daily['precipitation_sum'][0]:.1f} mm\n- **ET₀:** {daily.get('et0_fao_evapotranspiration',[0])[0]:.1f} mm\n- **UV:** {daily.get('uv_index_max',[0])[0]:.1f}")
        with col3:
            st.subheader("منطقه")
            st.markdown(f"- عرض: {loc['lat']}\n- طول: {loc['lon']}\n- ارتفاع: ~{loc.get('elev','—')} متر")
        st.markdown("---")
        st.subheader("جدول ۷ روزه")
        df7 = pd.DataFrame({"تاریخ": daily["time"], "حداقل": [round(x,1) for x in daily["temperature_2m_min"]], "حداکثر": [round(x,1) for x in daily["temperature_2m_max"]], "احتمال بارش": daily["precipitation_probability_max"], "بارش": [round(x,1) for x in daily["precipitation_sum"]], "ET₀": [round(x,1) for x in daily.get("et0_fao_evapotranspiration",[0]*7)], "وضعیت": [weather_code_to_text(c) for c in daily["weather_code"]]})
        st.dataframe(df7, use_container_width=True, hide_index=True)
    else:
        st.error("داده در دسترس نیست.")

elif page == "📊 مقایسه مناطق":
    st.title("📊 مقایسه مناطق فارس")
    selected_locs = st.multiselect("مناطق برای مقایسه", list(LOCATIONS.keys()), default=["بابامنیر", "نورآباد ممسنی", "ماهور میلاتی", "کازرون"])
    if selected_locs:
        with st.spinner("دریافت همزمان داده..."):
            all_w = get_multiple_weather(selected_locs)
        rows = []
        for name in selected_locs:
            w = all_w.get(name)
            if w:
                cur, dai = w["current"], w["daily"]
                rows.append({"منطقه": name, "دما": round(cur["temperature_2m"],1), "رطوبت": cur["relative_humidity_2m"], "باد": round(cur["wind_speed_10m"],0), "حداقل": round(dai["temperature_2m_min"][0],1), "حداکثر": round(dai["temperature_2m_max"][0],1), "احتمال بارش": dai["precipitation_probability_max"][0], "ET₀": round(dai.get("et0_fao_evapotranspiration",[0])[0],1), "وضعیت": weather_code_to_text(cur["weather_code"])})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            fig = go.Figure()
            for row in rows:
                fig.add_trace(go.Bar(name=row["منطقه"], x=["فعلی","حداقل","حداکثر"], y=[row["دما"], row["حداقل"], row["حداکثر"]]))
            fig.update_layout(barmode="group", height=360, margin=dict(l=10,r=10,t=30,b=10), legend=dict(orientation="h", y=1.12))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.warning("داده‌ای دریافت نشد.")
    else:
        st.info("حداقل یک منطقه انتخاب کنید.")

elif page == "📰 اخبار و هشتگ‌ها":
    st.title("📰 اخبار و فیلتر هشتگ")
    all_tags = sorted(set(t for n in SAMPLE_NEWS for t in n["tags"]))
    selected_tags = st.multiselect("فیلتر هشتگ", all_tags)
    filtered = SAMPLE_NEWS
    if selected_tags:
        filtered = [n for n in SAMPLE_NEWS if any(t in n["tags"] for t in selected_tags)]
    filtered = sorted(filtered, key=lambda x: -x["priority"])
    if not filtered:
        st.info("خبری با این هشتگ‌ها یافت نشد.")
    else:
        for news in filtered:
            tags_html = " ".join([f'<span class="tag">{t}</span>' for t in news["tags"]])
            st.markdown(f'<div class="news-card"><strong>{news["title"]}</strong><br><small>{news["time"]} | {news["source"]} | اهمیت: {news["priority"]}/5</small><p style="margin:8px 0 4px 0;">{news["summary"]}</p>{tags_html}</div>', unsafe_allow_html=True)
    st.info("بخش اخبار فعلاً نمونه است و بعداً به منابع زنده متصل می‌شود.")

elif page == "💬 از من بپرس":
    st.title("💬 از من بپرس")
    st.markdown("""
    <div class="ask-box">
        <strong>سوال خود را درباره هوا، کشت، کود، بذر، قیمت یا وضعیت منطقه بنویسید.</strong><br>
        سعی می‌کنم راهنمایی اولیه بدهم. برای مشاوره دقیق‌تر با دفتر فنی در تماس باشید.
    </div>
    """, unsafe_allow_html=True)
    question = st.text_input("سوال شما:", placeholder="مثلاً: وضعیت باران چطوره؟ قیمت اوره چقدره؟")
    if st.button("بپرس", type="primary"):
        if question.strip():
            st.success(answer_question(question))
        else:
            st.warning("لطفاً سوالی بنویسید.")
    st.markdown("---")
    st.markdown("#### سوالات پرتکرار")
    st.markdown("- وضعیت هوا و بارندگی؟\n- قیمت کود اوره؟\n- توصیه برای کشت گندم و جو؟\n- بذر مناسب چیست؟\n- چطور با دفتر فنی تماس بگیرم؟")
    st.info("📱 واتساپ: ۰۹۱۷۶۸۰۸۷۵۵  |  📲 ایتا و روبیکا: @a.d3469")

elif page == "💰 قیمت نهاده‌ها":
    st.title("💰 قیمت روز نهاده‌ها")
    st.warning("قیمت‌ها متغیر است. حتماً استعلام محلی بگیرید.")
    st.markdown("#### بذر")
    st.dataframe(pd.DataFrame({"نهاده": ["بذر گندم نان گواهی‌شده", "بذر گندم دوروم", "بذر جو"], "قیمت تقریبی": ["۶۷–۷۲ هزار", "۷۵–۸۰ هزار", "۶۵–۷۲ هزار"], "واحد": ["کیلو", "کیلو", "کیلو"]}), use_container_width=True, hide_index=True)
    st.markdown("#### کود")
    st.dataframe(pd.DataFrame({"نهاده": ["اوره ۵۰ک", "سوپرفسفات تریپل", "سولفات پتاسیم", "NPK"], "قیمت تقریبی": ["۳٫۱–۳٫۷ میلیون", "۶٫۵–۸ میلیون", "۶–۷٫۵ میلیون", "متغیر"], "واحد": ["کیسه", "کیسه", "کیسه", "کیسه"]}), use_container_width=True, hide_index=True)

elif page == "🚜 توصیه‌های فنی":
    st.title("🚜 توصیه‌های فنی امروز")
    st.markdown(f"**{selected_location}** | {get_shamsi_date()} — {get_current_time_str()}")
    st.markdown("---")
    if weather:
        for i, rec in enumerate(generate_recommendations(weather, selected_location), 1):
            st.markdown(f"**{i}.** {rec}")
        st.markdown("---")
        st.markdown("- از بذر گواهی‌شده استفاده کنید.\n- کود را بر اساس نیاز واقعی مصرف کنید.\n- از ورود ماشین به مزرعه خیس خودداری کنید.")
    else:
        st.error("داده هواشناسی لازم است.")

elif page == "⚙️ تنظیمات و نوتیفیکیشن":
    st.title("⚙️ تنظیمات و نوتیفیکیشن")
    st.markdown("### 🔔 نوتیفیکیشن مرورگر")
    st.write("برای دریافت هشدار، اجازه نوتیفیکیشن را فعال کنید.")
    st.components.v1.html("""
    <button id="notifBtn" style="padding:10px 18px;background:#198754;color:white;border:none;border-radius:8px;cursor:pointer;font-size:15px;font-family:Tahoma;">درخواست مجوز نوتیفیکیشن</button>
    <p id="notifStatus" style="margin-top:10px;font-family:Tahoma;"></p>
    <script>
    const btn=document.getElementById('notifBtn');
    const status=document.getElementById('notifStatus');
    if(!('Notification' in window)){status.innerText='مرورگر پشتیبانی نمی‌کند.';}
    else if(Notification.permission==='granted'){status.innerText='✅ مجوز قبلاً داده شده.';}
    else if(Notification.permission==='denied'){status.innerText='❌ مجوز رد شده. از تنظیمات مرورگر فعال کنید.';}
    btn.onclick=function(){
        Notification.requestPermission().then(function(p){
            if(p==='granted'){
                status.innerText='✅ مجوز داده شد.';
                new Notification('از بابامنیر چه خبر',{body:'نوتیفیکیشن فعال شد.',icon:'https://img.icons8.com/color/96/wheat.png'});
            } else {status.innerText='مجوز داده نشد.';}
        });
    };
    </script>
    """, height=130)
    st.markdown("---")
    st.info("اخبار هواشناسی هر ۱۵ دقیقه به‌روز می‌شود.")
    st.markdown("**مناطق فعلی:** " + "، ".join(LOCATIONS.keys()))

st.markdown("---")
st.markdown(f"<div style='text-align:center;color:#6c757d;font-size:0.85em;'>🌾 از بابامنیر چه خبر | دفتر فنی بابامنیر<br>واتساپ: ۰۹۱۷۶۸۰۸۷۵۵ | ساعت: {get_current_time_str()}</div>", unsafe_allow_html=True)
