"""
داشبورد کامل دفتر فنی بابامنیر - نسخه پیشرفته
شامل: هواشناسی چندمنبعی + تبلیغات چرخشی + اخبار کشاورزی + خدمات فنی + چت هوشمند
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime
import time
import random
import jdatetime
from streamlit.components.v1 import html
from openai import OpenAI

# -----------------------------
# تنظیمات صفحه
# -----------------------------
st.set_page_config(
    page_title="دفتر فنی بابامنیر | گزارش روزانه کشاورزی",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# استایل‌های سفارشی (RTL + انیمیشن)
# -----------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Vazirmatn', Tahoma, sans-serif !important;
        direction: rtl;
    }
    
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* انیمیشن لرزش برای اخبار */
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
        20%, 40%, 60%, 80% { transform: translateX(2px); }
    }
    
    .news-box {
        animation: shake 3s ease-in-out infinite;
        border: 2px solid #e67e22;
        border-radius: 12px;
        padding: 12px;
        background: linear-gradient(135deg, #fff8f0, #fff);
        box-shadow: 0 4px 15px rgba(230, 126, 34, 0.2);
    }
    
    .ad-card {
        border: 2px solid #27ae60;
        border-radius: 12px;
        padding: 16px;
        background: linear-gradient(135deg, #e8f8f0, #fff);
        text-align: center;
        min-height: 180px;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .ad-card:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 25px rgba(39, 174, 96, 0.3);
    }
    
    .service-card {
        border: 2px solid #3498db;
        border-radius: 12px;
        padding: 14px;
        background: linear-gradient(135deg, #ebf5fb, #fff);
        min-height: 140px;
    }
    
    .precip-bar {
        height: 28px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        color: white;
        margin: 8px 0;
        font-size: 14px;
    }
    
    .chat-box {
        border: 2px solid #9b59b6;
        border-radius: 12px;
        padding: 12px;
        background: #f9f5ff;
        max-height: 320px;
        overflow-y: auto;
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
    }
    
    div[data-testid="stSidebar"] {
        background-color: #1a3c34;
    }
    
    div[data-testid="stSidebar"] * {
        color: #ecf0f1 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# داده‌های ثابت
# -----------------------------
LOCATIONS = {
    "بابامنیر": {"lat": 30.07, "lon": 51.52, "name": "بابامنیر"},
    "نورآباد ممسنی": {"lat": 30.11, "lon": 51.52, "name": "نورآباد ممسنی"},
    "ماهور میلاتی": {"lat": 29.95, "lon": 51.45, "name": "ماهور میلاتی"}
}

# ۱۰ تبلیغ نمونه (می‌تونی بعداً عوض کنی)
ADS = [
    {
        "id": 1,
        "title": "تعمیر تخصصی گوشی‌های چینی و سامسونگ",
        "desc": "تعویض ال‌سی‌دی و باتری با گارانتی. مراجعه حضوری یا در محل.",
        "phone": "۰۹۱۷۴۸۰۸۷۵۵",
        "link": "https://t.me/a_d3469",
        "color": "#27ae60"
    },
    {
        "id": 2,
        "title": "بذر گندم گواهی‌شده دیم",
        "desc": "بذر گندم نان و دوروم با گواهی رسمی جهاد کشاورزی. مناسب منطقه بابامنیر.",
        "phone": "۰۹۱۷۴۸۰۸۷۵۵",
        "link": "#",
        "color": "#e67e22"
    },
    {
        "id": 3,
        "title": "فروش کود اوره و سوپرفسفات",
        "desc": "کود اوره ۵۰ کیلویی و سوپرفسفات تریپل با قیمت رقابتی. تحویل در محل.",
        "phone": "۰۹۱۷۴۸۰۸۷۵۵",
        "link": "#",
        "color": "#2980b9"
    },
    {
        "id": 4,
        "title": "خدمات جوشکاری و تعمیر تراکتور",
        "desc": "جوشکاری سیار + تعمیر موتور و گیربکس تراکتور در محل مزرعه.",
        "phone": "۰۹۱۷۴۸۰۸۷۵۵",
        "link": "#",
        "color": "#8e44ad"
    },
    {
        "id": 5,
        "title": "نصب و تعمیر آبگرمکن و یخچال",
        "desc": "خدمات فنی در محل شما. تعمیر تخصصی لوازم خانگی.",
        "phone": "۰۹۱۷۴۸۰۸۷۵۵",
        "link": "#",
        "color": "#c0392b"
    },
    {
        "id": 6,
        "title": "مشاوره رایگان کشت دیم",
        "desc": "مشاوره فنی رایگان برای کشت گندم و جو دیم توسط مهندس افشین دهقان.",
        "phone": "۰۹۱۷۴۸۰۸۷۵۵",
        "link": "#",
        "color": "#16a085"
    },
    {
        "id": 7,
        "title": "فروش سموم و آفت‌کش‌های مجاز",
        "desc": "سموم استاندارد با مشاوره مصرف صحیح. مناسب باغ و زراعت.",
        "phone": "۰۹۱۷۴۸۰۸۷۵۵",
        "link": "#",
        "color": "#d35400"
    },
    {
        "id": 8,
        "title": "اجاره تراکتور و ادوات کشاورزی",
        "desc": "اجاره تراکتور و ادوات خاک‌ورزی با راننده مجرب.",
        "phone": "۰۹۱۷۴۸۰۸۷۵۵",
        "link": "#",
        "color": "#2c3e50"
    },
    {
        "id": 9,
        "title": "تعمیرات برق و الکتروموتور چاه",
        "desc": "تعمیر تخصصی الکتروموتور چاه‌های کشاورزی و سیستم‌های آبیاری.",
        "phone": "۰۹۱۷۴۸۰۸۷۵۵",
        "link": "#",
        "color": "#1abc9c"
    },
    {
        "id": 10,
        "title": "خرید و فروش گوشی کارکرده",
        "desc": "خرید گوشی کارکرده با قیمت منصفانه + فروش گوشی‌های تست‌شده.",
        "phone": "۰۹۱۷۴۸۰۸۷۵۵",
        "link": "#",
        "color": "#9b59b6"
    }
]

# خدمات فنی
TECH_SERVICES = [
    {"title": "تعمیر گوشی", "desc": "چینی، سامسونگ، موتورولا - ال‌سی‌دی و باتری", "icon": "📱"},
    {"title": "تعمیر لوازم خانگی", "desc": "تلویزیون، یخچال، آبگرمکن در محل", "icon": "🔧"},
    {"title": "جوشکاری سیار", "desc": "جوشکاری در محل مزرعه و خانه", "icon": "⚡"},
    {"title": "تعمیر تراکتور", "desc": "موتور، گیربکس و ادوات کشاورزی", "icon": "🚜"},
    {"title": "برق و الکتروموتور", "desc": "چاه کشاورزی و سیستم آبیاری", "icon": "💡"},
    {"title": "مشاوره کشاورزی", "desc": "کشت دیم، کود و سموم", "icon": "🌱"}
]

# اخبار نمونه کشاورزی (با لینک واقعی)
NEWS_ITEMS = [
    {
        "title": "افزایش قیمت کود اوره و تأثیر آن بر کشت دیم",
        "source": "ایرنا",
        "link": "https://www.irna.ir",
        "time": "۲ ساعت پیش"
    },
    {
        "title": "تخصیص سهمیه سوخت تراکتورهای کشاورزی در فارس",
        "source": "ایسنا",
        "link": "https://www.isna.ir",
        "time": "۵ ساعت پیش"
    },
    {
        "title": "هشدار جهاد کشاورزی درباره آبیاری چاه‌های غیرمجاز",
        "source": "تسنیم",
        "link": "https://www.tasnimnews.com",
        "time": "۸ ساعت پیش"
    },
    {
        "title": "شرایط مناسب برای ادامه کشت گندم دیم در مناطق گرمسیر",
        "source": "جهاد کشاورزی فارس",
        "link": "https://www.maj.ir",
        "time": "دیروز"
    },
    {
        "title": "توزیع بذر گواهی‌شده گندم و جو در نورآباد ممسنی",
        "source": "ایرنا فارس",
        "link": "https://www.irna.ir",
        "time": "دیروز"
    },
    {
        "title": "پیش‌بینی بارش‌های پراکنده در هفته آینده",
        "source": "هواشناسی فارس",
        "link": "https://www.irimo.ir",
        "time": "امروز"
    }
]

# -----------------------------
# توابع کمکی
# -----------------------------
@st.cache_data(ttl=1800)
def get_weather_multi(lat, lon):
    """دریافت داده از Open-Meteo با چند مدل (شبیه‌سازی ۵ منبع)"""
    models = ["best_match", "ecmwf_ifs", "gfs_seamless", "icon_seamless", "gem_seamless"]
    results = {}
    
    for model in models:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m,precipitation",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,weather_code,et0_fao_evapotranspiration",
                "timezone": "Asia/Tehran",
                "forecast_days": 7,
                "models": model
            }
            r = requests.get(url, params=params, timeout=8)
            if r.status_code == 200:
                results[model] = r.json()
        except:
            continue
    
    # اگر هیچ مدلی نیامد، حداقل best_match را بگیر
    if not results:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,weather_code,et0_fao_evapotranspiration",
                "timezone": "Asia/Tehran",
                "forecast_days": 7
            }
            r = requests.get(url, params=params, timeout=10)
            results["best_match"] = r.json()
        except Exception as e:
            st.error(f"خطا در دریافت داده هواشناسی: {e}")
            return None
    
    return results

def weather_code_to_text(code):
    mapping = {
        0: "صاف و آفتابی", 1: "عمدتاً صاف", 2: "نیمه‌ابری", 3: "ابری",
        45: "مه", 48: "مه یخ‌زده",
        51: "باران ریز", 53: "باران سبک", 55: "باران متوسط",
        61: "باران سبک", 63: "باران متوسط", 65: "باران شدید",
        71: "برف سبک", 80: "رگبار", 95: "رعد و برق"
    }
    return mapping.get(code, "نامشخص")

def get_precip_color(prob):
    """رنگ نوار احتمال بارش"""
    if prob == 0:
        return "#85c1e9"  # آبی کمرنگ
    elif prob < 30:
        return "#aab7b8"  # خاکستری ابری
    elif prob < 60:
        return "#7f8c8d"  # ابری تیره‌تر
    else:
        return "#5d6d7e"  # رنگ ابر بارانی

def get_shamsi_date():
    try:
        now = jdatetime.datetime.now()
        days = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
        return f"{days[now.weekday()]} {now.day} {now.j_months_fa[now.month-1]} {now.year}"
    except:
        return datetime.now().strftime("%Y-%m-%d")

def get_grok_client():
    """ایجاد کلاینت Grok با استفاده از API Key از Secrets"""
    api_key = st.secrets.get("XAI_API_KEY", None)
    if not api_key:
        return None
    return OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )

def call_grok(question: str, history: list = None) -> str:
    """
    فراخوانی واقعی Grok API
    اگر API Key نباشد، به پاسخ ساده برمی‌گردد.
    """
    client = get_grok_client()
    
    if client is None:
        # حالت بدون API Key (پاسخ ساده)
        return (
            "⚠️ کلید API گروک تنظیم نشده است.\n\n"
            "برای فعال‌سازی چت واقعی با Grok:\n"
            "1. به console.x.ai بروید و API Key بسازید\n"
            "2. در Streamlit Cloud → Settings → Secrets این خط را اضافه کنید:\n"
            'XAI_API_KEY = "xai-..."\n\n'
            "فعلاً می‌توانید با شماره ۰۹۱۷۴۸۰۸۷۵۵ تماس بگیرید."
        )
    
    system_prompt = """تو مشاور هوشمند دفتر فنی بابامنیر هستی، زیر نظر مهندس افشین دهقان.
