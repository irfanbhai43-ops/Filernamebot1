import os
import motor.motor_asyncio

MONGO_URL = os.environ.get("MONGO_URL", "")
DB_NAME = os.environ.get("DB_NAME", "filerenamebot")

_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
_db = _client[DB_NAME]
_users = _db["users"]


async def get_user(user_id: int) -> dict:
    user = await _users.find_one({"_id": user_id})
    return user or {}


async def set_thumbnail(user_id: int, file_id: str):
    await _users.update_one(
        {"_id": user_id},
        {"$set": {"thumb_file_id": file_id}},
        upsert=True,
    )


async def get_thumbnail(user_id: int):
    user = await get_user(user_id)
    return user.get("thumb_file_id")


async def del_thumbnail(user_id: int):
    await _users.update_one(
        {"_id": user_id},
        {"$unset": {"thumb_file_id": ""}},
    )


async def set_caption(user_id: int, caption: str):
    await _users.update_one(
        {"_id": user_id},
        {"$set": {"caption": caption}},
        upsert=True,
    )


async def get_caption(user_id: int):
    user = await get_user(user_id)
    return user.get("caption")
