import os
from datetime import datetime
from typing import Final

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN: Final[str | None] = os.getenv("BOT_TOKEN")
GOOGLE_SHEETS_ID: Final[str | None] = os.getenv("GOOGLE_SHEETS_ID")
GOOGLE_SERVICE_ACCOUNT_FILE: Final[str | None] = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",")
# Barcha bosqichlar
(
    MAIN_MENU, SOTISH_KATEGORIYA, BUYUM_TURI, GRAMM, NARX, KURS,
    SOTIB_OLISH_KIMDAN, MIJOZDAN_TURI, XARAJAT_TOIFA, XARAJAT_IZOH, XARAJAT_NARX
) = range(11)

# Tugmalar
MAIN_BUTTONS = [["Sotish", "Sotib olish"], ["Xarajatlar"]]
SOTISH_BUTTONS = [["Buyumlar", "Lom"]]
BUYUM_BUTTONS = [["Bilaguzuk", "Uzuk"], ["Zirak", "Zanjir", "Boshqa"]]
SOTIB_OLISH_BUTTONS = [["Zavoddan (lom)", "Mijozdan (b.u)"]]
MIJOZDAN_BUTTONS = [["Buyumlar", "Lom"]]
XARAJAT_TOIFALARI = [["Ijara", "Oylik", "Soliq"], ["Elektr", "Kanselyariya", "Boshqa xarajat"]]


# --- GOOGLE SHEETS ULANISH VA DINAMIK LIST YARATISH ---
def get_worksheet(sheet_name: str):
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(GOOGLE_SHEETS_ID)
    
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        # Agar list yo'q bo'lsa, uni yaratib, mos sarlavhalarni qo'shamiz
        ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=10)
        
        if sheet_name == "Sotish":
            headers = ["Sana", "Kategoriya", "Nomi/Izoh", "Gramm", "Narx", "Kurs", "Foydalanuvchi", "Oy", "Yil"]
        elif sheet_name == "Sotib olish":
            headers = ["Sana", "Kimdan", "Kategoriya", "Nomi/Izoh", "Gramm", "Narx", "Kurs", "Foydalanuvchi", "Oy", "Yil"]
        elif sheet_name == "Xarajatlar":
            headers = ["Sana", "Toifa", "Izoh", "Summa", "Foydalanuvchi", "Oy", "Yil"]
        else:
            headers = ["Sana", "Ma'lumot"]
            
        ws.append_row(headers)
    return ws


