import sqlite3
import argparse
# from datetime import datetime


def init_db() -> sqlite3.Connection:
  conn = sqlite3.connect('expenses.db')
  cursor = conn.cursor()
  _ = cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  amount REAL NOT NULL,
  category TEXT NOT NULL,
  description TEXT,
  date TEXT DEFAULT (datetime('now'))
  );""")
  conn.commit()
  return conn

def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest='command')
  add_parser = subparsers.add_parser('add')
  _ = add_parser.add_argument('--amount', type=float, required=True)
  _ = add_parser.add_argument('--category', type=str, required=True)
  _ = add_parser.add_argument('--description', type=str, default='')

  show_parser = subparsers.add_parser('show')
  group = show_parser.add_mutually_exclusive_group()
  group = show_parser.add_argument('--total', action='store_true', help='Show totals grouped by category')
  group = show_parser.add_argument('--entries', action='store_true', help='Show each entry and with id for removing if needed')

  remove_parser = subparsers.add_parser('remove')
  return parser.parse_args()



def show_entries(conn : sqlite3.Connection):
  cursor = conn.cursor()
  print(f"{'id':<10} {'Category':<10} {'Amount':<10}")
  print("-" * 16)
  _ = cursor.execute("""
  SELECT id, category, amount  FROM expenses
  """)
  for row in cursor.fetchall():
    print(f"{row[0]:<10} {row[1]:<10} {row[2]:<10.2f}")

def show_totals(conn : sqlite3.Connection):
  cursor = conn.cursor()
  print(f"{'id':<10} {'Category':<10} {'Amount':<10}")
  print("-" * 16)
  _ = cursor.execute("""
  SELECT id, category, SUM(amount) as total
  FROM expenses
  GROUP BY category
  """)
  for row in cursor.fetchall():
    print(f"{row[0]:<10} {row[1]:<10} {row[2]:<10.2f}")

def remove_expense(conn: sqlite3.Connection):
  show_entries(conn)
  remove = int(input("Which expense to remove?: "))
  cursor = conn.cursor()
  _ = cursor.execute("SELECT COUNT(*) FROM expenses")
  size : int  = cursor.fetchone()[0]
  if remove > size or remove < 0:
    print("Error index")
    return 
  _ = cursor.execute(" DELETE FROM expenses WHERE id = ?", (remove,))
  conn.commit()

def add_expense(conn: sqlite3.Connection, amount: int, category: str, description: str):
      cursor = conn.cursor()
      _ = cursor.execute("""
        INSERT INTO expenses (amount, category, description)
        VALUES(?, ?, ?)
      """ , (amount, category, description))
      conn.commit()

if __name__ == '__main__':
  args = parse_args()
  conn = init_db()
  match args.command:
    case 'add':
      add_expense(conn, args.amount, args.category, args.description)
    case 'remove':
      remove_expense(conn)
    case 'show':
      if args.total:
        show_totals(conn)
      if args.entries:
        show_entries(conn)
    case 'stats':
      show_totals(conn)
  conn.close()
