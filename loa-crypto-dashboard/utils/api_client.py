import os
import time
import requests
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_BASE_URL = os.environ.get("API_BASE_URL", "http://153.80.184.34")
REQUEST_TIMEOUT = 10


def _api_get(endpoint, params=None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json(), True
    except Exception:
        return None, False


def _api_post(endpoint, data=None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        resp = requests.post(url, json=data, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json(), True
    except Exception:
        return None, False


def _api_delete(endpoint):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        resp = requests.delete(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json(), True
    except Exception:
        return None, False


@st.cache_data(ttl=30)
def get_prices():
    data, ok = _api_get("/api/v1/prices/")
    if ok and data:
        raw = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(raw, list) and raw:
            transformed = []
            for item in raw:
                transformed.append({
                    "symbol": item.get("symbol", ""),
                    "name": item.get("name", item.get("symbol", "")),
                    "price": float(item.get("price_usd", item.get("price", 0.0))),
                    "change_24h": float(item.get("change_24h", 0.0)),
                    "market_cap": item.get("market_cap", 0),
                    "volume_24h": item.get("volume_24h", 0),
                })
            return transformed, True
    return [], False


def get_user(user_id):
    data, ok = _api_get(f"/api/v1/users/{user_id}")
    if ok and data:
        raw = data.get("data", data) if isinstance(data, dict) and "data" in data else data
        is_admin = raw.get("is_admin", False) or raw.get("role") == "admin"
        plan = raw.get("plan", raw.get("subscription", "free"))
        normalized = {
            "user_id": str(user_id),
            "vk_id": str(user_id),
            "username": raw.get("username", raw.get("name", f"user_{user_id}")),
            "role": "admin" if is_admin else "user",
            "subscription": plan,
            "plan": plan,
            "is_admin": is_admin,
            "email": raw.get("email", ""),
        }
        return normalized, True
    return None, False


def get_portfolio(user_id):
    data, ok = _api_get(f"/api/v1/users/{user_id}/portfolio")
    if ok and data is not None:
        if isinstance(data, list):
            return data, True
        items = data.get("items", data.get("data", data.get("portfolio", [])))
        return items if isinstance(items, list) else [], True
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


def get_alerts(user_id):
    data, ok = _api_get(f"/api/v1/users/{user_id}/alerts")
    if ok and data is not None:
        if isinstance(data, list):
            return data, True
        items = data.get("alerts", data.get("data", []))
        return items if isinstance(items, list) else [], True
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


def get_transactions(user_id):
    data, ok = _api_get(f"/api/v1/users/{user_id}/transactions")
    if ok and data is not None:
        if isinstance(data, list):
            return data, True
        items = data.get("transactions", data.get("data", []))
        return items if isinstance(items, list) else [], True
    return [], False


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


def get_system_status():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = {}

    t0 = time.time()
    health_data, api_ok = _api_get("/health")
    api_latency = int((time.time() - t0) * 1000)
    results["api"] = {
        "status": "ok" if api_ok else "error",
        "latency_ms": api_latency,
        "last_check": now,
    }

    if api_ok and isinstance(health_data, dict):
        components = health_data.get("components", health_data.get("services", {}))
        for key, info in components.items():
            if isinstance(info, dict):
                results[key] = {
                    "status": info.get("status", "unknown"),
                    "latency_ms": info.get("latency_ms", 0),
                    "last_check": now,
                }

    if "database" not in results:
        results["database"] = {"status": "unknown", "latency_ms": 0, "last_check": now}
    if "vk_bot" not in results:
        results["vk_bot"] = {"status": "unknown", "latency_ms": 0, "last_check": now}
    if "coingecko_api" not in results:
        results["coingecko_api"] = {"status": "unknown", "latency_ms": 0, "last_check": now}

    return results, api_ok


def get_all_users():
    data, ok = _api_get("/api/v1/admin/users")
    if ok and data is not None:
        if isinstance(data, list):
            return data, True
        items = data.get("users", data.get("data", []))
        return items if isinstance(items, list) else [], True
    return [], False


def set_subscription(vk_id, plan):
    _, ok = _api_post(
        f"/api/v1/admin/users/{vk_id}/subscription",
        {"plan": plan},
    )
    return ok


def get_logs():
    data, ok = _api_get("/api/v1/admin/logs")
    if ok and data is not None:
        if isinstance(data, list):
            return data, True
        items = data.get("logs", data.get("data", []))
        return items if isinstance(items, list) else [], True
    return [], False


def delete_user_data(user_id):
    _, ok = _api_delete(f"/api/v1/admin/users/{user_id}/data")
    return ok
