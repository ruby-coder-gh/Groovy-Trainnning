"""
🗄️ Database Query Tool (Stretch Goal)

Allows the agent to run SQL queries against a local SQLite database.

Useful for demo purposes — the agent can create tables, insert data,
and query information.
"""

import os
import sqlite3
from typing import Optional, List, Dict, Any
from pathlib import Path


# Default database path (relative to project root)
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_data.db")


def _get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def query_database(sql: str, db_path: Optional[str] = None) -> str:
    """
    Execute a SQL query against the local SQLite database.

    Supports SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, etc.

    Args:
        sql: The SQL query to execute
        db_path: Path to SQLite database file (default: agent_data.db in project root)

    Returns:
        Formatted query results or status message
    """
    path = db_path or DEFAULT_DB_PATH

    try:
        conn = _get_connection(path)
        cursor = conn.cursor()
        cursor.execute(sql)

        # Determine if this returns rows
        if sql.strip().upper().startswith("SELECT") or sql.strip().upper().startswith("WITH"):
            rows = cursor.fetchall()
            if not rows:
                conn.close()
                return "✅ Query executed successfully — no rows returned."

            # Get column names
            col_names = [desc[0] for desc in cursor.description]

            # Format as a simple table
            lines = []
            # Header
            lines.append(" | ".join(col_names))
            lines.append("-" * len(lines[0]))

            # Data rows
            for row in rows:
                values = [str(row[col]) if row[col] is not None else "NULL" for col in col_names]
                lines.append(" | ".join(values))

            conn.close()
            return f"✅ {len(rows)} row(s) returned:\n" + "\n".join(lines)
        else:
            # Non-SELECT: commit changes
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            return f"✅ Query OK — {affected} row(s) affected."

    except sqlite3.Error as e:
        return f"❌ SQLite error: {e}"
    except Exception as e:
        return f"❌ Database error: {e}"


def setup_sample_database(db_path: Optional[str] = None):
    """
    Create sample tables and data for the agent to query.
    Run this once to populate the database.
    """
    path = db_path or DEFAULT_DB_PATH

    try:
        conn = _get_connection(path)
        cursor = conn.cursor()

        # Create sample tables
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                price REAL,
                stock INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity INTEGER,
                total REAL,
                status TEXT DEFAULT 'pending',
                order_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                role TEXT DEFAULT 'user',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Seed data (only if empty)
            INSERT OR IGNORE INTO products (name, category, price, stock) VALUES
                ('Laptop Pro', 'Electronics', 1299.99, 25),
                ('Wireless Mouse', 'Electronics', 29.99, 150),
                ('Desk Chair', 'Furniture', 349.99, 10),
                ('Coffee Mug', 'Kitchen', 12.99, 200),
                ('USB-C Hub', 'Electronics', 49.99, 80),
                ('Notebook Set', 'Stationery', 8.99, 500),
                ('Monitor 27"', 'Electronics', 449.99, 15),
                ('Keyboard Mech', 'Electronics', 89.99, 45);

            INSERT OR IGNORE INTO orders (product_id, quantity, total, status) VALUES
                (1, 2, 2599.98, 'shipped'),
                (3, 1, 349.99, 'delivered'),
                (5, 3, 149.97, 'pending'),
                (2, 10, 299.90, 'delivered'),
                (7, 1, 449.99, 'pending'),
                (4, 24, 311.76, 'shipped');

            INSERT OR IGNORE INTO users (name, email, role) VALUES
                ('Alice Smith', 'alice@example.com', 'admin'),
                ('Bob Jones', 'bob@example.com', 'user'),
                ('Charlie Lee', 'charlie@example.com', 'user'),
                ('Diana Ross', 'diana@example.com', 'moderator');
        """)

        conn.commit()
        conn.close()
        print(f"✅ Sample database created at: {path}")
        print("   Tables: products, orders, users")

    except sqlite3.Error as e:
        print(f"❌ Error setting up database: {e}")


# ──────────────────────────────────────────────────────────────
# JSON Schema for tool calling
# ──────────────────────────────────────────────────────────────

SCHEMA = {
    "name": "query_database",
    "description": "Execute SQL queries against a local SQLite database with sample tables: products, orders, users",
    "parameters": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "The SQL query to execute (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, etc.)",
            },
        },
        "required": ["sql"],
    },
}


# ──────────────────────────────────────────────────────────────
# Smoke test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🗄️  Database Tool Test")
    print("-" * 40)

    # Setup sample data
    setup_sample_database()

    # Test queries
    print("\n--- All Products ---")
    print(query_database("SELECT * FROM products"))

    print("\n--- Orders with Product Names ---")
    print(query_database(
        "SELECT o.id, p.name, o.quantity, o.total, o.status "
        "FROM orders o JOIN products p ON o.product_id = p.id"
    ))

    print("\n--- Users ---")
    print(query_database("SELECT name, email, role FROM users"))
