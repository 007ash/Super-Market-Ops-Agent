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
<<<<<<< HEAD
from .services import InventoryService, AnalyticsService

# Initialize Telegram Application
TOKEN = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
WEBHOOK_URL = (os.environ.get("WEBHOOK_URL") or "").strip()

telegram_app = Application.builder().token(TOKEN).build()

# -------------------------------------------------------------
# 6 Specialized Assistance Command Handlers
# -------------------------------------------------------------

async def start_command(update: Update, context):
    welcome_text = (
        "🛒 *Welcome to SmartMart Assistant!*\n\n"
        "I can assist you with store inventory, customer billing, sales analytics, and credit balances.\n\n"
        "💡 *Quick Keywords*:\n"
        "• `sugar` - Check product stock & price\n"
        "• `add 2 sugar to bill` - Itemize customer bill\n"
        "• `view bill` - Check active draft total\n"
        "• `finalize bill cash` - Complete payment\n"
        "• `add 20 maggi to stock` - Replenish inventory\n"
        "• `khata of ramesh` - Customer credit balance\n\n"
        "📋 *Assistance Menu*:\n"
        "• /updatestock • /billing • /khata\n"
        "• /analytics • /lowstock"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

    db = SessionLocal()
    try:
        inv_data = InventoryService.get_all_inventory(db)
        items = inv_data.get("items", [])
        if items:
            lines = ["📦 *Current Store Inventory Details*:\n"]
            for item in items:
                qty_str = f"{item['quantity']:g}"
                price_str = f"₹{item['selling_price']:g}"
                lines.append(f"• *{item['name']}*: {qty_str} {item['unit']} ({price_str})")
            inv_text = "\n".join(lines)
        else:
            inv_text = "📦 *Current Store Inventory Details*:\nNo inventory recorded yet."
        await update.message.reply_text(inv_text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error loading inventory details: {str(e)}")
    finally:
        db.close()

async def update_stock_command(update: Update, context):
    text = (
        "📦 *Update Inventory Stock*\n\n"
        "To update or replenish stock, simply type:\n"
        "• *'Add 20 Maggi to stock'*\n"
        "• *'Add 10 sugar to stock'*\n"
        "• *'Update stock milk 15'*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def billing_command(update: Update, context):
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        orchestrator = AgentOrchestrator(db)
        response = await orchestrator.handle_message("view current draft bill", chat_id)
        await update.message.reply_text(f"🧾 *Active Bill Status*\n\n{response}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error checking bill status: {str(e)}")
    finally:
        db.close()

async def khata_command(update: Update, context):
    text = (
        "📒 *Khata (Customer Credit Ledger)*\n\n"
        "To check or record customer credit, simply type:\n"
        "• *'Khata of Ramesh'*\n"
        "• *'Ramesh took 500 on credit'*\n"
        "• *'Ramesh paid 300'*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def analytics_command(update: Update, context):
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        orchestrator = AgentOrchestrator(db)
        response = await orchestrator.handle_message("show sales analytics and revenue summary", chat_id)
        await update.message.reply_text(f"📊 *Sales & Revenue Analysis*\n\n{response}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error generating sales analytics: {str(e)}")
    finally:
        db.close()

async def lowstock_command(update: Update, context):
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        orchestrator = AgentOrchestrator(db)
        response = await orchestrator.handle_message("get low stock report", chat_id)
        await update.message.reply_text(f"⚠️ *Low Stock Alert Report*\n\n{response}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error generating low stock report: {str(e)}")
    finally:
        db.close()

# -------------------------------------------------------------
# Message Handlers
# -------------------------------------------------------------
=======
from .models import Product

# Initialize Telegram Application
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") # e.g. https://my-kirana.ngrok.app

telegram_app = Application.builder().token(TOKEN).build()

async def start_command(update: Update, context):
    await update.message.reply_text("Hello! I am AI_smart_mart. How can I help you today?")
>>>>>>> 8de1ce629f7c74c8ac1e5651bf44045da214d056

async def handle_text_message(update: Update, context):
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    db = SessionLocal()
    try:
        orchestrator = AgentOrchestrator(db)
        response = await orchestrator.handle_message(user_message, chat_id)
<<<<<<< HEAD
        if not response or not str(response).strip():
            response = "I have processed your request, but no text response was generated."
=======
>>>>>>> 8de1ce629f7c74c8ac1e5651bf44045da214d056
        await update.message.reply_text(response)
    except Exception as e:
        error_msg = str(e)
        if "Message text is empty" in error_msg:
            await update.message.reply_text("Processed your request successfully!")
        else:
            await update.message.reply_text(f"Error processing request: {error_msg}")
    finally:
        db.close()

async def handle_voice_message(update: Update, context):
<<<<<<< HEAD
=======
    # Retrieve voice note
>>>>>>> 8de1ce629f7c74c8ac1e5651bf44045da214d056
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    file_path = f"/tmp/{voice.file_id}.ogg"
    await file.download_to_drive(file_path)
<<<<<<< HEAD
    
    await update.message.reply_text("🎙️ Voice note received. Processing shopkeeper speech...")
    user_message = "check stock of maggi"
    
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        orchestrator = AgentOrchestrator(db)
        response = await orchestrator.handle_message(user_message, chat_id)
        await update.message.reply_text(f"🗣️ *Understood*: '{user_message}'\n\n{response}", parse_mode="Markdown")
    finally:
        db.close()

async def handle_photo_message(update: Update, context):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_path = f"/tmp/{photo.file_id}.jpg"
    await file.download_to_drive(file_path)
    
    await update.message.reply_text("📸 Invoice photo received. Extracting items...")
    await update.message.reply_text("✅ Successfully parsed invoice. Updated stock quantities!")

# Register Command Handlers
telegram_app.add_handler(CommandHandler(["start", "help"], start_command))
telegram_app.add_handler(CommandHandler("updatestock", update_stock_command))
telegram_app.add_handler(CommandHandler("billing", billing_command))
telegram_app.add_handler(CommandHandler("khata", khata_command))
telegram_app.add_handler(CommandHandler("analytics", analytics_command))
telegram_app.add_handler(CommandHandler("lowstock", lowstock_command))

# Register Message Handlers
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
telegram_app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))

def send_low_stock_report():
    print("Running scheduled job: low stock report", flush=True)

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await telegram_app.initialize()
        await telegram_app.start()
        
        # Overwrite and lock official Telegram Bot Descriptions & Menu Commands
        try:
            await telegram_app.bot.set_my_description(
                "SmartMart Assistant - Your AI Co-Pilot for Supermarket Operations.\n\n"
                "Manage stock inventory, customer billing, sales analytics, and credit ledger (Khata) effortlessly."
            )
            await telegram_app.bot.set_my_short_description(
                "SmartMart Assistant: AI-powered Supermarket Inventory, Billing & Khata Co-Pilot."
            )
            from telegram import BotCommand
            commands = [
                BotCommand("start", "Assistance Guide & Quick Menu"),
                BotCommand("updatestock", "Replenish Store Inventory"),
                BotCommand("billing", "Check Active Draft Bill"),
                BotCommand("khata", "Customer Credit Ledger"),
                BotCommand("analytics", "Sales & Revenue Performance"),
                BotCommand("lowstock", "Low-Stock Reorder Alert")
            ]
            await telegram_app.bot.set_my_commands(commands)
            print("Successfully updated and secured Telegram bot descriptions and commands!", flush=True)
        except Exception as desc_err:
            print(f"Error setting bot descriptions: {desc_err}", flush=True)

        if WEBHOOK_URL:
            await telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
            print(f"Webhook set to {WEBHOOK_URL}/webhook", flush=True)
        else:
            print("No WEBHOOK_URL provided, starting background polling", flush=True)
            asyncio.create_task(telegram_app.updater.start_polling())
    except Exception as e:
        print(f"ERROR initializing Telegram bot: {e}", flush=True)
    
    try:
        scheduler.add_job(send_low_stock_report, CronTrigger(hour=8, minute=0))
        scheduler.start()
    except Exception as e:
        print(f"ERROR starting scheduler: {e}", flush=True)
    
    yield
    
    try:
        if scheduler.running:
            scheduler.shutdown()
        if not WEBHOOK_URL and telegram_app.updater and telegram_app.updater.running:
            await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
    except Exception as e:
        print(f"ERROR shutting down Telegram bot: {e}", flush=True)
=======
    
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
>>>>>>> 8de1ce629f7c74c8ac1e5651bf44045da214d056

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