منطقه فعالیت: بابامنیر، نورآباد ممسنی و ماهور میلاتی در استان فارس.
تخصص‌ها: کشاورزی دیم (گندم و جو)، کود و سموم، خدمات فنی (تعمیر گوشی، لوازم خانگی، تراکتور، چاه کشاورزی).
شماره تماس: ۰۹۱۷۴۸۰۸۷۵۵ | ایتا و روبیکا: @a.d3469

قوانین پاسخ:
- همیشه به فارسی و محترمانه جواب بده.
- اگر سوال کشاورزی است، راهنمایی عملی و محلی بده.
- اگر سوال فنی است، خدمات دفتر را معرفی کن.
- اگر نمی‌دانی، صادقانه بگو و پیشنهاد تماس با مهندس دهقان را بده.
- پاسخ‌ها را کوتاه، مفید و قابل اجرا نگه دار."""

    messages = [{"role": "system", "content": system_prompt}]
    
    # اضافه کردن تاریخچه محدود (آخرین ۴ پیام)
    if history:
        for msg in history[-4:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": question})
    
    try:
        response = client.chat.completions.create(
            model="grok-4-1-fast-reasoning",   # مدل سریع و مناسب
            messages=messages,
            temperature=0.7,
            max_tokens=600
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"خطا در ارتباط با Grok: {str(e)}\n\nلطفاً چند لحظه دیگر دوباره تلاش کنید یا با ۰۹۱۷۴۸۰۸۷۵۵ تماس بگیرید."

# -----------------------------
# سایدبار
# -----------------------------
with st.sidebar:
    st.markdown("### 🌾 دفتر فنی بابامنیر")
    st.caption("زیر نظر مهندس افشین دهقان")
    st.markdown("---")
    
    selected_location = st.selectbox(
        "📍 انتخاب منطقه",
        list(LOCATIONS.keys()),
        index=0
    )
    
    st.markdown("---")
    st.markdown("#### بخش‌های داشبورد")
    page = st.radio(
        "صفحه",
        ["🏠 صفحه اصلی", "📱 خدمات موبایل", "🛠️ تعمیرات لوازم خانگی", 
         "📝 ثبت سوال و درخواست", "💰 قیمت نهاده‌ها", "🚜 توصیه‌های فنی"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("**تماس:** ۰۹۱۷۴۸۰۸۷۵۵")
    st.markdown("**ایتا و روبیکا:** @a.d3469")
    st.caption("داده هواشناسی: Open-Meteo (چند مدل)")

# -----------------------------
# دریافت داده هواشناسی
# -----------------------------
loc = LOCATIONS[selected_location]
weather_data = get_weather_multi(loc["lat"], loc["lon"])

# -----------------------------
# صفحه اصلی (لی‌اوت جدید)
# -----------------------------
if page == "🏠 صفحه اصلی":
    
    # ردیف بالا: اخبار (چپ) + عنوان (وسط)
    col_news, col_title = st.columns([1, 2])
    
    with col_news:
        st.markdown("#### 📰 اخبار کشاورزی")
        news_html = '<div class="news-box">'
        for item in NEWS_ITEMS[:5]:
            news_html += f'''
            <div style="margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:6px;">
                <a href="{item['link']}" target="_blank" style="color:#2c3e50; text-decoration:none; font-weight:500;">
                    {item['title']}
                </a>
                <br>
                <small style="color:#7f8c8d;">{item['source']} • {item['time']}</small>
            </div>
            '''
        news_html += '</div>'
        st.markdown(news_html, unsafe_allow_html=True)
    
    with col_title:
        st.title("🌾 گزارش روزانه کشاورزی بابامنیر")
        st.markdown(f"**منطقه:** {selected_location} | **تاریخ:** {get_shamsi_date()}")
        
        # بنر تبلیغاتی ثابت
        st.markdown("""
        <div style="background:#1a3c34; color:white; padding:10px 16px; border-radius:8px; text-align:center; margin:8px 0;">
            📱 تعمیر تخصصی گوشی‌های چینی، سامسونگ و موتورولا — تعویض ال‌سی‌دی و باتری | ۰۹۱۷۴۸۰۸۷۵۵
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ردیف اصلی: چت (چپ) + هواشناسی (وسط) + تبلیغات و خدمات (راست)
    col_chat, col_weather, col_ads = st.columns([1, 2, 1])
    
    # ----- ستون چپ: چت -----
    with col_chat:
        st.markdown("#### 💬 پرسش از مشاور")
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "assistant", "content": "سلام! سوال کشاورزی یا خدمات فنی خود را بپرسید."}
            ]
        
        chat_container = st.container()
        with chat_container:
            st.markdown('<div class="chat-box">', unsafe_allow_html=True)
            for msg in st.session_state.chat_history[-6:]:
                if msg["role"] == "user":
                    st.markdown(f"**شما:** {msg['content']}")
                else:
                    st.markdown(f"**مشاور:** {msg['content']}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.form("chat_form", clear_on_submit=True):
            user_q = st.text_input("سوال خود را بنویسید...", key="chat_input", label_visibility="collapsed")
            submitted = st.form_submit_button("ارسال 🚀")
            
            if submitted and user_q.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_q})
                
                with st.spinner("در حال فکر کردن با Grok..."):
                    # ارسال تاریخچه برای حفظ زمینه گفتگو
                    answer = call_grok(user_q, st.session_state.chat_history)
                
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()
    
    # ----- ستون وسط: هواشناسی -----
    with col_weather:
        st.markdown("#### 🌤️ وضعیت هواشناسی (چندمنبعی)")
        
        if weather_data:
            # استفاده از بهترین مدل موجود
            main_model = list(weather_data.keys())[0]
            data = weather_data[main_model]
            current = data.get("current", {})
            daily = data.get("daily", {})
            
            # متریک‌ها
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.metric("دمای فعلی", f"{current.get('temperature_2m', 0):.1f}°C")
            with m2:
                st.metric("رطوبت", f"{current.get('relative_humidity_2m', 0)}%")
            with m3:
                tmax = daily.get('temperature_2m_max', [0])[0]
                tmin = daily.get('temperature_2m_min', [0])[0]
                st.metric("حداقل / حداکثر", f"{tmin:.0f} / {tmax:.0f}°C")
            with m4:
                precip_prob = daily.get('precipitation_probability_max', [0])[0]
                st.metric("احتمال بارش", f"{precip_prob}%")
            with m5:
                et0 = daily.get('et0_fao_evapotranspiration', [0])[0]
                st.metric("ET₀", f"{et0:.1f} mm")
            
            # وضعیت فعلی
            code = current.get('weather_code', 0)
            wind = current.get('wind_speed_10m', 0)
            st.info(f"**وضعیت فعلی:** {weather_code_to_text(code)} | باد: {wind} km/h")
            
            # نوار احتمال بارش (نارنجی / رنگی)
            precip_prob = daily.get('precipitation_probability_max', [0])[0]
            color = get_precip_color(precip_prob)
            st.markdown(f"""
            <div class="precip-bar" style="background:{color};">
                احتمال بارش امروز: {precip_prob}% — منبع: Open-Meteo (مدل‌های ترکیبی)
            </div>
            """, unsafe_allow_html=True)
            
            # نمودار ۷ روزه
            if "time" in daily:
                df = pd.DataFrame({
                    "تاریخ": daily["time"],
                    "حداکثر": daily["temperature_2m_max"],
                    "حداقل": daily["temperature_2m_min"]
                })
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df["تاریخ"], y=df["حداکثر"],
                    mode="lines+markers", name="حداکثر",
                    line=dict(color="#e74c3c", width=3)
                ))
                fig.add_trace(go.Scatter(
                    x=df["تاریخ"], y=df["حداقل"],
                    mode="lines+markers", name="حداقل",
                    line=dict(color="#3498db", width=3)
                ))
                fig.update_layout(
                    title="پیش‌بینی دمای ۷ روز آینده",
                    height=320,
                    margin=dict(l=20, r=20, t=40, b=20),
                    hovermode="x unified",
                    legend=dict(orientation="h", y=1.1)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # نمایش منابع (شبیه‌سازی ۵ سایت)
            st.caption(f"منابع داده: {', '.join(weather_data.keys())} | به‌روزرسانی خودکار هر ۳۰ دقیقه")
        else:
            st.error("دریافت داده هواشناسی با مشکل مواجه شد.")
    
    # ----- ستون راست: تبلیغات چرخشی + خدمات فنی -----
    with col_ads:
        st.markdown("#### 📢 تبلیغات")
        
        # تبلیغات چرخشی با fragment
        @st.fragment(run_every=2)
        def ads_carousel():
            if "ad_index" not in st.session_state:
                st.session_state.ad_index = 0
            
            ad = ADS[st.session_state.ad_index % len(ADS)]
            
            st.markdown(f"""
            <div class="ad-card" style="border-color:{ad['color']};">
                <h4 style="color:{ad['color']}; margin:0 0 8px 0;">{ad['title']}</h4>
                <p style="font-size:13px; color:#555; margin:0 0 10px 0;">{ad['desc']}</p>
                <p style="font-weight:600; margin:0;">📞 {ad['phone']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # دکمه جزئیات
            if st.button("مشاهده جزئیات تبلیغ", key=f"ad_detail_{st.session_state.ad_index}"):
                st.session_state.selected_ad = ad
            
            st.session_state.ad_index += 1
        
        ads_carousel()
        
        # نمایش جزئیات تبلیغ انتخاب‌شده
        if "selected_ad" in st.session_state:
            ad = st.session_state.selected_ad
            with st.expander("📋 جزئیات تبلیغ", expanded=True):
                st.markdown(f"**{ad['title']}**")
                st.write(ad['desc'])
                st.write(f"تماس: {ad['phone']}")
                if ad['link'] and ad['link'] != "#":
                    st.markdown(f"[لینک مرتبط]({ad['link']})")
                if st.button("بستن"):
                    del st.session_state.selected_ad
                    st.rerun()
        
        st.markdown("---")
        st.markdown("#### 🛠️ خدمات فنی")
        
        # خدمات فنی چرخشی
        @st.fragment(run_every=3)
        def services_carousel():
            if "svc_index" not in st.session_state:
                st.session_state.svc_index = 0
            
            svc = TECH_SERVICES[st.session_state.svc_index % len(TECH_SERVICES)]
            
            st.markdown(f"""
            <div class="service-card">
                <div style="font-size:28px; margin-bottom:6px;">{svc['icon']}</div>
                <h5 style="margin:0 0 6px 0;">{svc['title']}</h5>
                <p style="font-size:13px; color:#555; margin:0;">{svc['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state.svc_index += 1
        
        services_carousel()
        
        st.caption("برای درخواست خدمات با ۰۹۱۷۴۸۰۸۷۵۵ تماس بگیرید")

# -----------------------------
# صفحات دیگر (حفظ قابلیت‌های قبلی)
# -----------------------------
elif page == "📱 خدمات موبایل":
    st.title("📱 خدمات موبایل")
    st.markdown("کلیه کارهای فنی و تعمیراتی توسط تعمیرکار مجرب انجام می‌شود.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔧 تعمیرات تخصصی")
        st.markdown("""
        **انواع گوشی‌های تحت پوشش:**
        - گوشی‌های چینی (شیائومی، آنر، هواوی، پوکو و ...)
        - سامسونگ (تمام سری‌ها)
        - موتورولا
        
        **خدمات قابل ارائه:**
        - تعویض ال‌سی‌دی و تاچ
        - تعویض باتری اصل و فیک
        - تعمیرات برد و ریزکاری
        - حل مشکلات نرم‌افزاری و آنلاک
        - تعویض درب پشت، قاب و قطعات جانبی
        - گارانتی خدمات انجام‌شده
        """)
    with col2:
        st.markdown("### 💰 خرید و فروش")
        st.markdown("""
        - خرید گوشی کارکرده با قیمت منصفانه
        - فروش گوشی‌های سالم و تست‌شده
        - معاوضه گوشی
        - مشاوره قبل از خرید
        - کارشناسی گوشی در محل
        """)
    
    st.success("برای ثبت درخواست تعمیر یا خرید و فروش با شماره ۰۹۱۷۴۸۰۸۷۵۵ تماس بگیرید یا در ایتا پیام دهید.")

elif page == "🛠️ تعمیرات لوازم خانگی":
    st.title("🛠️ تعمیرات لوازم خانگی و خدمات در محل")
    st.markdown("خدمات فنی در محل شما انجام می‌شود.")
    
    st.markdown("""
    **خدمات قابل ارائه:**
    - تنظیمات و تعمیر تلویزیون
    - تعمیر و سرویس آبگرمکن
    - تعمیر یخچال و فریزر
    - نصب و تعمیر کابینت
    - جوشکاری سیار
    - پیک‌نیک پر کنی در محل
    - سایر خدمات فنی ساختمانی و خانگی
    """)
    st.info("برای هماهنگی و اعزام تعمیرکار با شماره ۰۹۱۷۴۸۰۸۷۵۵ تماس بگیرید.")

elif page == "📝 ثبت سوال و درخواست":
    st.title("📝 ثبت سوال و درخواست")
    st.markdown("سوالات خود را در زمینه کشاورزی، خدمات فنی، نرم‌افزار گوشی یا سایر موضوعات بنویسید. پاسخ از طریق تماس یا پیام اعلام می‌شود.")
    
    with st.form("request_form"):
        name = st.text_input("نام و نام خانوادگی")
        contact = st.text_input("شماره تماس یا ایمیل")
        subject = st.selectbox("موضوع سوال", [
            "مشکلات کشاورزی و باغداری",
            "خدمات تعمیرات موبایل",
            "تعمیرات لوازم خانگی",
            "قیمت نهاده‌ها",
            "سایر"
        ])
        message = st.text_area("متن سوال یا درخواست", height=150)
        submitted = st.form_submit_button("ارسال سوال")
        
        if submitted:
            if name and contact and message:
                st.success("✅ سوال شما با موفقیت ثبت شد. در اسرع وقت پاسخ داده خواهد شد.")
                # اینجا می‌تونی به دیتابیس یا ایمیل وصل کنی
            else:
                st.warning("لطفاً تمام فیلدها را پر کنید.")

elif page == "💰 قیمت نهاده‌ها":
    st.title("💰 قیمت روز نهاده‌های کشاورزی")
    st.warning("⚠️ قیمت کودها به‌شدت متغیر است. استعلام محلی از کارگزاری نورآباد و جهاد کشاورزی ممسنی ضروری است.")
    
    prices_data = {
        "نهاده": [
            "بذر گندم نان گواهی‌شده",
            "بذر گندم دوروم گواهی‌شده",
            "بذر جو گواهی‌شده",
            "کود اوره ۵۰ کیلویی (بازار)",
            "سوپرفسفات تریپل ۵۰ک",
            "سولفات پتاسیم ۵۰ک"
        ],
        "قیمت تقریبی (تومان)": [72000, 75600, 72000, 3600000, 7500000, 6900000],
        "واحد": ["کیلوگرم", "کیلوگرم", "کیلوگرم", "کیسه", "کیسه", "کیسه"],
        "توضیح": [
            "با یارانه برای دیم واجد شرایط",
            "بدون یارانه مستقیم",
            "با یارانه برای طبقات دیم",
            "نوسان شدید - نیازمند استعلام محلی",
            "بازار آزاد تقریبی",
            "بازار آزاد تقریبی"
        ]
    }
    st.dataframe(pd.DataFrame(prices_data), use_container_width=True, hide_index=True)

elif page == "🚜 توصیه‌های فنی":
    st.title("🚜 توصیه‌های فنی امروز")
    
    recommendations = [
        "با توجه به شرایط فعلی هوا، فرصت مناسبی برای ادامه کشت گندم و جو دیم وجود دارد. از بذر گواهی‌شده استفاده کنید.",
        "به دلیل نوسان شدید قیمت کود اوره، مصرف را بر اساس آزمون خاک و نیاز واقعی گیاه تنظیم کنید.",
        "خطر یخبندان فعلاً پایین است، اما شب‌ها خنک می‌شود؛ مراقب شبنم صبحگاهی باشید.",
        "قبل از هرگونه سم‌پاشی، سرعت باد و رطوبت را بررسی کنید.",
        "برای جلوگیری از هدررفت آب، آبیاری را در ساعات خنک روز انجام دهید."
    ]
    for i, rec in enumerate(recommendations, 1):
        st.markdown(f"**{i}.** {rec}")
        st.markdown("---")

# -----------------------------
# فوتر
# -----------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
        🌱 دفتر فنی و خدمات کشاورزی بابامنیر<br>
        مشاوره | اطلاع‌رسانی | خدمات فنی و کشاورزی<br>
        تماس: ۰۹۱۷۴۸۰۸۷۵۵ | ایتا و روبیکا: @a.d3469
    </div>
    """,
    unsafe_allow_html=True
)
