from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "**File Renamer Bot ku Vanakkam! 🤖**\n\n"
        "Enakku edhavadhu file (document/video/audio) anuppunga, "
        "naan pudhusa peru vecha, thumbnail set panni, "
        "vendiya audio/subtitle streams remove panni thirumba anுppuven.\n\n"
        "**Commands:**\n"
        "/set_thumb - Photo ku reply pannitu inda command kudunga, thumbnail save aagum\n"
        "/view_thumb - Save aana thumbnail paakalam\n"
        "/del_thumb - Thumbnail delete pannalam\n"
        "/set_caption - Custom caption vekalam ({filename}, {filesize} use pannalam)\n\n"
        "File anuppi try pannunga! 🚀"
    )


@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client: Client, message: Message):
    await start_cmd(client, message)
