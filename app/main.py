from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import time
import logging

from .routes import offers, reco, auth, stats, notifications
from .database import lifespan
from .metrics import record_route

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="SupDeVinci Travel Hub", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_duration(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logging.info(f"{request.method} {request.url.path} → {response.status_code} ({duration_ms:.1f}ms)")
    record_route(request.url.path, duration_ms)
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.1f}"
    return response

app.include_router(offers.router)
app.include_router(reco.router)
app.include_router(auth.router)
app.include_router(stats.router)
app.include_router(notifications.router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def index():
    return FileResponse("static/index.html")
