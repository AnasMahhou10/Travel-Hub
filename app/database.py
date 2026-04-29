import os
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import AsyncGraphDatabase

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB", "sth")
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "password")

#Redis
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

def get_redis():
    return redis_client

#MongoDB
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[MONGO_DB]
offers_collection = db["offers"]

def get_mongo_offers():
    return offers_collection

#Neo4j
neo4j_driver = AsyncGraphDatabase.driver(
    NEO4J_URL,
    auth=(NEO4J_USER, NEO4J_PASS)
)

def get_neo4j():
    return neo4j_driver

async def ensure_mongo_indexes():
    await offers_collection.create_index([("from", 1), ("to", 1), ("price", 1)])

    async for index in offers_collection.list_indexes():
        key = index.get("key", {})
        is_text_index = any(value == "text" for value in key.values())
        if is_text_index and index["name"] != "offer_text_search":
            await offers_collection.drop_index(index["name"])

    await offers_collection.create_index(
        [
            ("provider", "text"),
            ("hotel.name", "text"),
            ("activity.title", "text"),
        ],
        name="offer_text_search",
        default_language="none",
    )

@asynccontextmanager
async def lifespan(app):
    await ensure_mongo_indexes()
    try:
        yield
    finally:
        await redis_client.aclose()
        mongo_client.close()
        await neo4j_driver.close()