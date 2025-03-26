from ast import arg
from re import A
import sqlite3
import argparse
from datetime import datetime


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
  _ = add_parser.add_argument('--amout', type=float, required=True)
  _ = add_parser.add_argument('--category', type=str, required=True)
  _ = add_parser.add_argument('--description', type=str, default='')
  _ = subparsers.add_parser('stats')
  return parser.parse_args()

def add_expense(conn: sqlite3.Connection, amount: int, category: str, description: str):
      cursor = conn.cursor()
      _ = cursor.execute("""
      INSERT INTO expenses (amount, category, description)
      VALUE(?, ?, ?) """
  , (amount, category, description))
      conn.commit()


def show_stats(conn):
  cursor = conn.cursor()
  _ = cursor.execute("""
  SELECT category, SUM(amount) as total
  FROM expenses
  GROUP BY category
  """)
  for row in cursor.fecthall():
    print(f"{row[0]}: {row[1]:.2f}")



if __name__ == '__main__':
  args = parse_args()
  conn = init_db()
  if (args.command == 'add'):
    add_expense(conn, args.amount, args.category, args.description)
  elif args.command == 'stats':
    show_stats(conn)
  conn.close()


