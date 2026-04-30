import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.database import redis_client

router = APIRouter(tags=["notifications"])


@router.get("/notifications/stream")
async def stream_notifications(request: Request):
    async def event_generator():
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("offers:new")

        try:
            async for message in pubsub.listen():
                if await request.is_disconnected():
                    break

                if message["type"] != "message":
                    continue

                payload = message["data"]
                # Keep the browser payload valid even if another publisher sends plain text.
                try:
                    json.loads(payload)
                    data = payload
                except Exception:
                    data = json.dumps({"message": payload})

                yield f"event: offer-new\ndata: {data}\n\n"
        finally:
            await pubsub.unsubscribe("offers:new")
            await pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
