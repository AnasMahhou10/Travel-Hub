from fastapi import APIRouter, HTTPException, Query

from app.database import get_neo4j

router = APIRouter(tags=["reco"])


@router.get("/reco")
async def get_recommendations(
    city: str = Query(..., description="Code IATA de la ville source"),
    k: int = Query(3, ge=1, le=20),
):
    neo4j = get_neo4j()

    async with neo4j.session() as session:
        result = await session.run(
            """
            MATCH (c:City {code: $city})-[r:NEAR]->(n:City)
            RETURN n.code AS city, n.name AS name, max(r.weight) AS score
            ORDER BY score DESC
            LIMIT $k
            """,
            city=city.upper(),
            k=k,
        )
        records = [
            {"city": r["city"], "name": r["name"], "score": round(r["score"], 3)}
            async for r in result
        ]

    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"Aucune recommandation trouvée pour la ville '{city}'",
        )

    return records