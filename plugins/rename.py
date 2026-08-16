import os
import time
import json
import asyncio

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    ForceReply,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from config import DOWNLOAD_DIR, DEFAULT_CAPTION
from helpers import database as db
from helpers.progress import progress_callback, human_size

# In-memory state. Chinna bot ku idhu podhum; periya scale na Redis/DB use pannunga.
pending_files = {}
sessions = {}


def _session_id(user_id, msg_id):
    return f"{user_id}:{msg_id}"


@Client.on_message(
    filters.private
    & (filters.document | filters.video | filters.audio)
)
async def receive_file(client: Client, message: Message):
    media = message.document or message.video or message.audio
    old_name = media.file_name or "unknown_file"

    pending_files[message.from_user.id] = {
        "message_id": message.id,
        "file_name": old_name,
        "file_size": media.file_size,
    }

    await message.reply_text(
        f"**File kidaichuchu:** `{old_name}`\n"
        f"**Size:** {human_size(media.file_size)}\n\n"
        f"Pudhu peruku **reply** pannunga (extension oda sேrthu, eg: `Movie.Name.2026.mkv`):",
        reply_markup=ForceReply(selective=True),
    )


@Client.on_message(filters.private & filters.reply & filters.text)
async def receive_new_name(client: Client, message: Message):
    user_id = message.from_user.id
    pending = pending_files.get(user_id)

    if not pending or not message.reply_to_message:
        return
    if "Pudhu peruku" not in (message.reply_to_message.text or ""):
        return

    new_name = message.text.strip()
    if not new_name:
        await message.reply_text("Sariyana peru kudunga.")
        return

    sid = _session_id(user_id, pending["message_id"])
    sessions[sid] = {
        "orig_message_id": pending["message_id"],
        "new_name": new_name,
        "remove_streams": [],
    }
    pending_files.pop(user_id, None)

    buttons = [
        [InlineKeyboardButton("✅ Rename Mattum", callback_data=f"ronly:{sid}")],
        [InlineKeyboardButton("🎞 Audio/Sub Streams Remove Panni Rename", callback_data=f"rstream:{sid}")],
    ]
    await message.reply_text(
        f"Pudhu peru: `{new_name}`\n\nEppadi process pannanum?",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def _download_source(client: Client, chat_id: int, orig_message_id: int, status: Message):
    orig_msg = await client.get_messages(chat_id, orig_message_id)
    start = time.time()
    path = await client.download_media(
        orig_msg,
        file_name=os.path.join(DOWNLOAD_DIR, f"src_{orig_message_id}"),
        progress=progress_callback,
        progress_args=(status, start, "Downloading"),
    )
    return path


async def _run_cmd(*args):
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    return proc.returncode, out.decode(errors="ignore"), err.decode(errors="ignore")


async def _probe_streams(path):
    code, out, err = await _run_cmd(
        "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", path
    )
    if code != 0:
        return []
    return json.loads(out).get("streams", [])


async def _finalize_and_send(client: Client, chat_id: int, status: Message, final_path: str, sid: str):
    user_id = int(sid.split(":")[0])
    thumb = await db.get_thumbnail(user_id)
    caption_tpl = await db.get_caption(user_id) or DEFAULT_CAPTION
    caption = caption_tpl.format(
        filename=os.path.basename(final_path),
        filesize=human_size(os.path.getsize(final_path)),
    )

    start = time.time()
    await client.send_document(
        chat_id,
        final_path,
        thumb=thumb,
        caption=caption,
        force_document=False,
        progress=progress_callback,
        progress_args=(status, start, "Uploading"),
    )
    await status.edit_text("✅ Mudinjachu!")

    try:
        os.remove(final_path)
    except OSError:
        pass
    sessions.pop(sid, None)


@Client.on_callback_query(filters.regex(r"^ronly:"))
async def cb_rename_only(client: Client, query: CallbackQuery):
    sid = query.data.split(":", 1)[1]
    session = sessions.get(sid)
    if not session:
        await query.answer("Session expire aayiduchu, mudhala try pannunga.", show_alert=True)
        return

    await query.answer()
    status = await query.message.edit_text("Download start aagudhu...")

    chat_id = query.message.chat.id
    src_path = await _download_source(client, chat_id, session["orig_message_id"], status)

    ext = os.path.splitext(session["new_name"])[1] or os.path.splitext(src_path)[1]
    new_name = session["new_name"]
    if not new_name.endswith(ext):
        new_name += ext
    final_path = os.path.join(DOWNLOAD_DIR, new_name)
    os.rename(src_path, final_path)

    await status.edit_text("Upload start aagudhu...")
    await _finalize_and_send(client, chat_id, status, final_path, sid)


@Client.on_callback_query(filters.regex(r"^rstream:"))
async def cb_rename_stream(client: Client, query: CallbackQuery):
    sid = query.data.split(":", 1)[1]
    session = sessions.get(sid)
    if not session:
        await query.answer("Session expire aayiduchu, mudhala try pannunga.", show_alert=True)
        return

    await query.answer()
    status = await query.message.edit_text("Download start aagudhu (streams paakanum na file download aganum)...")

    chat_id = query.message.chat.id
    src_path = await _download_source(client, chat_id, session["orig_message_id"], status)
    session["src_path"] = src_path

    streams = await _probe_streams(src_path)
    session["streams"] = streams

    await status.edit_text(
        "Ethana streams remove pannanum nu select pannunga, apram Done click pannunga:",
        reply_markup=_stream_keyboard(sid, session),
    )


def _stream_keyboard(sid, session):
    buttons = []
    for s in session["streams"]:
        idx = s.get("index")
        codec_type = s.get("codec_type")
        if codec_type not in ("audio", "subtitle"):
            continue
        lang = s.get("tags", {}).get("language", "und")
        codec = s.get("codec_name", "?")
        mark = "❌" if idx in session["remove_streams"] else "⬜"
        label = f"{mark} #{idx} {codec_type} ({codec}, {lang})"
        buttons.append([InlineKeyboardButton(label, callback_data=f"toggle:{sid}:{idx}")])
    buttons.append([InlineKeyboardButton("✅ Done - Process Pannu", callback_data=f"streamdone:{sid}")])
    return InlineKeyboardMarkup(buttons)


@Client.on_callback_query(filters.regex(r"^toggle:"))
async def cb_toggle_stream(client: Client, query: CallbackQuery):
    _, sid, idx = query.data.split(":")
    idx = int(idx)
    session = sessions.get(sid)
    if not session:
        await query.answer("Session expire aayiduchu.", show_alert=True)
        return

    if idx in session["remove_streams"]:
        session["remove_streams"].remove(idx)
    else:
        session["remove_streams"].append(idx)

    await query.edit_message_reply_markup(reply_markup=_stream_keyboard(sid, session))
    await query.answer()


@Client.on_callback_query(filters.regex(r"^streamdone:"))
async def cb_stream_done(client: Client, query: CallbackQuery):
    sid = query.data.split(":", 1)[1]
    session = sessions.get(sid)
    if not session:
        await query.answer("Session expire aayiduchu.", show_alert=True)
        return

    await query.answer()
    status = query.message
    chat_id = status.chat.id
    src_path = session["src_path"]

    ext = os.path.splitext(session["new_name"])[1] or os.path.splitext(src_path)[1]
    new_name = session["new_name"]
    if not new_name.endswith(ext):
        new_name += ext
    final_path = os.path.join(DOWNLOAD_DIR, new_name)

    if session["remove_streams"]:
        await status.edit_text("🎞 Selected streams remove pannikittu irukom (ffmpeg)...")
        map_args = ["-map", "0"]
        for idx in session["remove_streams"]:
            map_args += ["-map", f"-0:{idx}"]

        title = os.path.splitext(os.path.basename(final_path))[0]
        code, out, err = await _run_cmd(
            "ffmpeg", "-y", "-i", src_path,
            *map_args,
            "-c", "copy",
            "-metadata", f"title={title}",
            final_path,
        )
        if code != 0:
            await status.edit_text(f"❌ ffmpeg error:\n`{err[-800:]}`")
            return
        os.remove(src_path)
    else:
        os.rename(src_path, final_path)

    await status.edit_text("Upload start aagudhu...")
    await _finalize_and_send(client, chat_id, status, final_path, sid)
