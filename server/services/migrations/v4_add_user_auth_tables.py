# server/services/migrations/v4_add_user_auth_tables.py

from . import Migration
import sqlite3

class V4AddUserAuthTables(Migration):
    version = 4
    description = "Add tables for user authentication and API key storage with full user schema"

    def up(self, conn: sqlite3.Connection) -> None:
        # Tabel untuk menyimpan data pengguna dengan skema lengkap
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
        """)

        # Tabel untuk menyimpan kunci API per pengguna
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                providers_config TEXT NOT NULL, -- Menyimpan seluruh konfigurasi provider sebagai JSON
                updated_at TEXT DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_api_keys_user_id ON user_api_keys(user_id)")

    def down(self, conn: sqlite3.Connection) -> None:
        conn.execute("DROP TABLE IF EXISTS user_api_keys")
        conn.execute("DROP TABLE IF EXISTS users")