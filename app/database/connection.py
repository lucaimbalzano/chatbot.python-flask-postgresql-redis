# connection.py
import os
import time
import redis
from supabase import create_client, Client
from postgrest import APIError
import logging

# ────────────────────────────────────────────────
# ENVIRONMENT ------------------------------------
SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
REDIS_URL            = os.environ["REDIS_URL"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
r = redis.from_url(REDIS_URL, decode_responses=True)

# ────────────────────────────────────────────────
# CONSTANTS --------------------------------------
CACHE_TTL = 60 * 60 * 24      # 24 h
RUN_TTL   = 60 * 30           # 30 min
LOCK_TTL  = 5                 # 5 s

# ────────────────────────────────────────────────
# THREAD-ID CACHE  (returns the BIGINT id) -------
def get_thread_id(wa_id: str) -> int | None:
    cache_key = f"waid:{wa_id}"

    # 1) Try Redis
    try:
        tid_str = r.get(cache_key)
        if tid_str is not None:
            try:
                return int(tid_str)
            except ValueError:
                # wrong format in cache → delete and fallback
                r.delete(cache_key)
    except redis.RedisError:
        pass

    # 2) Fall back to Supabase
    try:
        res = (
            supabase.table("threads")
                    .select("id")
                    .eq("wa_id", wa_id)
                    .maybe_single()
                    .execute()
        )
    except APIError:
        return None

    if res and res.data:
        tid = res.data["id"]
        try:
            r.setex(cache_key, CACHE_TTL, tid)
        except redis.RedisError:
            pass
        return tid

    return None

def save_thread(
    wa_id: str,
    openai_thread_id: str,
    assistant_id: str
) -> int:
    """
    Upsert a thread row keyed on wa_id, return its BIGINT id.
    Uses returning="representation" to get back the full row.
    Raises RuntimeError on failure.
    """
    try:
        res = (
            supabase
            .table("threads")
            .upsert(
                {
                    "openai_thread_id": openai_thread_id,
                    "wa_id":            wa_id,
                    "assistant_id":     assistant_id,
                    "last_seen":        "now()",
                },
                returning="representation"   # ask PostgREST to give us back the row
            )
            .execute()
        )
    except Exception as e:
        logging.error(f"[save_thread] Supabase upsert error for wa_id={wa_id}: {e}")
        raise RuntimeError("Database error in save_thread") from e

    # res.data is a list of row-dicts
    if not res or not getattr(res, "data", None):
        logging.error(f"[save_thread] No data returned for wa_id={wa_id}, res={res!r}")
        raise RuntimeError("Failed to retrieve thread row after upsert")

    # grab the first (and only) row
    row = res.data[0]
    if "id" not in row:
        logging.error(f"[save_thread] Upsert returned row without id: {row}")
        raise RuntimeError("Missing id in save_thread result")

    internal_id = row["id"]                 # the BIGINT from Postgres

    # cache it in Redis
    try:
        r.setex(f"waid:{wa_id}", CACHE_TTL, internal_id)
    except redis.RedisError as err:
        logging.warning(f"[save_thread] Could not cache in Redis: {err}")

    return internal_id


# ────────────────────────────────────────────────
# OPTIONAL METADATA / RUN STATUS -----------------
def cache_thread_meta(thread_id: int, wa_id: str, assistant_id: str):
    key = f"thread:{thread_id}"
    now = int(time.time())
    try:
        r.hset(key, mapping={
            "wa_id":        wa_id,
            "assistant_id": assistant_id,
            "created_at":   now,
            "last_seen":    now,
        })
        r.expire(key, CACHE_TTL)
    except redis.RedisError:
        pass


def cache_run_status(run_id: str, status: str, tokens: int | None = None):
    key = f"run:{run_id}"
    try:
        r.hset(key, mapping={
            "status":     status,
            "last_poll":  int(time.time()),
            **({"tokens": tokens} if tokens is not None else {}),
        })
        r.expire(key, RUN_TTL)
    except redis.RedisError:
        pass


def get_run_status(run_id: str) -> dict | None:
    try:
        data = r.hgetall(f"run:{run_id}")
    except redis.RedisError:
        return None
    return data or None


# ────────────────────────────────────────────────
# SIMPLE DISTRIBUTED LOCK ------------------------
def acquire_lock(wa_id: str) -> bool:
    try:
        return r.set(f"lock:{wa_id}", "1", nx=True, ex=LOCK_TTL)
    except redis.RedisError:
        return False


def release_lock(wa_id: str):
    try:
        r.delete(f"lock:{wa_id}")
    except redis.RedisError:
        pass
