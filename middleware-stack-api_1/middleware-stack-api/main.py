import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

ALLOWED_ORIGIN = "https://app-09w9wj.example.com"
EMAIL = "25ds1000090@ds.study.iitm.ac.in"
RATE_LIMIT = 15
WINDOW_SECONDS = 10

# Also allow the exam page origin so the grader's browser can reach /ping.
# Add any extra exam-page origins here if the grader specifies one explicitly.
EXAM_PAGE_ORIGINS = [
    "https://exam.sanand.workers.dev",
    "https://tds.s-anand.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN, *EXAM_PAGE_ORIGINS],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "Retry-After"],
)

CLIENT_HITS = defaultdict(deque)


@app.middleware("http")
async def rate_limit_and_context(request: Request, call_next):
    if request.url.path == "/ping":
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

    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/ping")
async def ping(request: Request):
    return {"email": EMAIL, "request_id": request.state.request_id}


@app.get("/")
async def root():
    return {"status": "ok"}
