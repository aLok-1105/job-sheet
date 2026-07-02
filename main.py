import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from parser import parse_job_message
from sheets import add_to_sheet

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("JobSheetBot")

# Load environment variables
load_dotenv()

# Configuration validation
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")
TELEGRAM_PASSWORD = os.getenv("TELEGRAM_PASSWORD")
SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME", "job_sheet_session")
GROUP_IDS_STR = os.getenv("TELEGRAM_GROUP_IDENTIFIER")

if not API_ID or not API_HASH:
    logger.critical("TELEGRAM_API_ID and TELEGRAM_API_HASH must be configured in your .env file!")
    sys.exit(1)

# Convert API_ID to int
try:
    API_ID = int(API_ID)
except ValueError:
    logger.critical("TELEGRAM_API_ID must be an integer!")
    sys.exit(1)

if not GROUP_IDS_STR:
    logger.critical("TELEGRAM_GROUP_IDENTIFIER must be configured in your .env file!")
    sys.exit(1)

# Parse groups to listen to (handles usernames, join links, web client URLs, or numeric IDs)
target_chats = []
for item in GROUP_IDS_STR.split(","):
    item = item.strip()
    if not item:
        continue
    
    # Extract from Web Telegram URLs (e.g. https://web.telegram.org/k/#getjobss)
    if "web.telegram.org" in item:
        if "#" in item:
            item = item.split("#")[-1]
            
    # Clean standard prefixes
    clean_item = item.replace("https://t.me/", "").replace("@", "").lstrip('/')
    
    # Check if the result is an ID
    if (clean_item.startswith('-') and clean_item[1:].isdigit()) or clean_item.isdigit():
        val = clean_item.lstrip('-')
        # Telegram channel/supergroup IDs from web client are usually 10 digits and need -100 prefix
        if len(val) >= 9:
            if not clean_item.startswith('-100'):
                target_chats.append(int(f"-100{val}"))
            else:
                target_chats.append(int(clean_item))
        else:
            target_chats.append(int(clean_item))
    else:
        target_chats.append(clean_item)

logger.info(f"Configured to listen to chats: {target_chats}")

# Initialize Telegram client
# Telethon will use the session file or string session to store authorization state.
STRING_SESSION = os.getenv("TELEGRAM_STRING_SESSION")
if STRING_SESSION:
    from telethon.sessions import StringSession
    logger.info("Initializing Telegram client with String Session...")
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
else:
    logger.info(f"Initializing Telegram client with Session File '{SESSION_NAME}'...")
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


@client.on(events.NewMessage(chats=target_chats))
async def handle_new_message(event):
    message_text = event.message.message
    if not message_text:
        return
        
    chat = await event.get_chat()
    chat_title = getattr(chat, 'title', getattr(chat, 'username', str(chat.id)))
    
    logger.info(f"New message received from '{chat_title}' (ID: {event.chat_id})")
    
    # Parse the message
    job_data = parse_job_message(message_text)
    if job_data:
        logger.info(f"Parsed Job: {job_data['company']} - {job_data['position']}")
        
        # Save to Google Sheets
        success = add_to_sheet(job_data)
        if success:
            logger.info("Successfully saved to Google Sheets.")
        else:
            logger.error("Failed to save to Google Sheets.")
    else:
        logger.info("Message did not match the job posting format. Ignored.")

async def handle_health_check(reader, writer):
    try:
        await reader.readuntil(b"\r\n\r\n")
    except asyncio.IncompleteReadError:
        pass
    
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 2\r\n"
        "Connection: close\r\n"
        "\r\n"
        "OK"
    )
    writer.write(response.encode("utf-8"))
    await writer.drain()
    writer.close()
    try:
        await writer.wait_closed()
    except Exception:
        pass

async def start_health_check_server():
    port = int(os.getenv("PORT", "10000"))
    server = await asyncio.start_server(handle_health_check, "0.0.0.0", port)
    logger.info(f"Health check server started on port {port}")
    asyncio.create_task(server.serve_forever())

async def main():
    # Start dummy health check server if PORT is set (useful for Render web service)
    if os.getenv("PORT"):
        await start_health_check_server()

    logger.info("Starting Telegram listener...")
    
    # Authenticate as bot if BOT_TOKEN is provided, otherwise as user
    if BOT_TOKEN:
        logger.info("Logging in using Bot Token...")
        await client.start(bot_token=BOT_TOKEN)
    else:
        logger.info("Logging in using User account...")
        await client.start(
            phone=TELEGRAM_PHONE if TELEGRAM_PHONE else None,
            password=TELEGRAM_PASSWORD if TELEGRAM_PASSWORD else None
        )
        
    me = await client.get_me()
    username = me.username or "No Username"
    logger.info(f"Successfully logged in as: {me.first_name} (@{username})")
    logger.info("Listening for new job postings... Press Ctrl+C to stop.")
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        # Run client main loop
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.exception(f"Unhandled exception in main loop: {e}")
