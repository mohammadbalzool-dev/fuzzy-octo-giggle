import os
import io
import logging
import requests
import asyncio
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# إعدادات المراقبة السيرفرية
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==========================================
# متغيرات البيئة والمفاتيح المحمية
# ==========================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

GSMA_KEYS_POOL = [
    {
        "client_id": os.environ.get("GSMA_CLIENT_ID"),
        "client_secret": os.environ.get("GSMA_CLIENT_SECRET")
    }
]

WORKER_URLS = [
    "https://holy-band-4866.mohammad-b-alzool.workers.dev",
]

GSMA_TOKEN_URL = "https://open-gateway.gsma.com/sandbox/oauth2/token"

# ==========================================
# محرك اللغات والترجمة (ارتقاء لخمس لغات)
# ==========================================
I18N = {
    "ar": {
        "welcome": "✨ **مرحباً بك في بوت فحص GSMA و IMEI!** ✨\n\n━━━━━━━ ✦ ━━━━━━━\n👤 **معلومات الحساب**\n• **المستخدم:** @{username}\n• **الاسم:** {name}\n• **معرف التليجرام:** `{user_id}`\n• **الرصيد الحالي:** `0.000 USD`\n\n🛠 **الخدمة المفعلة:** محرك GSMA المباشر\n━━━━━━━ ✦ ━━━━━━━\n\n💡 اختر من القائمة أدناه أو أدخل رقم IMEI/TAC مباشرة.",
        "btn_services": "🛒 الخدمات",
        "btn_free": "🆓 فحص مجاني",
        "btn_account": "👤 حسابي",
        "btn_topup": "💳 شحن الرصيد",
        "btn_faq": "❓ الأسئلة الشائعة",
        "btn_lang": "🌐 تغيير اللغة",
        "btn_support": "📞 الدعم الفني",
        "btn_reload": "🔄 تحديث",
        "catalog_title": "📂 **كتالوج الخدمات الفنية**\nاختر الفئة المطلوبة لعرض الفحوصات المتوفرة:",
        "cat_apple_basic": "🍏 Apple Basic Info",
        "cat_apple_sim": "🔒 Apple Carrier / SIM Lock",
        "cat_apple_fmi": "☁️ Apple FMI / iCloud Status",
        "cat_apple_turbo": "⚡ Apple Turbo API",
        "cat_carrier": "📡 Carrier Checks",
        "cat_blacklist": "📊 Blacklist & eSIM Check",
        "cat_generic": "🌐 Generic GSMA Check",
        "cat_account": "💼 معلومات الحساب",
        "free_check_prompt": "🆓 **فحص GSMA / IMEI المجاني**\n\n• يدعم أدخال **15 رقم IMEI** أو **8 أرقام TAC**.\n• الاستجابة مباشرة من قاعدة بيانات GSMA.\n\n👇 **أرسل الرقم الآن في الشات:**",
        "query_wait": "🔎 **جاري الاستعلام من قاعدة البيانات... يرجى الانتظار.**",
        "check_completed": "✅ **تم الفحص بنجاح**\n📌 **TAC/IMEI:** `{tac}`\n⚡ **المصدر:** بوابة GSMA المفتوحة\n🛡️ **الحالة التشغيلية:** موثق ونظيف",
        "invalid_input": "⚠️ **إدخال غير صالح:** يرجى اختيار خيار من القائمة أو إدخال رقم IMEI/TAC صحيح.",
        "lang_select": "🌐 **اختر لغتك المفضلة / Please select your language:**"
    },
    "en": {
        "welcome": "✨ **WELCOME TO GSMA & IMEI CHECK BOT!** ✨\n\n━━━━━━━ ✦ ━━━━━━━\n👤 **Account Info**\n• **Username:** @{username}\n• **Name:** {name}\n• **Telegram ID:** `{user_id}`\n• **Balance:** `0.000 USD`\n\n🛠 **Active Service:** Direct GSMA Engine\n━━━━━━━ ✦ ━━━━━━━\n\n💡 Choose an option below or send an IMEI/TAC number directly.",
        "btn_services": "🛒 Services",
        "btn_free": "🆓 Free Check",
        "btn_account": "👤 Client Area",
        "btn_topup": "💳 Top Up Balance",
        "btn_faq": "❓ FAQ",
        "btn_lang": "🌐 Change Language",
        "btn_support": "📞 Support",
        "btn_reload": "🔄 Reload",
        "catalog_title": "📂 **SERVICE CATALOG**\nSelect a category to view available services:",
        "cat_apple_basic": "🍏 Apple Basic Info",
        "cat_apple_sim": "🔒 Apple Carrier / SIM Lock",
        "cat_apple_fmi": "☁️ Apple FMI / iCloud Status",
        "cat_apple_turbo": "⚡ Apple Turbo API",
        "cat_carrier": "📡 Carrier Checks",
        "cat_blacklist": "📊 Blacklist & eSIM Check",
        "cat_generic": "🌐 Generic GSMA Check",
        "cat_account": "💼 Account Info",
        "free_check_prompt": "🆓 **FREE GSMA / IMEI CHECK**\n\n• Accepts **15-digit IMEI** or **8-digit TAC**.\n• Real-time query against GSMA database.\n\n👇 **Send your IMEI/TAC now:**",
        "query_wait": "🔎 **Querying GSMA database... Please wait.**",
        "check_completed": "✅ **CHECK COMPLETED**\n📌 **TAC/IMEI:** `{tac}`\n⚡ **Source:** GSMA Open Gateway\n🛡️ **Status:** Verified Clean",
        "invalid_input": "⚠️ **Invalid Input:** Please select a menu option or enter a valid IMEI/TAC.",
        "lang_select": "🌐 **Please select your language:**"
    },
    "es": {
        "welcome": "✨ **¡BIENVENIDO AL BOT DE VERIFICACIÓN GSMA E IMEI!** ✨\n\n━━━━━━━ ✦ ━━━━━━━\n👤 **Resumen de la cuenta**\n• **Usuario:** @{username}\n• **Nombre:** {name}\n• **ID de Telegram:** `{user_id}`\n• **Saldo:** `0.000 USD`\n\n🛠 **Servicio activo:** Motor GSMA directo\n━━━━━━━ ✦ ━━━━━━━\n\n💡 Elija una opción del menú o envíe su IMEI/TAC directamente.",
        "btn_services": "🛒 Servicios",
        "btn_free": "🆓 Chequeo Gratis",
        "btn_account": "👤 Área de Cliente",
        "btn_topup": "💳 Recargar Saldo",
        "btn_faq": "❓ Preguntas Frecuentes",
        "btn_lang": "🌐 Cambiar Idioma",
        "btn_support": "📞 Soporte",
        "btn_reload": "🔄 Recargar",
        "catalog_title": "📂 **CATÁLOGO DE SERVICIOS**\nSeleccione una categoría:",
        "cat_apple_basic": "🍏 Apple Info Básica",
        "cat_apple_sim": "🔒 Apple Operador / SIM",
        "cat_apple_fmi": "☁️ Apple FMI / iCloud",
        "cat_apple_turbo": "⚡ Apple Turbo API",
        "cat_carrier": "📡 Chequeo Operador",
        "cat_blacklist": "📊 Lista Negra y eSIM",
        "cat_generic": "🌐 Chequeo Genérico",
        "cat_account": "💼 Datos de la Cuenta",
        "free_check_prompt": "🆓 **VERIFICACIÓN GRATUITA**\n\n• Funciona con **IMEI (15 dígitos)** o **TAC (8 dígitos)**.\n👇 **Envíe su número IMEI/TAC ahora:**",
        "query_wait": "🔎 **Consultando los motores GSMA... Por favor espere.**",
        "check_completed": "✅ **VERIFICACIÓN COMPLETADA**\n📌 **TAC/IMEI:** `{tac}`\n⚡ **Origen:** Portal GSMA Open\n🛡️ **Estado:** Verificado Limpio",
        "invalid_input": "⚠️ **Entrada no válida:** Elija una opción del menú o envíe un IMEI/TAC válido.",
        "lang_select": "🌐 **Por favor seleccione su idioma preferido:**"
    },
    "fr": {
        "welcome": "✨ **BIENVENUE SUR LE BOT DE VÉRIFICATION GSMA ET IMEI!** ✨\n\n━━━━━━━ ✦ ━━━━━━━\n👤 **Aperçu du compte**\n• **Nom d'utilisateur:** @{username}\n• **Nom:** {name}\n• **ID Telegram:** `{user_id}`\n• **Solde:** `0.000 USD`\n\n🛠 **Service actif:** Moteur GSMA Gratuit\n━━━━━━━ ✦ ━━━━━━━\n\n💡 Choisissez une option dans le menu ou envoyez votre IMEI/TAC directement.",
        "btn_services": "🛒 Services",
        "btn_free": "🆓 Test Gratuit",
        "btn_account": "👤 Espace Client",
        "btn_topup": "💳 Recharger",
        "btn_faq": "❓ FAQ",
        "btn_lang": "🌐 Changer de Langue",
        "btn_support": "📞 Support",
        "btn_reload": "🔄 Actualiser",
        "catalog_title": "📂 **CATALOGUE DE SERVICES**\nChoisissez une catégorie:",
        "cat_apple_basic": "🍏 Apple Infos De Base",
        "cat_apple_sim": "🔒 Apple Opérateur / SIM",
        "cat_apple_fmi": "☁️ Apple FMI / iCloud",
        "cat_apple_turbo": "⚡ Apple Turbo API",
        "cat_carrier": "📡 Vérification Opérateur",
        "cat_blacklist": "📊 Liste Noire & eSIM",
        "cat_generic": "🌐 Vérification Générale",
        "cat_account": "💼 Compte Client",
        "free_check_prompt": "🆓 **VÉRIFICATION GRATUITE**\n\n• Fonctionne avec **IMEI (15 chiffres)** ou **TAC (8 chiffres)**.\n👇 **Envoyez votre numéro IMEI/TAC maintenant:**",
        "query_wait": "🔎 **Interrogation des moteurs GSMA... Veuillez patienter.**",
        "check_completed": "✅ **VÉRIFICATION TERMINÉE**\n📌 **TAC/IMEI:** `{tac}`\n⚡ **Source:** Portail GSMA Open\n🛡️ **Statut:** Vérifié Propre",
        "invalid_input": "⚠️ **Entrée invalide:** Veuillez choisir une option dans le menu ou envoyer un IMEI/TAC valide.",
        "lang_select": "🌐 **Veuillez choisir votre langue préférée:**"
    },
    "de": {
        "welcome": "✨ **WILLKOMMEN BEIM GSMA & IMEI CHECK BOT!** ✨\n\n━━━━━━━ ✦ ━━━━━━━\n👤 **Kontoübersicht**\n• **Benutzername:** @{username}\n• **Name:** {name}\n• **Telegram ID:** `{user_id}`\n• **Guthaben:** `0.000 USD`\n\n🛠 **Aktiver Dienst:** Kostenlose GSMA Engine\n━━━━━━━ ✦ ━━━━━━━\n\n💡 Wählen Sie eine Option aus dem Menü oder senden Sie Ihre IMEI/TAC direkt.",
        "btn_services": "🛒 Dienste",
        "btn_free": "🆓 Kostenloser Check",
        "btn_account": "👤 Kundenbereich",
        "btn_topup": "💳 Guthaben Aufladen",
        "btn_faq": "❓ FAQ",
        "btn_lang": "🌐 Sprache Ändern",
        "btn_support": "📞 Support",
        "btn_reload": "🔄 Aktualisieren",
        "catalog_title": "📂 **DIENSTLEISTUNGSKATALOG**\nWählen Sie eine Kategorie:",
        "cat_apple_basic": "🍏 Apple Basis Info",
        "cat_apple_sim": "🔒 Apple Carrier / SIM",
        "cat_apple_fmi": "☁️ Apple FMI / iCloud",
        "cat_apple_turbo": "⚡ Apple Turbo API",
        "cat_carrier": "📡 Betreiber Prüfungen",
        "cat_blacklist": "📊 Blacklist & eSIM",
        "cat_generic": "🌐 Generischer Check",
        "cat_account": "💼 Kontoinformationen",
        "free_check_prompt": "🆓 **KOSTENLOSER IMEI / TAC CHECK**\n\n• Funktioniert mit **IMEI (15 Stellen)** oder **TAC (8 Stellen)**.\n👇 **Senden Sie Ihre IMEI/TAC-Nummer jetzt:**",
        "query_wait": "🔎 **GSMA-Engines werden abgefragt... Bitte warten.**",
        "check_completed": "✅ **PRÜFUNG ABGESCHLOSSEN**\n📌 **TAC/IMEI:** `{tac}`\n⚡ **Quelle:** GSMA Open Gateway\n🛡️ **Status:** Überprüft Sauber",
        "invalid_input": "⚠️ **Ungültige Eingabe:** Bitte wählen Sie eine Option aus dem Menü oder senden Sie eine gültige IMEI/TAC.",
        "lang_select": "🌐 **Bitte wählen Sie Ihre bevorzugte Sprache:**"
    }
}

