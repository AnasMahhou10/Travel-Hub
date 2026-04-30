import json
from datetime import date, datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from app.cache import pack_json, unpack_json
from app.database import redis_client, offers_collection, neo4j_driver
from app.metrics import record_cache_hit

router = APIRouter(tags=["offers"])
OFFERS_NEW_CHANNEL = "offers:new"


class Leg(BaseModel):
    flightNum: str
    dep: str
    arr: str
    duration: str


class Hotel(BaseModel):
    name: str
    nights: int
    price: float


class Activity(BaseModel):
    title: str
    price: float


class OfferCreate(BaseModel):
    from_city: str = Field(..., alias="from")
    to: str
    departDate: datetime
    returnDate: datetime
    provider: str
    price: float
    currency: str
    legs: list[Leg]
    hotel: Hotel | None = None
    activity: Activity | None = None

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


async def invalidate_offer_caches(from_city: str, to_city: str):
    cache_keys = [
        f"offers:{from_city}:{to_city}",
        "stats:top-destinations:5",
    ]

    async for key in redis_client.scan_iter(f"offers:{from_city}:{to_city}:q:*"):
        cache_keys.append(key)

    async for key in redis_client.scan_iter("stats:top-destinations:*"):
        if key not in cache_keys:
            cache_keys.append(key)

    if cache_keys:
        await redis_client.delete(*cache_keys)


async def publish_new_offer(offer: dict):
    message = {
        "event": "offer.created",
        "channel": OFFERS_NEW_CHANNEL,
        "publishedAt": datetime.now(timezone.utc).isoformat(),
        "offerId": offer["id"],
        "from": offer["from"],
        "to": offer["to"],
        "provider": offer["provider"],
        "price": offer["price"],
        "currency": offer["currency"],
        "offer": offer,
    }

    await redis_client.publish(OFFERS_NEW_CHANNEL, json.dumps(message))

# ── GET /offers ──────────────────────────────────────────────────────────────
@router.get("/offers")
async def get_offers(
    from_city: str = Query(..., alias="from"),
    to_city:   str = Query(..., alias="to"),
    q: str | None = Query(None),
    limit:     int = Query(10, ge=1, le=100)
):
    from_city = from_city.upper()
    to_city = to_city.upper()
    cache_key = f"offers:{from_city}:{to_city}" if not q else f"offers:{from_city}:{to_city}:q:{q}:limit:{limit}"

    # 1. Cache Redis
    cached = await redis_client.get(cache_key)
    if cached:
        record_cache_hit(True)
        return unpack_json(cached)
    record_cache_hit(False)

    # 2. MongoDB
    filters = {"from": from_city, "to": to_city}
    if q:
        if q.lower() in {"hotel", "hotels", "hebergement", "hébergement"}:
            filters["hotel"] = {"$ne": None}
        else:
            filters["$text"] = {"$search": q}

    cursor = offers_collection.find(filters).sort("price", 1).limit(limit)

    offers = [serialize(o) async for o in cursor]

    if not offers:
        raise HTTPException(status_code=404, detail="No offers found")

    # 3. Stocker dans Redis TTL 60s en JSON gzip
    await redis_client.set(cache_key, pack_json(offers), ex=60)

    return offers


@router.post("/offers", status_code=status.HTTP_201_CREATED)
async def create_offer(offer: OfferCreate):
    document = offer.model_dump()
    document["from"] = document.pop("from_city")
    document["from"] = document["from"].upper()
    document["to"] = document["to"].upper()

    result = await offers_collection.insert_one(document)
    created_offer = serialize({"_id": result.inserted_id, **document})

    await publish_new_offer(created_offer)
    await invalidate_offer_caches(document["from"], document["to"])

    return created_offer


# ── GET /offers/{id} ─────────────────────────────────────────────────────────
@router.get("/offers/{offer_id}")
async def get_offer_by_id(offer_id: str):
    cache_key = f"offers:{offer_id}"

    # 1. Cache Redis
    cached = await redis_client.get(cache_key)
    if cached:
        record_cache_hit(True)
        return unpack_json(cached)
    record_cache_hit(False)

    # 2. MongoDB
    try:
        oid = ObjectId(offer_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid offer ID")

    offer_doc = await offers_collection.find_one({"_id": oid})
    if not offer_doc:
        raise HTTPException(status_code=404, detail="Offer not found")

    depart_date = offer_doc.get("departDate")
    return_date = offer_doc.get("returnDate")
    offer = serialize(offer_doc)

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
            {
                "_id": {"$ne": oid},
                "to": {"$in": nearby_codes},
                "departDate": depart_date,
                "returnDate": return_date,
            }
        ).limit(3)
        related_ids = [str(o["_id"]) async for o in cursor]

    offer["relatedOffers"] = related_ids

    # 4. Stocker dans Redis TTL 300s
    await redis_client.set(cache_key, pack_json(offer), ex=300)

    return offer
