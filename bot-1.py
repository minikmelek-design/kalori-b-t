import os
import logging
import httpx
import base64
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """Sen bir kalori ve beslenme uzmanısın. Kullanıcı sana yemek fotoğrafı gönderdiğinde:

Yanıtını SADECE şu formatta ver, başka hiçbir şey yazma:

🍽️ *[Yemek Adı]*
📏 Porsiyon: [tahmin]

🔥 *[X] kcal*

🥩 Protein: [X]g
🌾 Karbonhidrat: [X]g  
🧈 Yağ: [X]g

💡 [Kısa bir not - opsiyonel]

Eğer görselde yemek yoksa sadece şunu yaz: "Görselde yemek bulunamadı 🤔"
Tahmin belirsizse makul ortalama değeri kullan."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba! 👋 Ben *KaloriBot*.\n\n"
        "Yediğin yemeğin fotoğrafını gönder, kalorini hesaplayayım! 📸\n\n"
        "Ne kadar doğru fotoğraf, o kadar doğru tahmin 😄",
        parse_mode="Markdown"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Analiz ediyorum... 🔍")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(file.file_path)
            image_data = base64.standard_b64encode(response.content).decode("utf-8")

        image_part = {
            "mime_type": "image/jpeg",
            "data": image_data
        }

        response = model.generate_content([
            SYSTEM_PROMPT + "\n\nBu yemeğin kalorilerini hesapla.",
            image_part
        ])

        result = response.text
        await update.message.reply_text(result, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Hata: {e}")
        await update.message.reply_text("Bir hata oluştu, tekrar dene. 😅")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Fotoğraf gönder, yazı değil 😄📸"
    )


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot başlatılıyor...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
