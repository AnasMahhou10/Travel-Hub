import json
from datetime import date, datetime
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from app.database import redis_client, offers_collection, neo4j_driver

router = APIRouter()

def json_safe(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    return value

def serialize(offer) -> dict:
    offer = json_safe(offer)
    offer["id"] = offer.pop("_id")
    return offer

# ── GET /offers ──────────────────────────────────────────────────────────────
@router.get("/offers")
async def get_offers(
    from_city: str = Query(..., alias="from"),
    to_city:   str = Query(..., alias="to"),
    q: str | None = Query(None),
    limit:     int = Query(10, ge=1, le=100)
):
    cache_key = f"offers:{from_city}:{to_city}:{q or ''}:{limit}"

    # 1. Cache Redis
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. MongoDB
    filters = {"from": from_city, "to": to_city}
    if q:
        filters["$text"] = {"$search": q}

    cursor = offers_collection.find(filters).sort("price", 1).limit(limit)

    offers = [serialize(o) async for o in cursor]

    if not offers:
        raise HTTPException(status_code=404, detail="No offers found")

    # 3. Stocker dans Redis TTL 60s
    await redis_client.set(cache_key, json.dumps(offers), ex=60)

    return offers


# ── GET /offers/{id} ─────────────────────────────────────────────────────────
@router.get("/offers/{offer_id}")
async def get_offer_by_id(offer_id: str):
    cache_key = f"offers:{offer_id}"

    # 1. Cache Redis
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. MongoDB
    try:
        oid = ObjectId(offer_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid offer ID")

    offer = await offers_collection.find_one({"_id": oid})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    offer = serialize(offer)

    # 3. Neo4j — villes proches de la destination → relatedOffers
    to_city = offer.get("to")
    related_ids = []

    async with neo4j_driver.session() as session:
        result = await session.run(
            """
            MATCH (c:City {code: $city})-[:NEAR]->(n:City)
            RETURN n.code AS code
            LIMIT 3
            """,
            city=to_city
        )
        nearby_codes = [r["code"] async for r in result]

    if nearby_codes:
        cursor = offers_collection.find(
            {"to": {"$in": nearby_codes}}
        ).limit(3)
        related_ids = [str(o["_id"]) async for o in cursor]

    offer["relatedOffers"] = related_ids

    # 4. Stocker dans Redis TTL 300s
    await redis_client.set(cache_key, json.dumps(offer), ex=300)

    return offer
