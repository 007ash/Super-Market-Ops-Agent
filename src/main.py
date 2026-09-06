import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .database import SessionLocal
from .agent import AgentOrchestrator
from .models import Product

# Initialize Telegram Application
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") # e.g. https://my-kirana.ngrok.app

telegram_app = Application.builder().token(TOKEN).build()

async def start_command(update: Update, context):
    await update.message.reply_text("Hello! I am AI_smart_mart. How can I help you today?")

async def handle_text_message(update: Update, context):
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    db = SessionLocal()
    try:
        orchestrator = AgentOrchestrator(db)
        response = await orchestrator.handle_message(user_message, chat_id)
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"Error processing request: {str(e)}")
    finally:
        db.close()

async def handle_voice_message(update: Update, context):
    # Retrieve voice note
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    file_path = f"/tmp/{voice.file_id}.ogg"
    await file.download_to_drive(file_path)
    
    # In production, we use OpenAI Whisper to transcribe
    await update.message.reply_text("🎙️ Voice note received. Transcribing... (Simulated)")
    # simulated transcription
    user_message = "check stock of maggi"
    
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        orchestrator = AgentOrchestrator(db)
        response = await orchestrator.handle_message(user_message, chat_id)
        await update.message.reply_text(f"🗣️ You said: '{user_message}'\n\n{response}")
    finally:
        db.close()

async def handle_photo_message(update: Update, context):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_path = f"/tmp/{photo.file_id}.jpg"
    await file.download_to_drive(file_path)
    
    await update.message.reply_text("📸 Image received. Extracting invoice details using Gemini Vision... (Simulated)")
    await update.message.reply_text("✅ Successfully parsed invoice. Added 10 packets of Maggi to stock.")

telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
telegram_app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))

def send_low_stock_report():
    print("Running scheduled job: low stock report")
    # For a real implementation, we'd query db and use context.bot.send_message
    
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set webhook on startup
    await telegram_app.initialize()
    if WEBHOOK_URL:
        await telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        print(f"Webhook set to {WEBHOOK_URL}/webhook")
    else:
        # Fallback to polling for local dev if no webhook
        print("No WEBHOOK_URL provided, falling back to polling")
        asyncio.create_task(telegram_app.updater.start_polling())
    
    await telegram_app.start()
    
    # Schedule Jobs
    scheduler.add_job(send_low_stock_report, CronTrigger(hour=8, minute=0))
    scheduler.start()
    
    yield
    
    # Clean up
    scheduler.shutdown()
    await telegram_app.stop()
    if not WEBHOOK_URL:
        await telegram_app.updater.stop()

app = FastAPI(lifespan=lifespan, title="AI_smart_mart API")

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=True)
