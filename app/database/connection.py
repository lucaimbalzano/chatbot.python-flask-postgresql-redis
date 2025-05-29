# connection.py
import os, time, redis
from supabase import create_client, Client

# ────────────────────────────────────────────────
# ENVIRONMENT ------------------------------------
SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
REDIS_URL            = os.environ["REDIS_URL"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
r        = redis.from_url(REDIS_URL, decode_responses=True)

# ────────────────────────────────────────────────
# CONSTANTS --------------------------------------
CACHE_TTL = 60 * 60 * 24      # 24 h
RUN_TTL   = 60 * 30           # 30 min
LOCK_TTL  = 5                 # 5 s

# ────────────────────────────────────────────────
# THREAD-ID CACHE --------------------------------
def get_thread_id(wa_id: str) -> str | None:
    """
    Fast path: Redis → fallback to Supabase.
    """
    if tid := r.get(f"waid:{wa_id}"):
        return tid

    res = supabase.table("threads").select("id").eq("wa_id", wa_id).single().execute()
    if res.data:
        tid = res.data["id"]
        r.setex(f"waid:{wa_id}", CACHE_TTL, tid)
        return tid
    return None


def save_thread(wa_id: str, thread_id: str, assistant_id: str):
    """
    Persist both caches (Redis + Supabase). Upsert keeps it idempotent.
    """
    r.setex(f"waid:{wa_id}", CACHE_TTL, thread_id)

    supabase.table("threads").upsert({
        "id":          thread_id,
        "wa_id":       wa_id,
        "assistant_id": assistant_id,
        "last_seen":   "now()",
    }).execute()


# ────────────────────────────────────────────────
# OPTIONAL METADATA / RUN STATUS -----------------
def cache_thread_meta(thread_id: str, wa_id: str, assistant_id: str):
    key = f"thread:{thread_id}"
    now = int(time.time())
    r.hset(key, mapping={
        "wa_id":        wa_id,
        "assistant_id": assistant_id,
        "created_at":   now,
        "last_seen":    now,
    })
    r.expire(key, CACHE_TTL)


def cache_run_status(run_id: str, status: str, tokens: int | None = None):
    key = f"run:{run_id}"
    r.hset(key, mapping={
        "status":     status,
        "last_poll":  int(time.time()),
        **({"tokens": tokens} if tokens is not None else {}),
    })
    r.expire(key, RUN_TTL)


def get_run_status(run_id: str) -> dict | None:
    data = r.hgetall(f"run:{run_id}")
    return data or None


# ────────────────────────────────────────────────
# SIMPLE DISTRIBUTED LOCK ------------------------
def acquire_lock(wa_id: str) -> bool:
    """
    Returns True if lock acquired, False otherwise.
    """
    return r.set(f"lock:{wa_id}", "1", nx=True, ex=LOCK_TTL)


def release_lock(wa_id: str):
    r.delete(f"lock:{wa_id}")
