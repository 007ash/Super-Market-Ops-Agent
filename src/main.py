import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from .database import SessionLocal
from .agent import AgentOrchestrator

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am AI_smart_mart agent. How can I help you today?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    db = SessionLocal()
    try:
        orchestrator = AgentOrchestrator(db)
        response = orchestrator.handle_message(user_message, chat_id)
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"Error processing request: {str(e)}")
    finally:
        db.close()

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        return
        
    print("AI_smart_mart bot is starting...")
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Polling started. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
