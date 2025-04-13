import sqlite3
import requests
import time

def get_cached_rate(conn: sqlite3.Connection, base: str, target: str)->tuple[float | None, int | None, str | None]:
  cursor = conn.cursor()
  _ = cursor.execute("SELECT value FROM api_metadata WHERE key = 'ttl_seconds'")
  ttl = int(cursor.fetchone()[0])
  _ = cursor.execute("""
      SELECT rate, timestamp
      FROM exchange_rates
      WHERE base_currency = ?
      AND target_currency = ?
      ORDER by timestamp DESC
      LIMIT 1
  """,(base, target))

  if row := cursor.fetchone():
    rate, timestamp = row
    is_fresh = (time.time() - timestamp) < ttl
    return (rate, timestamp, "fresh" if is_fresh else "stale")
  return (None, None, None)

def fetch_live_rate(base:str, target:str) -> float:
  try:
    response = requests.get(
    f"https://api.exchagerate.host/latest?base={base}",
    timeout=5
  )
    response.raise_for_status()
    return response.json()["rates"][target]
  except (requests.RequestException, KeyError) as e:
    raise RuntimeError(f"Failed to fetch live rate: {str(e)}") from e

def cache_rate( conn:sqlite3.Connection, base: str, target: str, rate: float)->None:
  with conn:
    _ = conn.execute("""
        INSERT INTO exchange_rates
        (base_currency, target_currency, rate, timestamp)
        VALUES(?,?,?)
    """,(base, target, rate, int(time.time())))
    _ = conn.execute("""
        UPDATE api_metadata
        SET value = ?
        WHERE key = 'last_updated'
        """, (str(int(time.time()))))
    
