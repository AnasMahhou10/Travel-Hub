from collections import defaultdict

route_stats = defaultdict(lambda: {"count": 0, "total_ms": 0.0})
cache_stats = {"hits": 0, "misses": 0}


def record_route(path: str, duration_ms: float):
    stats = route_stats[path]
    stats["count"] += 1
    stats["total_ms"] += duration_ms


def record_cache_hit(hit: bool):
    if hit:
        cache_stats["hits"] += 1
    else:
        cache_stats["misses"] += 1


def render_prometheus() -> str:
    lines = [
        "# HELP sth_route_duration_avg_ms Average route duration in milliseconds.",
        "# TYPE sth_route_duration_avg_ms gauge",
    ]

    for route, stats in sorted(route_stats.items()):
        avg_ms = stats["total_ms"] / stats["count"]
        lines.append(f'sth_route_duration_avg_ms{{route="{route}"}} {avg_ms:.3f}')

    total_cache = cache_stats["hits"] + cache_stats["misses"]
    hit_rate = cache_stats["hits"] / total_cache if total_cache else 0

    lines.extend(
        [
            "# HELP sth_cache_hits_total Total Redis cache hits.",
            "# TYPE sth_cache_hits_total counter",
            f"sth_cache_hits_total {cache_stats['hits']}",
            "# HELP sth_cache_misses_total Total Redis cache misses.",
            "# TYPE sth_cache_misses_total counter",
            f"sth_cache_misses_total {cache_stats['misses']}",
            "# HELP sth_cache_hit_rate Redis cache hit ratio.",
            "# TYPE sth_cache_hit_rate gauge",
            f"sth_cache_hit_rate {hit_rate:.3f}",
        ]
    )

    return "\n".join(lines) + "\n"


def render_summary() -> dict:
    total_cache = cache_stats["hits"] + cache_stats["misses"]
    hit_rate = cache_stats["hits"] / total_cache if total_cache else 0

    routes = []
    for route, stats in sorted(route_stats.items()):
        avg_ms = stats["total_ms"] / stats["count"] if stats["count"] else 0
        routes.append(
            {
                "route": route,
                "requests": stats["count"],
                "average_ms": round(avg_ms, 3),
            }
        )

    return {
        "routes": routes,
        "cache": {
            "hits": cache_stats["hits"],
            "misses": cache_stats["misses"],
            "total": total_cache,
            "hit_rate": round(hit_rate, 3),
            "hit_rate_percent": round(hit_rate * 100, 1),
        },
    }
