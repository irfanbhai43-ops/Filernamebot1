import time
import math

# Ovvoru user/message ku last edit time track pannurathukku
_last_update = {}


def human_size(size: float) -> str:
    if not size:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return f"{s} {units[i]}"


def human_time(seconds: float) -> str:
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def make_bar(percentage: float, length: int = 12) -> str:
    filled = int(length * percentage / 100)
    return "●" * filled + "○" * (length - filled)


async def progress_callback(current, total, message, start_time, action="Processing"):
    """
    Pyrogram download/upload progress hook.
    Rate-limit pannitu 3 seconds ku oru thadava mattum message edit pannum,
    illana Telegram FloodWait varum.
    """
    key = message.chat.id if hasattr(message, "chat") else id(message)
    now = time.time()

    if key in _last_update and (now - _last_update[key]) < 3 and current != total:
        return

    _last_update[key] = now

    percentage = current * 100 / total if total else 0
    elapsed = now - start_time
    speed = current / elapsed if elapsed > 0 else 0
    eta = (total - current) / speed if speed > 0 else 0

    text = (
        f"**{action}...**\n\n"
        f"[{make_bar(percentage)}] {percentage:.1f}%\n\n"
        f"**Done:** {human_size(current)} / {human_size(total)}\n"
        f"**Speed:** {human_size(speed)}/s\n"
        f"**ETA:** {human_time(eta)}"
    )

    try:
        await message.edit_text(text)
    except Exception:
        # Message edit pannradhula edhavadhu error (e.g. MESSAGE_NOT_MODIFIED) ah ignore pannalam
        pass
