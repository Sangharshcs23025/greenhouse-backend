import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.mongo_uri, tlsCAFile=certifi.where())
db = client[settings.mongo_db_name]

# Collections
users_collection = db["users"]
sensor_readings_collection = db["sensor_readings"]
devices_collection = db["devices"]
predictions_collection = db["predictions"]


async def init_indexes():
    """Call once at startup to make queries fast and enforce uniqueness."""
    await users_collection.create_index("email", unique=True)
    await sensor_readings_collection.create_index("timestamp")
    await devices_collection.create_index("device_id", unique=True)