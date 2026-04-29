import json

from fastapi import APIRouter, Query

from app.database import offers_collection, redis_client

router = APIRouter(tags=["stats"])


@router.get("/stats/top-destinations")
async def get_top_destinations(limit: int = Query(5, ge=1, le=20)):
    cache_key = f"stats:top-destinations:{limit}"

    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    pipeline = [
        {
            "$group": {
                "_id": "$to",
                "count": {"$sum": 1},
                "avgPrice": {"$avg": "$price"},
                "minPrice": {"$min": "$price"},
            }
        },
        {"$sort": {"count": -1, "avgPrice": 1}},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "destination": "$_id",
                "count": 1,
                "avgPrice": {"$round": ["$avgPrice", 2]},
                "minPrice": 1,
            }
        },
    ]

    stats = [row async for row in offers_collection.aggregate(pipeline)]

    await redis_client.set(cache_key, json.dumps(stats), ex=120)

    return stats