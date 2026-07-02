import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

# Load environment variables
load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")
TELEGRAM_PASSWORD = os.getenv("TELEGRAM_PASSWORD")
SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME", "job_sheet_session")

if not API_ID or not API_HASH:
    print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be configured in your .env file!")
    exit(1)

try:
    API_ID = int(API_ID)
except ValueError:
    print("Error: TELEGRAM_API_ID must be an integer!")
    exit(1)

async def main():
    # 1. Try to load the existing local session file
    session_file = f"{SESSION_NAME}.session"
    if os.path.exists(session_file):
        print(f"Found existing session file: {session_file}")
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.connect()
        
        if await client.is_user_authorized():
            # Export the existing SQLite session as a String Session
            session_str = StringSession.save(client.session)
            print("\n" + "="*80)
            print("SUCCESSFULLY EXPORTED EXISTING SESSION!")
            print("="*80)
            print("Copy this entire string (it is a single line) and add it to your Render Environment Variables:")
            print(f"\nTELEGRAM_STRING_SESSION={session_str}\n")
            print("="*80)
            await client.disconnect()
            return
        else:
            print("Existing session file is not authorized.")
            await client.disconnect()

    # 2. If no valid local session exists, start a new interactive login session
    print("\nStarting a new interactive session to generate a String Session...")
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    await client.start(
        phone=TELEGRAM_PHONE if TELEGRAM_PHONE else None,
        password=TELEGRAM_PASSWORD if TELEGRAM_PASSWORD else None
    )
    
    session_str = client.session.save()
    
    print("\n" + "="*80)
    print("LOGIN SUCCESSFUL & STRING SESSION GENERATED!")
    print("="*80)
    print("Copy this entire string (it is a single line) and add it to your Render Environment Variables:")
    print(f"\nTELEGRAM_STRING_SESSION={session_str}\n")
    print("="*80)
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
