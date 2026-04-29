import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.api_client import get_wallets, add_wallet, delete_wallet
from utils.theme_manager import get_theme, apply_theme

st.set_page_config(page_title="Кошельки | LOA-CryptoHub", page_icon="👛", layout="wide")

theme = get_theme(st.session_state.get("theme_name", "Тёмная"))
apply_theme(theme)

if st.session_state.get("user") is None:
    st.warning("⚠️ Пожалуйста, войдите через VK ID на главной странице.")
    st.stop()

user = st.session_state.user
user_id = user.get("user_id", "")

st.markdown(f"<h1 style='color:{theme['accent1']}'>👛 Мои кошельки</h1>", unsafe_allow_html=True)
st.caption(f"Пользователь: {user.get('username', user_id)} | VK ID: {user_id}")

BLOCKCHAIN_NAMES = {
    "ETH": "Ethereum",
    "BSC": "BNB Chain",
    "SOL": "Solana",
    "BTC": "Bitcoin",
    "MATIC": "Polygon",
    "AVAX": "Avalanche",
    "TRX": "Tron",
    "ARB": "Arbitrum",
}

wallets, api_ok = get_wallets(user_id)

if not api_ok:
    st.warning("⚠️ Не удалось загрузить кошельки с API.")

if wallets:
    total_wallets = len(wallets)
    blockchains = list({w.get("blockchain", "?") for w in wallets})

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего кошельков", total_wallets)
    with col2:
        st.metric("Блокчейны", len(blockchains))
    with col3:
        total_balance = sum(float(w.get("balance_usd", 0) or 0) for w in wallets)
        st.metric("Общий баланс (USD)", f"${total_balance:,.2f}")

    st.markdown("---")
    st.subheader("Список кошельков")

    for w in wallets:
        addr = w.get("address", "")
        chain = w.get("blockchain", "?")
        label = w.get("label", w.get("name", ""))
        balance = float(w.get("balance_usd", 0) or 0)
        balance_native = w.get("balance_native", "")
        last_activity = w.get("last_activity", w.get("updated_at", "N/A"))
        wallet_id = w.get("id", w.get("wallet_id", addr))

        col_info, col_del = st.columns([6, 1])
        with col_info:
            chain_full = BLOCKCHAIN_NAMES.get(chain, chain)
            addr_short = f"{addr[:8]}...{addr[-6:]}" if len(addr) > 16 else addr
            native_str = f" | {balance_native}" if balance_native else ""
            st.markdown(
                f"""
                <div class="metric-card">
                    <div style="display:flex;align-items:center;gap:12px">
                        <span style="font-size:1.3em">🔗</span>
                        <div>
                            <strong style="color:{theme['accent1']}">{label or addr_short}</strong>
                            <span style="color:{theme['subtext']}"> — {chain_full} ({chain})</span><br/>
                            <span style="color:{theme['subtext']};font-size:0.85em;font-family:monospace">{addr}</span><br/>
                            <span>Баланс: <strong>${balance:,.2f}</strong>{native_str}</span>
                            <span style="color:{theme['subtext']};font-size:0.8em"> | Активность: {last_activity}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_del:
            if st.button("🗑️", key=f"del_wallet_{wallet_id}", help="Удалить кошелёк"):
                ok = delete_wallet(user_id, addr)
                if ok:
                    st.success(f"✅ Кошелёк {addr_short} удалён")
                else:
                    st.error("❌ Не удалось удалить кошелёк")
                st.rerun()
else:
    st.info("Кошельки не добавлены. Добавьте первый кошелёк ниже.")

st.markdown("---")
st.subheader("➕ Добавить кошелёк")

with st.form("add_wallet_form"):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        new_address = st.text_input("Адрес кошелька", placeholder="0x..., 1A2B3C..., etc.")
    with col_b:
        new_blockchain = st.selectbox(
            "Блокчейн",
            list(BLOCKCHAIN_NAMES.keys()),
            format_func=lambda x: f"{x} — {BLOCKCHAIN_NAMES[x]}",
        )
    with col_c:
        new_label = st.text_input("Метка (необязательно)", placeholder="Мой основной кошелёк")

    submitted = st.form_submit_button("Добавить кошелёк", use_container_width=True)
    if submitted:
        if new_address.strip():
            ok = add_wallet(user_id, new_address.strip(), new_blockchain, new_label.strip())
            if ok:
                st.success(f"✅ Кошелёк {new_address[:12]}... добавлен!")
                st.rerun()
            else:
                st.error("❌ Не удалось добавить кошелёк. Проверьте адрес и подключение к API.")
        else:
            st.warning("Введите адрес кошелька.")

st.markdown("---")
st.subheader("ℹ️ Поддерживаемые блокчейны")
cols = st.columns(4)
for i, (code, name) in enumerate(BLOCKCHAIN_NAMES.items()):
    with cols[i % 4]:
        st.markdown(
            f"""<div class="metric-card" style="text-align:center;padding:12px">
                <div style="font-weight:bold;color:{theme['accent1']}">{code}</div>
                <div style="color:{theme['subtext']};font-size:0.85em">{name}</div>
            </div>""",
            unsafe_allow_html=True,
        )
