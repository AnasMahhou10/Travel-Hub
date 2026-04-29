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

# Redis
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

# MongoDB
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[MONGO_DB]
offers_collection = db["offers"]

# Neo4j
neo4j_driver = AsyncGraphDatabase.driver(
    NEO4J_URL,
    auth=(NEO4J_USER, NEO4J_PASS)
)

@asynccontextmanager
async def lifespan(app):
    try:
        yield
    finally:
        await redis_client.aclose()
        mongo_client.close()
        await neo4j_driver.close()