# --- MA'LUMOTLARNI SAQLASH (Dinamik qatorlar) ---
async def save_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    now = datetime.now()
    user = update.effective_user
    bolim = context.user_data.get("bolim", "Boshqa")
    
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    common_tail = [user.full_name if user else "Noma'lum", now.strftime("%m"), now.strftime("%Y")]

    # Qaysi bo'limdaligiga qarab, qatorni turlicha yig'amiz
    if bolim == "Sotish":
        row = [
            date_str,
            context.user_data.get("kategoriya", ""),
            context.user_data.get("nomi", ""),
            context.user_data.get("gramm", ""),
            context.user_data.get("narx", ""),
            context.user_data.get("kurs", "")
        ] + common_tail
    elif bolim == "Sotib olish":
        row = [
            date_str,
            context.user_data.get("kimdan", ""),
            context.user_data.get("kategoriya", ""),
            context.user_data.get("nomi", ""),
            context.user_data.get("gramm", ""),
            context.user_data.get("narx", ""),
            context.user_data.get("kurs", "")
        ] + common_tail
    elif bolim == "Xarajatlar":
        row = [
            date_str,
            context.user_data.get("kategoriya", ""), # Toifa
            context.user_data.get("nomi", ""),       # Izoh
            context.user_data.get("narx", "")        # Summa
        ] + common_tail

    try:
        ws = get_worksheet(bolim) # Bo'lim nomidagi listga ulanadi
        ws.append_row(row, value_input_option="USER_ENTERED")
        await update.message.reply_text(
            f"✅ Ma'lumot '{bolim}' ro'yxatiga saqlandi!\nYangi amaliyot uchun /start bosing.",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as exc:
        await update.message.reply_text(f"❌ Saqlashda xatolik: {exc}\nQaytadan /start bosing.")

    return ConversationHandler.END


# --- BOSH MENYU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.effective_user.id)
    
    # QOROVUL QISMI: Agar foydalanuvchi ID si ro'yxatda bo'lmasa, haydab yuboramiz
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("🚫 Kechirasiz, siz tizimga kirish huquqiga ega emassiz.")
        return ConversationHandler.END

    # Agar o'zimiznikilar bo'lsa, odatdagidek ishlayveradi
    context.user_data.clear()
    markup = ReplyKeyboardMarkup(MAIN_BUTTONS, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Assalomu alaykum! Asosiy menyu. Qaysi bo'limga kiramiz?", reply_markup=markup)
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tanlov = update.message.text
    context.user_data["bolim"] = tanlov

    if tanlov == "Sotish":
        markup = ReplyKeyboardMarkup(SOTISH_BUTTONS, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Sotish bo'limi. Kategoriya tanlang:", reply_markup=markup)
        return SOTISH_KATEGORIYA
    elif tanlov == "Sotib olish":
        markup = ReplyKeyboardMarkup(SOTIB_OLISH_BUTTONS, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Kimdan sotib olyapsiz?", reply_markup=markup)
        return SOTIB_OLISH_KIMDAN
    elif tanlov == "Xarajatlar":
        markup = ReplyKeyboardMarkup(XARAJAT_TOIFALARI, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Xarajat toifasini tanlang (yoki o'zingiz yozing):", reply_markup=markup)
        return XARAJAT_TOIFA
    return MAIN_MENU

# --- 1. SOTISH BO'LIMI ---
async def sotish_kategoriya_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["kategoriya"] = update.message.text
    if update.message.text == "Buyumlar":
        markup = ReplyKeyboardMarkup(BUYUM_BUTTONS, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Qanday buyum sotilyapti?", reply_markup=markup)
        return BUYUM_TURI
    elif update.message.text == "Lom":
        context.user_data["nomi"] = "Lom"
        await update.message.reply_text("Lomning og'irligini kiriting (gramm):", reply_markup=ReplyKeyboardRemove())
        return GRAMM
    return SOTISH_KATEGORIYA

# --- 2. SOTIB OLISH BO'LIMI ---
async def sotib_olish_kimdan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tanlov = update.message.text
    context.user_data["kimdan"] = tanlov
    if tanlov == "Zavoddan (lom)":
        context.user_data["kategoriya"] = "Lom"
        context.user_data["nomi"] = "Lom"
        await update.message.reply_text("Lomning og'irligini kiriting (gramm):", reply_markup=ReplyKeyboardRemove())
        return GRAMM
    elif tanlov == "Mijozdan (b.u)":
        markup = ReplyKeyboardMarkup(MIJOZDAN_BUTTONS, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Mijoz nima topshiryapti?", reply_markup=markup)
        return MIJOZDAN_TURI
    return SOTIB_OLISH_KIMDAN

async def mijozdan_turi_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tanlov = update.message.text
    context.user_data["kategoriya"] = tanlov
    if tanlov == "Buyumlar":
        markup = ReplyKeyboardMarkup(BUYUM_BUTTONS, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Qanday buyum?", reply_markup=markup)
        return BUYUM_TURI
    elif tanlov == "Lom":
        context.user_data["nomi"] = "Lom"
        await update.message.reply_text("Lomning og'irligini kiriting (gramm):", reply_markup=ReplyKeyboardRemove())
        return GRAMM
    return MIJOZDAN_TURI

# --- 3. XARAJATLAR BO'LIMI ---
async def xarajat_toifa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["kategoriya"] = update.message.text # Toifa sifatida saqlaymiz
    await update.message.reply_text("Xarajat uchun izoh kiriting (masalan: May oyi ijara uchun):", reply_markup=ReplyKeyboardRemove())
    return XARAJAT_IZOH

async def xarajat_izoh_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["nomi"] = update.message.text # Izoh sifatida saqlaymiz
    await update.message.reply_text("Xarajat summasini kiriting (masalan: 1500000):")
    return XARAJAT_NARX

async def xarajat_narx_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["narx"] = float(update.message.text.replace(" ", "").replace(",", "."))
        return await save_data(update, context)
    except ValueError:
        await update.message.reply_text("Iltimos, summani faqat sonlarda kiriting:")
        return XARAJAT_NARX

# --- UMUMIY (GRAMM, NARX, KURS) ---
async def buyum_turi_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["nomi"] = update.message.text
    await update.message.reply_text("Og'irligini kiriting (grammda, masalan: 5.4):", reply_markup=ReplyKeyboardRemove())
    return GRAMM

async def gramm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["gramm"] = float(update.message.text.replace(",", "."))
        await update.message.reply_text("Narxini kiriting (masalan: 3500000):")
        return NARX
    except ValueError:
        await update.message.reply_text("Iltimos, grammni faqat sonlarda kiriting:")
        return GRAMM

async def narx_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["narx"] = float(update.message.text.replace(" ", "").replace(",", "."))
        await update.message.reply_text("Kursni kiriting (masalan: 12600):")
        return KURS
    except ValueError:
        await update.message.reply_text("Iltimos, narxni faqat sonlarda kiriting:")
        return NARX

async def kurs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["kurs"] = float(update.message.text.replace(" ", "").replace(",", "."))
        return await save_data(update, context)
    except ValueError:
        await update.message.reply_text("Iltimos, kursni faqat sonlarda kiriting:")
        return KURS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Amaliyot bekor qilindi. /start bosing.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- MAIN FUNKSIYASI ---
async def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)],
            SOTISH_KATEGORIYA: [MessageHandler(filters.TEXT & ~filters.COMMAND, sotish_kategoriya_handler)],
            SOTIB_OLISH_KIMDAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, sotib_olish_kimdan_handler)],
            MIJOZDAN_TURI: [MessageHandler(filters.TEXT & ~filters.COMMAND, mijozdan_turi_handler)],
            BUYUM_TURI: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyum_turi_handler)],
            XARAJAT_TOIFA: [MessageHandler(filters.TEXT & ~filters.COMMAND, xarajat_toifa_handler)],
            XARAJAT_IZOH: [MessageHandler(filters.TEXT & ~filters.COMMAND, xarajat_izoh_handler)],
            XARAJAT_NARX: [MessageHandler(filters.TEXT & ~filters.COMMAND, xarajat_narx_handler)],
            GRAMM: [MessageHandler(filters.TEXT & ~filters.COMMAND, gramm_handler)],
            NARX: [MessageHandler(filters.TEXT & ~filters.COMMAND, narx_handler)],
            KURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, kurs_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    
    async with app:
        await app.initialize()
        await app.start()
        print("Bot 3 ta alohida list uchun ishga tushdi...")
        await app.updater.start_polling()
        
        import asyncio
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, SystemExit):
            await app.updater.stop()
            await app.stop()
            await app.shutdown()

if __name__ == "__main__":
    import asyncio
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())