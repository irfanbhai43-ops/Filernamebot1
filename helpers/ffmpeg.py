import os
import time
import asyncio
import logging

logger = logging.getLogger(__name__)


async def get_streams(file_path: str):
    """
    ffprobe use panni file la irukura audio/subtitle streams ah
    list panna help pannura function.
    Return: list of dicts [{index, codec_type, codec_name, language}, ...]
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "stream=index,codec_type,codec_name:stream_tags=language",
        "-of", "csv=p=0",
        file_path,
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error(f"ffprobe error: {stderr.decode()}")
        return []

    streams = []
    for line in stdout.decode().strip().split("\n"):
        if not line:
            continue
        parts = line.split(",")
        index = parts[0]
        codec_type = parts[1] if len(parts) > 1 else ""
        codec_name = parts[2] if len(parts) > 2 else ""
        language = parts[3] if len(parts) > 3 else "und"
        streams.append({
            "index": index,
            "codec_type": codec_type,
            "codec_name": codec_name,
            "language": language,
        })
    return streams


async def remove_streams(
    input_path: str,
    output_path: str,
    remove_audio: bool = False,
    remove_subtitle: bool = False,
    keep_audio_indexes: list = None,
    keep_subtitle_indexes: list = None,
):
    """
    Video stream ah quality/codec maratha (re-encode pannama) audio/subtitle
    streams ah mattum remove pannura function.

    remove_audio / remove_subtitle: True na antha type full ah drop pannum.
    keep_audio_indexes / keep_subtitle_indexes: specific stream indexes mattum
    vekanum na antha list kudunga (0-based index list of that stream type).

    -map -0:a -map -0:s madhiri "negative map" use panni, source file la irundhu
    nera antha streams ah exclude pannuvom. Video + container maaradhu, adhanala
    processing romba fast (no re-encode).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file kedaikala: {input_path}")

    cmd = ["ffmpeg", "-y", "-i", input_path]

    # Base mapping: video always keep pannum
    cmd += ["-map", "0:v"]

    # Audio handling
    if remove_audio:
        pass  # audio streams ah map pannave maatom -> fully removed
    elif keep_audio_indexes:
        for idx in keep_audio_indexes:
            cmd += ["-map", f"0:a:{idx}"]
    else:
        cmd += ["-map", "0:a?"]  # ellame keep (default)

    # Subtitle handling
    if remove_subtitle:
        pass
    elif keep_subtitle_indexes:
        for idx in keep_subtitle_indexes:
            cmd += ["-map", f"0:s:{idx}"]
    else:
        cmd += ["-map", "0:s?"]

    # Codec copy -> re-encode illa, adhanala fast + quality loss illa
    cmd += ["-c", "copy", output_path]

    logger.info(f"Running ffmpeg cmd: {' '.join(cmd)}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode()
        logger.error(f"ffmpeg failed: {error_msg}")
        raise RuntimeError(f"Stream removal failed:\n{error_msg[-1500:]}")

    if not os.path.exists(output_path):
        raise RuntimeError("Output file create aagala, ffmpeg silent ah fail aayiruchu")

    return output_path


# ---- Example usage inside your Pyrogram handler ----
#
# from ffmpeg import remove_streams
#
# @app.on_message(filters.command("removeaudio"))
# async def remove_audio_handler(client, message):
#     input_path = "downloads/input.mkv"
#     output_path = "downloads/output.mkv"
#     status = await message.reply("Processing... audio streams remove pandrom")
#     try:
#         await remove_streams(input_path, output_path, remove_audio=True)
#         await client.send_document(message.chat.id, output_path)
#     except Exception as e:
#         await status.edit(f"Error: {e}")
#     finally:
#         for f in (input_path, output_path):
#             if os.path.exists(f):
#                 os.remove(f)
