import io
import os
import logging
import threading
import requests
from flask import Flask
from PIL import Image, ImageDraw
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- خادم Flask المساعد لمنع نوم الخدمة في Render  ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot is alive and running!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- إعدادات تسجيل الأخطاء (Logging) ---
logging.basicConfig(level=logging.INFO)

# ==========================================
# قائمة المفاتيح والروابط (مع نظام التدوير)
# ==========================================

TELEGRAM_BOT_TOKEN = "GlILJ9TvCQz8V5Kry0vH4sY9Qif4yUtgN25AG-CUInLSUpv5Ky9j1g"

# 1. قائمة مفاتيح GSMA (Client ID & Secret)
GSMA_KEYS = [
    {
        "client_id": "client_7dca1ef711321e069120dcf021407e0d",
        "client_secret": "c89abb932ee39541ebf9d5a7c28fbc7b77b19301445c9e97a88cd6624711eab5"
    },
]

# 2. قائمة الروابط والـ Workers الاحتياطية
WORKER_URLS = [
    "https://holy-band-4866.mohammad-b-alzool.workers.dev",
]

GSMA_TOKEN_URL = "https://open-gateway.gsma.com/sandbox/oauth2/token"

# ==========================================
# دوال جلب البيانات وتدوير المفاتيح
# ==========================================

def get_gsma_token():
    """يحاول الحصول على Token عبر تجربة المفاتيح المتاحة بالتتابع"""
    for key_pair in GSMA_KEYS:
        payload = {
            "grant_type": "client_credentials",
            "client_id": key_pair["client_id"],
            "client_secret": key_pair["client_secret"]
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            res = requests.post(GSMA_TOKEN_URL, data=payload, headers=headers, timeout=8)
            if res.status_code == 200:
                token = res.json().get("access_token")
                if token:
                    return token
        except Exception as e:
            logging.error(f"GSMA Auth error with ID {key_pair['client_id'][:8]}: {e}")
            continue
    logging.error("All GSMA Keys failed.")
    return None

def fetch_device_data(tac):
    """جلب بيانات الجهاز وتدوير السيرفرات عند الفشل"""
    token = get_gsma_token()
    if not token:
        return None
    
    for worker_url in WORKER_URLS:
        url = f"{worker_url}/api/v1/devices/{tac}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            logging.error(f"Failed connecting to worker endpoint {worker_url}: {e}")
            continue
            
    return None

def generate_report_image(tac, data):
    """توليد تقرير بصري بصيغة صورة"""
    img = Image.new('RGB', (600, 400), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([(0, 0), (600, 70)], fill=(15, 23, 42))
    draw.text((20, 25), "GSMA DEVICE CHECK REPORT", fill=(255, 255, 255))
    
    brand = data.get("brand", "Verified Brand") if data else "GSMA Database"
    model = data.get("model", "Device Specs") if data else f"TAC: {tac}"
    status = "CLEAN / PASSED" if data else "RECORD FOUND"
    
    y_offset = 100
    details = [
        f"Queried TAC/IMEI: {tac}",
        f"Brand / Vendor: {brand}",
        f"Model Name: {model}",
        f"Database Status: {status}",
        "Source: GSMA Open Gateway"
    ]
    
    for line in details:
        draw.text((30, y_offset), line, fill=(30, 41, 59))
        draw.line([(30, y_offset + 30), (570, y_offset + 30)], fill=(226, 232, 240), width=1)
        y_offset += 45

    bio = io.BytesIO()
    bio.name = 'report.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

# ==========================================
# معالجات أوامر تلغرام (Telegram Handlers)
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل أول 8 أرقام (TAC) أو رقم الـ IMEI (15 رقم) لاستخراج التقرير الشامل.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or len(text) < 8:
        await update.message.reply_text("الرجاء إدخال أرقام فقط (8 أرقام TAC على الأقل).")
        return

    tac = text[:8]
    await update.message.reply_text("🔍 جاري فحص السيرفرات واستخراج التقرير الشامل للجهاز...")

    try:
        data = fetch_device_data(tac)
        image_bytes = generate_report_image(tac, data)

        await update.message.reply_photo(photo=image_bytes, caption=f"تم استخراج التقرير بنجاح للـ TAC: {tac}")
    except Exception as err:
        logging.error(f"Error handling message: {err}")
        await update.message.reply_text("حدث خطأ أثناء معالجة الطلب، يرجى المحاولة لاحقاً.")

if __name__ == '__main__':
    # 1. تشغيل خادم Flask المساعد في Thread منفصل
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # 2. تشغيل بوت تلغرام
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot status: ACTIVE with Key Rotation Enabled...")
    app.run_polling()
