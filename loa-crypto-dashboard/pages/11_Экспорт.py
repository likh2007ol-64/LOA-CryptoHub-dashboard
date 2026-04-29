import streamlit as st
import pandas as pd
import io
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import (
    export_portfolio_csv, export_transactions_csv,
    export_alerts_csv, export_reports_csv,
    get_portfolio, get_transactions, get_alerts, get_reports_subscription,
)
from utils.theme_manager import get_theme, apply_theme

st.set_page_config(page_title="Экспорт | LOA-CryptoHub", page_icon="📥", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
user_id = user.get("user_id", "")

st.markdown(f"<h1 style='color:{theme['accent1']}'>📥 Экспорт данных</h1>", unsafe_allow_html=True)
st.caption(f"Пользователь: {user.get('username', user_id)} | VK ID: {user_id}")


def _make_csv_from_list(data):
    if not data:
        return b""
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode("utf-8")


def _get_download_data(api_fn, fallback_fn, fallback_arg):
    raw, ok = api_fn(fallback_arg)
    if ok and raw:
        return raw, True
    fallback_data, _ = fallback_fn(fallback_arg)
    return _make_csv_from_list(fallback_data), False


st.subheader("Выберите данные для экспорта")

st.markdown(
    f"""
    <div class="metric-card">
        <p style="color:{theme['subtext']}">
            Скачайте ваши данные в формате CSV для дальнейшего анализа в Excel, Google Sheets или других инструментах.
            Если API-эндпоинт экспорта недоступен, CSV генерируется локально из текущих данных.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""<div class="metric-card">
            <div style="font-size:1.2em;font-weight:bold;color:{theme['text']}">💼 Портфель</div>
            <p style="color:{theme['subtext']}">Список монет, количество, цена покупки, текущая стоимость.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("📥 Скачать портфель (CSV)", use_container_width=True, key="dl_portfolio"):
        with st.spinner("Подготовка файла..."):
            csv_data, from_api = _get_download_data(export_portfolio_csv, get_portfolio, user_id)
        if csv_data:
            st.download_button(
                label="⬇️ Скачать portfolio.csv",
                data=csv_data,
                file_name=f"portfolio_{user_id}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            if not from_api:
                st.caption("ℹ️ CSV сгенерирован локально — эндпоинт `/portfolio/export` в разработке")
        else:
            st.warning("Портфель пуст или данные недоступны.")

with col2:
    st.markdown(
        f"""<div class="metric-card">
            <div style="font-size:1.2em;font-weight:bold;color:{theme['text']}">📜 История транзакций</div>
            <p style="color:{theme['subtext']}">Все покупки и продажи с датами, суммами и ценами.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("📥 Скачать транзакции (CSV)", use_container_width=True, key="dl_transactions"):
        with st.spinner("Подготовка файла..."):
            csv_data, from_api = _get_download_data(export_transactions_csv, get_transactions, user_id)
        if csv_data:
            st.download_button(
                label="⬇️ Скачать transactions.csv",
                data=csv_data,
                file_name=f"transactions_{user_id}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            if not from_api:
                st.caption("ℹ️ CSV сгенерирован локально — эндпоинт `/transactions/export` в разработке")
        else:
            st.warning("История транзакций пуста или недоступна.")

col3, col4 = st.columns(2)

with col3:
    st.markdown(
        f"""<div class="metric-card">
            <div style="font-size:1.2em;font-weight:bold;color:{theme['text']}">🔔 Уведомления (алерты)</div>
            <p style="color:{theme['subtext']}">Список настроенных ценовых алертов.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("📥 Скачать алерты (CSV)", use_container_width=True, key="dl_alerts"):
        with st.spinner("Подготовка файла..."):
            csv_data, from_api = _get_download_data(export_alerts_csv, get_alerts, user_id)
        if csv_data:
            st.download_button(
                label="⬇️ Скачать alerts.csv",
                data=csv_data,
                file_name=f"alerts_{user_id}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            if not from_api:
                st.caption("ℹ️ CSV сгенерирован локально — эндпоинт `/alerts/export` в разработке")
        else:
            st.warning("Алерты не найдены или недоступны.")

with col4:
    st.markdown(
        f"""<div class="metric-card">
            <div style="font-size:1.2em;font-weight:bold;color:{theme['text']}">📋 Настройки отчётов</div>
            <p style="color:{theme['subtext']}">Параметры подписки на ежедневные отчёты.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("📥 Скачать отчёты (CSV)", use_container_width=True, key="dl_reports"):
        with st.spinner("Подготовка файла..."):
            raw, ok = export_reports_csv(user_id)
            if ok and raw:
                csv_data = raw
                from_api = True
            else:
                sub, _ = get_reports_subscription(user_id)
                sub_list = [sub] if sub else []
                csv_data = _make_csv_from_list(sub_list)
                from_api = False
        if csv_data:
            st.download_button(
                label="⬇️ Скачать reports.csv",
                data=csv_data,
                file_name=f"reports_{user_id}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            if not from_api:
                st.caption("ℹ️ CSV сгенерирован локально — эндпоинт `/reports/export` в разработке")
        else:
            st.warning("Данные отчётов недоступны.")

st.markdown("---")
st.subheader("📊 Полный экспорт (все данные)")

if st.button("📦 Скачать все данные одним архивом", use_container_width=True):
    st.info("⚙️ Функция пакетного экспорта в разработке. Используйте кнопки выше для скачивания по разделам.")
