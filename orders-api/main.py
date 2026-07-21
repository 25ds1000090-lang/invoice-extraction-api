import base64
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)

TOTAL_ORDERS = 41
RATE_LIMIT = 15
WINDOW_SECONDS = 10

# Fixed catalog of orders 1..T
CATALOG = [{"id": i, "item": f"item-{i}", "status": "confirmed"} for i in range(1, TOTAL_ORDERS + 1)]

# Idempotency store: key -> order dict
IDEMPOTENCY_STORE = {}

# Rate limiting: client_id -> deque of timestamps
CLIENT_HITS = defaultdict(deque)


def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode()).decode()


def decode_cursor(cursor: str) -> int:
    try:
        return int(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception:
        return 0


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/orders" and request.method in ("GET", "POST"):
        client_id = request.headers.get("x-client-id", "anonymous")
        now = time.monotonic()
        hits = CLIENT_HITS[client_id]
        while hits and now - hits[0] > WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= RATE_LIMIT:
            retry_after = max(1, int(WINDOW_SECONDS - (now - hits[0])))
            return JSONResponse(
                status_code=429,
                content={"detail": "rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )
        hits.append(now)
    return await call_next(request)


@app.post("/orders")
async def create_order(request: Request, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header required")

    if idempotency_key in IDEMPOTENCY_STORE:
        order = IDEMPOTENCY_STORE[idempotency_key]
        return JSONResponse(status_code=200, content=order)

    order = {"id": str(uuid.uuid4()), "status": "created"}
    IDEMPOTENCY_STORE[idempotency_key] = order
    return JSONResponse(status_code=201, content=order)


@app.get("/orders")
async def list_orders(limit: int = 10, cursor: str | None = None):
    offset = decode_cursor(cursor) if cursor else 0
    limit = max(1, limit)
    items = CATALOG[offset: offset + limit]
    next_offset = offset + len(items)
    next_cursor = encode_cursor(next_offset) if next_offset < TOTAL_ORDERS else None
    return {"items": items, "next_cursor": next_cursor}


@app.get("/")
async def root():
    return {"status": "ok"}
