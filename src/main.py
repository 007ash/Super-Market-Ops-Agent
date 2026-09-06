import os
import sys
import time


def main() -> int:
    print("AI_smart_mart starting...")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token == "your_telegram_bot_token_from_botfather":
        print("No TELEGRAM_BOT_TOKEN configured; starting in local demo mode.")
        print("Project is bootable, but Telegram integration remains disabled until a valid bot token is supplied.")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("Shutting down AI_smart_mart...")
            return 0
    print("Telegram bot token detected; app initialization would continue here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
