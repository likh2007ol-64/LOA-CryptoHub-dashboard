import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_reports_subscription, update_reports_subscription
from utils.theme_manager import get_theme, apply_theme

st.set_page_config(page_title="Отчёты | LOA-CryptoHub", page_icon="📋", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
user_id = user.get("user_id", "")

st.markdown(f"<h1 style='color:{theme['accent1']}'>📋 Отчёты и подписки</h1>", unsafe_allow_html=True)
st.caption(f"Пользователь: {user.get('username', user_id)} | VK ID: {user_id}")

subscription, api_ok = get_reports_subscription(user_id)

if not api_ok:
    st.warning("⚠️ Не удалось загрузить настройки подписки с API.")

st.subheader("📧 Подписка на ежедневные отчёты")

st.markdown(
    f"""
    <div class="metric-card">
        <p>Получайте ежедневные отчёты о состоянии вашего портфеля, ценовых изменениях и аналитику прямо на email или в VK.</p>
        <p style="color:{theme['subtext']}">Отчёты включают: P&L за период, топ монеты, сработавшие уведомления, рекомендации.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("subscription_form"):
    is_subscribed = st.checkbox(
        "Подписаться на отчёты",
        value=subscription.get("subscribed", False),
    )
    email = st.text_input(
        "Email для отчётов",
        value=subscription.get("email", user.get("email", "")),
        placeholder="your@email.com",
    )
    freq_options = ["daily", "weekly", "monthly"]
    current_freq = subscription.get("frequency", "daily")
    freq_index = freq_options.index(current_freq) if current_freq in freq_options else 0
    frequency = st.selectbox(
        "Частота отчётов",
        freq_options,
        index=freq_index,
        format_func=lambda x: {"daily": "Ежедневно", "weekly": "Еженедельно", "monthly": "Ежемесячно"}[x],
    )
    submitted = st.form_submit_button("Сохранить настройки", use_container_width=True)
    if submitted:
        ok = update_reports_subscription(user_id, is_subscribed, email, frequency)
        if is_subscribed:
            st.success(f"✅ Подписка оформлена! Отчёты будут приходить на {email}")
        else:
            st.info("Подписка отменена.")

st.markdown("---")
st.subheader("📊 Доступные типы отчётов")

report_types = [
    {"name": "📈 Портфельный отчёт", "desc": "Полный обзор портфеля: P&L, распределение, динамика", "freq": "Ежедневно"},
    {"name": "💹 Рыночный отчёт", "desc": "Топ-10 монет по изменению цены, объём торгов", "freq": "Ежедневно"},
    {"name": "🔔 Отчёт по уведомлениям", "desc": "Сработавшие оповещения за период", "freq": "По срабатыванию"},
    {"name": "📅 Недельная аналитика", "desc": "Сводка за неделю: лучшие/худшие монеты, P&L", "freq": "Еженедельно"},
    {"name": "📆 Месячный обзор", "desc": "Полная статистика портфеля за месяц, налоговый отчёт", "freq": "Ежемесячно"},
]

cols = st.columns(2)
for i, report in enumerate(report_types):
    with cols[i % 2]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size:1.1em;font-weight:bold;color:{theme['text']}">{report['name']}</div>
                <div style="color:{theme['subtext']};margin:6px 0">{report['desc']}</div>
                <div style="color:{theme['accent1']};font-size:0.85em">Частота: {report['freq']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
