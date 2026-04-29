import os
import io
import time
import requests
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_BASE_URL = os.environ.get("API_BASE_URL", "http://153.80.184.34")
REQUEST_TIMEOUT = 10


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _api_get(endpoint, params=None):
    try:
        resp = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json(), True
    except Exception:
        return None, False


def _api_post(endpoint, data=None):
    try:
        resp = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json(), True
    except Exception:
        return None, False


def _api_delete(endpoint):
    try:
        resp = requests.delete(f"{API_BASE_URL}{endpoint}", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json(), True
    except Exception:
        return None, False


def _api_get_raw(endpoint, params=None):
    """Return raw bytes (for CSV downloads)."""
    try:
        resp = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.content, True
    except Exception:
        return None, False


def _extract_list(data, *keys):
    """Try each key in order, return first list found, else []."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in keys:
            val = data.get(k)
            if isinstance(val, list):
                return val
    return []


# ---------------------------------------------------------------------------
# Prices
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def get_prices():
    data, ok = _api_get("/api/v1/prices/")
    if ok and data:
        raw = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(raw, list) and raw:
            return [
                {
                    "symbol":     item.get("symbol", ""),
                    "name":       item.get("name", item.get("symbol", "")),
                    "price":      float(item.get("price_usd", item.get("price", 0.0))),
                    "change_24h": float(item.get("change_24h", 0.0)),
                    "market_cap": item.get("market_cap", 0),
                    "volume_24h": item.get("volume_24h", 0),
                }
                for item in raw
            ], True
    return [], False


# ---------------------------------------------------------------------------
# Users / Auth
# ---------------------------------------------------------------------------

def get_user(user_id):
    data, ok = _api_get(f"/api/v1/users/{user_id}")
    if ok and data:
        raw = data.get("data", data) if isinstance(data, dict) and "data" in data else data
        is_admin = raw.get("is_admin", False) or raw.get("role") == "admin"
        plan = raw.get("plan", raw.get("subscription", "free"))
        return {
            "user_id":      str(user_id),
            "vk_id":        str(user_id),
            "username":     raw.get("username", raw.get("name", f"user_{user_id}")),
            "role":         "admin" if is_admin else "user",
            "subscription": plan,
            "plan":         plan,
            "is_admin":     is_admin,
            "email":        raw.get("email", ""),
        }, True
    return None, False


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

def get_portfolio(user_id):
    data, ok = _api_get(f"/api/v1/users/{user_id}/portfolio")
    if ok and data is not None:
        return _extract_list(data, "items", "data", "portfolio"), True
    return [], False


def add_portfolio_item(user_id, symbol, amount, avg_buy_price):
    _, ok = _api_post(
        f"/api/v1/users/{user_id}/portfolio",
        {"symbol": symbol, "amount": amount, "avg_buy_price": avg_buy_price},
    )
    return ok


def delete_portfolio_item(user_id, symbol):
    _, ok = _api_delete(f"/api/v1/users/{user_id}/portfolio/{symbol}")
    return ok


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

def get_alerts(user_id):
    data, ok = _api_get(f"/api/v1/users/{user_id}/alerts")
    if ok and data is not None:
        return _extract_list(data, "alerts", "data"), True
    return [], False


def create_alert(user_id, symbol, condition, target_price):
    _, ok = _api_post(
        f"/api/v1/users/{user_id}/alerts",
        {"symbol": symbol, "condition": condition, "target_price": target_price},
    )
    return ok


def delete_alert(user_id, alert_id):
    _, ok = _api_delete(f"/api/v1/users/{user_id}/alerts/{alert_id}")
    return ok


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def get_transactions(user_id):
    data, ok = _api_get(f"/api/v1/users/{user_id}/transactions")
    if ok and data is not None:
        return _extract_list(data, "transactions", "data"), True
    return [], False


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def get_reports_subscription(user_id):
    data, ok = _api_get(f"/api/v1/users/{user_id}/reports")
    if ok and data is not None:
        raw = data.get("data", data) if isinstance(data, dict) else {}
        return raw, True
    return {"subscribed": False}, False


def update_reports_subscription(user_id, subscribed, email, frequency):
    _, ok = _api_post(
        "/api/v1/reports",
        {"vk_id": user_id, "subscribed": subscribed, "email": email, "frequency": frequency},
    )
    return ok


# ---------------------------------------------------------------------------
# Wallets
# ---------------------------------------------------------------------------

def get_wallets(user_id):
    data, ok = _api_get(f"/api/v1/users/{user_id}/wallets")
    if ok and data is not None:
        return _extract_list(data, "wallets", "data"), True
    return [], False


def add_wallet(user_id, address, blockchain, label=""):
    _, ok = _api_post(
        f"/api/v1/users/{user_id}/wallets",
        {"address": address, "blockchain": blockchain, "label": label},
    )
    return ok


def delete_wallet(user_id, address):
    _, ok = _api_delete(f"/api/v1/users/{user_id}/wallets/{address}")
    return ok


# ---------------------------------------------------------------------------
# AI Signals
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def get_all_signals():
    data, ok = _api_get("/api/v1/signals")
    if ok and data is not None:
        return _extract_list(data, "signals", "data"), True
    return [], False


@st.cache_data(ttl=60)
def get_signal(symbol):
    data, ok = _api_get(f"/api/v1/signals/{symbol}")
    if ok and data:
        raw = data.get("data", data) if isinstance(data, dict) and "data" in data else data
        return raw, True
    return None, False


# ---------------------------------------------------------------------------
# DeFi Analytics
# ---------------------------------------------------------------------------

@st.cache_data(ttl=120)
def get_tvl():
    data, ok = _api_get("/api/v1/defi/tvl")
    if ok and data:
        raw = data.get("data", data) if isinstance(data, dict) and "data" in data else data
        return raw, True
    return None, False


@st.cache_data(ttl=300)
def get_apy(symbol):
    data, ok = _api_get(f"/api/v1/defi/apy/{symbol}")
    if ok and data:
        raw = data.get("data", data) if isinstance(data, dict) and "data" in data else data
        return raw, True
    return None, False


@st.cache_data(ttl=30)
def get_gas_price():
    data, ok = _api_get("/api/v1/defi/gas")
    if ok and data:
        raw = data.get("data", data) if isinstance(data, dict) and "data" in data else data
        return raw, True
    return None, False


# ---------------------------------------------------------------------------
# System / Admin Monitoring
# ---------------------------------------------------------------------------

def get_system_status():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = {}
    t0 = time.time()
    health_data, api_ok = _api_get("/health")
    api_latency = int((time.time() - t0) * 1000)
    results["api"] = {"status": "ok" if api_ok else "error", "latency_ms": api_latency, "last_check": now}

    if api_ok and isinstance(health_data, dict):
        components = health_data.get("components", health_data.get("services", {}))
        for key, info in components.items():
            if isinstance(info, dict):
                results[key] = {"status": info.get("status", "unknown"), "latency_ms": info.get("latency_ms", 0), "last_check": now}

    for key in ("database", "vk_bot", "coingecko_api"):
        if key not in results:
            results[key] = {"status": "unknown", "latency_ms": 0, "last_check": now}
    return results, api_ok


def get_health_all():
    data, ok = _api_get("/api/v1/admin/health/all")
    if ok and data:
        raw = data.get("data", data) if isinstance(data, dict) and "data" in data else data
        return raw, True
    return {}, False


def get_metrics():
    data, ok = _api_get("/api/v1/admin/metrics")
    if ok and data:
        raw = data.get("data", data) if isinstance(data, dict) and "data" in data else data
        return raw, True
    return {}, False


def get_system_info():
    data, ok = _api_get("/api/v1/admin/system-info")
    if ok and data:
        raw = data.get("data", data) if isinstance(data, dict) and "data" in data else data
        return raw, True
    return {}, False


# ---------------------------------------------------------------------------
# Admin User Management
# ---------------------------------------------------------------------------

def get_all_users():
    data, ok = _api_get("/api/v1/admin/users")
    if ok and data is not None:
        return _extract_list(data, "users", "data"), True
    return [], False


def set_subscription(vk_id, plan):
    _, ok = _api_post(f"/api/v1/admin/users/{vk_id}/subscription", {"plan": plan})
    return ok


def get_logs():
    data, ok = _api_get("/api/v1/admin/logs")
    if ok and data is not None:
        return _extract_list(data, "logs", "data"), True
    return [], False


def delete_user_data(user_id):
    _, ok = _api_delete(f"/api/v1/admin/users/{user_id}/data")
    return ok


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------

def export_portfolio_csv(user_id):
    return _api_get_raw(f"/api/v1/users/{user_id}/portfolio/export")


def export_transactions_csv(user_id):
    return _api_get_raw(f"/api/v1/users/{user_id}/transactions/export")


def export_alerts_csv(user_id):
    return _api_get_raw(f"/api/v1/users/{user_id}/alerts/export")


def export_reports_csv(user_id):
    return _api_get_raw(f"/api/v1/users/{user_id}/reports/export")
