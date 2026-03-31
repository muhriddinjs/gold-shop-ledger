# Gold Shop CRM Bot (Telegram + Google Sheets)

Bu bot oltin do'kon uchun sodda CRM vazifasini bajaradi va ma'lumotlarni Google Sheets'ga yozadi.

## Kiritiladigan turlar

- Oltin olish
- Oltin sotish
- Ijara to'lovi
- Elektr to'lovi
- Issiq suv to'lovi

## 1) O'rnatish

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Telegram bot token olish

1. Telegram'da `@BotFather` oching
2. `/newbot` orqali bot yarating
3. Berilgan tokenni nusxalang

## 3) Google Sheets ulash

1. [Google Cloud Console](https://console.cloud.google.com/) da project oching
2. Google Sheets API'ni yoqing
3. Service Account yarating va JSON key yuklab oling
4. JSON faylni loyiha ichiga `service_account.json` nomi bilan qo'ying
5. Google Sheets fayl yarating
6. Sheet'ni service account email bilan "Editor" qilib share qiling
7. URL'dan `spreadsheet id` ni oling

## 4) .env sozlash

`.env.example` ni `.env` ga nusxalang va to'ldiring:

```env
BOT_TOKEN=...
GOOGLE_SHEETS_ID=...
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
GOOGLE_WORKSHEET_NAME=transactions
```

## 5) Ishga tushirish

```bash
python bot.py
```

Botda `/start` bosing va ma'lumot kiriting.

## Eslatma

- Birinchi ishga tushishda `transactions` worksheet bo'lmasa, bot uni yaratadi.
- Ustunlar: Sana, Telegram ID, Foydalanuvchi, Tur, Miqdor, Izoh, Oy, Yil.
