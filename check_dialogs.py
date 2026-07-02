import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME", "job_sheet_session")

async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()
    
    print("\n--- Your Telegram Dialogs ---")
    async for dialog in client.iter_dialogs():
        # Print the title, username (if any), and the exact Telethon ID
        username_str = f"(@{dialog.entity.username})" if getattr(dialog.entity, 'username', None) else ""
        print(f"Name: {dialog.name} | ID: {dialog.id} {username_str} | Type: {type(dialog.entity).__name__}")
        
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
