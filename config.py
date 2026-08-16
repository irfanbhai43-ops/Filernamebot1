import os

# Telegram App credentials - my.telegram.org la vangunga
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")

# BotFather kudukura bot token
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Bot velaya panra namba (optional, session name)
SESSION_NAME = os.environ.get("SESSION_NAME", "FileRenameBot")

# Download/output oda temp folder
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "./downloads")

# Default caption format. {filename} {filesize} nu placeholders use pannalam
DEFAULT_CAPTION = os.environ.get(
    "DEFAULT_CAPTION", "**{filename}**\n\nSize: {filesize}"
)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
