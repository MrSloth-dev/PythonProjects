import requests
from csv import Error
import sqlite3
import argparse

def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest='command')
  add_parser = subparsers.add_parser('add')
  _ = add_parser.add_argument('--amount', type=float, required=True)
  _ = add_parser.add_argument('--category', type=str, required=True)
  _ = add_parser.add_argument('--description', type=str, default='')

  show_parser = subparsers.add_parser('show')
  group = show_parser.add_mutually_exclusive_group(required=True)
  group = show_parser.add_argument('--total', action='store_true', help='Show totals grouped by category')
  group = show_parser.add_argument('--entries', action='store_true', help='Show each entry and with id for removing if needed')

  remove_parser = subparsers.add_parser('remove')
  return parser.parse_args()

def init_db() -> sqlite3.Connection:
  conn = sqlite3.connect('expenses.db')
  cursor = conn.cursor()
  try:
    _ = cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    date TEXT DEFAULT (datetime('now'))
    );""")
  except sqlite3.Error as e:
    print(f"Database error: {e}")
    conn.rollback()

  conn.commit()
  return conn




if __name__ == '__main__':
  args = parse_args()
  conn = init_db()
  match args.command:
    case 'add':
        print("Hello, world")
