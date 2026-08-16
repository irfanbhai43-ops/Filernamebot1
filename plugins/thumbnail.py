from pyrogram import Client, filters
from pyrogram.types import Message

from helpers import database as db


@Client.on_message(filters.command("set_thumb") & filters.private)
async def set_thumb(client: Client, message: Message):
    reply = message.reply_to_message
    if not reply or not reply.photo:
        await message.reply_text(
            "Oru photo ku **reply** pannitu `/set_thumb` nu anuppunga."
        )
        return

    await db.set_thumbnail(message.from_user.id, reply.photo.file_id)
    await message.reply_text("✅ Thumbnail save aachu!")


@Client.on_message(filters.command("view_thumb") & filters.private)
async def view_thumb(client: Client, message: Message):
    thumb = await db.get_thumbnail(message.from_user.id)
    if not thumb:
        await message.reply_text("Neenga innum thumbnail set pannala.")
        return
    await client.send_photo(message.chat.id, thumb, caption="Ithu dhan unga current thumbnail")


@Client.on_message(filters.command("del_thumb") & filters.private)
async def del_thumb(client: Client, message: Message):
    await db.del_thumbnail(message.from_user.id)
    await message.reply_text("🗑 Thumbnail delete pannachu.")


@Client.on_message(filters.command("set_caption") & filters.private)
async def set_caption(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text(
            "Format: `/set_caption {filename}\\n\\nSize: {filesize}`\n\n"
            "`{filename}` and `{filesize}` placeholders use pannalam."
        )
        return
    caption = message.text.split(None, 1)[1]
    await db.set_caption(message.from_user.id, caption)
    await message.reply_text("✅ Caption save aachu!")
