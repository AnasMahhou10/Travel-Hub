from fastapi import APIRouter, Query, Response

from app.cache import pack_json, unpack_json
from app.database import offers_collection, redis_client
from app.metrics import record_cache_hit, render_prometheus

router = APIRouter(tags=["stats"])


@router.get("/stats/top-destinations")
async def get_top_destinations(limit: int = Query(5, ge=1, le=20)):
    cache_key = f"stats:top-destinations:{limit}"

    cached = await redis_client.get(cache_key)
    if cached:
        record_cache_hit(True)
        return unpack_json(cached)
    record_cache_hit(False)

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
    await redis_client.set(cache_key, pack_json(stats), ex=120)

    return stats


@router.get("/metrics")
async def metrics():
    return Response(
        content=render_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
