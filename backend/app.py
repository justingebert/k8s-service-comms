import os
import logging
from flask import Flask, jsonify

app = Flask(__name__)

_db_conn = None
_db_ready = False


def _db_env():
    return {
        "host": os.environ.get("DB_HOST"),
        "port": int(os.environ.get("DB_PORT", 5432)),
        "dbname": os.environ.get("DB_NAME"),
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
    }


def _connect_db():
    global _db_conn, _db_ready
    if _db_conn is not None:
        return _db_conn
    cfg = _db_env()
    if not all([cfg["host"], cfg["dbname"], cfg["user"], cfg["password"]]):
        logging.info("DB env incomplete; skipping DB connection")
        return None
    try:
        import psycopg2  # imported lazily so local dev without DB still works
        _db_conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["dbname"],
            user=cfg["user"],
            password=cfg["password"],
            connect_timeout=5,
        )
        _db_conn.autocommit = True
        _ensure_table()
        _db_ready = True
        logging.info("Connected to Postgres and ensured table")
    except Exception as e:
        logging.warning(f"Postgres connection failed: {e}")
        _db_conn = None
    return _db_conn


def _ensure_table():
    if _db_conn is None:
        return
    try:
        with _db_conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS hello_calls (
                    id BIGSERIAL PRIMARY KEY,
                    called_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    from_pod TEXT
                );
                """
            )
    except Exception as e:
        logging.warning(f"Ensuring table failed: {e}")


def _log_hello(from_pod: str):
    conn = _connect_db()
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO hello_calls (from_pod) VALUES (%s);",
                (from_pod,),
            )
    except Exception as e:
        logging.warning(f"Insert hello log failed: {e}")


def _count_calls():
    conn = _connect_db()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM hello_calls;")
            row = cur.fetchone()
            return int(row[0]) if row else 0
    except Exception as e:
        logging.warning(f"Counting calls failed: {e}")
        return None


@app.get("/api/hello")
def hello():
    hostname = os.uname().nodename
    _log_hello(hostname)
    return jsonify({
        "message": "Hello from the backend!",
        "from_pod": hostname
    })


@app.get("/api/hello/stats")
def hello_stats():
    count = _count_calls()
    return jsonify({
        "logged": count is not None,
        "count": count if count is not None else 0
    })


def _fetch_history(limit: int = 20):
    conn = _connect_db()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, called_at, from_pod FROM hello_calls ORDER BY id DESC LIMIT %s;",
                (limit,),
            )
            rows = cur.fetchall()
            # Convert to JSON-serializable dicts
            return [
                {
                    "id": r[0],
                    "called_at": r[1].isoformat() if r[1] is not None else None,
                    "from_pod": r[2],
                }
                for r in rows
            ]
    except Exception as e:
        logging.warning(f"Fetching history failed: {e}")
        return None


@app.get("/api/hello/history")
def hello_history():
    # Optional query param ?limit=NN, capped to 200
    try:
        default_limit = int(os.environ.get("HISTORY_LIMIT_DEFAULT", 20))
    except Exception:
        default_limit = 20
    try:
        from flask import request
        q = request.args.get("limit")
        if q is not None:
            limit = max(1, min(200, int(q)))
        else:
            limit = default_limit
    except Exception:
        limit = default_limit

    rows = _fetch_history(limit)
    if rows is None:
        return jsonify({"logged": False, "rows": []})
    return jsonify({"logged": True, "rows": rows})


@app.get("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)