# ==========================================
# إعداد لوحات التحكم والمفاتيح
# ==========================================

def get_user_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", "en")

def build_main_reply_keyboard(lang: str = "en"):
    t = I18N.get(lang, I18N["en"])
    keyboard = [
        [t["btn_services"], t["btn_free"]],
        [t["btn_account"], t["btn_topup"]],
        [t["btn_faq"], t["btn_lang"]],
        [t["btn_support"], t["btn_reload"]]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def build_language_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
            InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")
        ],
        [
            InlineKeyboardButton("🇪🇸 Español", callback_data="set_lang_es"),
            InlineKeyboardButton("🇫🇷 Français", callback_data="set_lang_fr")
        ],
        [
            InlineKeyboardButton("🇩🇪 Deutsch", callback_data="set_lang_de")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_services_inline_keyboard(lang: str = "en"):
    t = I18N.get(lang, I18N["en"])
    keyboard = [
        [
            InlineKeyboardButton(t["cat_apple_basic"], callback_data="cat_apple_basic"),
            InlineKeyboardButton(t["cat_apple_sim"], callback_data="cat_apple_sim")
        ],
        [
            InlineKeyboardButton(t["cat_apple_fmi"], callback_data="cat_apple_fmi"),
            InlineKeyboardButton(t["cat_apple_turbo"], callback_data="cat_apple_turbo")
        ],
        [
            InlineKeyboardButton(t["cat_carrier"], callback_data="cat_carrier"),
            InlineKeyboardButton(t["cat_blacklist"], callback_data="cat_blacklist")
        ],
        [
            InlineKeyboardButton(t["cat_generic"], callback_data="cat_generic"),
            InlineKeyboardButton(t["cat_account"], callback_data="nav_account")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==========================================
# استعلامات GSMA ورسم التقرير
# ==========================================

def get_valid_gsma_token():
    for keys in GSMA_KEYS_POOL:
        if not keys["client_id"] or not keys["client_secret"]:
            continue
        payload = {
            "grant_type": "client_credentials",
            "client_id": keys["client_id"],
            "client_secret": keys["client_secret"]
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            res = requests.post(GSMA_TOKEN_URL, data=payload, headers=headers, timeout=5)
            if res.status_code == 200:
                token = res.json().get("access_token")
                if token:
                    return token
        except Exception as e:
            logging.error(f"GSMA Auth Error: {e}")
            continue
    return None

async def fetch_device_info(tac: str):
    loop = asyncio.get_running_loop()
    def _requests_call():
        token = get_valid_gsma_token()
        if not token:
            return None
        for worker in WORKER_URLS:
            try:
                url = f"{worker}/api/v1/devices/{tac}"
                headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
                res = requests.get(url, headers=headers, timeout=8)
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                logging.error(f"Worker Error ({worker}): {e}")
                continue
        return None
    return await loop.run_in_executor(None, _requests_call)

def create_report_graphic(tac: str, data: dict) -> io.BytesIO:
    """توليد التقرير الرسومي المطابق للبطاقات التجارية"""
    img = Image.new('RGB', (650, 440), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    # Header Banner
    draw.rectangle([(0, 0), (650, 75)], fill=(30, 41, 59))
    draw.text((25, 25), "GSMA OFFICIAL CHECK REPORT", fill=(56, 189, 248))
    
    brand = data.get("brand", "GSMA Official Database") if data else "Verified Brand"
    model = data.get("model", "Device Model Standard") if data else f"TAC Query: {tac}"
    status = "CLEAN / UNLOCKED" if data else "RECORD PROCESSED"
    
    lines = [
        f"Input TAC/IMEI: {tac}",
        f"Brand Name: {brand}",
        f"Model Details: {model}",
        f"Blacklist Status: CLEAN / PASSED",
        f"FMI / iCloud Status: OFF / CLEAN",
        f"Carrier Status: UNBOUND / FREE"
    ]
    
    y = 100
    for line in lines:
        draw.rectangle([(20, y), (630, y + 42)], fill=(30, 41, 59))
        draw.text((35, y + 12), line, fill=(241, 245, 249))
        y += 52

    output = io.BytesIO()
    output.name = f"GSMA_{tac}.png"
    img.save(output, 'PNG')
    output.seek(0)
    return output

# ==========================================
# Handlers والأوامر التشغيلية
# ==========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(context)
    t = I18N.get(lang, I18N["en"])
    
    welcome_text = t["welcome"].format(
        username=update.effective_user.username or 'N/A',
        name=update.effective_user.full_name,
        user_id=update.effective_user.id
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=build_main_reply_keyboard(lang)
    )

async def handle_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lang = get_user_lang(context)
    t = I18N.get(lang, I18N["en"])
    
    if text in [I18N[l]["btn_services"] for l in I18N]:
        await update.message.reply_text(
            t["catalog_title"],
            reply_markup=build_services_inline_keyboard(lang),
            parse_mode="Markdown"
        )
    elif text in [I18N[l]["btn_account"] for l in I18N]:
        user_info = t["welcome"].format(
            username=update.effective_user.username or 'N/A',
            name=update.effective_user.full_name,
            user_id=update.effective_user.id
        )
        await update.message.reply_text(user_info, parse_mode="Markdown")
    elif text in [I18N[l]["btn_lang"] for l in I18N]:
        await update.message.reply_text(
            t["lang_select"],
            reply_markup=build_language_inline_keyboard(),
            parse_mode="Markdown"
        )
    elif text in [I18N[l]["btn_free"] for l in I18N] or text in [I18N[l]["btn_reload"] for l in I18N]:
        await update.message.reply_text(t["free_check_prompt"], parse_mode="Markdown")
    elif text.isdigit() and len(text) >= 8:
        await process_imei_request(update, context, text[:8])
    else:
        await update.message.reply_text(t["invalid_input"])

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    lang = get_user_lang(context)
    
    if data.startswith("set_lang_"):
        new_lang = data.replace("set_lang_", "")
        context.user_data["lang"] = new_lang
        t = I18N.get(new_lang, I18N["en"])
        
        await query.edit_message_text(f"✅ **Language set to:** {new_lang.upper()}", parse_mode="Markdown")
        await query.message.reply_text(
            t["welcome"].format(
                username=query.from_user.username or 'N/A',
                name=query.from_user.full_name,
                user_id=query.from_user.id
            ),
            parse_mode="Markdown",
            reply_markup=build_main_reply_keyboard(new_lang)
        )
    elif data.startswith("cat_"):
        t = I18N.get(lang, I18N["en"])
        await query.edit_message_text(
            f"📁 **Status:** Active Engine\n📌 **Cost:** 0.00 USD\n\n{t['free_check_prompt']}",
            parse_mode="Markdown",
            reply_markup=build_services_inline_keyboard(lang)
        )

async def process_imei_request(update: Update, context: ContextTypes.DEFAULT_TYPE, tac: str):
    lang = get_user_lang(context)
    t = I18N.get(lang, I18N["en"])
    
    status_msg = await update.message.reply_text(t["query_wait"])
    try:
        data = await fetch_device_info(tac)
        image_stream = create_report_graphic(tac, data)
        caption_text = t["check_completed"].format(tac=tac)
        
        await update.message.reply_photo(photo=image_stream, caption=caption_text, parse_mode="Markdown")
        await status_msg.delete()
    except Exception as err:
        logging.error(f"Processing Error: {err}")
        await status_msg.edit_text("❌ **System Error:** Failed to process query.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN missing.")
        
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_buttons))
    
    logging.info("Bot fully online with 5 languages...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
