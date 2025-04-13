from get_rates import *
import argparse

def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Currency Coverter",
    epilog="Example: converty.py --from EUR --to USD --amount 100"
  )
  conversion_group = parser.add_argument_group('Conversion')
  conversion_group.add_argument('--from', '-f',
                      dest='base_currency',
                      type=str.upper,
                      required=True,
                      help="Base currency code, use converty.py --code for list")
  conversion_group.add_argument('--to', '-t',
                      dest='target_currency',
                      type=str.upper,
                      required=True,
                      help="Target currency code, use converty.py --code for list")
  conversion_group.add_argument('--amount', '-a',
                      type=float,
                      required=True,
                      help="Amount to convert")
  info_group = parser.add_argument_group('Info')
  info_group.add_argument('--code',
                      action='store_true',
                      help="List available currency codes")

  args = parser.parse_args()
  if args.code:
    return args

  if not all([args.base_currency, args.target_currency, args.amount]):
    parser.error("Missing required arguments for conversion (use --help)")
  if conn:
    valid, msg = validate_currencies(conn, args.base_currency, args.target_currency)
    if not valid:
      parser.error(msg)
  return parser.parse_args()

def validate_currencies(conn: sqlite3.Connection, base: str, target: str)->tuple[bool,str]:
  cursor = conn.cursor()
  cursor.execute("""
    SELECT COUNT(DISTINCT target_currency)
    FROM exchange_rates
    WHERE timestamp >= unixepoch('now', '-7 days')
      AND (base_currency = ? OR target_currency = ?)
      GROUP BY target_currency
  """, (base, target))
  found_currencies = {row[0] for row in cursor.fetchall()}
  errors = []
  if base not in found_currencies:
    errors.append(f"Base currency {base} not in available rates")
  if target not in found_currencies:
    errors.append(f"Target currency {target} not in available rates")
  return (len(errors) == 0, "; ".join(errors))


def init_db(db_path: str = 'exchange_rates.db') -> sqlite3.Connection:
  conn = None
  try:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    with conn:
      cursor = conn.cursor()
    schema = ["""CREATE TABLE IF NOT EXISTS exchange_rates (
    base_currency TEXT NOT NULL CHECK(length(base_currency) = 3),
    target_currency TEXT NOT NULL CHECK(length(target_currency) = 3),
    rate REAL NOT NULL CHECK(rate > 0),
    timestamp INTEGER NOT NULL CHECK(timestamp > 0),
    source TEXT DEFAULT 'API',
    PRIMARY KEY(base_currency, target_currency, timestamp)
    );""",
              """CREATE TABLE IF NOT EXISTS api_metadata (
    key TEXT NOT NULL,
    value TEXT NOT NULL
    );""",
              """INSERT OR IGNORE INTO api_metadata VALUES
    ('last_updated', '0'),
    ('ttl_seconds', '360');
    """,
              """CREATE INDEX IF NOT EXISTS idx_rates_lookup ON exchange_rates
    (base_currency, target_currency, timestamp DESC);
    """,
              """CREATE INDEX IF NOT EXISTS idx_rates_timestamp ON exchange_rates
    (timestamp);
    """
              ]
    for statement in schema:
      _ = cursor.execute(statement)
    if not validate_schema(conn):
      raise RuntimeError(f"Schema validation failed")
    
  except sqlite3.Error as e:
    if conn:
      conn.rollback()
      conn.close()
    raise RuntimeError(f"Database initialization failed: {e}") from e
  conn.commit()
  return conn

def validate_schema(conn: sqlite3.Connection)->bool:
  required_tables = {'exchange_rates', 'api_metadata'}
  cursor = conn.cursor()
  try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}
    if not required_tables.issubset(existing_tables):
      return False
  except sqlite3.Error:
    return False
  return True

def convert_currency(conn: sqlite3.Connection, base_currency: str, target_currency: str, amount: float)->tuple[float, float, str | None]:
  rate, timetamp, cache_status = get_cached_rate(conn, base_currency, target_currency)
  if rate is None:
    try: 
      rate = fetch_live_rate(base_currency, target_currency)
      cache_status = "live"
      cache_rate(conn, base_currency, target_currency, rate)
    except Exception as e:
      raise RuntimeError(f"Failed to get rate: {str(e)}") from e

  converted_amount = amount * rate
  return (converted_amount, rate, cache_status)

  # match args.command:
  #   case 'add':


if __name__ == '__main__':
  conn = None
  try:
    conn = init_db()
    args = parse_args()
    if args.code:
      print("Code list")
    else:
      amount , rate, source  = convert_currency(conn, args.base_currency, args.target_currency, args.amount)
      print(f"Result: {amount:.2f}, (Rate: {rate:.4f}), Source: {source}")
  except Exception as e:
    print(f"Something went wrong: {str(e)}")
  finally:
    if conn:
      conn.close()
