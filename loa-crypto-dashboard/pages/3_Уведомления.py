import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_alerts, create_alert, delete_alert, get_prices
from utils.theme_manager import get_theme, apply_theme

st.set_page_config(page_title="Уведомления | LOA-CryptoHub", page_icon="🔔", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
user_id = user.get("user_id", "")

st.markdown(f"<h1 style='color:{theme['accent1']}'>🔔 Ценовые уведомления</h1>", unsafe_allow_html=True)
st.caption(f"Пользователь: {user.get('username', user_id)} | VK ID: {user_id}")

alerts, alerts_ok = get_alerts(user_id)
prices, prices_ok = get_prices()
price_map = {p["symbol"]: p["price"] for p in prices} if prices else {}

if not alerts_ok:
    st.warning("⚠️ Не удалось загрузить уведомления с API.")

st.subheader("Активные уведомления")

if alerts:
    for alert in alerts:
        symbol = alert.get("symbol", "")
        condition = alert.get("condition", "above")
        target = float(alert.get("target_price", alert.get("price", 0)))
        current = price_map.get(symbol, 0)
        active = alert.get("active", alert.get("is_active", True))
        alert_id = alert.get("id", alert.get("alert_id", ""))

        condition_text = "выше" if condition == "above" else "ниже"
        current_str = f"${current:,.4f}" if current < 1 else f"${current:,.2f}"
        target_str = f"${target:,.4f}" if target < 1 else f"${target:,.2f}"
        status = "🟢 Активно" if active else "⚫ Неактивно"

        if current > 0:
            triggered = (condition == "above" and current >= target) or (condition == "below" and current <= target)
            if triggered:
                st.warning(f"🚨 **СРАБОТАЛО!** {symbol}: цена {current_str} {condition_text} цели {target_str}")

        col_a, col_b = st.columns([5, 1])
        with col_a:
            st.markdown(
                f"""
                <div class="metric-card">
                    <strong style="color:{theme['accent1']}">{symbol}</strong> &nbsp; {status}<br/>
                    Условие: цена <em>{condition_text}</em> {target_str}<br/>
                    <span class="subtext">
                        Текущая цена: {current_str if current > 0 else "N/A"}
                        &nbsp;|&nbsp; Создано: {alert.get('created_at', alert.get('created', 'N/A'))}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_b:
            if st.button("🗑️ Удалить", key=f"del_alert_{alert_id}"):
                ok = delete_alert(user_id, alert_id)
                if ok:
                    st.success("✅ Уведомление удалено!")
                else:
                    st.error("❌ Не удалось удалить уведомление.")
                st.rerun()
else:
    st.info("Нет активных уведомлений.")

st.markdown("---")
st.subheader("➕ Создать уведомление")

with st.form("create_alert_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        symbols = [p["symbol"] for p in prices] if prices else []
        if symbols:
            new_symbol = st.selectbox("Монета", symbols)
        else:
            new_symbol = st.text_input("Тикер монеты", placeholder="BTC")
    with col2:
        new_condition = st.selectbox(
            "Условие",
            ["above", "below"],
            format_func=lambda x: "Выше" if x == "above" else "Ниже",
        )
    with col3:
        current_for_sym = price_map.get(new_symbol, 1.0) if prices else 1.0
        default_target = float(current_for_sym) * 1.05
        new_target = st.number_input(
            "Целевая цена ($)",
            min_value=0.0001,
            value=default_target,
            format="%.4f",
        )

    submitted = st.form_submit_button("Создать уведомление", use_container_width=True)
    if submitted and new_symbol:
        ok = create_alert(user_id, new_symbol, new_condition, new_target)
        if ok:
            st.success(f"✅ Уведомление для {new_symbol} создано!")
            st.rerun()
        else:
            st.error(f"❌ Не удалось создать уведомление. Проверьте подключение к API.")
